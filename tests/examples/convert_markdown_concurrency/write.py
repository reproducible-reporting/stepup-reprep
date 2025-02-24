#!/usr/bin/env python3
import random
import sys

TEXT_SNIPPETS = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
""".split()


def main():
    """Write a randomized markdown file."""
    random.seed(int(sys.argv[1]))
    print(" ".join(random.choice(TEXT_SNIPPETS) for _ in range(100)))


if __name__ == "__main__":
    main()
