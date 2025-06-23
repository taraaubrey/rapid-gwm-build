import numpy as np
import gridit as gi


class Mesh:
    def __init__(
            self,
            crs: str = "EPSG:2193",  # coordinate reference system
            # kind: str = "structured",
            nlay = 1,
            nrow = 10,
            ncol = 10,
            # delr = None,
            # delc = None,
            resolution = None,
            # top: np.ndarray = None,
            # bottoms: np.ndarray = None,
            xorigin = 0.0, # based on xorigin of the upper-left corner of the upper-left pixel
            yorigin = 0.0, # based on yorigin of the upper-left corner of the upper-left pixel
            active_domain = None,
            # pipeline=None,
            # cfg: dict = None,
    ):
        # create grid
        self.resolution = resolution
        self.nlay = nlay
        self.crs = crs
        self._grid = self._make2DGrid(active_domain, ncol, nrow, xorigin, yorigin)

        self.active_domain = self.make_active_domain(active_domain) if active_domain else np.ones((self.nlay, self.nrow, self.ncol), dtype=bool)
    	

    @property
    def delr(self):
        return np.ones(self.ncol) * self.resolution
    @property
    def delc(self):
        return np.ones(self.nrow) * self.resolution
    @property
    def nrow(self):
        return self._grid.shape[0]
    @property
    def ncol(self):
        return self._grid.shape[1]
    @property
    def grid(self):
        return self._grid

    def make_active_domain(self, active_domain):
        # make 2d grid a 3d array
        arr = self._grid.array_from_vector(active_domain)
        arr = arr[np.newaxis, :, :]  # shape (1, nrow, ncol)
        arr3d = np.broadcast_to(arr.data, (self.nlay, self.nrow, self.ncol))
        return arr3d
        #reshape to (nlay, nrow, ncol)


    def _make2DGrid(self, active_domain=None,  ncol=None, nrow=None, xorigin=None, yorigin=None):
        """
        Create a 2D grid based on the mesh parameters.
        """
        if active_domain:
            return gi.Grid.from_vector(active_domain, self.resolution)
        if ncol and nrow and xorigin and yorigin:
            xy_shape = (self.ncol, self.nrow)
            return gi.Grid(resolution=self.resolution, shape=xy_shape, top_left=(xorigin, yorigin))
        else:
            raise ValueError("Insufficient parameters to create a 2D grid. Provide either active_domain or ncol, nrow, xorigin, and yorigin.")

    def _set_bottoms(self, bottoms):
        """
        Set the bottoms of the mesh.
        """
        if isinstance(bottoms, dict):
            raise NotImplementedError
        elif isinstance(bottoms, np.ndarray):
            ndim = bottoms.ndim
            if ndim == 2 and self.nlay == 1:
                # 2D array, reshape to (nlay, nrow, ncol)
                bottoms = bottoms.reshape(self.nlay, self.nrow, self.ncol)
            else:
                raise NotImplementedError("Haven't written any explicit bottom layering functions yet.")
            return bottoms
        else:
            raise ValueError("Bottoms must be a dictionary or a numpy array.")