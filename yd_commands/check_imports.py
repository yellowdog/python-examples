"""
Handle optional imports.
"""


def check_jsonnet_import():
    # Jsonnet is not installed by default, due to a binary build requirement
    # on some platforms.
    try:
        from _jsonnet import evaluate_file
    except ImportError:
        raise Exception(
            "The 'jsonnet' package is not installed by default; "
            "it can be installed using 'pip install jsonnet'"
        )
