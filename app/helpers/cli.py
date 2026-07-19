
# app/helpers/cli.py

import argparse


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Synapse."""

    parser = argparse.ArgumentParser(
        description="Synapse CLI"
    )

    parser.add_argument(
        "platform",
        choices=["telegram", "teams"],
        help="The platform to run Synapse on.",
    )

    return parser.parse_args()
