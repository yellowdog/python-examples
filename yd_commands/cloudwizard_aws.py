"""
Configuration and utilities related to AWS account setup.
"""

import json
from time import sleep
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from yellowdog_client import PlatformClient

from yd_commands.cloudwizard_aws_types import (
    AWSAccessKey,
    AWSAvailabilityZone,
    AWSSecurityGroup,
    AWSUser,
)
from yd_commands.cloudwizard_common import CommonCloudConfig
from yd_commands.create import create_resources
from yd_commands.interactive import confirmed, select
from yd_commands.printing import print_error, print_log, print_warning
from yd_commands.remove import remove_resources
from yd_commands.settings import RN_SOURCE_TEMPLATE, RN_STORAGE_CONFIGURATION

IAM_USER_NAME = "yellowdog-cloudwizard-user"
IAM_POLICY_NAME = "yellowdog-cloudwizard-policy"
S3_BUCKET_NAME_PREFIX = "yellowdog-cloudwizard"
EC2_SPOT_SERVICE_LINKED_ROLE_NAME = "AWSServiceRoleForEC2Spot"
MAX_ITEMS = 1000  # Maximum number of items to return from an AWS API call

YD_KEYRING_NAME = "cloudwizard-aws"
YD_CREDENTIAL_NAME = "cloudwizard-aws"
YD_RESOURCE_PREFIX = "cloudwizard-aws"
YD_RESOURCES_FILE = f"{YD_RESOURCE_PREFIX}-yellowdog-resources.json"
YD_INSTANCE_TAG = {"yd-cloudwizard": "yellowdog-cloudwizard-source"}
YD_NAMESPACE = "cloudwizard-aws"
YD_DEFAULT_INSTANCE_TYPE = "{{instance_type:=t3a.micro}}"

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
                "EC2:DescribeSecurityGroups",
                "EC2:DescribeSubnets",
                "EC2:ModifyFleet",
                "EC2:RebootInstances",
                "EC2:RunInstances",
                "EC2:StartInstances",
                "EC2:StopInstances",
                "EC2:TerminateInstances",
                "S3:AbortMultipartUpload",
                "S3:CreateBucket",
                "S3:DeleteBucket",
                "S3:DeleteObject",
                "S3:GetObject",
                "S3:ListBucketMultipartUploads",
                "S3:ListMultipartUploadParts",
                "S3:ListObjects",
                "S3:PutBucketPolicy",
                "S3:PutObject",
            ],
            "Resource": "*",
        }
    ],
}


