import matplotlib.pyplot as plt
import os
import gridit as gi
import numpy as np
import flopy as fp
import pandas as pd
from scipy.ndimage import uniform_filter

from utils import *

MODEL_NAME = 'local2'  # name of the model

# model domain
RES = 10
NLAY = 8
NLAY_THICKNESS = 10  # thickness of each layer in meters

#% paths
DOMAIN = r"C:\Users\tfo46\OneDrive - University of Canterbury\Tara_PhD\c_PhD\c_Data\b_derived\mod_model_files\pakipaki\shp\model2_domain.shp"
TOP = r"C:\Users\tfo46\OneDrive - University of Canterbury\Tara_PhD\c_PhD\c_Data/b_derived/dem_elevation_derivatives/dem_clipped.tif"
BOTTOM = r"C:\Users\tfo46\e_Python\a_rbm\rapid-gwm-build\examples\pakipaki\models\derived_data\basement_z.tif"
DRAINS = r"C:\Users\tfo46\OneDrive - University of Canterbury\Tara_PhD\c_PhD\c_Data\b_derived\mod_model_files\pakipaki\shp\model2_drains.shp"
MBR = r"C:\Users\tfo46\OneDrive - University of Canterbury\Tara_PhD\c_PhD\c_Data\b_derived\mod_model_files\pakipaki\shp\model2_mbr.shp"
LIMESTONE_INACTIVE = r"C:\Users\tfo46\OneDrive - University of Canterbury\Tara_PhD\c_PhD\c_Data\b_derived\mod_model_files\pakipaki\shp\model2_limestone_inactive_bottom.shp"
POUKAWA_BOUNDARY = r"C:\Users\tfo46\OneDrive - University of Canterbury\Tara_PhD\c_PhD\c_Data\b_derived\mod_model_files\pakipaki\shp\model2_chd.shp"
INFLUX_BOUNDARY = r"C:\Users\tfo46\OneDrive - University of Canterbury\Tara_PhD\c_PhD\c_Data\b_derived\mod_model_files\pakipaki\shp\model2_influx.shp"
OUTFLUX_BOUNDARY = r"C:\Users\tfo46\OneDrive - University of Canterbury\Tara_PhD\c_PhD\c_Data\b_derived\mod_model_files\pakipaki\shp\model2_outflux.shp"

# Directories

FIG_DIR = f'examples/manual_builds/models/{MODEL_NAME}/figures'  # directory for figures
MODEL_DIR = f'examples/manual_builds/models/{MODEL_NAME}/{MODEL_NAME}' # model workspace to be used

# create directories if they do not exist
if not os.path.exists(FIG_DIR):
    os.makedirs(FIG_DIR)

grid = gi.Grid.from_vector(DOMAIN, RES)

# top & bottom
top = grid.array_from_raster(TOP)
bottom = grid.array_from_raster(BOTTOM)  # get the bottom elevation

# open domain
arr = grid.array_from_vector(DOMAIN)
# arr = np.where(top.data > 15, 0, arr)

arr3d = arr[np.newaxis, :, :]  # shape (1, nrow, ncol)
idomain = np.broadcast_to(arr3d.data, (NLAY-2, grid.shape[0], grid.shape[1]))
#limeston_inactive
limestone = grid.array_from_vector(LIMESTONE_INACTIVE)
arr_limestone = np.where(limestone == 1, 0, arr)
# add arr_limestone to idomain
idomain = np.vstack([idomain, arr_limestone[np.newaxis, :, :], arr_limestone[np.newaxis, :, :]])

nrow = grid.shape[0]
ncol = grid.shape[1]
delr = np.ones(ncol) * RES
delc = np.ones(nrow) * RES


# dis
top = top.data  # use the top elevation for the first layer, only where idomain is active
bottom_shallow = np.where(bottom.data < 5, 5, bottom.data)  # set bottom elevation to top elevation where it is higher
thickness_shallow = top.data - bottom_shallow  # calculate the thickness of the layers
thickness_deeper = np.ones_like(thickness_shallow) * 10  # set the thickness of the deeper layers
# bottoms
min_b = 1

thicknesses = []
botm = []
b0 = top.copy()
for i in range(NLAY):
    if i < 6:
        b = np.where(thickness_shallow/6 < min_b, min_b, thickness_shallow/6)
        ibotm = b0 - b  # calculate the bottom elevation for each layer
    else:
        b = np.where(thickness_deeper/2 < min_b, min_b, thickness_deeper/2)
        ibotm = b0 - b  # calculate the bottom elevation for each layer
    thicknesses.append(b)
    botm.append(ibotm)
    b0 = ibotm.copy()  # update the bottom elevation for the next layer

