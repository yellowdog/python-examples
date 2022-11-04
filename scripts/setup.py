import io
import re

import setuptools  # type: ignore

src = io.open("__init__.py", encoding="utf-8").read()
metadata = dict(re.findall('__([a-z]+)__ = "([^"]+)"', src))

REQUIREMENTS = list(open("requirements.txt"))
VERSION = metadata["version"]

setuptools.setup(
    name="yellowdog-python-examples",
    version=VERSION,
    author="YellowDog Limited",
    description="YellowDog Python Example Scripts",
    url="https://github.com/yellowdog/python-examples",
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
        "Programming Language :: Python :: 3",
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
