from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class FileOpener(ABC):
    @abstractmethod
    def open(filepath, opener_kwargs):
        pass


@dataclass
class YamlOpener(FileOpener):

    def open(filepath, opener_kwargs={}):
        from yaml import load, BaseLoader

        with open(filepath, "r") as file:
            return load(file, Loader=BaseLoader)

@dataclass
class RasterOpener(FileOpener):
    def open(self, opener_kwargs={}):
        pass

@dataclass
class ShapefileOpener(FileOpener):
    def open(self, opener_kwargs={}):
        pass

@dataclass
class NetCDFOpener(FileOpener):
    def open(self, opener_kwargs={}):
        pass

@dataclass
class CSVOpener(FileOpener):
    def open(filepath, opener_kwargs={}):
        import pandas as pd
        return pd.read_csv(filepath, **opener_kwargs)

@dataclass
class ArrayOpener(FileOpener):
    def open(filepath, opener_kwargs={}):
        import numpy as np
        return np.loadtxt(filepath, **opener_kwargs)