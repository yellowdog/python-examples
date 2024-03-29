"""
Configuration and utilities related to Azure account setup.
"""

from os import environ
from typing import Dict, List, Optional

from azure.identity import EnvironmentCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import NetworkSecurityGroup
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountKey, StorageAccountListKeysResult
from azure.mgmt.subscription import SubscriptionClient
from yellowdog_client import PlatformClient
from yellowdog_client.model import KeyringSummary

from yd_commands.cloudwizard_common import CommonCloudConfig
from yd_commands.create import create_resources
from yd_commands.interactive import confirmed, select
from yd_commands.printing import print_error, print_log, print_warning
from yd_commands.remove import remove_resources
from yd_commands.settings import RN_SOURCE_TEMPLATE, RN_STORAGE_CONFIGURATION

RESOURCE_PREFIX = "yellowdog-cloudwizard"
RESOURCE_GROUP_PREFIX = f"{RESOURCE_PREFIX}-rg"
VNET_PREFIX = f"{RESOURCE_PREFIX}-vnet"
SUBNET_PREFIX = f"{RESOURCE_PREFIX}-subnet"
SECURITY_GROUP_PREFIX = f"{RESOURCE_PREFIX}-secgrp"
STORAGE_ACCOUNT_NAME_PREFIX = "yellowdogcw"
STORAGE_BLOB_NAME = f"{RESOURCE_PREFIX}-namespace-storage-config"
STORAGE_REGION = "northeurope"
ADDRESS_PREFIX = "10.0.0.0/18"

YD_KEYRING_NAME = "cloudwizard-azure"
YD_CREDENTIAL_NAME = "cloudwizard-azure"
YD_CREDENTIAL_NAME_STORAGE = f"{YD_CREDENTIAL_NAME}-storage"
YD_RESOURCE_PREFIX = "cloudwizard-azure"
YD_RESOURCES_FILE = f"{YD_RESOURCE_PREFIX}-yellowdog-resources.json"
YD_INSTANCE_TAG = {"yd-cloudwizard": "yellowdog-cloudwizard-source"}
YD_NAMESPACE = "cloudwizard-azure"
YD_DEFAULT_INSTANCE_TYPE = "{{instance_type:=Standard_A1_v2}}"
YD_SPOT_MAX_PRICE = 1.0

AZURE_SUBSCRIPTION_ID = "AZURE_SUBSCRIPTION_ID"
AZURE_TENANT_ID = "AZURE_TENANT_ID"
AZURE_CLIENT_ID = "AZURE_CLIENT_ID"
AZURE_CLIENT_SECRET = "AZURE_CLIENT_SECRET"


AZURE_YD_IMAGE_REGIONS = [
    "northeurope",
]


