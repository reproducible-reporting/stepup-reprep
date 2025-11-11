#!/usr/bin/env python3
"""Compare unplot output to expected output."""

import argparse
import json
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="validate-unplot",
        description="Validate unplot output against expected output.",
    )
    parser.add_argument("reference", type=str, help="Path to the expected unplot output JSON file.")
    parser.add_argument("current", type=str, help="Path to the actual unplot output JSON file.")
    return parser.parse_args(argv)


def main():
    args = parse_args()

    with open(args.reference) as ref_file:
        reference = json.load(ref_file)

    with open(args.current) as curr_file:
        current = json.load(curr_file)

    if reference["units"] != current["units"]:
        print(f"Units do not match: expected {reference['units']}, got {current['units']}")
        sys.exit(1)
    if set(reference["curves"]) != set(current["curves"]):
        print("Curve names do not match:")
        print(f"Expected: {list(reference['curves'])}")
        print(f"Got:      {list(current['curves'])}")
        sys.exit(1)
    for key_curve, curve in reference["curves"].items():
        if set(curve) != set(current["curves"][key_curve]):
            print(f"Data keys do not match in curve '{key_curve}':")
            print(f"Expected: {list(curve)}")
            print(f"Got:      {list(current['curves'][key_curve])}")
            sys.exit(1)
        for key_data, ref_data in curve.items():
            cur_data = current["curves"][key_curve][key_data]
            if len(ref_data) != len(cur_data):
                print(f"Data length mismatch in curve '{key_curve}', data '{key_data}':")
                print(f"Expected length: {len(ref_data)}")
                print(f"Got length:      {len(cur_data)}")
                sys.exit(1)
            for i, (ref_value, cur_value) in enumerate(zip(ref_data, cur_data, strict=True)):
                if abs(ref_value - cur_value) > 1e-6 * max(abs(ref_value), abs(cur_value)):
                    print(
                        f"Data value mismatch in curve '{key_curve}', data '{key_data}', "
                        f"index {i}: expected {ref_value}, got {cur_value}"
                    )
                    sys.exit(1)


if __name__ == "__main__":
    main()
