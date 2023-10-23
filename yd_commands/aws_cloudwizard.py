"""
Configuration and utilities related to AWS account setup.
"""
import json
from os.path import exists
from time import sleep
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from yellowdog_client import PlatformClient

from yd_commands.aws_types import AWSAccessKey, AWSAvailabilityZone, AWSSecurityGroup
from yd_commands.compact_json import CompactJSONEncoder
from yd_commands.create import create_resources
from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import (
    clear_compute_requirement_template_cache,
    clear_compute_source_template_cache,
    find_compute_source_id_by_name,
    get_all_compute_sources,
    get_all_compute_templates,
)
from yd_commands.printing import print_log, print_warning
from yd_commands.remove import remove_resource_by_id

IAM_USER_NAME = "yellowdog-cloudwizard-iam-user"
IAM_POLICY_NAME = "yellowdog-cloudwizard-policy"
EC2_SPOT_SERVICE_LINKED_ROLE_NAME = "AWSServiceRoleForEC2Spot"
MAX_ITEMS = 1000  # Maximum number of items to return from an AWS API call

YD_KEYRING_NAME = "cloudwizard-aws"
YD_CREDENTIAL_NAME = "cloudwizard-aws"
YD_RESOURCE_PREFIX = "cloudwizard-aws"
YD_RESOURCES_FILE = f"{YD_RESOURCE_PREFIX}-yellowdog-resources.json"
YD_INSTANCE_TAG = {"ydtag": "yellowdog-cloudwizard-source"}


AWS_DEFAULT_REGION = "eu-west-2"

AWS_ALL_REGIONS = [
    "af-south-1",
    "ap-east-1",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-northeast-3",
    "ap-south-1",
    "ap-south-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-southeast-3",
    "ap-southeast-3",
    "ap-southeast-4",
    "ca-central-1",
    "eu-central-1",
    "eu-central-2",
    "eu-north-1",
    "eu-south-1",
    "eu-south-2",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "il-central-1",
    "me-central-1",
    "me-south-1",
    "sa-east-1",
    "us-east-1",
    "us-east-2",
    "us-west-2",
]

AWS_YD_IMAGE_REGIONS = [
    "eu-west-1",
    "eu-west-2",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
]

YELLOWDOG_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "EC2:CancelSpotInstanceRequests",
                "EC2:CreateFleet",
                "EC2:CreateLaunchTemplate",
                "EC2:CreatePlacementGroup",
                "EC2:CreateTags",
                "EC2:DeleteFleets",
                "EC2:DeleteLaunchTemplate",
                "EC2:DeletePlacementGroup",
                "EC2:DescribeFleets",
                "EC2:DescribeInstanceTypes",
                "EC2:DescribeInstances",
                "EC2:DescribeLaunchTemplates",
                "EC2:DescribePlacementGroups",
                "EC2:DescribeSpotInstanceRequests",
                "EC2:ModifyFleet",
                "EC2:RebootInstances",
                "EC2:RequestSpotInstances",
                "EC2:RunInstances",
                "EC2:StartInstances",
                "EC2:StopInstances",
                "EC2:TerminateInstances",
                "S3:AbortMultipartUpload",
                "S3:DeleteObject",
                "S3:GetObject",
                "S3:ListBucketMultipartUploads",
                "S3:ListMultipartUploadParts",
                "S3:PutObject",
            ],
            "Resource": "*",
        }
    ],
}


