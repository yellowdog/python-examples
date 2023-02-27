#!/usr/bin/env python3

"""
Report version numbers, etc.
"""

from os.path import abspath
from sys import argv, executable, path
from sys import version as py_version

from yellowdog_client._version import __version__ as yd_sdk_version

from yd_commands.__init__ import __version__

DOCS_URL = f"https://github.com/yellowdog/python-examples/blob/v{__version__}/README.md"


def check_for_jsonnet() -> str:
    try:
        from _jsonnet import evaluate_file, version

        return f"Jsonnet is installed (version {version})"
    except ImportError:
        return "Jsonnet is not installed"


def main():
    print(f"  YellowDog Python Examples Version:   {__version__} (Docs: {DOCS_URL})")
    print(f"  Jsonnet Support:                     {check_for_jsonnet()}")
    print(f"  YellowDog SDK Version:               {yd_sdk_version}")
    print(f"  Python Version:                      {py_version.split()[0]} ")
    if "--debug" in argv:
        print(f"  Command:                             {abspath(__file__)}")
        print(f"  Python Executable:                   {executable}")
        for i, p in enumerate(path, start=1):
            print(f"    Path-{str(i).zfill(2)}:                           {p}")


if __name__ == "__main__":
    main()