class AWSConfig(CommonCloudConfig):
    """
    Class for managing the AWS configuration.
    """

    def __init__(
        self,
        client: PlatformClient,
        region_name: Optional[str],
        show_secrets: bool = False,
        instance_type: Optional[str] = None,
    ):
        """
        Set up AWS config details.
        """
        super().__init__(client=client, cloud_provider="AWS")
        try:  # Check for valid credentials
            boto3.client("iam").list_users(MaxItems=1)
        except ClientError as e:
            raise Exception(
                f"Invalid or missing AWS credentials. Did you remember to set/export"
                f" the AWS account credentials?"
            )

        # Establish the region to use (for the S3 bucket, primarily)
        if region_name is None:  # Use the default region from the SDK
            self.region_name = boto3.client("s3").meta.region_name
        elif region_name.lower() in AWS_ALL_REGIONS:
            self.region_name = region_name.lower()
        else:
            raise Exception(f"Invalid AWS region name '{region_name}'")

        self._show_secrets = show_secrets
        self._instance_type = (
            YD_DEFAULT_INSTANCE_TYPE if instance_type is None else instance_type
        )
        self._availability_zones: List[AWSAvailabilityZone] = []
        self._iam_policy_arn: Optional[str] = None
        self._access_keys: List[AWSAccessKey] = []
        self._aws_user: Optional[AWSUser] = None

    def setup(self):
        """
        Set up all AWS and YellowDog assets
        """
        self._load_aws_resources()
        self._create_aws_resources()
        self._gather_aws_network_information()
        self._create_yellowdog_resources()

    def teardown(self):
        """
        Remove all AWS and YellowDog assets
        """
        self._load_aws_resources()
        self._remove_yellowdog_resources()
        self._remove_aws_resources()

    def set_ssh_ingress_rule(self, operation: str, selected_region: str = None):
        """
        Add or remove SSH ingress for all relevant security groups.
        A list of regions can be supplied as an argument.
        The 'operation' argument must be 'add-ssh' or 'remove-ssh'.
        """
        ssh_ipv4_ingress_rule = [
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": f"0.0.0.0/0"}],
            }
        ]
        for region in (
            AWS_YD_IMAGE_REGIONS if selected_region is None else [selected_region]
        ):
            ec2_client = boto3.client("ec2", region_name=region)
            # Collect the default security group for the region
            try:
                response = ec2_client.describe_security_groups(Filters=[])
            except ClientError as e:
                if "AuthFailure" in str(e):
                    pass
                else:
                    print_error(
                        f"Cannot retrieve security groups for region '{region}': {e}"
                    )
                continue

            for sec_grp in response["SecurityGroups"]:
                name = sec_grp["GroupName"]
                if "default" in name.lower():
                    aws_sec_grp = AWSSecurityGroup(name=name, id=sec_grp["GroupId"])
                    if operation == "add-ssh":
                        AWSConfig._add_security_group_ingress_rule(
                            ec2_client, aws_sec_grp, ssh_ipv4_ingress_rule, "SSH"
                        )
                    elif operation == "remove-ssh":
                        AWSConfig._remove_security_group_ingress_rule(
                            ec2_client, aws_sec_grp, ssh_ipv4_ingress_rule, "SSH"
                        )
                    break

    def _create_aws_resources(self):
        """
        Create the required assets in the AWS account, for use with YellowDog.
        """
        print_log("Inserting YellowDog-created assets into the AWS account")
        iam_client = boto3.client("iam", region_name=self.region_name)
        self._create_iam_user(iam_client)
        self._create_iam_policy(iam_client)
        self._attach_iam_policy(iam_client)
        self._create_access_key(iam_client)
        self._add_service_linked_role_for_ec2_spot(iam_client)
        self._create_s3_bucket()

    def _load_aws_resources(self):
        """
        Load the required AWS IDs that are non-constants.
        """
        print_log("Querying AWS account for existing assets")
        iam_client = boto3.client("iam", region_name=self.region_name)

        # Get the IAM Policy ARN
        try:
            response = iam_client.list_policies(
                Scope="Local",
                MaxItems=MAX_ITEMS,
            )
            for policy in response["Policies"]:
                if policy["PolicyName"] == IAM_POLICY_NAME:
                    self._iam_policy_arn = policy["Arn"]
                    break
        except ClientError as e:
            print_error(f"Unable to list IAM policies: {e}")

        # Get the Access Key ID(s)
        try:
            response = iam_client.list_access_keys(UserName=IAM_USER_NAME)
            access_keys = response.get("AccessKeyMetadata", [])
            for access_key in access_keys:
                if access_key["UserName"] == IAM_USER_NAME:
                    self._access_keys.append(AWSAccessKey(access_key["AccessKeyId"]))
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                pass
            else:
                print_error(f"Unable to list access keys: {e}")

        # Get the IAM user details
        try:
            response = iam_client.get_user(UserName=IAM_USER_NAME)
            self._aws_user = AWSUser(
                arn=response["User"]["Arn"], user_id=response["User"]["UserId"]
            )
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                pass
            else:
                print_error(f"Unable to get details of user '{IAM_USER_NAME}': {e}")

    def _remove_aws_resources(self):
        """
        Remove the Cloud Wizard assets in the AWS account.
        """
        print_log("Removing all YellowDog-created assets in the AWS account")
        iam_client = boto3.client("iam", region_name=self.region_name)
        self._delete_s3_bucket()
        self._delete_access_keys(iam_client)
        self._detach_iam_policy(iam_client)
        self._delete_iam_policy(iam_client)
        self._delete_iam_user(iam_client)
        self._delete_service_linked_role_for_ec2_spot(iam_client)

    def _create_yellowdog_resources(self):
        """
        Create the YellowDog resources and save the resource definition file.
        """

        print_log("Creating resources in the YellowDog account")

        # Select Compute Source Templates
        print_log(
            "Please select the AWS availability zones for which to create YellowDog"
            " Compute Source Templates"
        )
        selected_azs = select(
            self._client,
            self._availability_zones,
            force_interactive=True,
            override_quiet=True,
        )

        for az in selected_azs:
            if az.default_sec_grp.id == "":
                print_warning(
                    f"Cannot create Compute Source Template for {az.az}: no security"
                    " group ID"
                )
                continue
            name = f"{YD_RESOURCE_PREFIX}-{az.az}-ondemand"
            self._source_template_resources.append(
                self._generate_aws_compute_source_template(az, name=name, spot=False)
            )
            self._source_names_ondemand.append(name)
            name = f"{YD_RESOURCE_PREFIX}-{az.az}-spot"
            self._source_template_resources.append(
                self._generate_aws_compute_source_template(az, name=name, spot=True)
            )
            self._source_names_spot.append(name)

        if len(self._source_template_resources) == 0:
            print_warning("No Compute Source Templates defined")
            return

        # Create Compute Source Templates
        print_log("Creating YellowDog Compute Source Templates")
        create_resources(self._source_template_resources)

        # Create Compute Requirement Templates
        self._create_compute_requirement_templates(resource_prefix=YD_RESOURCE_PREFIX)

        # Create Keyring and remember the Keyring password
        self._create_keyring(keyring_name=YD_KEYRING_NAME)

        # Create Credential; assume use of the first (probably only) access key
        try:
            if self._wait_until_access_key_is_valid_for_ec2(
                access_key=self._access_keys[0]
            ):
                credential_resource = self._generate_yd_aws_credential(
                    YD_KEYRING_NAME, YD_CREDENTIAL_NAME, self._access_keys[0]
                )
                create_resources([credential_resource])
            else:
                print_warning("AWS Credential not added to YellowDog Keyring")
        except IndexError:
            print_error("No access keys loaded; can't create Credential")

        # Create namespace configuration (Keyring/Credential creation must come first)
        print_log(
            "Creating YellowDog Namespace Configuration"
            f" 'S3:{self._get_s3_bucket_name()}' -> '{YD_NAMESPACE}'"
        )
        create_resources(
            [
                self._generate_yd_namespace_configuration(
                    namespace=YD_NAMESPACE, s3_bucket_name=self._get_s3_bucket_name()
                )
            ]
        )

        # Sequence the Compute Requirement Templates before the Compute Source
        # Templates for subsequent removals.
        # - Omit the Keyring to prevent overwrites if using 'yd-create' with the
        #   resource file.
        # - Omit the Credential for security reasons.
        self._save_resource_list(
            self._requirement_template_resources + self._source_template_resources,
            YD_RESOURCES_FILE,
        )

        # Always show Keyring details
        self._print_keyring_details()

    def _remove_yellowdog_resources(self):
        """
        Remove a set of resources identified by their prefix/name.
        """
        self._remove_yd_templates_by_prefix(
            client=self._client, name_prefix=YD_RESOURCE_PREFIX
        )

        # Keyring is removed separately.
        self._remove_keyring(keyring_name=YD_KEYRING_NAME)

        # Remove the Namespace Configuration
        remove_resources(
            [
                self._generate_yd_namespace_configuration(
                    YD_NAMESPACE, self._get_s3_bucket_name()
                )
            ]
        )

    def _gather_aws_network_information(self):
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
                    raise Exception(f"Unable to list security groups: {e}")

            aws_sec_grp = AWSSecurityGroup(name="", id="")
            for sec_grp in response["SecurityGroups"]:
                name = sec_grp["GroupName"]
                if "default" in name.lower():
                    aws_sec_grp = AWSSecurityGroup(name=name, id=sec_grp["GroupId"])
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
                self._availability_zones.append(aws_az)

    def _create_iam_user(self, iam_client):
        """
        Create the YellowDog IAM user, if it doesn't already exist.
        """
        try:
            response = iam_client.create_user(UserName=IAM_USER_NAME)
            arn = response["User"]["Arn"]
            user_id = response["User"]["UserId"]
            print_log(f"Created IAM user '{IAM_USER_NAME}' ({arn})")

        except ClientError as e:
            if "EntityAlreadyExists" in str(e):
                print_warning(
                    f"User '{IAM_USER_NAME}' was not created because it already exists"
                )
                try:
                    response = iam_client.get_user(UserName=IAM_USER_NAME)
                    arn = response["User"]["Arn"]
                    user_id = response["User"]["UserId"]
                except ClientError as e:
                    print_error(f"Unable to get user details for {IAM_USER_NAME}: {e}")
                    return
            else:
                print_error(f"Error creating user '{IAM_USER_NAME}': {e}")
                return

        self._aws_user = AWSUser(arn=arn, user_id=user_id)

    @staticmethod
    def _delete_iam_user(iam_client):
        """
        Delete the YellowDog IAM user.
        """

        if not confirmed(f"Delete IAM user '{IAM_USER_NAME}' (if it exists)?"):
            return

        try:
            iam_client.delete_user(UserName=IAM_USER_NAME)
            print_log(f"Deleted IAM user '{IAM_USER_NAME}'")
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                print_warning(f"No user '{IAM_USER_NAME}' to delete")
            else:
                print_error(f"Failed to delete IAM user '{IAM_USER_NAME}': {e}")

    def _create_iam_policy(self, iam_client):
        """
        Create the YellowDog IAM policy.
        """
        try:
            response = iam_client.create_policy(
                PolicyName=IAM_POLICY_NAME, PolicyDocument=json.dumps(YELLOWDOG_POLICY)
            )
            self._iam_policy_arn = response["Policy"]["Arn"]
            print_log(
                f"Created IAM Policy '{IAM_POLICY_NAME}' ({self._iam_policy_arn})"
            )
        except ClientError as e:
            if "EntityAlreadyExists" in str(e):
                # If already exists, we need to store its ARN
                response = iam_client.list_policies(
                    Scope="Local",
                )
                for policy in response["Policies"]:
                    if policy["PolicyName"] == IAM_POLICY_NAME:
                        self._iam_policy_arn = policy["Arn"]
                        break
                print_warning(
                    f"IAM policy '{IAM_POLICY_NAME}' was not created because it already"
                    " exists"
                )
            else:
                print_error(f"Failed to create IAM policy: {e}")

    def _delete_iam_policy(self, iam_client):
        """
        Delete the YellowDog IAM policy.
        """
        if self._iam_policy_arn is None:
            print_warning(f"No IAM policy '{IAM_POLICY_NAME}' to delete")
            return

        if not confirmed(f"Delete IAM policy '{IAM_POLICY_NAME}'?"):
            return

        try:
            iam_client.delete_policy(PolicyArn=self._iam_policy_arn)
            print_log(f"Deleted IAM policy '{IAM_POLICY_NAME}'")
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                print_warning(
                    f"IAM policy '{IAM_POLICY_NAME}' was not deleted because it doesn't"
                    " exist"
                )
            else:
                print_error(f"Failed to delete IAM policy '{IAM_POLICY_NAME}': {e}")

    def _attach_iam_policy(self, iam_client):
        """
        Attach the IAM policy to the user.
        """
        if self._iam_policy_arn is None:
            print_warning(f"No recorded IAM policy '{IAM_POLICY_NAME}' to attach")
            return

        try:
            # This call appears to be idempotent
            iam_client.attach_user_policy(
                UserName=IAM_USER_NAME, PolicyArn=self._iam_policy_arn
            )
            print_log(
                f"Attached IAM policy '{IAM_POLICY_NAME}' to user '{IAM_USER_NAME}'"
            )
        except ClientError as e:
            print_error(
                f"Failed to attach IAM policy '{IAM_POLICY_NAME}' to user"
                f" '{IAM_USER_NAME}': {e}"
            )

    def _detach_iam_policy(self, iam_client):
        """
        Detach the IAM policy from the user.
        """
        if self._iam_policy_arn is None:
            print_warning(f"No IAM policy '{IAM_POLICY_NAME}' to detach")
            return

        if not confirmed(
            f"Detach IAM policy '{IAM_POLICY_NAME}' from user '{IAM_USER_NAME}'"
        ):
            return

        try:
            iam_client.detach_user_policy(
                UserName=IAM_USER_NAME, PolicyArn=self._iam_policy_arn
            )
            print_log(
                f"Detached IAM policy '{IAM_POLICY_NAME}' from user '{IAM_USER_NAME}'"
            )
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                print_warning(f"IAM policy '{IAM_POLICY_NAME}' not attached to user")
            else:
                print_error(f"Failed to detach IAM policy '{IAM_POLICY_NAME}': {e}")

    def _create_access_key(self, iam_client):
        """
        Create an access key for use in a YellowDog Credential:
        """
        if len(self._access_keys) > 0:
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
            self._access_keys.append(access_key)
            print_log(
                f"Created AWS_ACCESS_KEY_ID='{access_key.access_key_id}' for user"
                f" '{IAM_USER_NAME}'"
            )
            if self._show_secrets:
                print_log(
                    f"        AWS_SECRET_ACCESS_KEY='{access_key.secret_access_key}'"
                )
        except ClientError as e:
            print_error(f"Error creating access key for user '{IAM_USER_NAME}': {e}")

    def _delete_access_keys(self, iam_client):
        """
        Delete the access key(s).
        """
        if len(self._access_keys) == 0:
            print_warning(f"No access keys to delete for user '{IAM_USER_NAME}'")
            return

        for access_key in self._access_keys:
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
                    print_error(
                        f"Unable to delete access key '{access_key.access_key_id}': {e}"
                    )

        self._access_keys.clear()

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
                print_error(
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
                print_warning(
                    f"No service linked role '{EC2_SPOT_SERVICE_LINKED_ROLE_NAME}' to"
                    " delete"
                )
            else:
                print_error(
                    "Unable to delete service linked role"
                    f" '{EC2_SPOT_SERVICE_LINKED_ROLE_NAME}' from AWS account: {e}"
                )

    def _create_s3_bucket(self):
        """
        Create an S3 bucket for use in namespace to object store mapping.
        """
        s3_client = boto3.client(
            "s3",
            region_name=self.region_name,
        )

        s3_bucket_name = self._get_s3_bucket_name()

        # Create bucket
        try:
            # Strange quirk of AWS; can't use the default region 'us-east-1'
            # as the location constraint ...
            if self.region_name != "us-east-1":
                s3_client.create_bucket(
                    Bucket=s3_bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": self.region_name},
                )
            else:
                s3_client.create_bucket(Bucket=s3_bucket_name)
            print_log(
                f"Created S3 bucket '{s3_bucket_name}' in region '{self.region_name}'"
            )
        except ClientError as e:
            if "BucketAlreadyOwnedByYou" in str(e):
                print_warning("Bucket already exists and is owned by this account")
            else:
                print_error(
                    f"Unable to create S3 bucket '{s3_bucket_name}' in region"
                    f" '{self.region_name}': {e}"
                )

        # Attach policy
        retry_interval = 5
        max_retries = 10
        for index in range(max_retries):
            try:
                s3_client.put_bucket_policy(
                    Bucket=s3_bucket_name,
                    Policy=self._generate_s3_bucket_policy(),
                )
                print_log(f"Attached policy to S3 bucket '{s3_bucket_name}'")
                return
            except ClientError as e:
                if "MalformedPolicy" in str(e):
                    print_log(
                        f"Waiting {retry_interval}s for S3 bucket to be ready for"
                        f" policy attachment (Attempt {index + 1} of"
                        f" {max_retries}) ..."
                    )
                    sleep(retry_interval)
                else:
                    print_error(f"Unable to attach policy to '{s3_bucket_name}': {e}")
                    return

    @staticmethod
    def _delete_all_s3_objects(s3_client, s3_bucket_name: str):
        """
        Delete all objects in the S3 bucket.
        """
        if not confirmed(f"Delete all objects in S3 bucket '{s3_bucket_name}'?"):
            return

        try:
            paginator = s3_client.get_paginator("list_objects")
            for page in paginator.paginate(
                Bucket=s3_bucket_name, PaginationConfig={"MaxItems": MAX_ITEMS}
            ):
                objects_to_delete = [
                    {"Key": obj["Key"]} for obj in page.get("Contents", [])
                ]
                if len(objects_to_delete) > 0:
                    s3_client.delete_objects(
                        Bucket=s3_bucket_name, Delete={"Objects": objects_to_delete}
                    )
                    print_log(
                        f"Deleted {len(objects_to_delete)} object(s) in S3 bucket"
                        f" '{s3_bucket_name}'"
                    )
                else:
                    print_log(f"No objects to delete in S3 bucket '{s3_bucket_name}'")

        except ClientError as e:
            if "NoSuchBucket" in str(e):
                print_warning(
                    f"No S3 bucket '{s3_bucket_name}' from which to delete objects"
                )
            else:
                print_error(
                    "Unable to list/delete objects in S3 bucket"
                    f" '{s3_bucket_name}': {e}"
                )

    def _delete_s3_bucket(self):
        """
        Delete the S3 bucket.
        """
        s3_client = boto3.client("s3", region_name=self.region_name)
        s3_bucket_name = self._get_s3_bucket_name()

        if s3_bucket_name == "":
            print_warning("No S3 bucket to remove")
            return

        # The bucket must first be empty
        AWSConfig._delete_all_s3_objects(s3_client, s3_bucket_name)

        if not confirmed(f"Delete S3 bucket '{s3_bucket_name}'?"):
            return
        try:
            s3_client.delete_bucket(Bucket=s3_bucket_name)
            print_log(f"Deleted S3 bucket '{s3_bucket_name}'")
        except ClientError as e:
            if "NoSuchBucket" in str(e):
                print_warning(f"No S3 bucket '{s3_bucket_name}' to delete")
            else:
                print_error(f"Unable to delete S3 bucket '{s3_bucket_name}': {e}")

    @staticmethod
    def _add_security_group_ingress_rule(
        ec2_client, security_group: AWSSecurityGroup, ingress_rule: List, rule_name: str
    ):
        """
        Add an ingress rule to a security group.
        """
        try:
            ec2_client.authorize_security_group_ingress(
                GroupId=security_group.id,
                IpPermissions=ingress_rule,
            )
            print_log(
                f"Added {rule_name} inbound rule to security group"
                f" '{security_group.name}' ('{security_group.id}') in region"
                f" '{ec2_client.meta.region_name}'"
            )
        except ClientError as e:
            if "Duplicate" in str(e):
                print_warning(
                    f"Inbound {rule_name} rule already exists for"
                    f" '{security_group.name}' ('{security_group.id}') in region"
                    f" '{ec2_client.meta.region_name}'"
                )
            else:
                print_error(
                    f"Unable to add inbound {rule_name} rule to security group"
                    f" '{security_group.name}' ('{security_group.id}') in region"
                    f" '{ec2_client.meta.region_name}': {e}"
                )

    @staticmethod
    def _remove_security_group_ingress_rule(
        ec2_client, security_group: AWSSecurityGroup, ingress_rule: List, rule_name: str
    ):
        """
        Remove an ingress rule from a security group.
        """
        try:
            ec2_client.revoke_security_group_ingress(
                GroupId=security_group.id,
                IpPermissions=ingress_rule,
            )
            print_log(
                f"Removed inbound {rule_name} rule from security group"
                f" '{security_group.name}' ('{security_group.id}') in region"
                f" '{ec2_client.meta.region_name}' (if present)"
            )
        except ClientError as e:
            print_error(
                f"Unable to remove inbound {rule_name} rule from security group"
                f" '{security_group.name}' ('{security_group.id}') in region"
                f" '{ec2_client.meta.region_name}': {e}"
            )

    @staticmethod
    def _generate_aws_compute_source_template(
        az: AWSAvailabilityZone, name: str, spot: bool
    ) -> Dict:
        """
        Create a minimal populated YellowDog Compute Source Template resource definition.
        """
        spot_str = "Spot" if spot is True else "On-Demand"
        return {
            "resource": RN_SOURCE_TEMPLATE,
            "description": (
                f"AWS {az.az} {spot_str} Compute Source Template automatically created"
                " by YellowDog Cloud Wizard"
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

    def _generate_yd_namespace_configuration(
        self, namespace: str, s3_bucket_name: str
    ) -> Dict:
        """
        Generate a Namespace configuration using an S3 bucket.
        """
        return {
            "resource": RN_STORAGE_CONFIGURATION,
            "type": "co.yellowdog.platform.model.S3NamespaceStorageConfiguration",
            "namespace": namespace,
            "bucketName": s3_bucket_name,
            "region": self.region_name,
            "credential": f"{YD_KEYRING_NAME}/{YD_CREDENTIAL_NAME}",
        }

    def _generate_s3_bucket_policy(self) -> str:
        """
        Generate the required policy statement to be attached to the S3 bucket.
        """
        assert self._aws_user is not None
        s3_bucket_name = self._get_s3_bucket_name()
        return json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": self._aws_user.arn},
                        "Action": "s3:*",
                        "Resource": f"arn:aws:s3:::{s3_bucket_name}/*",
                    },
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": self._aws_user.arn},
                        "Action": "s3:ListBucket",
                        "Resource": f"arn:aws:s3:::{s3_bucket_name}",
                    },
                ],
            }
        )

    def _get_s3_bucket_name(self) -> str:
        """
        Get the unique name of the S3 bucket.
        """
        return (
            f"{S3_BUCKET_NAME_PREFIX}-{self._aws_user.user_id.lower()}"
            if self._aws_user is not None
            else ""
        )

    def _wait_until_access_key_is_valid_for_ec2(
        self,
        access_key: AWSAccessKey,
        retry_interval_seconds: int = 5,
        max_retries: int = 10,
    ) -> bool:
        """
        Wait until an access key is valid for use with EC2.
        """
        client = boto3.client(
            "ec2",
            region_name=self.region_name,
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
                        f" become valid for EC2 (attempt {index + 1} of"
                        f" {max_retries}) ..."
                    )
                    sleep(retry_interval_seconds)

        print_error(f"Unable to validate AWS access key '{access_key.access_key_id}'")
        return False
