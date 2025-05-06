"""
String and numeric constants, etc.
"""

DEFAULT_URL = "https://api.yellowdog.ai"

YD_KEY = "YD_KEY"
YD_SECRET = "YD_SECRET"
YD_NAMESPACE = "YD_NAMESPACE"
YD_TAG = "YD_TAG"
YD_URL = "YD_URL"
YD_ENV_VAR_PREFIX = "YD_VAR_"
ENV_VAR_SUB_PREFIX = "env:"
RAND_VAR_SIZE = 0xFFF

TASK_BATCH_SIZE_DEFAULT = 1000
MAX_PARALLEL_TASK_BATCH_UPLOAD_THREADS = 1
MAX_BATCH_SUBMIT_ATTEMPTS = 4  # Initial attempt plus retries

CR_BATCH_SIZE_DEFAULT = 10000

EVENT_STREAM_RETRY_INTERVAL = 5.0  # Seconds

NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR = "::"
NAMESPACE_PREFIX_SEPARATOR = "/"
DEFAULT_NAMESPACE = "default"
WP_VARIABLES_PREFIX = "__"
WP_VARIABLES_POSTFIX = "__"
CSV_VAR_OPENING_DELIMITER = "{{"
CSV_VAR_CLOSING_DELIMITER = "}}"
VAR_OPENING_DELIMITER = "{{"
VAR_CLOSING_DELIMITER = "}}"
VAR_DEFAULT_SEPARATOR = ":="
TYPE_TAG_TERMINATOR = ":"
TAG_DEFAULT_DIFF = "="
NUMBER_TYPE_TAG = "num" + TYPE_TAG_TERMINATOR
BOOL_TYPE_TAG = "bool" + TYPE_TAG_TERMINATOR
ARRAY_TYPE_TAG = "array" + TYPE_TAG_TERMINATOR
TABLE_TYPE_TAG = "table" + TYPE_TAG_TERMINATOR
FORMAT_NAME_TYPE_TAG = "format_name" + TYPE_TAG_TERMINATOR
TOML_VAR_NESTED_DEPTH = 3

VAR_NAME_OF_UNNAMED_TASK = "none"

DEFAULT_LOG_WIDTH = 120
MAX_LINES_COLOURED_FORMATTING = 1024
ERROR_STYLE = "bold red3"
WARNING_STYLE = "red3"
JSON_INDENT = 2
HIGHLIGHTED_STATES = [
    r"(?P<active>ALLOCATED)",
    r"(?P<active>DOING_TASK)",
    r"(?P<active>EXECUTING)",
    r"(?P<active>EXPECTED)",
    r"(?P<active>PENDING)",
    r"(?P<active>READY)",
    r"(?P<active>RUNNING)",
    r"(?P<active>TARGET)",
    r"(?P<active>ALIVE)",
    r"(?P<active>MATCHING)",
    r"(?P<cancelled>ABORTED)",
    r"(?P<cancelled>CANCELLED)",
    r"(?P<cancelled>CANCELLING)",
    r"(?P<cancelled>DEREGISTERED)",
    r"(?P<cancelled>SHUTDOWN)",
    r"(?P<cancelled>STOPPED)",
    r"(?P<cancelled>TERMINATED)",
    r"(?P<completed>COMPLETED)",
    r"(?P<failed>FAILED)",
    r"(?P<failed>FAILING)",
    r"(?P<failed>LOST)",
    r"(?P<failed>NON-MATCHING)",
    r"(?P<idle>EMPTY)",
    r"(?P<idle>FOUND)",
    r"(?P<idle>IDLE)",
    r"(?P<idle>SLEEPING)",
    r"(?P<idle>STOPPED)",
    r"(?P<idle>STARTING)",
    r"(?P<idle>WAITING)",
    r"(?P<idle>HELD)",
    r"(?P<starved>STARVED)",
    r"(?P<transitioning>CONFIGURING)",
    r"(?P<transitioning>DOWNLOADING)",
    r"(?P<transitioning>LATE)",
    r"(?P<transitioning>NEW)",
    r"(?P<transitioning>PROVISIONING)",
    r"(?P<transitioning>STOPPING)",
    r"(?P<transitioning>TERMINATING)",
    r"(?P<transitioning>UNAVAILABLE)",
    r"(?P<transitioning>UNKNOWN)",
    r"(?P<transitioning>UPLOADING)",
]
# For Rich colour options, see colour list & swatches at:
# https://rich.readthedocs.io/en/stable/appendix/colors.html
DEFAULT_THEME = {
    "pyexamples.date_time": "bold deep_sky_blue1",
    "pyexamples.quoted": "bold green4",
    "pyexamples.url": "bold green4",
    "pyexamples.ydid": "bold dark_orange",
    "pyexamples.table_outline": "bold deep_sky_blue4",
    "pyexamples.table_content": "bold green4",
    "pyexamples.transitioning": "bold dark_orange",
    "pyexamples.executing": "bold deep_sky_blue4",
    "pyexamples.failed": "bold red3",
    "pyexamples.completed": "bold green4",
    "pyexamples.cancelled": "bold grey35",
    "pyexamples.active": "bold deep_sky_blue4",
    "pyexamples.idle": "bold dark_goldenrod",
    "pyexamples.starved": "bold dark_orange",
}

# Resource type names for create/remove
RESOURCE_PROPERTY_NAME = "resource"
RN_ALLOWANCE = "Allowance"
RN_APPLICATION = "Application"
RN_CONFIGURED_POOL = "ConfiguredWorkerPool"
RN_CREDENTIAL = "Credential"
RN_GROUP = "Group"
RN_IMAGE_FAMILY = "MachineImageFamily"
RN_KEYRING = "Keyring"
RN_NAMESPACE_POLICY = "NamespacePolicy"
RN_NUMERIC_ATTRIBUTE_DEFINITION = "NumericAttributeDefinition"
RN_REQUIREMENT_TEMPLATE = "ComputeRequirementTemplate"
RN_ROLE = "Role"
RN_SOURCE_TEMPLATE = "ComputeSourceTemplate"
RN_STORAGE_CONFIGURATION = "NamespaceStorageConfiguration"
RN_STRING_ATTRIBUTE_DEFINITION = "StringAttributeDefinition"
RN_USER = "User"

# Property Names
PROP_AUTOSCALING_MAX_NODES = "autoscalingMaxNodes"
PROP_CREDENTIAL = "credential"
PROP_CST_ID = "sourceTemplateId"
PROP_DEFAULT_RANK_ORDER = "defaultRankOrder"
PROP_DESCRIPTION = "description"
PROP_EFFECTIVE_FROM = "effectiveFrom"
PROP_EFFECTIVE_UNTIL = "effectiveUntil"
PROP_IMAGE = "image"
PROP_IMAGES_ID = "imagesId"
PROP_IMAGE_ID = "imageId"
PROP_KEYRING = "keyring"
PROP_KEYRING_NAME = "keyringName"
PROP_NAME = "name"
PROP_NAMESPACE = "namespace"
PROP_OPTIONS = "options"
PROP_OS_TYPE = "osType"
PROP_RANGE = "range"
PROP_REQUIREMENT_CREATED_FROM = "requirementCreatedFromId"
PROP_RESOURCE = "resource"
PROP_SOURCE = "source"
PROP_SOURCES = "sources"
PROP_SOURCE_CREATED_FROM = "sourceCreatedFromId"
PROP_TITLE = "title"
PROP_TYPE = "type"
PROP_UNITS = "units"
