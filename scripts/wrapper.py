"""
Decorator to catch exceptions
"""

from common import print_log


def main_wrapper(func):
    def wrapper():
        try:
            func()
        except Exception as e:
            print_log(f"Error: {e}", override_quiet=True, use_stderr=True)
            print_log("Done")
            exit(1)
        except KeyboardInterrupt:
            print_log("\nCancelled")
            exit(1)
        print_log("Done")
        exit(0)
    return wrapper
