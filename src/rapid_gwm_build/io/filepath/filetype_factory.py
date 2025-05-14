from typing import Dict, Union
from .file_openers import (
    FileOpener,
    YamlOpener,
    RasterOpener,
    ShapefileOpener,
    NetCDFOpener,
    CSVOpener,
    ArrayOpener
)

class FileTypeFactory:
    def __init__(self):
        self._registery: Dict[str, FileOpener] = {}
    
    def register(self, ext: str, definition: FileOpener):
        # TODO: error checking
        self._registery[ext] = definition
    
    def get(self, ext: str) -> Union[FileOpener, None]:
        try :
            return self._registery[ext]
        except KeyError:
            return ValueError(f"Extension {ext} not found in registry.")

    def list_types(self) -> Dict[str, FileOpener]:
        return self._registery
    
    def open(self, filepath, opener_kwargs={}):
        ext = filepath.split(".")[-1]
        opener = self.get(ext)
        return opener.open(filepath, opener_kwargs)
    

filetype_factory = FileTypeFactory()  

# Register valid types of inputs in the yaml file
filetype_factory.register("yaml", YamlOpener)
filetype_factory.register("tif", RasterOpener)
filetype_factory.register("asc", RasterOpener)
filetype_factory.register("shp", ShapefileOpener)
filetype_factory.register("cdf", NetCDFOpener)
filetype_factory.register("csv", CSVOpener)
filetype_factory.register("arr", ArrayOpener)
