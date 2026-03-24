E402 Module level import not at top of file
  --> examples/pakipaki02/client_code.py:17:1
   |
15 | )
16 |
17 | from rapid_gwm_build.parsers.config_parser import ConfigParser
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from rapid_gwm_build.nodes.parse.node_parser import NodeParser
19 | from rapid_gwm_build.graph_builder import GraphBuilder
   |

E402 Module level import not at top of file
  --> examples/pakipaki02/client_code.py:18:1
   |
17 | from rapid_gwm_build.parsers.config_parser import ConfigParser
18 | from rapid_gwm_build.nodes.parse.node_parser import NodeParser
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from rapid_gwm_build.graph_builder import GraphBuilder
20 | from rapid_gwm_build.node_engine import NodeBuildEngine
   |

E402 Module level import not at top of file
  --> examples/pakipaki02/client_code.py:19:1
   |
17 | from rapid_gwm_build.parsers.config_parser import ConfigParser
18 | from rapid_gwm_build.nodes.parse.node_parser import NodeParser
19 | from rapid_gwm_build.graph_builder import GraphBuilder
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from rapid_gwm_build.node_engine import NodeBuildEngine
21 | from rapid_gwm_build.rmb_runner import RMBRunner
   |

E402 Module level import not at top of file
  --> examples/pakipaki02/client_code.py:20:1
   |
18 | from rapid_gwm_build.nodes.parse.node_parser import NodeParser
19 | from rapid_gwm_build.graph_builder import GraphBuilder
20 | from rapid_gwm_build.node_engine import NodeBuildEngine
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 | from rapid_gwm_build.rmb_runner import RMBRunner
   |

E402 Module level import not at top of file
  --> examples/pakipaki02/client_code.py:21:1
   |
19 | from rapid_gwm_build.graph_builder import GraphBuilder
20 | from rapid_gwm_build.node_engine import NodeBuildEngine
21 | from rapid_gwm_build.rmb_runner import RMBRunner
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
22 |
23 | from rapid_gwm_build.registries import BUILDER_REGISTRY
   |

E402 Module level import not at top of file
  --> examples/pakipaki02/client_code.py:23:1
   |
21 | from rapid_gwm_build.rmb_runner import RMBRunner
22 |
23 | from rapid_gwm_build.registries import BUILDER_REGISTRY
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
24 |
25 | def main():
   |

F841 Local variable `setup` is assigned to but never used
  --> examples/pakipaki02/client_code.py:47:5
   |
45 |     # Process each simulation block
46 |     sim_cfg = config.get("simulation", {})
47 |     setup = sim_cfg.pop('setup', {})
   |     ^^^^^
48 |
49 |     print("\tPrepping: Processing simulation...")
   |
help: Remove assignment to unused variable `setup`

F841 Local variable `G` is assigned to but never used
  --> examples/pakipaki02/client_code.py:65:5
   |
63 |     print("\tBuild stage 1: Creating dependency graph...")
64 |     graphbuilder = GraphBuilder(all_nodes)
65 |     G = graphbuilder.build()
   |     ^
66 |     sG = graphbuilder.get_subgraph(ntype='module')
67 |     cG = graphbuilder.get_subgraph(ntype='mesh_config')
   |
help: Remove assignment to unused variable `G`

F841 Local variable `nlist` is assigned to but never used
  --> refs/mp7_utils.py:47:5
   |
45 |     from scipy.spatial import KDTree
46 |     print('building KDTree')
47 |     nlist = []
   |     ^^^^^
48 |     sidxlist = []
49 |     if mask is None:
   |
help: Remove assignment to unused variable `nlist`

E721 Use `is` and `is not` for type comparisons, or `isinstance()` for isinstance checks
   --> refs/mp7_utils.py:132:8
    |
131 |     # get parameters for particle locations
132 |     if type(indf) == str:
    |        ^^^^^^^^^^^^^^^^^
133 |         indf = pd.read_csv(os.path.join(sim_ws, indf))
134 |     if 'obsnme' in indf.columns:
    |

F821 Undefined name `sim_ws`
   --> refs/mp7_utils.py:222:28
    |
220 |     df = pd.DataFrame([x, y, z], index=['dx', 'dy', 'dz']).T
221 |     df.index.name = 'pnum'
222 |     df.to_csv(os.path.join(sim_ws, 'random_parts.csv'))
    |                            ^^^^^^
