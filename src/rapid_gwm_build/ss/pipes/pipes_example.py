input_kwargs = {
    'key': 'top',
}
input = 'top'
in_node = 'core.2Dmesh' #pipeline
out_node = 'dis-mydis.top' #cmd_kwarg

#PIPE Function (needs the network to access variables)
def attr_from_mesh(out_key:str, network=None):
    # get the mesh from the network
    mesh = network.get_node('core.2Dmesh').mesh

    attr = mesh.get_attr(input)  # get the top array from the mesh

    # add node and new edge
    network.add_node('top.attr_from_mesh.dis-mydis.top', ntype='pipe', attr=attr)



def array2text(data, dtype='int', delimeter= ' '):
    # convert the array to a text file
    if dtype == 'int':
        arr = data.astype(int)
    elif dtype == 'float':
        arr = data.astype(float)
    else:
        raise ValueError(f"Unsupported dtype: {dtype}")

    # convert the array to a string with the specified delimiter
    arr_str = delimeter.join(map(str, arr))

    return arr_str


in_node = 'usr.drn-mydrn.cond' #where data is a filename/value
temp1_node = 'data.drn-mydrn.cond' #array
temp2_node = 'data.drn-mydrn.elev' #array

# SIMPLE PIPELINE
# 1 - create array of data
#   (usr.drn-mydrn.elev, core.mesh) -> from_the_mesh -> data.drn-mydrn.elev
# 2 - create arary of data
#   (usr.drn-mydrn.cond, core.mesh) -> from_the_mesh -> data.drn-mydrn.cond
# 3 - create active layer
#   (core.mesh) -> domain_from_top -> core.mesh.domain_from_top
# 4 - create stress period data
#   (core.mesh.domain_from_top ; data.drn-mydrn.cond ; data.drn-mydrn.elev) -> stress_period_data -> core.mesh.stress_period_data
final_node = 'mf6.drn-mydrn.stressperioddata' #cmd_kwarg


def discretize_2D(data, network):
    # get the mesh from the network
    mesh = network.get_node('core.2Dmesh').mesh

    # get the data from the mesh
    data = mesh.get_attr(input)  # get the top array from the mesh

    # discretize the data
    data = data.astype(int)

    # add node and new edge
    network.add_node('top.discretize.dis-mydis.top', ntype='pipe', attr=data)