botm = np.array(botm)
b_arr = np.array(thicknesses)
# plot_array_layers(b_arr, figsize=(15, 5), cmap='viridis', titles=None)

# drains
drain_arr = grid.array_from_vector(DRAINS)
drain_elev = grid.array_from_raster(TOP, resampling='min') * drain_arr.data * idomain[0]  # use the top elevation for drains, only where idomain is active
drain_input = extract_value_with_indices(drain_elev, layer=0, val_col='elev', mask_value=0)  # extract non-NaN values from the drain elevation array

# add top drains
drain_top = top * np.where(drain_elev > 0, 0, 1) * idomain[0]
drn_top_input = extract_value_with_indices(drain_top, layer=0, val_col='elev', mask_value=0)  # extract non-NaN values


# mbr
mbr_arr = grid.array_from_vector(MBR)
mbr_indices = []
for i in range(NLAY-2):  # remove mbr from bottom 2 layers
    in_idomarr, idom_i = get_interior_indices(idomain[i], layer=i)  # idomainget interior indices of the mbr area
    mbr_active = np.logical_and(mbr_arr.data, in_idomarr)  # mbr area that is active in the model domain
    mbr_indices.extend(get_indices(mbr_active, layer=i))
mbr_df = pd.DataFrame({'index': mbr_indices})

# chd - Poukawa boundary
top_min = grid.array_from_raster(TOP, resampling='min')
chd_pw_arr = grid.array_from_vector(POUKAWA_BOUNDARY)
chd_pw_active = np.logical_and(chd_pw_arr.data, in_idomarr)  # mbr area that is active in the model domain
chd_pw_active = chd_pw_active * top_min.data
chd_pw_indices = get_indices(chd_pw_active, layer=0, value=True)

chd_pw_df = pd.DataFrame({'index': [i[0] for i in chd_pw_indices]})


# influx boundaries
influx_arr = grid.array_from_vector(INFLUX_BOUNDARY)
influx_indices = []
for i in range(NLAY-2): # remove influx from bottom 2 layers
    in_idomarr, idom_i = get_interior_indices(idomain[i], layer=i)  # idomainget interior indices of the mbr area
    influx_active = np.logical_and(influx_arr.data, in_idomarr)  # mbr area that is active in the model domain
    influx_indices.extend(get_indices(influx_active, layer=i))
influx_df = pd.DataFrame({'index': influx_indices})

# outflux boundaries
outflux_arr = grid.array_from_vector(OUTFLUX_BOUNDARY)
outflux_indices = []
for i in range(NLAY-2):
    in_idomarr, idom_i = get_interior_indices(idomain[i], layer=i)  # idomainget interior indices of the mbr area
    outflux_active = np.logical_and(outflux_arr.data, in_idomarr)  # mbr area that is active in the model domain
    outflux_indices.extend(get_indices(outflux_active, layer=i))
outflux_df = pd.DataFrame({'index': outflux_indices})

# chd - confined boundary inflow
# chd_conf_arr = idomain[-1]
# chd_conf_indices = get_indices(chd_conf_arr, layer=NLAY-1)
# chd_conf_df = pd.DataFrame({'index': chd_conf_indices})
chd_conf_in = influx_df.copy()
chd_conf_out = outflux_df.copy()

# k
all_k = []
for i in range(NLAY):
    if i == 2:
        k = np.ones((nrow, ncol)) * 0.001  # horizontal hydraulic conductivity in m/day
    elif i < 6:
        k = np.ones((nrow, ncol)) * 10
    elif i == 6:
        k = np.ones((nrow, ncol)) * 0.001
    else:
        k = np.ones((nrow, ncol)) * 1000  # horizontal hydraulic conductivity in m/day
    all_k.append(k)
k_hor = np.array(all_k)  # horizontal hydraulic conductivity

# --------------------------------------------------------------------------
# other model parameters
init_h = drain_input['elev'].mean()  # initial head, based on average drain elevation

#drn
drain_input['cond'] = RES**2 * 1
drn_top_input['cond'] = 1

# chd
chd_pw_df['head'] = [i[1] for i in chd_pw_indices]  # head for Poukawa boundary
chd_conf_in['head'] = 13  # head for confined boundary
chd_conf_out['head'] = 12  # head for confined boundary

# mbr
mbr_df['flux'] = 2 # m3/d
mbr_df = mbr_df[~mbr_df['index'].isin(chd_pw_df['index'])]  # remove chd indices from mbr

