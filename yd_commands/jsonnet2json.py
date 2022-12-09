#!/usr/bin/env python3

"""
Simple utility to take a Jsonnet file and output its JSON representation
to stdout. General purpose, not YellowDog specific.
"""

import sys


def main():
    # Jsonnet is not installed by default, due to a binary build requirement
    # on some platforms.
    try:
        from _jsonnet import evaluate_file
    except ImportError:
        raise Exception(
            "The 'jsonnet' package is not installed by default; "
            "it can be installed using 'pip install jsonnet'"
        )

    if len(sys.argv) != 2:
        print("Usage: yd-jsonnet2json <file.jsonnet>")
        exit(1)

    try:
        print(evaluate_file(sys.argv[1]))
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


# Entry point
if __name__ == "__main__":
    main()
