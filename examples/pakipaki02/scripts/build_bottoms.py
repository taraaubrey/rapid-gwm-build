import numpy as np

def build_bottoms(
            abs_bottom: np.ndarray,
            top: np.ndarray,
            nlay: int,
            group_nlay: list,
            group_bottoms: list,
            min_thickness=1,
            ) -> np.ndarray:

    if nlay != sum(group_nlay):
        raise ValueError(f"nlay {nlay} does not match sum of group_nlay {group_nlay}: sum={sum(group_nlay)}")
    
    botms = []
    b0 = top.copy()  # initial bottom elevation is the same as the top elevation
    for i, n in enumerate(group_nlay):
        nlay_i = group_nlay[i]
        btm_i = group_bottoms[i] # constants for the bottom elevation of each group
        if abs_bottom.any():
            btm_i = np.where(abs_bottom < btm_i, btm_i, abs_bottom)  # set bottom elevation to group bottom where it is higher
        
        b_i = top - btm_i # thickness
        b_i = np.where(b_i < (min_thickness* nlay_i), (min_thickness*nlay_i), b_i) # correct to minimum thickness

        for j in range(nlay_i):
            btm_j = b0 - b_i/nlay_i  # calculate the bottom elevation for each layer
            botms.append(btm_j)
            b0 = btm_j.copy()  # update the bottom elevation for the next layer
    
    return np.array(botms)