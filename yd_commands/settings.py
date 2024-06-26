"""
String and numeric constants, etc.
"""

DEFAULT_URL = "https://portal.yellowdog.co/api"

YD_KEY = "YD_KEY"
YD_SECRET = "YD_SECRET"
YD_NAMESPACE = "YD_NAMESPACE"
YD_TAG = "YD_TAG"
YD_URL = "YD_URL"
ENV_VAR_PREFIX = "YD_VAR_"
RAND_VAR_SIZE = 0xFFF

TASK_BATCH_SIZE_DEFAULT = 2000
CR_BATCH_SIZE_DEFAULT = 10000

TASK_ABORT_CHECK_INTERVAL = 20  # Seconds

NAMESPACE_PREFIX_SEPARATOR = "::"
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

DEFAULT_LOG_WIDTH = 120
MAX_LINES_COLOURED_JSON = 1024
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
    r"(?P<idle>EMPTY)",
    r"(?P<idle>FOUND)",
    r"(?P<idle>IDLE)",
    r"(?P<idle>SLEEPING)",
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
RN_ALLOWANCE = "Allowance"
RN_CONFIGURED_POOL = "ConfiguredWorkerPool"
RN_CREDENTIAL = "Credential"
RN_IMAGE_FAMILY = "MachineImageFamily"
RN_KEYRING = "Keyring"
RN_REQUIREMENT_TEMPLATE = "ComputeRequirementTemplate"
RN_SOURCE_TEMPLATE = "ComputeSourceTemplate"
RN_STORAGE_CONFIGURATION = "NamespaceStorageConfiguration"
RN_STRING_ATTRIBUTE_DEFINITION = "StringAttributeDefinition"
RN_NUMERIC_ATTRIBUTE_DEFINITION = "NumericAttributeDefinition"
RN_NAMESPACE_POLICY = "NamespacePolicy"
