"""
Handle optional imports.
"""


def check_jsonnet_import():
    # Jsonnet is not installed by default, due to a binary build requirement
    # on some platforms. The 'jsonnet-binary' package can be used to overcome
    # the requirement for build tools to be installed.
    try:
        from _jsonnet import evaluate_file
    except ImportError:
        raise Exception(
            "Jsonnet support is not included by default. The 'jsonnet' Python package"
            " can usually be installed by adding the option to pip:"
            ' pip install -U "yellowdog-python-examples[jsonnet]"'
        )


def check_cloudwizard_imports():
    # The cloud provider SDKs for Cloud Wizard are not installed by default.
    try:
        import boto3  # One example package required for Cloud Wizard
    except ImportError:
        raise Exception(
            "The cloud provider SDKs needed for Cloud Wizard are not installed"
            " by default. They can be installed by adding the option to pip:"
            ' pip install -U "yellowdog-python-examples[cloudwizard]"'
        )
