import flopy as fp
import numpy as np

def create_btms(nlay, top, model_thickness):
    btms = []
    thickness = model_thickness / nlay
    topi = top.copy()
    for i in range(nlay):
        btmi = topi - thickness
        topi = btmi.copy()
        btms.append(btmi)
    return np.array(btms)

def create_wel_pkg(indices, q):
    inlays = indices[0,:,0,-1]
    inrows = indices[1,:,0,-1]
    incols = indices[2,:,0,-1]
    iqs = np.ones_like(inlays) * q
    return zip(inlays, inrows, incols, iqs)

res = 10
head = -2

period_data = [
    [1, 1, 1],
    [7, 1, 1],
    [50, 1, 1],
    [100, 1, 1],
    [365, 1, 1],
]

k = np.ones(shape=(10,1,100)) * 10

nlay = k.shape[0]
nrow = k.shape[1]
ncol = k.shape[2]
delc = np.ones_like(k[0,:,0]) * res
delr = np.ones_like(k[0,0,:]) * res
top = np.zeros_like(delc)
btm = create_btms(nlay, top, model_thickness=100)
idomain = np.ones_like(k)

strt = np.ones_like(delc) * head

indices = np.indices(k.shape)

wel_meta = create_wel_pkg(indices, q=100)
wel = {
    0: [(j, i, k, q) for j, i, k, q in wel_meta]
}
chd = {
    0: [(0,0,0,head)] # stream level at model top
}

sim = fp.mf6.MFSimulation(exe_name=r'notebooks/mf6')
tdis = fp.mf6.ModflowTdis(
    simulation=sim,
    nper=len(period_data),
    perioddata=period_data
    )
ims = fp.mf6.ModflowIms(simulation=sim)
gwf = fp.mf6.ModflowGwf(simulation=sim)

npf = fp.mf6.ModflowGwfnpf(
    model=gwf,
    k=k)
dis = fp.mf6.ModflowGwfdis(
    model=gwf,
    nlay=nlay,
    nrow=nrow,
    ncol=ncol,
    delr=delr,
    delc=delc,
    top=top,
    botm=btm,
    idomain=idomain,
)
ic = fp.mf6.ModflowGwfic(
    model=gwf,
    strt=strt,
)
wel = fp.mf6.ModflowGwfwel(
    model=gwf,
    stress_period_data=wel,
)
chd = fp.mf6.ModflowGwfchd(
    model=gwf,
    stress_period_data=chd,
)

sim.write_simulation()
sim.run_simulation()

print('run successful')

# get heads
hds = gwf.output.__budget()

# plot heads xsection

# pest setup of anisotropy