223 |     return ()
    |

E721 Use `is` and `is not` for type comparisons, or `isinstance()` for isinstance checks
   --> refs/mp7_utils.py:254:8
    |
252 |     import flopy
253 |
254 |     if type(gwf) == str:
    |        ^^^^^^^^^^^^^^^^
255 |         # get model stuff
256 |         sim = flopy.mf6.MFSimulation.load(sim_ws=model_ws, load_only=['dis'])
    |

E721 Use `is` and `is not` for type comparisons, or `isinstance()` for isinstance checks
   --> refs/mp7_utils.py:270:8
    |
268 |     if len(gclass_keys)==0:
269 |         gclass_keys = [int(_) for _ in np.unique(gclass)]
270 |     if type(par) == str:
    |        ^^^^^^^^^^^^^^^^
271 |         par = pd.read_csv(os.path.join(model_ws, par), index_col=0)
272 |     if 'obsnme' in par.columns:
    |

F841 Local variable `tdis_name` is assigned to but never used
   --> refs/mp7_utils.py:402:13
    |
400 |     for f in os.listdir(model_ws):
401 |         if f.endswith('.tdis'):
402 |             tdis_name = f
    |             ^^^^^^^^^
403 |     # write mp7 files
404 |     with open(os.path.join(model_ws, f'{mpsim_name}.mpnam'), 'w+') as f:
    |
help: Remove assignment to unused variable `tdis_name`

E721 Use `is` and `is not` for type comparisons, or `isinstance()` for isinstance checks
   --> refs/mp7_utils.py:477:8
    |
475 |     date_rand_state = np.random.RandomState(666666666)
476 |     # gwf stuff
477 |     if type(gwf) == str:
    |        ^^^^^^^^^^^^^^^^
478 |         sim = flopy.mf6.MFSimulation.load(sim_ws=model_ws, load_only=['dis', 'ghb', 'wel'], verify_data=False)
479 |         gwf = sim.get_model()
    |

F821 Undefined name `plt`
   --> refs/mp7_utils.py:828:13
    |
