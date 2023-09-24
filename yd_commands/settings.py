"""
Textual and numeric constants, etc., that effect behaviour.
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
NUMBER_TYPE_TAG = "num:"
BOOL_TYPE_TAG = "bool:"
ARRAY_TYPE_TAG = "array:"
TABLE_TYPE_TAG = "table:"
VAR_DEFAULT_SEPARATOR = ":="
TOML_VAR_NESTED_DEPTH = 3

DEFAULT_LOG_WIDTH = 120
MAX_LINES_COLOURED_JSON = 1024
ERROR_STYLE = "bold red3"
WARNING_STYLE = "red3"
JSON_INDENT = 2
HIGHLIGHTED_STATES = [
    r"(?P<active>EXECUTING)",
    r"(?P<failed>FAILED)",
    r"(?P<completed>COMPLETED)",
    r"(?P<cancelled>CANCELLED)",
    r"(?P<cancelled>ABORTED)",
    r"(?P<active>RUNNING)",
    r"(?P<transitioning>PROVISIONING)",
    r"(?P<transitioning>TERMINATING)",
    r"(?P<cancelled>TERMINATED)",
    r"(?P<cancelled>SHUTDOWN)",
    r"(?P<cancelled>CANCELLING)",
    r"(?P<idle>IDLE)",
    r"(?P<active>PENDING)",
    r"(?P<idle>EMPTY)",
    r"(?P<active>READY)",
    r"(?P<active>ALLOCATED)",
    r"(?P<starved>STARVED)",
    r"(?P<transitioning>CONFIGURING)",
    r"(?P<transitioning>UPLOADING)",
    r"(?P<transitioning>DOWNLOADING)",
    r"(?P<idle>WAITING)",
    r"(?P<failed>FAILING)",
    r"(?P<transitioning>NEW)",
    r"(?P<transitioning>STOPPING)",
    r"(?P<cancelled>STOPPED)",
    r"(?P<transitioning>UNKNOWN)",
    r"(?P<transitioning>UNAVAILABLE)",
    r"(?P<active>DOING_TASK)",
    r"(?P<idle>SLEEPING)",
    r"(?P<transitioning>LATE)",
    r"(?P<idle>FOUND)",
    r"(?P<failed>LOST)",
    r"(?P<active>TARGET)",
    r"(?P<active>EXPECTED)",
]
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