class AzureConfig(CommonCloudConfig):
    """
    Class for managing the Azure configuration.
    """

    def __init__(
        self,
        client: PlatformClient,
        instance_type: Optional[str] = None,
    ):
        """
        Set up Azure config details.
        """
        super().__init__(client=client, cloud_provider="AZURE")

        # Check for required Azure credential environment variables
        error = False
        for env_var in [
            AZURE_TENANT_ID,
            AZURE_SUBSCRIPTION_ID,
            AZURE_CLIENT_ID,
            AZURE_CLIENT_SECRET,
        ]:
            if environ.get(env_var, None) is None:
                error = True
                print_error(f"Environment variable '{env_var}' is not set")
        if error:
            raise Exception(
                "Required Azure credential environment variable(s) not set ... exiting"
            )
        self._credential = EnvironmentCredential()

        self._instance_type = (
            YD_DEFAULT_INSTANCE_TYPE if instance_type is None else instance_type
        )

        self._all_regions: List[str] = []
        self._selected_regions: List[str] = []
        self._created_regions: List[str] = []

        self._subscription_id = environ[AZURE_SUBSCRIPTION_ID]

        self._subscription_client = SubscriptionClient(self._credential)
        self._resource_client = ResourceManagementClient(
            self._credential, self._subscription_id
        )
        self._network_client = NetworkManagementClient(
            self._credential, self._subscription_id
        )
        self._storage_client = StorageManagementClient(
            self._credential, self._subscription_id
        )
        self._storage_region: str = STORAGE_REGION
        self._storage_account_name: Optional[str] = None
        self._storage_account_key: Optional[StorageAccountKey] = None

    def setup(self):
        """
        Set up all Azure and YellowDog assets
        """
        # Keyring creation has to precede the generation of the Azure
        # storage account name
        print_log(f"Creating YellowDog Keyring '{YD_KEYRING_NAME}'")
        self._create_keyring(keyring_name=YD_KEYRING_NAME)
        self._all_regions = self._get_regions_list()
        self._create_azure_resources()
        self._create_yellowdog_resources()
        self._print_keyring_details()

    def teardown(self):
        """
        Remove all Azure and YellowDog assets.
        """
        self._remove_azure_resources()
        self._remove_yellowdog_resources()

    def _create_azure_resources(self):
        """
        Create the required assets in the Azure account, for use with YellowDog.
        """
        print_log("Creating YellowDog resources in the Azure account")
        print_log(
            "Please select the Azure regions in which to create resource groups and"
            " network resources"
        )
        print_log(
            "*** Note that only the following region(s) contain"
            f" YellowDog base VM images: {AZURE_YD_IMAGE_REGIONS} ***"
        )
        self._selected_regions = select(
            client=self._client,
            objects=self._all_regions,
            object_type_name="region",
            force_interactive=True,
            override_quiet=True,
            result_required=True,
        )
        self._create_resource_groups_and_network_resources()
        self._create_storage_account_and_blob()

    def _remove_azure_resources(self):
        """
        Remove the Cloud Wizard assets in the Azure account.
        """
        print_log("Removing all YellowDog-created resources in the Azure account")
        self._remove_resource_groups()

    def _create_resource_groups_and_network_resources(self):
        """
        Create YellowDog Resource Groups in each selected region.
        """
        regions = self._selected_regions[:]

        if self._storage_region not in regions:
            regions.append(self._storage_region)
            storage_region_added = True
        else:
            storage_region_added = False

        for region in regions:
            rg_name = self._generate_resource_group_name(region)

            # Does the resource group already exist?
            try:
                if self._resource_client.resource_groups.check_existence(rg_name):
                    if region == self._storage_region and storage_region_added:
                        continue
                    print_warning(f"Azure resource group '{rg_name}' already exists")
                    if self._create_network_resources(
                        resource_group_name=rg_name, region=region
                    ):
                        self._created_regions.append(region)
                    else:
                        self._remove_resource_group_by_name(rg_name)
                    continue
            except Exception as e:
                print_warning(
                    "Unable to check existence of Azure resource group"
                    f" '{rg_name}': {e}"
                )
                continue

            # Create the resource group
            try:
                rg_result = self._resource_client.resource_groups.create_or_update(
                    rg_name, {"location": region}
                )
                print_log(
                    f"Created (or updated) Azure resource group '{rg_result.name}' in"
                    f" region '{rg_result.location}'"
                )
                if region == self._storage_region and storage_region_added:
                    print_log(
                        f"Note: Resource group '{rg_name}' is automatically created to"
                        " contain the Azure storage account"
                    )
                    continue
                if self._create_network_resources(
                    resource_group_name=rg_name, region=region
                ):
                    self._created_regions.append(region)
                else:
                    self._remove_resource_group_by_name(rg_name)

            except Exception as e:
                if "LocationNotAvailable" in str(e):
                    print_warning(
                        f"Region '{region}' is not available for Resource Group"
                        " creation; excluding this region"
                    )
                elif "DisallowedLocation" in str(e):
                    print_warning(
                        f"Region '{region}' is disallowed for Resource Group"
                        " creation; excluding this region"
                    )
                elif "ResourceGroupBeingDeleted" in str(e):
                    print_warning(
                        f"Existing Resource Group '{rg_name}' is in the process of"
                        " being deleted; please try again later"
                    )
                else:
                    print_error(
                        f"Failed to create Azure resource group '{rg_name}' in region"
                        f" '{region}': {e}"
                    )
                continue

    def _remove_resource_groups(self):
        """
        Remove all YellowDog resource groups. Deletion of a resource group
        also deletes any contained resources.
        """
        print_log("Removing YellowDog resource groups")
        resource_groups = self._resource_client.resource_groups.list()
        count = 0
        for resource_group in resource_groups:
            if resource_group.name.startswith(RESOURCE_GROUP_PREFIX):
                if confirmed(
                    f"Delete Azure resource group '{resource_group.name}' and all"
                    " contained resources?"
                ):
                    try:
                        self._resource_client.resource_groups.begin_delete(
                            resource_group.name
                        )  # Deletion occurs asynchronously unless '.result()' is added
                        print_log(
                            "Requested deletion of Azure resource group"
                            f" '{resource_group.name}' and all contained resources"
                            " (asynchronous operation)"
                        )
                        count += 1
                    except Exception as e:
                        if "ResourceGroupNotFound" in str(e):
                            print_warning(
                                f"Resource Group '{resource_group.name}' not found; it"
                                " may have already been in the process of being"
                                " deleted"
                            )
                        else:
                            print_error(
                                "Unable to delete Azure resource group"
                                f" '{resource_group.name}': {e}"
                            )
                        continue

        if count == 0:
            print_log("No Azure resource groups deleted")
        else:
            print_log(f"{count} Azure resource group(s) deleted")

    def _remove_resource_group_by_name(self, rg_name: str):
        """
        Remove a resource group by its name.
        """
        try:
            self._resource_client.resource_groups.begin_delete(rg_name)
            print_log(f"Requested deletion of Azure resource group '{rg_name}'")
        except:
            print_warning(f"Unable to delete Azure resource group '{rg_name}'")

    def _create_network_resources(self, resource_group_name: str, region: str):
        """
        Create a virtual network and subnet in a resource group in a region.
        """

        def _location_not_available_for_resource_type(
            e: Exception, resource_name: str
        ) -> bool:
            if "LocationNotAvailableForResourceType" in str(e):
                print_warning(
                    f"Location '{region}' is not available for creation of resource"
                    f" '{resource_name}'; excluding this region"
                )
                return True
            return False

        def _resource_group_being_deleted(e: Exception, resource_name: str) -> bool:
            if "ResourceGroupBeingDeleted" in str(e):
                print_warning(
                    f"Resource Group '{resource_group_name}' is in the process of being"
                    f" deleted and resource '{resource_name}' cannot be created;"
                    " excluding this region"
                )
                return True
            return False

        vnet_name = self._generate_vnet_name(region)
        address_prefixes = [ADDRESS_PREFIX]
        try:
            self._network_client.virtual_networks.begin_create_or_update(
                resource_group_name,
                vnet_name,
                {
                    "location": region,
                    "address_space": {"address_prefixes": address_prefixes},
                },
            ).wait()
            print_log(
                f"Created (or updated) Azure virtual network '{vnet_name}' with address"
                f" prefixes {address_prefixes}"
            )
        except Exception as e:
            if _location_not_available_for_resource_type(e, vnet_name):
                return False
            if not _resource_group_being_deleted(e, vnet_name):
                print_error(
                    f"Failed to create Azure virtual network '{vnet_name}': {e}"
                )
            return False

        # Create network security group
        security_group_name = self._generate_security_group_name(region)
        try:
            self._network_client.network_security_groups.begin_create_or_update(
                resource_group_name,
                security_group_name,
                parameters=NetworkSecurityGroup(
                    id=security_group_name, location=region
                ),
            ).result()
            print_log(
                "Created (or updated) Azure network security group"
                f" '{security_group_name}'"
            )
        except Exception as e:
            if _location_not_available_for_resource_type(e, security_group_name):
                return False
            if not _resource_group_being_deleted(e, security_group_name):
                print_error(
                    "Unable to create Azure network security group"
                    f" '{security_group_name}': {e}"
                )
            return False

        # Add an outbound HTTPS rule to allow the Agent to reach the platform
        address_prefix = ADDRESS_PREFIX
        security_rule_name = "https-outbound-rule"
        try:
            self._network_client.security_rules.begin_create_or_update(
                resource_group_name=resource_group_name,
                network_security_group_name=security_group_name,
                security_rule_name=security_rule_name,
                security_rule_parameters={
                    "properties": {
                        "access": "Allow",
                        "destinationAddressPrefix": "*",
                        "destinationPortRange": "443",
                        "direction": "Outbound",
                        "priority": 100,
                        "protocol": "tcp",
                        "sourceAddressPrefix": address_prefix,
                        "sourcePortRange": "*",
                    }
                },
            ).result()
            print_log(
                "Added outbound HTTPS rule to Azure security group"
                f" '{security_group_name}'"
            )
        except Exception as e:
            if _location_not_available_for_resource_type(e, security_rule_name):
                return False
            if not _resource_group_being_deleted(e, security_rule_name):
                print_error(
                    "Unable to add outbound HTTPS rule to Azure security group"
                    f" '{security_group_name}': {e}"
                )
            return False

        # Create subnet and associate the security group
        subnet_name = self._generate_subnet_name(region)
        security_group_id = (
            f"/subscriptions/{self._subscription_id}/"
            f"resourceGroups/{resource_group_name}/"
            "providers/Microsoft.Network/"
            f"networkSecurityGroups/{security_group_name}"
        )
        try:
            self._network_client.subnets.begin_create_or_update(
                resource_group_name,
                vnet_name,
                subnet_name,
                {
                    "address_prefix": address_prefix,
                    "networkSecurityGroup": {
                        "id": security_group_id,
                        "location": region,
                    },
                },
            ).result()
            print_log(
                f"Created (or updated) Azure subnet '{subnet_name}' with address prefix"
                f" '{address_prefix}'"
            )
        except Exception as e:
            if _location_not_available_for_resource_type(e, subnet_name):
                return False
            if not _resource_group_being_deleted(e, subnet_name):
                print_error(f"Failed to create Azure subnet '{subnet_name}': {e}")
            return False

        return True

    def _create_yellowdog_resources(self):
        """
        Create the YellowDog resources and save the resource definition file.
        """
        print_log("Creating Azure resources in the YellowDog account")

        for region in self._created_regions:
            name = f"{YD_RESOURCE_PREFIX}-{region}-ondemand"
            self._source_template_resources.append(
                self._generate_azure_compute_source_template(
                    region, name=name, spot=False
                )
            )
            self._source_names_ondemand.append(name)
            name = f"{YD_RESOURCE_PREFIX}-{region}-spot"
            self._source_template_resources.append(
                self._generate_azure_compute_source_template(
                    region, name=name, spot=True
                )
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

        # Create Credentials
        try:
            credential_resource = self._generate_yd_azure_credential(
                YD_KEYRING_NAME, YD_CREDENTIAL_NAME
            )
            create_resources([credential_resource])
        except Exception as e:
            print_error(f"Unable to add credential '{YD_CREDENTIAL_NAME}': {e}")

        if self._storage_account_key is not None:
            try:
                credential_resource = self._generate_yd_azure_storage_credential(
                    YD_KEYRING_NAME, YD_CREDENTIAL_NAME_STORAGE
                )
                create_resources([credential_resource])
            except Exception as e:
                print_error(
                    f"Unable to add credential '{YD_CREDENTIAL_NAME_STORAGE}': {e}"
                )

        # Create namespace configuration (Keyring/Credential creation must come first)
        print_log(f"Creating YellowDog Namespace Configuration '{YD_NAMESPACE}'")
        create_resources(
            [
                self._generate_yd_namespace_configuration(
                    namespace=YD_NAMESPACE, storage_blob_name=STORAGE_BLOB_NAME
                )
            ]
        )

        # Save the list of resources
        # Sequence the Compute Requirement Templates before the Compute Source
        # Templates for subsequent removals.
        # - Omit the Keyring to prevent overwrites if using 'yd-create' with the
        #   resource file
        # - Omit the Credential for security reasons
        self._save_resource_list(
            self._requirement_template_resources + self._source_template_resources,
            YD_RESOURCES_FILE,
        )

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
            [self._generate_yd_namespace_configuration(YD_NAMESPACE, STORAGE_BLOB_NAME)]
        )

    def _create_storage_account_and_blob(self):
        """
        Create a storage account and blob for use in namespace to object store mapping.
        """
        self._storage_account_name = self._generate_azure_storage_account_name()
        resource_group_name = self._generate_resource_group_name(self._storage_region)

        availability = self._storage_client.storage_accounts.check_name_availability(
            {"name": self._storage_account_name}
        )
        if not availability.name_available:
            print_warning(
                f"Azure storage account '{self._storage_account_name}' already exists"
            )
        else:
            try:
                print_log(
                    f"Creating Azure storage account '{self._storage_account_name}'"
                )
                self._storage_client.storage_accounts.begin_create(
                    resource_group_name,
                    self._storage_account_name,
                    {
                        "location": self._storage_region,
                        "kind": "StorageV2",
                        "sku": {"name": "Standard_LRS"},
                    },
                ).result()
                print_log(
                    f"Created Azure storage account '{self._storage_account_name}' in"
                    f" region '{self._storage_region}'"
                )
            except Exception as e:
                print_error(
                    "Unable to create Azure storage account"
                    f" '{self._storage_account_name}' in region"
                    f" '{self._storage_region}': {e}"
                )

        try:
            keys: StorageAccountListKeysResult = (
                self._storage_client.storage_accounts.list_keys(
                    resource_group_name, self._storage_account_name
                )
            )
            self._storage_account_key = keys.keys[0]
        except Exception as e:
            print_error(f"Unable to obtain Azure storage account key: {e}")
            return

        blob_containers = self._storage_client.blob_containers.list(
            resource_group_name, self._storage_account_name
        )
        for blob in blob_containers:
            if blob.name == STORAGE_BLOB_NAME:
                print_warning(
                    f"Azure storage blob '{STORAGE_BLOB_NAME}' already exists"
                )
                return

        try:
            self._storage_client.blob_containers.create(
                resource_group_name, self._storage_account_name, STORAGE_BLOB_NAME, {}
            )
            print_log(f"Created Azure storage blob '{STORAGE_BLOB_NAME}'")
        except Exception as e:
            print_error(
                f"Unable to create Azure storage blob '{STORAGE_BLOB_NAME}': {e}"
            )
            return

    def _generate_azure_compute_source_template(
        self, region: str, name: str, spot: bool
    ) -> Dict:
        """
        Create a minimal populated YellowDog Compute Source Template resource definition.
        """
        spot_str = "Spot" if spot is True else "On-Demand"
        source = {
            "assignPublicIp": True,
            "credential": f"{YD_KEYRING_NAME}/{YD_CREDENTIAL_NAME}",
            "imageId": "*",
            "limit": 0,
            "name": name,
            "networkName": self._generate_vnet_name(region),
            "networkResourceGroupName": self._generate_resource_group_name(region),
            "region": region,
            "subnetName": self._generate_subnet_name(region),
            "type": "co.yellowdog.platform.model.AzureInstancesComputeSource",
            "useSpot": spot,
            "vmSize": "*",
        }
        if spot:
            source["spotMaxPrice"] = YD_SPOT_MAX_PRICE

        return {
            "resource": RN_SOURCE_TEMPLATE,
            "description": (
                f"Azure {region} {spot_str} Compute Source Template automatically"
                " created by YellowDog Cloud Wizard"
            ),
            "source": source,
        }

    def _generate_yd_namespace_configuration(
        self, namespace: str, storage_blob_name: str
    ) -> Dict:
        """
        Generate a Namespace configuration using an Azure storage blob.
        """
        return {
            "resource": RN_STORAGE_CONFIGURATION,
            "type": "co.yellowdog.platform.model.AzureNamespaceStorageConfiguration",
            "namespace": namespace,
            "containerName": storage_blob_name,
            "credential": f"{YD_KEYRING_NAME}/{YD_CREDENTIAL_NAME_STORAGE}",
        }

    @staticmethod
    def _generate_vnet_name(region: str) -> str:
        return f"{VNET_PREFIX}-{region}"

    @staticmethod
    def _generate_resource_group_name(region: str) -> str:
        return f"{RESOURCE_GROUP_PREFIX}-{region}"

    @staticmethod
    def _generate_subnet_name(region: str) -> str:
        return f"{SUBNET_PREFIX}-{region}"

    @staticmethod
    def _generate_security_group_name(region: str) -> str:
        return f"{SECURITY_GROUP_PREFIX}-{region}"

    @staticmethod
    def _generate_yd_azure_credential(keyring_name: str, credential_name: str) -> Dict:
        """
        Generate an Azure Credential resource definition.
        """
        return {
            "resource": "Credential",
            "keyringName": keyring_name,
            "credential": {
                "name": credential_name,
                "description": (
                    "Azure client credential automatically created by YellowDog Cloud"
                    " Wizard"
                ),
                "clientId": environ[AZURE_CLIENT_ID],
                "tenantId": environ[AZURE_TENANT_ID],
                "subscriptionId": environ[AZURE_SUBSCRIPTION_ID],
                "key": environ[AZURE_CLIENT_SECRET],
                "type": (
                    "co.yellowdog.platform.account.credentials.AzureClientCredential"
                ),
            },
        }

    def _generate_yd_azure_storage_credential(
        self, keyring_name: str, credential_name: str
    ) -> Dict:
        """
        Generate an Azure Storage Credential resource definition.
        """
        return {
            "resource": "Credential",
            "keyringName": keyring_name,
            "credential": {
                "name": credential_name,
                "description": (
                    "Azure storage credential automatically created by YellowDog Cloud"
                    " Wizard"
                ),
                "accountName": self._storage_account_name,
                "accountKey": self._storage_account_key.value,
                "type": (
                    "co.yellowdog.platform.account.credentials.AzureStorageCredential"
                ),
            },
        }

    def _generate_azure_storage_account_name(self) -> str:
        try:
            keyrings: List[KeyringSummary] = (
                self._client.keyring_client.find_all_keyrings()
            )
            return f"{STORAGE_ACCOUNT_NAME_PREFIX}{keyrings[0].id[13:19]}".lower()
        except Exception as e:
            raise Exception(f"Unable to generate Azure storage account name: {e}")

    def set_ssh_ingress_rule(self, operation: str, selected_region: str = None):
        """
        Add or remove an SSH ingress rule for the specified region.
        The 'operation' must be 'add-ssh' or 'remove-ssh'.
        """

        if selected_region is None:
            print_error("The 'region-name' option must be specified")
            return

        address_prefix = ADDRESS_PREFIX
        resource_group_name = self._generate_resource_group_name(selected_region)
        security_group_name = self._generate_security_group_name(selected_region)
        security_rule_name = "ssh-inbound"
        if operation == "add-ssh":
            print_log(
                "Adding inbound SSH rule to Azure security group"
                f" '{security_group_name}'"
            )
            try:
                self._network_client.security_rules.begin_create_or_update(
                    resource_group_name=resource_group_name,
                    network_security_group_name=security_group_name,
                    security_rule_name=security_rule_name,
                    security_rule_parameters={
                        "properties": {
                            "access": "Allow",
                            "destinationAddressPrefix": address_prefix,
                            "destinationPortRange": "22",
                            "direction": "Inbound",
                            "priority": 100,
                            "protocol": "tcp",
                            "sourceAddressPrefix": "*",
                            "sourcePortRange": "*",
                        }
                    },
                ).result()
                print_log(
                    "Added inbound SSH rule to Azure security group"
                    f" '{security_group_name}'"
                )
            except Exception as e:
                print_error(
                    "Unable to add inbound SSH rule to Azure security group"
                    f" '{security_group_name}': {e}"
                )

        elif operation == "remove-ssh":
            print_log(
                "Removing inbound SSH rule from Azure security group"
                f" '{security_group_name}'"
            )
            try:
                self._network_client.security_rules.begin_delete(
                    resource_group_name=resource_group_name,
                    network_security_group_name=security_group_name,
                    security_rule_name=security_rule_name,
                ).result()
                print_log(
                    "Removed inbound SSH rule from Azure security group"
                    f" '{security_group_name}' (if present)"
                )
            except Exception as e:
                print_error(
                    "Unable to remove inbound SSH rule from Azure security group"
                    f" '{security_group_name}': {e}"
                )

    def _get_regions_list(self) -> List[str]:
        """
        Generate the list of regions supported by this subscription.
        """
        try:
            return [
                location.name
                for location in self._subscription_client.subscriptions.list_locations(
                    self._subscription_id
                )
            ]
        except Exception as e:
            raise Exception(f"Unable to obtain list of Azure regions: {e}")
