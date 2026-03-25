"""Example: Build the pakipaki02 model using the rmb Python API."""
import flopy
from rapid_gwm_build import build

if __name__ == "__main__":
    result = build(
        "examples/pakipaki02/pakipaki02.yaml",
        cache=False,
        verbose=True,
    )
    print(result)

    sim = flopy.mf6.MFSimulation.load(sim_ws=str(result.workspace))
    print(f"Loaded simulation from {result.workspace}")