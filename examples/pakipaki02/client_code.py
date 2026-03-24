"""Example: Build the pakipaki02 model using the rmb Python API."""

from rapid_gwm_build import build

if __name__ == "__main__":
    result = build(
        "examples/pakipaki02/pakipaki02.yaml",
        cache=False,
        verbose=True,
    )
    print(result)