# influx/outfluc
influx_df['flux'] = 1  # m3/d
outflux_df['flux'] = -1  # m3/d

# remove where mbr is active
influx_df = influx_df[~influx_df['index'].isin(mbr_df['index'])]  # remove mbr indices from influx
outflux_df = outflux_df[~outflux_df['index'].isin(mbr_df['index'])]  # remove mbr indices from outflux

# recharge
recharge = 0.0001

# 2 BUILD A MODEL -------------------------------------------------------

modelname = MODEL_NAME # model name to be used
modelws = MODEL_DIR

sim = fp.mf6.MFSimulation(sim_name=modelname, # name of simulation
                          version='mf6', # version of MODFLOW
                          exe_name=r'C:\Users\tfo46\e_Python\a_rbm\rapid-gwm-build\examples\bin\mf6.exe', # absolute path to MODFLOW executable
                          sim_ws=modelws, # path to workspace where all files are stored
                         )

tdis = fp.mf6.ModflowTdis(simulation=sim, # add to the simulation called sim (defined in prevous code cell)
                          time_units='DAYS', 
                          nper=1, # number of stress periods
                          perioddata=[(1, 1, 1)], # period length, number of steps, timestep multiplier
                         )

ims = fp.mf6.ModflowIms(simulation=sim, 
                        complexity='COMPLEX',
                        print_option='ALL'
                       )

gwf = fp.mf6.ModflowGwf(simulation=sim, 
                        modelname=modelname, # model name
                        model_nam_file=f"{modelname}.nam", # name of nam file
                        save_flows=True # make sure all flows are stored in binary output file
                       )

dis = fp.mf6.ModflowGwfdis(model=gwf, # add to groundwater flow model called gwf
                           length_units='METERS', 
                           nlay=NLAY, 
                           nrow=nrow, 
                           ncol=ncol,
                           delr=delr, 
                           delc=delc, 
                           top=top, 
                           botm=botm,
                           idomain=idomain, # 3D array of active cells 
                          )

npf = fp.mf6.ModflowGwfnpf(model=gwf, #node property flow package
                           save_specific_discharge=True, # save the specific discharge for every cell
                           icelltype=0, # 0 means constant saturated thickness
                           k=k_hor, # horizontal k value
                          )

ic = fp.mf6.ModflowGwfic(model=gwf, 
                         strt=init_h, # initial head, only used for iterative solution in steady model (arbitrary)
                        )

rch = fp.mf6.ModflowGwfrcha(model=gwf, 
                            recharge=recharge, # recharge for each cell
                            pname='rch' # package name
                           )

drn_riv = fp.mf6.ModflowGwfdrn(model=gwf, # add drain package to model gwf (created in previous code cell)
                           stress_period_data={0: drain_input.values.tolist()},
                            pname='drn_r', # package name
                            )

chd_pw = fp.mf6.ModflowGwfchd(model=gwf, # add chd package to model gwf (created in previous code cell)
                            stress_period_data={0: chd_pw_df.values.tolist()},
                            pname='chd_pw', # package name
                            save_flows=True, # save flows for this package 
                           )
chd_conf_in = fp.mf6.ModflowGwfchd(model=gwf, # add chd package to model gwf (created in previous code cell)
                            stress_period_data={0: chd_conf_in.values.tolist()},
                            pname='chd_conf_in', # package name
                            save_flows=True, # save flows for this package 
                           )
chd_conf_out = fp.mf6.ModflowGwfchd(model=gwf, # add chd package to model gwf (created in previous code cell)
                            stress_period_data={0: chd_conf_out.values.tolist()},
                            pname='chd_conf_out', # package name
                            save_flows=True, # save flows for this package 
                           )
# drn_top = fp.mf6.ModflowGwfdrn(model=gwf, # add drain package to model gwf (created in previous code cell)
#                            stress_period_data={0: drn_top_input.values.tolist()},
#                             pname='drn_t', # package name
#                             )

wel = fp.mf6.ModflowGwfwel(model=gwf, 
                           stress_period_data={0: mbr_df.values.tolist()},
                           pname='mbr' # package name
                          )
influx = fp.mf6.ModflowGwfwel(model=gwf, 
                           stress_period_data={0: influx_df.values.tolist()},
                           pname='influx' # package name
                          )
outflux = fp.mf6.ModflowGwfwel(model=gwf, 
                           stress_period_data={0: outflux_df.values.tolist()},
                           pname='outflux' # package name
                          )

