#!/usr/bin/env python
import random

TEXT_SNIPPETS = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
""".split()


EQ_SNIPPETS = r"""
x y \sin(\theta) \hat{H} \vec{B} \int_0^\infty f(x)\,dx
\{i^2\}_{i=1}^N e^{2it\pi\omega} \tan(x)
""".split()


def main():
    parts = []
    for _ in range(100):
        parts.append(random.choice(TEXT_SNIPPETS))
        parts.append(f"$`{random.choice(EQ_SNIPPETS)}`$")
    print(" ".join(parts))


if __name__ == "__main__":
    main()
