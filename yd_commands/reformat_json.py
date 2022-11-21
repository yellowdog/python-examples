#!/usr/bin/env python3

"""
Reformat JSON files using a compact JSON encoder.
Usage: ./reformat_json.py file_1.json file_2.json ...
"""

import json
import sys

from compact_json import CompactJSONEncoder


def main():
    for filename in sys.argv[1:]:
        if not filename.lower().endswith("json"):
            print(f"Ignoring non-JSON file: '{filename}'")
            continue
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Unable to process: '{filename}': {e}")
            continue
        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=2, cls=CompactJSONEncoder)
                f.write("\n")
            print(f"Reformatted: '{filename}'")
        except Exception as e:
            print(f"Unable to write file: '{filename}': {e}")
            continue


if __name__ == "__main__":
    main()
