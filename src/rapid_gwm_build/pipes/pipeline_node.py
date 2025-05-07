
class PipelineNode:
    """
    A class representing a node in a pipeline.
    Each node can have multiple nkey and outputs, and can be connected to other nodes.
    """
    def __init__(self, name, operation, inkeys, outkeys):
        self.name = name
        self.operation = operation
        self.inkeys = inkeys
        self.outkeys = outkeys
        self.cached_output = None  # For caching results
        self.last_updated = None   # For tracking changes

    def execute(self, data_store):
        ikey_data = [data_store.get(i) for i in self.inkeys]

        if all(data is not None for data in ikey_data) or not self.inkeys:
            # Execute the operation if all nkey are available or if there are no nkey
            self.cached_output = self.operation(*ikey_data)
            data_store[self.outkeys] = self.cached_output
            return True
        else:
            print(f"Missing nkey for {self.name}: {self.nkey}")
            return False
        

class GraphPipeline:
    def __init__(self):
        self.local_cache = None

    def add_pipeline_node(self, pnode: PipelineNode, graph):
        # assume input nodes are already in the graph
        graph.add_node(pnode.name, ntype="pipeline", data=pnode)
        graph.add_edges_from([(pnode.name, ikey) for ikey in pnode.inkeys])
        graph.add_edges_from([(pnode.name, ikey) for ikey in pnode.outkeys])
            