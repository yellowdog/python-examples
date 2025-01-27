"""
Configuration and utilities related to GCP account setup.
"""

from typing import Dict, List

from google.cloud import compute_v1, storage
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from yellowdog_client import PlatformClient

from yellowdog_cli.create import create_resources
from yellowdog_cli.remove import remove_resources
from yellowdog_cli.utils.cloudwizard_common import CommonCloudConfig
from yellowdog_cli.utils.interactive import confirmed, select
from yellowdog_cli.utils.printing import print_error, print_log, print_warning
from yellowdog_cli.utils.settings import RN_SOURCE_TEMPLATE, RN_STORAGE_CONFIGURATION

YD_KEYRING_NAME = "cloudwizard-gcp"
YD_CREDENTIAL_NAME = "cloudwizard-gcp"
YD_RESOURCE_PREFIX = "cloudwizard-gcp"
YD_RESOURCES_FILE = f"{YD_RESOURCE_PREFIX}-yellowdog-resources.json"
YD_INSTANCE_TAG = {"yd-cloudwizard": "yellowdog-cloudwizard-source"}
YD_DEFAULT_INSTANCE_TYPE = "{{instance_type:=f1-micro}}"

GCP_BUCKET_PREFIX = "yellowdog-cloudwizard"
GCP_BUCKET_LOCATION = "europe-west1"