# ghb = fp.mf6.ModflowGwfghb(model=gwf,
#                            stress_period_data={0: ghb_df.values.tolist()},
#                            pname='ghb' # package name
#                           )

oc = fp.mf6.ModflowGwfoc(model=gwf, # add output control to model gwf (created in previous code cell)
                         budget_filerecord=f"{modelname}.cbc", # file name where all budget output is stored
                         head_filerecord=f"{modelname}.hds", # file name where all head output is stored
                         saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
                        )

# --------------------------------------------------------
print('Double checking model...')
# visual check
pmv = fp.plot.PlotMapView(model=gwf, layer=0) # create view of layer 0
pmv.plot_array(top *idomain[0], masked_values=[1e30], alpha=0.5, cmap='viridis') # plot top elevation

pmv.plot_bc(name='chd_pw', color='purple') # add 'chd' cells
pmv.plot_bc(name='mbr', color='orange') # add 'wells' cells
pmv.plot_bc(name='drn_r', color='blue') # add 'wells' cells
pmv.plot_bc(name='chd_conf_in', color='orange') # add 'chd' cells
pmv.plot_bc(name='chd_conf_out', color='gold') # add 'chd' cells
pmv.plot_bc(name='influx', color='green') # add 'influx' cells
pmv.plot_bc(name='outflux', color='red') # add 'outflux' cells
# pmv.plot_inactive(color='lightgray', alpha=0.5) # plot inactive cells
# pmv.plot_grid(colors='silver', lw=0.01); # add grid

# save to figures
plt.savefig(os.path.join(FIG_DIR, f'{modelname}_domain.png'), dpi=300, bbox_inches='tight') # save figure


# --------------------------------------------------------
print('Writing model files...')
sim.write_simulation()  # write all model files to disk
print('Running model...')
success, _ = sim.run_simulation()  # run the model


# ------------------------------------------------------------
print('lets look at some output...')

hds = gwf.output.head() # get handle to binary head file
head = hds.get_data() # get the head data from the file
print('size of head array:', head.shape)
print('minimum head in model: ', head.min())
print('maximum head in model: ', head.max())


# ----- WATER BUDGET -------------------------------------------
# print('lets look at the budget...')

# cbb = gwf.output.budget() # get handle to binary budget file
# cbb.get_unique_record_names() # the record names stored in the file

# for n in cbb.get_unique_record_names():
#     if n == 'FLOW-JA-FACE':
#         continue
#     print(n) # print the record names
#     Q = cbb.get_data(text=n) # get the data for each record
#     if len(Q) > 0:  # check if there is data for this record
#         print(f"{n} fluxes:", Q[0]['q'].sum()) # sum of all fluxes for this record
# # get the data for each record

# Q_mbr = cbb.get_data(text='WEL')[0] # item 0 in list
# Q_ghb = cbb.get_data(text='CHD')[0] # item 0 in list
# Q_drn = cbb.get_data(text='DRN')[0] # item 0 in list
# Q_rch = cbb.get_data(text='RCHA')[0] # item 0 in list

# print('mbr fluxes:', Q_mbr['q'].sum()) # sum of all mbr fluxes
# print('ghb fluxes:', Q_ghb['q'].sum()) # sum of all ghb fluxes
# print('drn fluxes:', Q_drn['q'].sum()) # sum of all drn fluxes
# print('rch fluxes:', Q_rch['q'].sum()) # sum of all rch fluxes

# Vin = Q_mbr['q'].sum() + Q_rch['q'].sum()
# Vout = Q_drn['q'].sum() + Q_ghb['q'].sum()

# print('Total volume in:', Vin) # total volume in
# print('Total volume out:', Vout) # total volume out
# print(f'Relative error {100 * (Vin + Vout) / Vin:.4f} %')
# -----------------------------------------------------------

# plot heads
idom_plt = np.where(idomain[0] == 1, np.nan, idomain[0])  # create a mask for the active domain

