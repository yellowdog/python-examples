import io
import re

import setuptools  # type: ignore

# with open("PYPI_README.md", "r") as fh:
#     long_description = fh.read()

src = io.open("__init__.py", encoding="utf-8").read()
metadata = dict(re.findall('__([a-z]+)__ = "([^"]+)"', src))

REQUIREMENTS = list(open("requirements.txt"))
VERSION = metadata["version"]

setuptools.setup(
    name="yellowdog-python-examples",
    version=VERSION,
    author="YellowDog Limited",
    description="YellowDog Python Examples",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    url="https://github.com/yellowdog/python-examples",
    # packages=setuptools.find_packages(),
    py_modules=[
        "args",
        "cancel",
        "common",
        "config_keys",
        "delete",
        "download",
        "provision",
        "shutdown",
        "submit",
        "terminate",
        "which_config",
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
            "yd-cancel=cancel:main",
            "yd-delete=delete:main",
            "yd-download=download:main",
            "yd-provision=provision:main",
            "yd-shutdown=shutdown:main",
            "yd-submit=submit:main",
            "yd-terminate=terminate:main",
            "yd-which-config=which_config:main",
        ]
    },
)
