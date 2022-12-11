#!/usr/bin/env python3

"""
Report version numbers
"""

from sys import executable
from sys import version as py_version

from yellowdog_client._version import __version__ as yd_sdk_version

from yd_commands.__init__ import __version__


def main():
    print(f" YellowDog Python Examples Version:   {__version__}")
    print(f" YellowDog SDK Version:               {yd_sdk_version}")
    print(f" Python Version:                      {py_version.split()[0]} ")
    print(f" Python Executable:                   {executable}")


if __name__ == "__main__":
    main()
