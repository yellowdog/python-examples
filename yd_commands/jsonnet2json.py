#!/usr/bin/env python3

"""
Simple utility to take a Jsonnet file and output its JSON representation
to stdout. General purpose, not YellowDog specific.
"""

import json
import sys

from yd_commands.check_imports import check_jsonnet_import
from yd_commands.compact_json import CompactJSONEncoder


def main():
    check_jsonnet_import()
    from _jsonnet import evaluate_file

    if len(sys.argv) != 2:
        print("Error: Usage: yd-jsonnet2json <file.jsonnet>")
        exit(1)

    try:
        json_data = json.loads(evaluate_file(sys.argv[1]))
        print(json.dumps(json_data, indent=2, cls=CompactJSONEncoder))
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


# Entry point
if __name__ == "__main__":
    main()