class GCPConfig(CommonCloudConfig):
    """
    Class for GCP resource creation.
    """

    def __init__(
        self, service_account_file: str, client: PlatformClient, instance_type: str
    ):
        super().__init__(client=client, cloud_provider="GCP")
        self._service_account_file = service_account_file
        try:
            self._credentials: Credentials = (
                service_account.Credentials.from_service_account_file(
                    service_account_file
                )
            )
        except FileNotFoundError:
            raise Exception(f"GCP credentials file '{service_account_file}' not found")

        self._regions_with_default_subnets: List[str] = []
        self._selected_regions: List[str] = []
        self._instance_type = (
            YD_DEFAULT_INSTANCE_TYPE if instance_type is None else instance_type
        )

    def setup(self):
        """
        Set up GCP and YellowDog assets in their respective accounts.
        """
        self._create_gcp_resources()
        self._create_yellowdog_resources()

    def teardown(self):
        """
        Remove YellowDog and GCP assets from their respective accounts.
        """
        self._remove_yellowdog_resources()
        self._remove_gcp_resources()

    def _create_gcp_resources(self):
        """
        Set up resources within GCP
        """
        self._create_storage_bucket()

    def _remove_gcp_resources(self):
        """
        Remove any resources created within GCP.
        """
        self._remove_storage_bucket()

    def _create_yellowdog_resources(self):
        """
        Set up YellowDog assets.
        """
        print_log(
            "Please select the Google Compute Engine regions for which to create"
            " YellowDog Compute Source Templates"
        )
        self._gather_regions()
        self._selected_regions = select(
            client=self._client,
            objects=self._regions_with_default_subnets,
            object_type_name="region",
            force_interactive=True,
            override_quiet=True,
        )

        if len(self._selected_regions) == 0:
            print_warning(
                "No regions selected; no Compute Source/Requirement Templates will be"
                " created"
            )
            return

        # Create Compute Source Templates
        for region in self._selected_regions:
            name = f"{YD_RESOURCE_PREFIX}-{region}-spot"
            self._source_template_resources.append(
                self._generate_gcp_compute_source_template(
                    region=region, name=name, spot=True
                )
            )
            self._source_names_spot.append(name)
            name = f"{YD_RESOURCE_PREFIX}-{region}-ondemand"
            self._source_template_resources.append(
                self._generate_gcp_compute_source_template(
                    region=region, name=name, spot=False
                )
            )
            self._source_names_ondemand.append(name)
        print_log("Creating YellowDog Compute Source Templates")
        create_resources(self._source_template_resources)

        # Create Compute Requirement Templates
        self._create_compute_requirement_templates(resource_prefix=YD_RESOURCE_PREFIX)

        # Create Keyring and remember the Keyring password
        self._create_keyring(keyring_name=YD_KEYRING_NAME)

        # Create Credential and add to Keyring
        create_resources(
            [self._generate_yd_gcp_credential(YD_KEYRING_NAME, YD_CREDENTIAL_NAME)]
        )

        # Save the Compute Requirement and Source Templates
        self._save_resource_list(
            self._requirement_template_resources + self._source_template_resources,
            YD_RESOURCES_FILE,
        )

        # Create the namespace mapped to the storage bucket
        namespace_configuration = self._generate_namespace_configuration(
            namespace=self._namespace,
            gcp_bucket_name=self._generate_bucket_name(),
            credential_name=f"{YD_KEYRING_NAME}/{YD_CREDENTIAL_NAME}",
        )
        create_resources([namespace_configuration])

        # Always show the Keyring details
        self._print_keyring_details()

    def _remove_yellowdog_resources(self):
        """
        Remove YellowDog resources in the Platform account.
        """
        self._remove_yd_templates_by_prefix(
            client=self._client, name_prefix=YD_RESOURCE_PREFIX
        )
        self._remove_keyring(YD_KEYRING_NAME)
        remove_resources(
            [
                self._generate_namespace_configuration(
                    self._namespace,
                    self._generate_bucket_name(),
                    credential_name=f"{YD_KEYRING_NAME}/{YD_CREDENTIAL_NAME}",
                )
            ]
        )

    def _gather_regions(self):
        """
        Find the regions in the default VPC with default subnets.
        """
        try:
            networks = compute_v1.NetworksClient(credentials=self._credentials).list(
                project=self._credentials.project_id
            )
        except Exception as e:
            if "401" in str(e):
                raise Exception(f"Invalid GCP credentials: {e}")
            else:
                raise e

        for network in networks:
            if network.name == "default":
                for subnet in network.subnetworks:
                    if "default" in subnet:
                        region = subnet.replace(
                            "https://www.googleapis.com/compute/v1/projects/"
                            f"{self._credentials.project_id}/regions/",
                            "",
                        ).replace("/subnetworks/default", "")
                        self._regions_with_default_subnets.append(region)
                break
        else:
            print_warning(
                f"Default VPC not found for project '{self._credentials.project_id}'"
            )

    def _generate_gcp_compute_source_template(
        self, region: str, name: str, spot: bool
    ) -> Dict:
        """
        Generate a GCP Compute Source Template resource definition.
        """
        spot_str = "Spot" if spot is True else "On-Demand"
        return {
            "resource": RN_SOURCE_TEMPLATE,
            "namespace": self._namespace,
            "description": (
                f"GCE {region} {spot_str} Compute Source Template automatically created"
                " by YellowDog Cloud Wizard"
            ),
            "source": {
                "assignPublicIp": True,
                "credential": f"{YD_KEYRING_NAME}/{YD_CREDENTIAL_NAME}",
                "image": "*",
                "machineType": "*",
                "name": name,
                "preemptible": False,
                "project": self._credentials.project_id,
                "region": region,
                "spot": spot,
                "type": "co.yellowdog.platform.model.GceInstancesComputeSource",
            },
        }

    def _generate_yd_gcp_credential(
        self,
        keyring_name: str,
        credential_name: str,
    ) -> Dict:
        """
        Generate an AWS Credential resource definition.
        """
        with open(self._service_account_file, "r") as f:
            service_account_file_contents = f.read()
        return {
            "resource": "Credential",
            "keyringName": keyring_name,
            "credential": {
                "type": (
                    "co.yellowdog.platform.account.credentials.GoogleCloudCredential"
                ),
                "name": credential_name,
                "description": (
                    "GCP credential automatically created by YellowDog Cloud Wizard"
                ),
                "serviceAccountKeyJson": service_account_file_contents,
            },
        }

    def _create_storage_bucket(self):
        """
        Create a storage bucket in Google storage.
        """
        bucket_name = self._generate_bucket_name()
        try:
            storage_client = storage.Client(credentials=self._credentials)
            storage_client.create_bucket(
                bucket_or_name=bucket_name, location=GCP_BUCKET_LOCATION
            )
            print_log(f"Created Google Storage Bucket '{bucket_name}'")
        except Exception as e:
            if "401" in str(e):
                raise Exception(f"Invalid GCP credentials: {e}")
            elif "409" in str(e):
                print_warning(
                    f"Google Storage Bucket '{bucket_name}' already exists and you"
                    " own it"
                )
            else:
                print_error(f"Unable to create Google Storage Bucket '{bucket_name}'")

    def _remove_storage_bucket(self):
        """
        Remove a Google Storage Bucket.
        """
        bucket_name = self._generate_bucket_name()
        if not confirmed(
            f"Delete Google Storage Bucket '{bucket_name}' and any objects it contains?"
        ):
            return
        try:
            storage_client = storage.Client(credentials=self._credentials)
            bucket = storage_client.get_bucket(bucket_or_name=bucket_name)
            try:
                # This only works for small populations of contained objects
                bucket.delete(force=True)
            except Exception:
                objects = storage_client.list_blobs(bucket_or_name=bucket_name)
                print_log(
                    "Deleting any remaining objects in Google Storage Bucket"
                    f" '{bucket_name}'"
                )
                counter = 0
                for obj in objects:
                    obj.delete()
                    counter += 1
                if counter > 0:
                    print_log(
                        f"Deleted {counter} object(s) from Google Storage Bucket"
                        f" '{bucket_name}'"
                    )
                else:
                    print_log(
                        f"No objects to delete in Google Storage Bucket '{bucket_name}'"
                    )
                bucket.delete()
            print_log(f"Deleted Google Storage Bucket '{bucket_name}'")
        except Exception as e:
            if "401" in str(e):
                raise Exception(f"Invalid GCP credentials: {e}")
            elif "404" in str(e):
                print_warning(f"Google Storage Bucket '{bucket_name}' does not exist")
            else:
                print_error(f"Google Storage Bucket operation failed: {e}")

    def _generate_bucket_name(self) -> str:
        return f"{GCP_BUCKET_PREFIX}-{self._credentials.project_id}"

    def _generate_namespace_configuration(
        self, namespace: str, gcp_bucket_name: str, credential_name: str
    ) -> Dict:
        """
        Generate a Namespace configuration using an S3 bucket.
        """
        return {
            "resource": RN_STORAGE_CONFIGURATION,
            "type": "co.yellowdog.platform.model.GcsNamespaceStorageConfiguration",
            "namespace": namespace,
            "bucketName": gcp_bucket_name,
            "credential": credential_name,
        }