for i in range(NLAY):
    pmv = fp.plot.PlotMapView(model=gwf, layer=i)

    pmv.plot_bc(name='chd_pw', color='purple') # add 'chd' cells
    pmv.plot_bc(name='mbr', color='orange') # add 'wells' cells
    pmv.plot_bc(name='drn_r', color='blue') # add 'wells' cells
    pmv.plot_bc(name='chd_conf_in', color='orange') # add 'chd' cells
    pmv.plot_bc(name='chd_conf_out', color='gold') # add 'chd' cells
    pmv.plot_bc(name='influx', color='green') # add 'influx' cells
    pmv.plot_bc(name='outflux', color='red') # add 'outflux' cells
    
    # pmv.plot_inactive(color='lightgray', alpha=0.5) # plot inactive cells
    # pmv.plot_array(idom_plt, cmap='gray', alpha=0.2) # plot head array for layer 0
    # pmv.plot_grid(colors='silver', lw=0.1); # add grid
    cs = pmv.contour_array(head[i], linewidths=1, colors='k') # contour plot of heads
    plt.clabel(cs, fmt='%1.1f'); # add contour labels with one decimal place

    # save to figures
    plt.savefig(os.path.join(FIG_DIR, f'{modelname}_heads{i}.png'), dpi=300, bbox_inches='tight') # save figure
    plt.close()

# -------------------------------------------------------------
# create a cross section grid & plot heads

cross_col = 15 #which row to show cross section
crossview = fp.plot.PlotCrossSection(model=gwf, line={'column': cross_col})
strtArray = crossview.plot_array(head, masked_values=[1e30], alpha=0.8) # plot the active domain
crossview.plot_grid(colors='black', lw=1); # add grid
crossview.plot_inactive(color='lightgray') # plot inactive cells
cb = plt.colorbar(strtArray, shrink=0.5) # add color bar
# strtArray = crossview.plot_array(head, masked_values=[1e30], alpha = 0.5) # plot the array of heads in cross section
plt.savefig(os.path.join(FIG_DIR, f'{modelname}_xsection_col{cross_col}.png'), dpi=300, bbox_inches='tight') # save figure
plt.close()  # close the figure to avoid memory issues


# -------------------------------------------------------------
partlocs = []
for ilay in range(NLAY):
    for jrow in range(0, nrow, 5):
        for jcol in range(0, ncol, 5):
            if idomain[ilay, jrow, jcol] == 1:
                # if the cell is active, add the particle location
                partlocs.append((int(ilay), int(jrow), int(jcol)))





# Specify the paricle data
particledata = fp.modpath.ParticleData(partlocs=partlocs,
                                       structured=True,
                                      )
# Group partcles in a group
pg = fp.modpath.ParticleGroup(particledata=particledata)

# Create a modpath model and call it mp
mp = fp.modpath.Modpath7(modelname=modelname, # name of the model
                         model_ws=modelws, # path to workspace where all files are stored
                         flowmodel=gwf, # groundwater flow model to get the flow from
                         exe_name=r'C:\Users\tfo46\e_Python\a_rbm\rapid-gwm-build\examples\bin\mp7.exe', # absolute path to MODPATH7 executable'
                        )

# Add the Basic package to the model called mp and specify the porosity
mpbas = fp.modpath.Modpath7Bas(model=mp, porosity=0.3)

# Add the MODPATH simulation package
mpsim = fp.modpath.Modpath7Sim(model=mp, # add to model called mp
                               particlegroups=pg, # particle group pg defined above
                               stoptimeoption='extend',
                               trackingdirection='forward',
                              )

mp.write_input()
mp.run_model(silent=False)

fname = os.path.join(modelws, f"{modelname}.mppth")
plf = fp.utils.PathlineFile(fname)

pline = plf.get_data(partid=5) # get data for particle with id number 5
pline.dtype.names # get names stored in a rec array

for i in range(NLAY):
    pmv = fp.plot.PlotMapView(model=gwf, layer=i)

    pmv.plot_bc(name='chd_pw', color='purple') # add 'chd' cells
    pmv.plot_bc(name='mbr', color='orange') # add 'wells' cells
    pmv.plot_bc(name='drn_r', color='blue') # add 'wells' cells
    pmv.plot_bc(name='chd_conf_in', color='orange') # add 'chd' cells
    pmv.plot_bc(name='chd_conf_out', color='gold') # add 'chd' cells
    pmv.plot_bc(name='influx', color='green') # add 'influx' cells
    pmv.plot_bc(name='outflux', color='red') # add 'outflux' cells
    
    pmv.contour_array(head[i], levels=np.arange(15, 30, 0.5), linewidths=1, colors='k')

    for j in range(len(partlocs)):
        pline = plf.get_data(partid=j)
        if partlocs[j][0] == i:
            plt.plot(pline['x'], pline['y'], 'C1', lw=0.2, alpha=0.5)  # plot the particle path for layer i

    # save to figures
    plt.title(f'Particle paths for layer {i}')
    plt.savefig(os.path.join(FIG_DIR, f'{modelname}_particles{i}.png'), dpi=300, bbox_inches='tight') # save figure
    plt.close()  # close the figure to avoid memory issues

print('here')