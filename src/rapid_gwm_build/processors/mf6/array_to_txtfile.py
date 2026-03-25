"""Processor for saving arrays to files."""
import numpy as np
import pandas as pd

from ...registries import register_processor

@register_processor("array_to_file", 
                    dependency_args={
                        'sim_ws': '@modules.sim.sim_ws',
                        'modelname': '@modules.gwf.modelname',
                        'nper': '@modules.tdis.nper', 
                        'idomain': '@mesh.active_domain',
                        }, 
                    context_required=True)
def array_to_file(data, output_type, sim_ws, **kwargs):
    """Save array data to various file formats."""

    if output_type == 'array':
        return _to_array(data, sim_ws, **kwargs)
    elif output_type == 'table':
        return _to_table(data, sim_ws, **kwargs)
    

def _to_array(data, sim_ws, context_path, modelname, idomain, nper,
                  by_layer=False, by_stress_period=False, dtype='float',
                  filename_format='{modelname}.{pkg_type_name}_{paramname}.txt',
                  **kwargs):

    fmt = '%d' if dtype == 'int' else '%.18e'

    if by_layer:
        filenames = []
        for ilay in range(idomain.shape[0]):
            filename = filename_format.format(
                    modelname=modelname,
                    pkg_type_name=context_path[1],
                    paramname=context_path[2],
                    ilay=ilay)
            _save_array(sim_ws, data[ilay], filename, fmt=fmt)
            filenames.append({'filename': filename})
        return filenames
    elif by_stress_period:
        output = {}
        for kper in range(nper):
            filename = filename_format.format(
                    modelname=modelname,
                    pkg_type_name=context_path[1],
                    paramname=context_path[2],
                    kper=kper)
            _save_array(sim_ws, data[kper], filename, fmt=fmt)
            output[kper] = {'filename': filename}
        return output
    else:
        filename = filename_format.format(
                modelname=modelname,
                pkg_type_name=context_path[1],
                paramname=context_path[2])

        _save_array(sim_ws, data, filename, fmt=fmt)
        return {'filename': filename}

def _save_array(sim_ws, data, filename, fmt='%.18e'):
    from pathlib import Path
    abs_path = Path(sim_ws) / Path(filename)
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(abs_path, data, fmt=fmt)


def _to_table(data, sim_ws, idomain, nper, col_names, filename_format, modelname, context_path, by_stress_period=True, **kwargs):
    """
    Save a DataFrame to a text file with specified separator.
    
    Args:
        df: pandas DataFrame to save
        filename: Name of the output text file
        sim_ws: model workspace directory
    """
    from pathlib import Path

    if by_stress_period:
        output = {}
        for kper in range(nper):
            
            if isinstance(data, np.ndarray):
                coordinate_cols = {'i', 'j', 'k'}
                data_cols = [col for col in col_names if col not in coordinate_cols]
                val_name = data_cols[0] if data_cols else 'value'
                data = {val_name: data}
            elif isinstance(data, dict):
                pass
            else:
                raise ValueError("Data must be a ndarray or dict.")
            
            df = datadict_to_df(kper, data, idomain, col_names)

            out_filename = filename_format.format(
                    modelname=modelname, 
                    pkg_type_name=context_path[1], 
                    paramname=context_path[2], 
                    kper=kper)
            abs_path = Path(sim_ws) / Path(out_filename)
            abs_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
            df.to_csv(
                abs_path, 
                sep=' ', 
                header=False, 
                index=False
                )
            output[kper] = {'filename': out_filename}
            # _args = resolve_return_args(return_arg, kper, out_filename)
            # out_arg.update(_args)
        return output
    else:
        raise NotImplementedError("Non-stress period output not implemented yet.")


def resolve_return_args(return_arg, kper, out_filename):
    for k, v in return_arg.items():
        if isinstance(k, str):
            key = k.format(kper=kper)
        else:
            raise ValueError(f"Key {k} in return_arg must be a string formatable with 'kper'.")
        
        if isinstance(v, str):
            value = v.format(filename=out_filename)
        elif isinstance(v, dict):
            value = resolve_return_args(v, kper, out_filename)
        else:
            raise ValueError(f"Value {v} in return_arg must be a string or dict formatable with 'filename'.")
    
        return {key: value}


def datadict_to_df(kper:int, data:dict, idomain:np.ndarray, col_names:list):
    """
    Convert a dictionary of arrays to a pandas DataFrame.
    
    Args:
        data: Dictionary where keys are indices and values are arrays.
        layer: Optional layer information to include in the DataFrame.
        val_col: Name of the column for values.
    
    Returns:
        pd.DataFrame: DataFrame with index and value columns.
    """

    if isinstance(data, dict) and 'mask' in data:
        mask = data.pop('mask')
        indices = np.where((mask[kper] != 0) & (idomain != 0))
    else:
        indices = np.where(idomain != 0)
    
    dfs = {}
    dfs['k'] = indices[0] + 1
    dfs['i'] = indices[1] + 1
    dfs['j'] = indices[2] + 1
    
    for key, arr in data.items():
        if not isinstance(arr, np.ndarray):
            raise ValueError(f"Value for key '{key}' is not a numpy array.")
        dfs[key] = arr[kper][indices]

    return pd.DataFrame(dfs)[col_names]



def data_to_csv(data, idomain, nper, filename):
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