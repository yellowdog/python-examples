#!/usr/bin/env python3

"""
Report version numbers, etc.
"""

from os.path import abspath
from sys import executable, path
from sys import version as py_version

from yellowdog_client._version import __version__ as yd_sdk_version

from yd_commands.__init__ import __version__

DOCS_URL = f"https://github.com/yellowdog/python-examples/blob/v{__version__}/README.md"


def main():
    print(f"  YellowDog Python Examples Version:   {__version__}")
    print(f"  YellowDog SDK Version:               {yd_sdk_version}")
    print(f"  Command:                             {abspath(__file__)}")
    print(f"  Python Version:                      {py_version.split()[0]} ")
    print(f"  Python Executable:                   {executable}")
    for i, p in enumerate(path, start=1):
        print(f"    Path-{str(i).zfill(2)}:                             {p}")
    print(f"  Documentation:                       {DOCS_URL}")


if __name__ == "__main__":
    main()
