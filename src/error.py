import sys


def fail_with_message(message: str):
    print(f"::error::{message}")
    sys.exit(1)