826 |         for site in mdf.index:
827 |             mpsim.loc[site,['mrtsim']].hist(bins=100)
828 |             plt.title(f"age for site {site}\n,"
    |             ^^^
829 |                       f"min = {mdf.loc[site, 'mrtsim_min']},\n"
830 |                       f"mean = {mdf.loc[site, 'mrtsim_mean']},\n"
    |

F821 Undefined name `plt`
   --> refs/mp7_utils.py:835:13
    |
833 |             if not os.path.exists(os.path.join(sim_ws, '..', 'figures')):
834 |                 os.mkdir(os.path.join(sim_ws, '..', 'figures'))
835 |             plt.savefig(os.path.join(sim_ws, '..', 'figures', f'{site}.png'))
    |             ^^^
836 |             plt.close()
837 |     return mdf
    |

F821 Undefined name `plt`
   --> refs/mp7_utils.py:836:13
    |
834 |                 os.mkdir(os.path.join(sim_ws, '..', 'figures'))
835 |             plt.savefig(os.path.join(sim_ws, '..', 'figures', f'{site}.png'))
836 |             plt.close()
    |             ^^^
837 |     return mdf
    |

F841 Local variable `par` is assigned to but never used
   --> refs/mp7_utils.py:859:5
    |
857 |     if par_file is None:
858 |         par_file = f'{mpsim_name}.par.csv'
859 |     par = pd.read_csv(os.path.join(sim_ws, par_file), index_col=0)
    |     ^^^
860 |     if outname is None:
861 |         outname = obs_file.replace('.obs','.sim')
    |
help: Remove assignment to unused variable `par`

E721 Use `is` and `is not` for type comparisons, or `isinstance()` for isinstance checks
   --> refs/mp7_utils.py:935:8
    |
933 |         return k
934 |
935 |     if type(og) == pd.DataFrame:
    |        ^^^^^^^^^^^^^^^^^^^^^^^^
936 |         og.columns = og.columns.str.lower()
937 |         if axis == 0:  # replace in index
    |

E721 Use `is` and `is not` for type comparisons, or `isinstance()` for isinstance checks
   --> refs/mp7_utils.py:952:10
    |
950 |         else:
951 |             AssertionError(axis in [0, 1])
952 |     elif type(og) == list:
    |          ^^^^^^^^^^^^^^^^
953 |         og = [str(_).lower() for _ in og]
954 |         og = rep(og)
    |

F401 `.cache.memory` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
 --> src/rapid_gwm_build/__init__.py:1:20
  |
1 | from .cache import memory
  |                    ^^^^^^
  |
help: Use an explicit re-export: `memory as memory`

F821 Undefined name `linput`
  --> src/rapid_gwm_build/nodes/parse/blocks/pipeline.py:39:12
   |
37 |     steps = _resolve_level_steps(level_config, ordered_input)
38 |     options = _resolve_level_options(level_config)
39 |     return linput, steps, options
   |            ^^^^^^
   |

F841 Local variable `input_data` is assigned to but never used
  --> src/rapid_gwm_build/nodes/ss_node_types.py:54:9
   |
52 |             return input_id
53 |
54 |         input_data = resolve_input(self.input_id)
   |         ^^^^^^^^^^
55 |
56 |         func_args = {}
   |
help: Remove assignment to unused variable `input_data`

F841 Local variable `pipeline` is assigned to but never used
   --> src/rapid_gwm_build/nodes/ss_node_types.py:305:21
    |
303 |             elif self.param in ['top', 'bottoms']:
304 |                 if self.param == 'top':
305 |                     pipeline = sim_nodes.get(mesh_node.src['top'])
    |                     ^^^^^^^^
306 |                     self._data = mesh_node.data.make_top(self.src)
307 |                 elif self.param == 'bottoms':
    |
help: Remove assignment to unused variable `pipeline`

F811 Redefinition of unused `dependencies` from line 64
   --> src/rapid_gwm_build/ss/nodes/node_base.py:176:9
    |
175 |     @property
176 |     def dependencies(self) -> list:
    |         ^^^^^^^^^^^^ `dependencies` redefined here
177 |         if self._dependencies is None:
178 |             self._dependencies = self._get_dependencies()
    |
   ::: src/rapid_gwm_build/ss/nodes/node_base.py:64:9
    |
 63 |     @property
 64 |     def dependencies(self):
    |         ------------ previous definition of `dependencies` here
 65 |         """
 66 |         Returns the dependencies of the node.
    |
help: Remove definition: `dependencies`

F841 Local variable `input_data` is assigned to but never used
  --> src/rapid_gwm_build/ss/nodes/node_types.py:54:9
   |
52 |             return input_id
53 |
54 |         input_data = resolve_input(self.input_id)
   |         ^^^^^^^^^^
55 |
56 |         func_args = {}
   |
help: Remove assignment to unused variable `input_data`

F841 Local variable `pipeline` is assigned to but never used
   --> src/rapid_gwm_build/ss/nodes/node_types.py:305:21
    |
303 |             elif self.param in ['top', 'bottoms']:
304 |                 if self.param == 'top':
305 |                     pipeline = sim_nodes.get(mesh_node.src['top'])
    |                     ^^^^^^^^
306 |                     self._data = mesh_node.data.make_top(self.src)
307 |                 elif self.param == 'bottoms':
    |
help: Remove assignment to unused variable `pipeline`

E712 Avoid equality comparisons to `False`; use `not check:` for false checks
  --> src/rapid_gwm_build/ss/simulation.py:92:20
   |
90 |                 check = self._check_nodeid_in_sim(dep_id)
91 |                 
92 |                 if check==False:
   |                    ^^^^^^^^^^^^
93 |                     if dep_id.split(".")[0] == "mesh":
94 |                         mesh_check = self._check_nodeid_in_sim('mesh')
   |
help: Replace with `not check`

F841 Local variable `dep_node` is assigned to but never used
   --> src/rapid_gwm_build/ss/simulation.py:113:21
    |
111 |                         self._new_node(ncfg=new_ncfg)
112 |                 else:
113 |                     dep_node = self.nodes.get(dep_id, None)
    |                     ^^^^^^^^
114 |                 
115 |                 if node:
    |
help: Remove assignment to unused variable `dep_node`

Found 30 errors.
No fixes available (11 hidden fixes can be enabled with the `--unsafe-fixes` option).
