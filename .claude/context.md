I want to plan about the logic of the mesh. There ar emultiple way to build a mesh:
- 3D grid:
    - structured
    - unstructured (not implemented)
- elements (not implemented)
- areas (2D) (not implemented)

I'm trying to figure out how to build out the 'mesh' based on all these types of meshes. I am not going to implement all fo them; but i want them to be considereed in the architecture.

All of these are obviously build from the config file.
SCHEMA is validated here: src/rapid_gwm_build/nodes/parse/node_schemas.py
    - I want to update the schema to represent all the required inputs.
    - alos this will depend on the 'type' of mesh

Lets go through all the ways you can build a mesh. In the final instance this is what i will need for the input:
- xorigin (double precision) – x-position of the lower-left corner of the model grid. a default value of zero is assigned if not specified. the value for xorigin does not affect the model simulation, but it is written to the binary grid file so that postprocessors can locate the grid in space.
- yorigin (double precision) – y-position of the lower-left corner of the model grid. if not specified, then a default value equal to zero is used. the value for yorigin does not affect the model simulation, but it is written to the binary grid file so that postprocessors can locate the grid in space.
- angrot (double precision) – counter-clockwise rotation angle (in degrees) of the lower-left corner of the model grid. if not specified, then a default value of 0.0 is assigned. the value for angrot does not affect the model simulation, but it is written to the binary grid file so that postprocessors can locate the grid in space.

build from various user inputs:
    user can specify:
        - resolution (assumes x and y length are the same)
        - nlay (integer) – is the number of layers in the model grid.
        - nrow (integer) – is the number of rows in the model grid.
        - x length (ie. total length of model in the x_direction)
        - y length (ie. total length of model in y direction
        - dx (resolution in x direction)
        - dy (resolution in y direction)

can internally compute (or compute explicitly):
nrow (integer) – is the number of rows in the model grid.
ncol (integer) – is the number of columns in the model grid.
delr ([double precision]) – is the column spacing in the row direction.
delc ([double precision]) – is the row spacing in the column direction.

data:
    top ([double precision]) – is the top elevation for each cell in the top model layer.
    botm ([double precision]) – is the bottom elevation for each cell.
    idomain ([integer]) – is an optional array that characterizes the existence status of a cell. if the idomain array is not specified, then all model cells exist within the solution. if the idomain value for a cell is 0, the cell does not exist in the simulation. input and output values will be read and written for the cell, but internal to the program, the cell is excluded from the solution. if the idomain value for a cell is 1 or greater, the cell exists in the simulation. if the idomain value for a cell is -1, the cell does not exist in the simulation. furthermore, the first existing cell above will be connected to the first existing cell below. this type of cell is referred to as a ‘vertical pass through’ cell.