class AWSConfig:
    """
    Class for managing the AWS configuration.
    """

    def __init__(self):
        try:  # Check for valid credentials
            boto3.client("iam", region_name=AWS_DEFAULT_REGION).list_users(MaxItems=1)
        except ClientError as e:
            raise Exception(
                f"Invalid or missing AWS credentials. Did you remember to set/export"
                f" the AWS account credentials?"
            )

        self.availability_zones: List[AWSAvailabilityZone] = []
        self.iam_policy_arn: Optional[str] = None
        self.access_keys: List[AWSAccessKey] = []

    def create_aws_account_assets(self, show_secrets: bool = False):
        """
        Create the required assets in the AWS account, for use with YellowDog.
        """
        iam_client = boto3.client("iam", region_name=AWS_DEFAULT_REGION)
        print_log("Inserting YellowDog-created assets into the AWS account")
        self._load_aws_account_assets(iam_client)
        self._create_iam_user(iam_client)
        self._create_iam_policy(iam_client)
        self._attach_iam_policy(iam_client)
        self._create_access_key(iam_client, show_secrets)
        self._add_service_linked_role_for_ec2_spot(iam_client)

    def remove_aws_account_assets(self):
        """
        Remove the Cloud Wizard assets in the AWS account.
        """
        iam_client = boto3.client("iam", region_name=AWS_DEFAULT_REGION)
        print_log("Removing all YellowDog-created assets in the AWS account")
        self._load_aws_account_assets(iam_client)
        self._delete_access_keys(iam_client)
        self._detach_iam_policy(iam_client)
        self._delete_iam_policy(iam_client)
        self._delete_iam_user(iam_client)
        self._delete_service_linked_role_for_ec2_spot(iam_client)

    def gather_network_information(self):
        """
        Collect network information about the enabled regions and AZs.
        """
        print_log(
            "Gathering network information for all AWS regions containing YellowDog VM"
            " images"
        )
        for region in AWS_YD_IMAGE_REGIONS:
            print_log(f"Gathering network information for region '{region}'")
            ec2_client = boto3.client("ec2", region_name=region)

            # Collect the default security group for the region
            try:
                response = ec2_client.describe_security_groups(Filters=[])
            except ClientError as e:
                if "AuthFailure" in str(e):
                    print_log(
                        f"Region '{region}' is not enabled (AuthFailure when fetching"
                        " security groups)"
                    )
                    continue
                else:
                    raise e

            aws_sec_grp = AWSSecurityGroup(description="", id="")
            for sec_grp in response["SecurityGroups"]:
                description = sec_grp["GroupName"]
                if "default" in description.lower():
                    aws_sec_grp = AWSSecurityGroup(
                        description=description, id=sec_grp["GroupId"]
                    )
                    break
                else:
                    print_warning(f"No default security group found for {region}")

            # Collect the default subnets for each AZ in the region
            response = ec2_client.describe_subnets(
                Filters=[
                    {
                        "Name": "defaultForAz",
                        "Values": ["true"],
                    },
                ]
            )
            for subnet in response["Subnets"]:
                aws_az = AWSAvailabilityZone(
                    region=region,
                    az=subnet["AvailabilityZone"],
                    default_subnet_id=subnet["SubnetId"],
                    default_sec_grp=aws_sec_grp,
                )
                self.availability_zones.append(aws_az)

    def create_yellowdog_resources(
        self, client: PlatformClient, show_secrets: bool = False
    ):
        """
        Create the YellowDog resources and save the resource definition file.
        """

        # Create Keyring
        keyring_resource = self._generate_yd_keyring()
        create_resources([keyring_resource], show_secrets)

        # Create Compute Source Templates
        print_log(
            "Please select the AWS availability zones for which to create YellowDog"
            " Source Templates"
        )
        selected_azs = select(
            client, self.availability_zones, force_interactive=True, override_quiet=True
        )
        source_names_spot: List[str] = []
        source_names_ondemand: List[str] = []
        source_template_resources = []

        for az in selected_azs:
            if az.default_sec_grp.id == "":
                print_warning(
                    f"Cannot create Compute Source Template for {az.az}: no security"
                    " group ID"
                )
                continue
            name = f"{YD_RESOURCE_PREFIX}-{az.az}-ondemand"
            source_template_resources.append(
                self._generate_aws_source_template(az, name=name, spot=False)
            )
            source_names_ondemand.append(name)
            name = f"{YD_RESOURCE_PREFIX}-{az.az}-spot"
            source_template_resources.append(
                self._generate_aws_source_template(az, name=name, spot=True)
            )
            source_names_spot.append(name)

        if len(source_template_resources) == 0:
            print_warning("No Compute Source Templates defined")
            return

        print_log("Creating YellowDog Compute Source Templates")
        create_resources(source_template_resources)

        # Create Compute Requirement Templates
        clear_compute_source_template_cache()
        compute_requirement_template_resources: List[Dict] = [
            self._generate_static_compute_requirement_template(
                client=client,
                source_names=source_names_ondemand,
                spot_or_ondemand="ondemand",
                strategy="Split",
                instance_type="t3a.micro",
            ),
            self._generate_static_compute_requirement_template(
                client=client,
                source_names=source_names_spot,
                spot_or_ondemand="spot",
                strategy="Split",
                instance_type="t3a.micro",
            ),
            self._generate_static_compute_requirement_template(
                client=client,
                source_names=source_names_ondemand,
                spot_or_ondemand="ondemand",
                strategy="Waterfall",
                instance_type="t3a.micro",
            ),
            self._generate_static_compute_requirement_template(
                client=client,
                source_names=source_names_spot,
                spot_or_ondemand="spot",
                strategy="Waterfall",
                instance_type="t3a.micro",
            ),
            self._generate_dynamic_compute_requirement_template(strategy="Waterfall"),
            self._generate_dynamic_compute_requirement_template(strategy="Split"),
        ]

        print_log("Creating YellowDog Compute Requirement Templates")
        create_resources(compute_requirement_template_resources)

        # Create Credential; assume use of the first (probably only) access key
        try:
            if self._wait_until_access_key_is_valid(self.access_keys[0]):
                credential_resource = self._generate_yd_aws_credential(
                    YD_KEYRING_NAME, YD_CREDENTIAL_NAME, self.access_keys[0]
                )
                create_resources([credential_resource])
            else:
                print_warning("AWS Credential not added to YellowDog Keyring")
        except IndexError:
            print_warning("No access keys loaded; can't create Credential")

        # Sequence the Compute Requirement Templates before the Compute Source
        # Templates for subsequent removals.
        # - Omit the Keyring to prevent overwrites if using 'yd-create' with the
        #   resource file.
        # - Omit the Credential for security reasons.
        self._save_resource_list(
            compute_requirement_template_resources + source_template_resources,
        )

    @staticmethod
    def remove_yellowdog_resources(client: PlatformClient):
        """
        Remove a set of resources identified by their prefix/name.
        """
        if confirmed(
            "Remove all Compute Requirement Templates and Compute Source Templates"
            f" with names starting with '{YD_RESOURCE_PREFIX}'?"
        ):
            AWSConfig._remove_yd_templates_by_prefix(client)

        # Keyring is removed separately.
        AWSConfig._remove_keyring(client)

    @staticmethod
    def _create_iam_user(iam_client):
        """
        Create the YellowDog IAM user, if it doesn't already exist.
        """
        try:
            response = iam_client.create_user(UserName=IAM_USER_NAME)
            arn = response["User"]["Arn"]
            print_log(f"Created IAM user '{IAM_USER_NAME}' ({arn})")
        except ClientError as e:
            if "EntityAlreadyExists" in str(e):
                print_warning(
                    f"User '{IAM_USER_NAME}' was not created because it already exists"
                )
            else:
                raise Exception(f"Error creating user '{IAM_USER_NAME}': {e}")

    @staticmethod
    def _delete_iam_user(iam_client):
        """
        Delete the YellowDog IAM user.
        """
        try:
            response = iam_client.list_users(MaxItems=MAX_ITEMS)
            for user in response["Users"]:
                if user["UserName"] == IAM_USER_NAME:
                    break
            else:
                print_log(f"No user '{IAM_USER_NAME}' to delete")
                return
        except ClientError:
            pass

        if not confirmed(f"Delete IAM user '{IAM_USER_NAME}' (if it exists)?"):
            return

        try:
            iam_client.delete_user(UserName=IAM_USER_NAME)
            print_log(f"Deleted IAM user '{IAM_USER_NAME}'")
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                print_log(f"No user '{IAM_USER_NAME}' to delete")
            else:
                raise Exception(f"Failed to delete IAM user '{IAM_USER_NAME}': {e}")

    def _create_iam_policy(self, iam_client):
        """
        Create the YellowDog IAM policy.
        """
        try:
            response = iam_client.create_policy(
                PolicyName=IAM_POLICY_NAME, PolicyDocument=json.dumps(YELLOWDOG_POLICY)
            )
            self.iam_policy_arn = response["Policy"]["Arn"]
            print_log(f"Created IAM Policy '{IAM_POLICY_NAME}' ({self.iam_policy_arn})")
        except ClientError as e:
            if "EntityAlreadyExists" in str(e):
                # If already exists, we need to store its ARN
                response = iam_client.list_policies(
                    Scope="Local",
                )
                for policy in response["Policies"]:
                    if policy["PolicyName"] == IAM_POLICY_NAME:
                        self.iam_policy_arn = policy["Arn"]
                        break
                print_warning(
                    f"IAM policy '{IAM_POLICY_NAME}' was not created because it already"
                    " exists"
                )
            else:
                raise Exception(f"Failed to create IAM policy: {e}")

    def _delete_iam_policy(self, iam_client):
        """
        Delete the YellowDog IAM policy.
        """
        if self.iam_policy_arn is None:
            print_log(f"No IAM policy '{IAM_POLICY_NAME}' to delete")
            return

        if not confirmed(f"Delete IAM policy '{IAM_POLICY_NAME}'?"):
            return

        try:
            iam_client.delete_policy(PolicyArn=self.iam_policy_arn)
            print_log(f"Deleted IAM policy '{IAM_POLICY_NAME}'")
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                print_warning(
                    f"IAM policy '{IAM_POLICY_NAME}' was not deleted because it doesn't"
                    " exist"
                )
            else:
                raise Exception(f"Failed to delete IAM policy '{IAM_POLICY_NAME}': {e}")

    def _attach_iam_policy(self, iam_client):
        """
        Attach the IAM policy to the user.
        """
        if self.iam_policy_arn is None:
            print_log(f"No recorded IAM policy '{IAM_POLICY_NAME}' to attach")
            return

        try:
            # This call appears to be idempotent
            iam_client.attach_user_policy(
                UserName=IAM_USER_NAME, PolicyArn=self.iam_policy_arn
            )
            print_log(
                f"Attached IAM policy '{IAM_POLICY_NAME}' to user '{IAM_USER_NAME}'"
            )
        except ClientError as e:
            raise Exception(
                f"Failed to attach IAM policy '{IAM_POLICY_NAME}' to user"
                f" '{IAM_USER_NAME}': {e}"
            )

    def _detach_iam_policy(self, iam_client):
        """
        Detach the IAM policy from the user.
        """
        if self.iam_policy_arn is None:
            print_log(f"No IAM policy '{IAM_POLICY_NAME}' to detach")
            return

        if not confirmed(
            f"Detach IAM policy '{IAM_POLICY_NAME}' from user '{IAM_USER_NAME}'"
        ):
            return

        try:
            iam_client.detach_user_policy(
                UserName=IAM_USER_NAME, PolicyArn=self.iam_policy_arn
            )
            print_log(
                f"Detached IAM policy '{IAM_POLICY_NAME}' from user '{IAM_USER_NAME}'"
            )
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                print_warning(f"IAM policy '{IAM_POLICY_NAME}' not attached to user")
            else:
                raise Exception(f"Failed to detach IAM policy '{IAM_POLICY_NAME}': {e}")

    def _create_access_key(self, iam_client, show_secrets: bool = False):
        """
        Create an access key for use in a YellowDog Credential:
        """
        if len(self.access_keys) > 0:
            print_warning(f"Access key(s) already exist for user '{IAM_USER_NAME}'")
            if confirmed("Delete existing access key(s) and generate a new key?"):
                self._delete_access_keys(iam_client)
            else:
                print_warning("Secret access keys will not be available")
                return

        try:
            response = iam_client.create_access_key(UserName=IAM_USER_NAME)
            access_key = AWSAccessKey(
                response["AccessKey"]["AccessKeyId"],
                response["AccessKey"]["SecretAccessKey"],
            )
            self.access_keys.append(access_key)
            print_log(
                f"Created AWS_ACCESS_KEY_ID='{access_key.access_key_id}' for user"
                f" '{IAM_USER_NAME}'"
            )
            if show_secrets:
                print_log(
                    f"        AWS_SECRET_ACCESS_KEY={access_key.secret_access_key}"
                )
        except ClientError as e:
            raise Exception(
                f"Error creating access key for user '{IAM_USER_NAME}': {e}"
            )

    def _delete_access_keys(self, iam_client):
        """
        Delete the access key(s).
        """
        if len(self.access_keys) == 0:
            print_log(f"No access keys to delete for user '{IAM_USER_NAME}'")
            return

        for access_key in self.access_keys:
            if not confirmed(
                f"Delete access key '{access_key.access_key_id}' from user"
                f" '{IAM_USER_NAME}'?"
            ):
                return
            try:
                iam_client.delete_access_key(
                    UserName=IAM_USER_NAME, AccessKeyId=access_key.access_key_id
                )
                print_log(f"Deleted access key '{access_key.access_key_id}'")
            except ClientError as e:
                if "NoSuchEntity" in str(e):
                    print_warning(
                        f"Access key '{access_key.access_key_id}' does not exist"
                    )
                else:
                    raise Exception(
                        f"Unable to delete access key '{access_key.access_key_id}': {e}"
                    )

        self.access_keys.clear()

    @staticmethod
    def _add_service_linked_role_for_ec2_spot(iam_client):
        """
        Add the service linked role for EC2 spot to the account.
        """
        try:
            iam_client.create_service_linked_role(
                AWSServiceName="spot.amazonaws.com",
                Description=EC2_SPOT_SERVICE_LINKED_ROLE_NAME,
            )
            print_log(
                f"Added service linked role '{EC2_SPOT_SERVICE_LINKED_ROLE_NAME}' to"
                " the AWS account"
            )
        except ClientError as e:
            if "has been taken" in str(e):
                print_warning(
                    f"Service role name '{EC2_SPOT_SERVICE_LINKED_ROLE_NAME}' has"
                    " already been taken in this account; service role not added"
                )
            else:
                raise Exception(
                    "Unable to add service linked role"
                    f" '{EC2_SPOT_SERVICE_LINKED_ROLE_NAME}' to AWS account: {e}"
                )

    @staticmethod
    def _delete_service_linked_role_for_ec2_spot(iam_client):
        """
        Delete the service linked role for EC2 spot from the account.
        """
        if not confirmed(
            f"Delete service linked role '{EC2_SPOT_SERVICE_LINKED_ROLE_NAME}' from the"
            " AWS account (if present)?"
        ):
            return

        try:
            iam_client.delete_service_linked_role(
                RoleName=EC2_SPOT_SERVICE_LINKED_ROLE_NAME
            )
            print_log(
                f"Deleted service linked role '{EC2_SPOT_SERVICE_LINKED_ROLE_NAME}'"
                " from AWS account"
            )
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                print_log(
                    f"No service linked role '{EC2_SPOT_SERVICE_LINKED_ROLE_NAME}' to"
                    " delete"
                )
            else:
                raise Exception(
                    "Unable to delete service linked role"
                    f" '{EC2_SPOT_SERVICE_LINKED_ROLE_NAME}' from AWS account: {e}"
                )

    def _load_aws_account_assets(self, iam_client):
        """
        Load the required AWS IDs that are non-constants.
        """
        print_log("Querying AWS account for existing assets")

        # Get the IAM Policy ARN
        try:
            response = iam_client.list_policies(
                Scope="Local",
                MaxItems=MAX_ITEMS,
            )
            for policy in response["Policies"]:
                if policy["PolicyName"] == IAM_POLICY_NAME:
                    self.iam_policy_arn = policy["Arn"]
                    break
        except ClientError as e:
            raise Exception(f"Unable to list IAM policies: {e}")

        # Get the Access Key ID(s)
        try:
            response = iam_client.list_access_keys(UserName=IAM_USER_NAME)
            access_keys = response.get("AccessKeyMetadata", [])
            for access_key in access_keys:
                if access_key["UserName"] == IAM_USER_NAME:
                    self.access_keys.append(AWSAccessKey(access_key["AccessKeyId"]))
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                # print_warning(
                #     f"Cannot list access keys: user '{IAM_USER_NAME}' does not exist"
                # )
                pass  # Placeholder for now
            else:
                raise Exception(f"Unable to list access keys: {e}")

    @staticmethod
    def _remove_yd_templates_by_prefix(client):
        """
        Remove YellowDog resources using their name prefix.
        """
        print_log(
            "Removing all Compute Requirement Templates with names starting with"
            f" '{YD_RESOURCE_PREFIX}'"
        )
        clear_compute_requirement_template_cache()
        for compute_requirement_template_summary in get_all_compute_templates(client):
            if compute_requirement_template_summary.name.startswith(YD_RESOURCE_PREFIX):
                try:
                    remove_resource_by_id(compute_requirement_template_summary.id)
                except Exception as e:
                    print_warning(f"Unable to remove Compute Requirement Template: {e}")

        print_log(
            "Removing all Compute Source Templates with names starting with"
            f" '{YD_RESOURCE_PREFIX}'"
        )
        clear_compute_source_template_cache()
        for compute_source_template_summary in get_all_compute_sources(client):
            if compute_source_template_summary.name.startswith(YD_RESOURCE_PREFIX):
                try:
                    remove_resource_by_id(compute_source_template_summary.id)
                except Exception as e:
                    print_warning(f"Unable to remove Compute Source Template: {e}")

    @staticmethod
    def _remove_keyring(client: PlatformClient):
        """
        Remove the Keyring by its name.
        """
        if confirmed(f"Remove Keyring '{YD_KEYRING_NAME}'?"):
            try:
                client.keyring_client.delete_keyring_by_name(YD_KEYRING_NAME)
                print_log(f"Removed Keyring '{YD_KEYRING_NAME}'")
            except Exception as e:
                if "NotFoundException" in str(e):
                    print_log(f"No Keyring '{YD_KEYRING_NAME}' to remove")

    @staticmethod
    def _save_resource_list(resource_list: List[Dict]) -> bool:
        """
        Save the list of generated resources. Returns True for success.
        """
        if exists(YD_RESOURCES_FILE):
            if not confirmed(
                f"YellowDog resources definition file '{YD_RESOURCES_FILE}' already"
                " exists; OK to overwrite?"
            ):
                print_log("Not overwriting YellowDog resources definition file")
                return False

        try:
            with open(YD_RESOURCES_FILE, "w") as f:
                json.dump(resource_list, f, indent=2, cls=CompactJSONEncoder)
                f.write("\n")
                print_log(
                    f"Saved YellowDog resource definitions to '{YD_RESOURCES_FILE}'"
                )
                return True
        except Exception as e:
            raise Exception(
                "Unable to save YellowDog resources definition file"
                f" '{YD_RESOURCES_FILE}'"
            )

    @staticmethod
    def _generate_aws_source_template(
        az: AWSAvailabilityZone, name: str, spot: bool
    ) -> Dict:
        """
        Create a minimal populated YellowDog Source Template resource definition.
        """
        spot_str = "spot" if spot is True else "ondemand"
        return {
            "resource": "ComputeSourceTemplate",
            "description": (
                f"AWS {az.region} {spot_str} Source Template automatically created by"
                " YellowDog Cloud Wizard"
            ),
            "source": {
                "assignPublicIp": True,
                "availabilityZone": f"{az.az}",
                "credential": YD_KEYRING_NAME + "/" + YD_CREDENTIAL_NAME,
                "imageId": "*",
                "instanceTags": YD_INSTANCE_TAG,
                "instanceType": "*",
                "limit": 0,
                "name": name,
                "region": f"{az.region}",
                "securityGroupId": f"{az.default_sec_grp.id}",
                "specifyMinimum": False,
                "spot": spot,
                "subnetId": f"{az.default_subnet_id}",
                "type": "co.yellowdog.platform.model.AwsInstancesComputeSource",
            },
        }

    @staticmethod
    def _generate_static_compute_requirement_template(
        client: PlatformClient,
        source_names: List[str],
        spot_or_ondemand: str,
        strategy: str,
        instance_type: str,
    ) -> Dict:
        """
        Generate a static compute requirement resource definition
        from a list of source names. Strategy can be one of:
        - SingleSource
        - Split
        - Waterfall
        Instance type must be a valid AWS instance type.
        """
        source_ids = []
        for source_name in source_names:
            source_id = find_compute_source_id_by_name(client, source_name)
            if source_id is None:
                raise Exception(
                    "Unable to find a Compute Source Template ID for source"
                    f" '{source_name}'"
                )
            source_ids.append(source_id)

        return {
            "resource": "ComputeRequirementTemplate",
            "name": (
                f"{YD_RESOURCE_PREFIX}-{strategy.lower()}-{spot_or_ondemand}-{instance_type.lower().replace('.', '')}"
            ),
            "description": (
                "Compute Requirement Template automatically created by YellowDog Cloud"
                " Wizard"
            ),
            "strategyType": f"co.yellowdog.platform.model.{strategy}ProvisionStrategy",
            "type": "co.yellowdog.platform.model.ComputeRequirementStaticTemplate",
            "sources": [
                {"instanceType": instance_type, "sourceTemplateId": id}
                for id in source_ids
            ],
        }

    @staticmethod
    def _generate_dynamic_compute_requirement_template(
        strategy: str,
    ) -> Dict:
        """
        Generate a dynamic compute requirement resource definition.
        Strategy can be one of:
        - SingleSource
        - Split
        - Waterfall
        """
        return {
            "resource": "ComputeRequirementTemplate",
            "name": f"{YD_RESOURCE_PREFIX}-dynamic-{strategy.lower()}-lowestcost",
            "constraints": [
                {
                    "attribute": "yd.ram",
                    "max": 4096,
                    "min": 4,
                    "type": "co.yellowdog.platform.model.NumericAttributeConstraint",
                },
                {
                    "anyOf": ["AWS"],
                    "attribute": "source.provider",
                    "type": "co.yellowdog.platform.model.StringAttributeConstraint",
                },
            ],
            "preferences": [
                {
                    "attribute": "yd.cost",
                    "rankOrder": "PREFER_LOWER",
                    "type": "co.yellowdog.platform.model.NumericAttributePreference",
                    "weight": 1,
                }
            ],
            "maximumSourceCount": 5,
            "minimumSourceCount": 1,
            "strategyType": f"co.yellowdog.platform.model.{strategy}ProvisionStrategy",
            "type": "co.yellowdog.platform.model.ComputeRequirementDynamicTemplate",
        }

    @staticmethod
    def _generate_yd_keyring() -> Dict:
        """
        Generate a YellowDog keyring resource definition.
        """
        return {
            "resource": "Keyring",
            "description": "Keyring created automatically by YellowDog Cloud Wizard",
            "name": YD_KEYRING_NAME,
        }

    @staticmethod
    def _generate_yd_aws_credential(
        keyring_name: str, credential_name: str, access_key: AWSAccessKey
    ) -> Dict:
        """
        Generate an AWS Credential resource definition.
        """
        return {
            "resource": "Credential",
            "keyringName": keyring_name,
            "credential": {
                "accessKeyId": access_key.access_key_id,
                "description": (
                    "AWS credential automatically created by YellowDog Cloud Wizard"
                ),
                "name": credential_name,
                "secretAccessKey": access_key.secret_access_key,
                "type": "co.yellowdog.platform.account.credentials.AwsCredential",
            },
        }

    @staticmethod
    def _wait_until_access_key_is_valid(
        access_key: AWSAccessKey, retry_interval_seconds: int = 5, max_retries: int = 5
    ) -> bool:
        """
        Wait until an access key is valid for use with EC2.
        """
        client = boto3.client(
            "ec2",
            region_name=AWS_DEFAULT_REGION,
            aws_access_key_id=access_key.access_key_id,
            aws_secret_access_key=access_key.secret_access_key,
        )

        for index in range(max_retries):
            try:
                client.describe_instances(
                    DryRun=True,
                )
            except ClientError as e:
                if "DryRunOperation" in str(e):
                    print_log(f"Validated AWS access key '{access_key.access_key_id}'")
                    return True
                elif "AuthFailure" in str(e):
                    print_log(
                        f"Waiting {retry_interval_seconds}s for AWS access key to"
                        f" become valid (attempt {index + 1} of {max_retries}) ..."
                    )
                    sleep(retry_interval_seconds)
                    continue

        print_warning(f"Unable to validate AWS access key '{access_key.access_key_id}'")
        return False
