"""Example: Build the simple Freyburg model using the rmb Python API.

NOTE: This example YAML uses the old 'simulations:' format and needs
updating to the canonical 'simulation:' + 'setup:' format before it will
work with the current API. See pakipaki02/pakipaki02.yaml for the
current format.
"""

from rapid_gwm_build import create_simulation

input_yaml = "examples/simple_freyburg/freyburg_1lyr_stress.yaml"

sim = create_simulation(input_yaml)
sim.build()
sim.write()

print("Done.")