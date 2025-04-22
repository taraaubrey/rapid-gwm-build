import gridit as gi


class Mesh:
    def __init__(
            self,
            nlay = 1,
            ncol = 10,
            nrow = 10,
            resolution = 10,
            top = 100,
            botms = [0],
            xorigin = 0.0, # based on xorigin of the upper-left corner of the upper-left pixel
            yorigin = 0.0, # based on yorigin of the upper-left corner of the upper-left pixel
            active_domain = None,
            cfg: dict = None,
    ):
        self.cfg = cfg
        self.nlay = nlay
        self.ncol = ncol
        self.nrow = nrow
        self.resolution = resolution
        self.top = top
        self.botms = botms
        self.xorigin = xorigin
        self.yorigin = yorigin
        self.active_domain = active_domain

        # create grid
        self.Grid2D = self._make2DGrid()

    @classmethod
    def from_cfg(cls, cfg: dict):
        """
        Create a Mesh object from a configuration dictionary.
        """
        nlay = cfg.get("nlay", 1)
        ncol = cfg.get("ncol", 10)
        nrow = cfg.get("nrow", 10)
        resolution = cfg.get("resolution", 10)
        top = cfg.get("top", 100)
        botms = cfg.get("botms", [0])
        xorigin = cfg.get("xorigin", 0.0)
        yorigin = cfg.get("yorigin", 0.0)
        active_domain = cfg.get("active_domain", None)

        return cls(
            nlay=nlay,
            ncol=ncol,
            nrow=nrow,
            resolution=resolution,
            top=top,
            botms=botms,
            xorigin=xorigin,
            yorigin=yorigin,
            active_domain=active_domain,
            cfg=cfg
        )
    
    def _make2DGrid(self):
        """
        Create a 2D grid based on the mesh parameters.
        """
        xy_shape = (self.ncol, self.nrow)
        return gi.Grid(resolution=self.resolution, shape=xy_shape, top_left=(self.xorigin, self.yorigin))