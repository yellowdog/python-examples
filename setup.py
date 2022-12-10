import io
import re

import setuptools  # type: ignore

with open("PYPI_README.md", "r") as fh:
    long_description = fh.read()

src = io.open("yd_commands/__init__.py", encoding="utf-8").read()
metadata = dict(re.findall('__([a-z]+)__ = "([^"]+)"', src))

REQUIREMENTS = list(open("requirements.txt"))
VERSION = metadata["version"]

setuptools.setup(
    name="yellowdog-python-examples",
    version=VERSION,
    author="YellowDog Limited",
    author_email="support@yellowdog.co",
    description="Example Python commands using the YellowDog Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yellowdog/python-examples",
    packages=setuptools.find_packages(),
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
            "yd-abort=yd_commands.abort:main",
            "yd-cancel=yd_commands.cancel:main",
            "yd-delete=yd_commands.delete:main",
            "yd-download=yd_commands.download:main",
            "yd-instantiate=yd_commands.instantiate:main",
            "yd-jsonnet2json=yd_commands.jsonnet2json:main",
            "yd-list=yd_commands.list:main",
            "yd-provision=yd_commands.provision:main",
            "yd-reformat-json=yd_commands.reformat_json:main",
            "yd-shutdown=yd_commands.shutdown:main",
            "yd-submit=yd_commands.submit:main",
            "yd-terminate=yd_commands.terminate:main",
            "yd-upload=yd_commands.upload:main",
            "yd-version=yd_commands.version:main",
        ]
    },
)
