
from rapid_gwm_build.pipeline_node import PipelineNode

def array2text(data, **kwargs):
    return 'output of array2text', 'some_filename'

def stress_period_data(mesh, cond, elev):
    # Example implementation
    return 'output of stess_period_data'

def discretize_2D(data, mesh):
    # Example implementation
    return 'output of discretize_2D'

def adjust_top(mesh, rbtom):
    # Example implementation
    return 'output of adjust_top'

from_mesh_top = PipelineNode(
    name="from_mesh_top",
    operation=lambda mesh: mesh.top,
    inkeys=['core.2Dmesh'],
    outkeys=['data.dis.top'],
)

adjust_from_rbtm = PipelineNode(
    name="adjust_top",
    operation=adjust_top,
    inkeys=['core.mesh.grid', 'data.sfr.rbtom'],
    outkeys=['core.mesh-modified.grid'],
)

top_output = PipelineNode(
    name="top_output",
    operation=array2text,
    inkeys=['dis.top'],
    outkeys=['dis.top', 'filename.dis.top'],
)

from_mesh_botm = PipelineNode(
    name="from_mesh_botm",
    operation=lambda mesh: mesh.botm,
    inkeys=['core.2Dmesh'],
    outkeys=['data.dis.botm'],
)

discretize_cond = PipelineNode(
    name="discretize_2D",
    operation=discretize_2D,
    inkeys=['usr.drn.cond', 'core.2Dmesh'],
    outkeys=['data.drn.cond'],
)

discretize_elev = PipelineNode(
    name="discretize_2D",
    operation=discretize_2D,
    inkeys=['usr.drn.elev', 'core.2Dmesh'],
    outkeys=['data.drn.elev'],
)

stress_period_data_drn = PipelineNode(
    name="stress_period_data_drn",
    operation=stress_period_data,
    inkeys=['core.2Dmesh', 'data.drn.cond', 'data.drn.elev'],
    outkeys=['mf6.drn-mydrn.stressperioddata'],
)


pipe_registry = {
    'from_mesh_top': from_mesh_top,
    'adjust_from_rbtm': adjust_from_rbtm,
    'top_output': top_output,
    'from_mesh_botm': from_mesh_botm,
    'discretize_cond': discretize_cond,
    'discretize_elev': discretize_elev,
    'stress_period_data_drn': stress_period_data_drn,
}