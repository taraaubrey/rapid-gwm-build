**Still under major development:** At the moment many placeholders, and very basic functionality (proof of concept).

# Overview/Goals of rmb
`rmb` (rapid model builder) is a Python package designed to streamline the creation and manipulation of groundwater model input files. It does this by leveraging a user-defined YAML input file and a set of backend templates.

- Generic to any model software (provided a template file exists)
- Rapid model framework: YAML input file
- Visualize and capture pre-processing pipelines through to model file creation in a single place
- Uses network graph models as backend to solve for dependancy (similar to snakemake)
- Hopefully future integration with data versioning CICD (ie. DVC)

## Core Functionality
**Model Template Selection**: The input file specifies a model_type, which rmb uses to pull the appropriate backend templates.

**Graph-Based Execution**: Using the input and backend dependencies, rmb constructs a directed graph where nodes represent processing modules (e.g. creating arrays, applying spatial data) and edges represent dependencies between them.

**Model Building**: Traversing this graph, rmb generates the required model input files for engines like MODFLOW or SWAT.

**Simulation Object (sim)**: Allows investigation of intermediate or gridded data. Supports plotting and diagnostics.

**Enables modular edits**: if a node is changed (e.g. a boundary condition or array), only downstream dependent nodes are recomputed.

![Example_model_graph.png](/docs/Example_model_graph.png)
Zoom in showing the pipeline nodes for ghb build.
![Example_model_graph_subset.png](/docs/Example_model_graph_subset.png)

# Usage

```python
input_yaml = r"examples\simple_freyburg\freyburg_1lyr_stress.yaml"

sim = create_simulation(input_yaml)
```

```python
#visualize model
sim.graph.plot() # all nodes in the model (including template, pipeline, default nodes)
sim.graph.plot(subgraph=True) # this is only the nodes which are built (ie. upstream of the module nodes)
```

```python
sim.build() # resolves all the data for the nodes upstream of module nodes (ie. runs the pipelines)

#view module data
dis = sim.nodes['module.dis'].data
dis.top # view top input data for flopy

#view pipeline/pipe specific data
sim.nodes['pipeline.ghb.stress_period_data'].data
```

```python
sim.write() # writes the simulation files
sim.nodes['module.sim'].data.run_simulation() # you can run the model

```


# Nodes
## Types of nodes/Edges

- **Input nodes**:
  - **User input**: from the user config file (ie. yamls)
  - **Template**: Specific to the template model files (ie. mf6, swat). related to module nodes. This is also the 'output' of rmb, but the input to the model.
- **Module nodes**: Derived based on core inputs in user input file and backend model type template files (ie. generic, mf6, swat). 
- **Mesh nodes**: Derived based on core inputs in user input file. Represents spatial discretization.
- **Pipeline nodes**: Represents operational processes. Will have input and output nodes. Maybe this is a type of edge?

## Node Naming Convention
| Node Type     | Description           | Suggested Naming Prefix   | Example ID                            |
| -----         | --------              | ---------                 | --------------                        |
| `input`    | From frontend YAML; scope is the dict path    | `input.<usr_key_path>.<param>.<hash>`        | `input.mesh.resolution` `input.module.gwf.modelname`  |
| `template` | Specific to backend model template; cmd kwargs in module inputs | `template.<mtype>.<module>.<param>` | `template.mf6.drn.stress_period_data` |
| `module` | Logical building block from templates |` module.<kind>.<usrname> `| `module.sfr.mysfr` |
| `mesh` | Spatial discretization | `mesh.<dimension/element>` | `mesh.grid` |
| `pipeline` | Operation/process node | `pipeline.<name>` | `pipeline.interpolate_rainfall` |