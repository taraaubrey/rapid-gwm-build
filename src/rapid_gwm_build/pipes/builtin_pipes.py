import logging
from pandas import DataFrame

# Define some example functions
def read_data(data, **kwargs):
    logging.debug(f"@ the read_data function")
    return data


def to_mf6_txt(data: DataFrame, map=None, cols=None, outdir=None, node_id=None, **kwargs):
    logging.debug(f"@ the to_mf6_txt function")

    pkg = node_id.split('.')[1] if node_id else None

    if map is not None:
        #rename columns from the map
        data = data.rename(columns=map)

    outs = {}
    if cols:
        if 'stress_period' in data.columns:
            stress_period = data['stress_period'].unique()
            for kper in stress_period:
                kper_data = data.loc[data['stress_period'] == kper]
                kper_data = kper_data.drop(columns=['stress_period'])
                kper_data = kper_data[cols]
                fname = f"{pkg}_stress_period_data_{kper}.txt"
                out_path = fname if outdir is None else f"{outdir}\{fname}"
                header = [f'#{col}' for col in cols]
                kper_data.to_csv(out_path, index=False, header=header, sep=' ')
                outs[int(kper)-1] = {'filename': out_path}
        else:
            data = data[cols]
            fname = f"{pkg}_stress_period_data_1.txt"
            out_path = fname if outdir is None else f"{outdir}\{fname}"
            header = [f'#{col}' for col in cols]
            data.to_csv(out_path, index=False, header=header, sep=' ')
            outs[1] = {'filename': out_path}
    else:
        outs = data

    return outs
