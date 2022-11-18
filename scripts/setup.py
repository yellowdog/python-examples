import io
import re

import setuptools  # type: ignore

with open("PYPI_README.md", "r") as fh:
    long_description = fh.read()

src = io.open("__init__.py", encoding="utf-8").read()
metadata = dict(re.findall('__([a-z]+)__ = "([^"]+)"', src))

REQUIREMENTS = list(open("requirements.txt"))
VERSION = metadata["version"]

setuptools.setup(
    name="yellowdog-python-examples",
    version=VERSION,
    author="YellowDog Limited",
    author_email="support@yellowdog.co",
    description="Example scripts using the YellowDog Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yellowdog/python-examples/tree/main/scripts",
    py_modules=[
        "__init__",
        "abort",
        "args",
        "cancel",
        "common",
        "compact_json",
        "config_keys",
        "delete",
        "download",
        "interactive",
        "list",
        "object_utilities",
        "printing",
        "provision",
        "reformat_json",
        "shutdown",
        "submit",
        "terminate",
        "version",
        "which_config",
        "wrapper",
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
    ],
    python_requires=">=3.7",
    install_requires=REQUIREMENTS,
    entry_points={
        "console_scripts": [
            "yd-abort=abort:main",
            "yd-cancel=cancel:main",
            "yd-delete=delete:main",
            "yd-download=download:main",
            "yd-list=list:main",
            "yd-provision=provision:main",
            "yd-reformat-json=reformat_json:main",
            "yd-shutdown=shutdown:main",
            "yd-submit=submit:main",
            "yd-terminate=terminate:main",
            "yd-version=version:main",
            "yd-which-config=which_config:main",
        ]
    },
)
