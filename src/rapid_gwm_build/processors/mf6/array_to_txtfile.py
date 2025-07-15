"""Processor for saving arrays to files."""

from ...config import CONFIG
from ...registries import register_processor

@register_processor("array_to_file", 
                    dependency_args={
                        'modelname': '@modules.gwf.modelname',
                        'nper': '@modules.tdis.nper', 
                        'idomain': '@mesh.active_domain'
                        }, 
                    context_required=True)
def array_to_file(data, output_type, **kwargs):
    """Save array data to various file formats."""

    if output_type == 'array':
        return _to_array(data, **kwargs)
    elif output_type == 'table':
        return _to_table(data, **kwargs)
    

def _to_array(data, context_path, modelname, idomain, nper, mask=None, 
                  by_layer=False, by_stress_period=False, 
                  filename_format=None,
                  cmdarg_template=None, **kwargs):
    import numpy as np
    if by_layer:
        filenames = []
        for ilay in range(idomain.shape[0]):
            filename = filename_format.format(
                    modelname=modelname,
                    pkg_type_name=context_path[1],
                    paramname=context_path[2],
                    ilay=ilay)
            np.savetxt(filename, data[ilay])
            filenames.append({'filename': filename})
        return filenames
    elif by_stress_period:
        output = []
        for kper in range(nper):
            filename = filename_format.format(
                    modelname=modelname,
                    pkg_type_name=context_path[1],
                    paramname=context_path[2],
                    kper=kper)
            np.savetxt(filename, data[kper])
            output[kper] = {'filename': filename}
        return output
    else:
        filename = filename_format.format(
                modelname=modelname,
                pkg_type_name=context_path[1],
                paramname=context_path[2])
        np.savetxt(filename, data)
        return {'filename': filename}
            

def _to_table(data, idomain, nper, mask=None, by_stress_period=True, **kwargs):
    """
    Save a DataFrame to a text file with specified separator.
    
    Args:
        df: pandas DataFrame to save
        filename: Name of the output text file
        sim_ws: model workspace directory
    """
    import pandas as pd

    if by_stress_period:
        # data needs to be in tdis format
        if data.ndim != 4:
            raise ValueError("Data must be a 4D array (t, k, i, j) for stress period output.")

        for kper in range(nper):
            indices = [get_indices(data[kper], layer=i) for i in range(idomain.shape[0])]
            df = pd.DataFrame({'index': indices})

            df['k'] = df['index'].apply(lambda x: int(x[0] + 1))
            df['i'] = df['index'].apply(lambda x: int(x[1] + 1))
            df['j'] = df['index'].apply(lambda x: int(x[2] + 1))
            # delete df['index']  # remove index column if not needed
            df = df.drop(columns=['index'])
            df = df[['k', 'i', 'j'] + [col for col in df.columns if col not in ['k', 'i', 'j']]]

            df.to_csv(filename, sep=' ', header=False, index=False)
    

def get_indices(arr, layer=None, keep_value=False):
    import numpy as np
    # Get indices where exterior mask is True
    indices = np.where(arr)
    result = []
    for i in range(len(indices[0])):
        index_tuple = tuple(int(idx[i]) for idx in indices)
        ivalue = arr[tuple(index_tuple)]
        if layer is not None:
            index_tuple = (layer, index_tuple[0], index_tuple[1])
        if keep_value:
            index_tuple = [index_tuple, ivalue]
        result.append(index_tuple)

    return result