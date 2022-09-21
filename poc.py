"""
Transformo Proof of Concept

Litterature:

https://www.degruyter.com/document/doi/10.2478/jogs-2013-0002/html
https://www.sciencedirect.com/science/article/pii/S0377042705006862
https://www.lantmateriet.se/contentassets/4a728c7e9f0145569edd5eb81fececa7/rapport_reit_eng.pdf


"""
import abc
import sys
from typing import Iterable

import numpy as np


class TransformoAbstractClass(metaclass=abc.ABCMeta):
    """
    A class for handling abstract interfaces within Transformo.

    Primary use case is as a parent for other base classes that define
    abstract methods for downstream implementation.
    """

    @classmethod
    def __subclasshook__(cls, subclass):
        """
        Make sure that all abstract methods are implemented in child classes.
        """
        for abstract_method in cls.__abstractmethods__:
            if not (hasattr(subclass, abstract_method) and callable(eval(f"subclass.{abstract_method}"))):
                raise NotImplemented

        return True


class BaseReader(TransformoAbstractClass):

    def __init__(self):
        pass


class BaseFitter(TransformoAbstractClass):
    """
    Basis for all transformation inversion.

    Perhaps an extra layer of fitters are needed: MathematicalFitter, GridFitter ?
    """

    def __init__(self, Ac: np.array, Aw: np.array, Bc: np.array, Bw: np.array):
        # Source data
        self.Ac = Ac
        self.Aw = Ac

        # Target data
        self.Bc = Bc
        self.Bw = Bw

        self.parameters = {}

    @abc.abstractmethod
    def fit(self):
        """
        Determine best fitting parameters for transformation between source and target coordinates
        """
        raise NotImplementedError

    @abc.abstractmethod
    def forward_operation(self):
        """
        Apply determined transformation parameters to input coordinates
        """
        raise NotImplementedError


class HelmertFitter(BaseFitter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def fit(self):
        return {
            "x": 23.2,
            "y": 12.6,
            "z": 3.16,
            "s": 0.042,
            "rx": 0.023,
            "ry": 0.152,
            "rz": 0.734,
        }


class AffineFitter(BaseFitter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def fit(self):
        pass


class ChainFitter(BaseFitter):
    """
    Combine Fitters in a chain.
    """
    def __init__(self, *args, fitter_chain:Iterable=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.chain = fitter_chain

    def fit(self):
        for link in self.chain:
            link.fit()



FITTERS = {
    "pipeline": ChainFitter,
    "helmert": HelmertFitter,
    "affine": AffineFitter,
}

class BaseWriter(TransformoAbstractClass):

    def __init__(self):
        pass


class Transformo():

    def __init__(self, source_cordinates, source_weights, target_coordinates, target_weights, fitter):

        if not issubclass(fitter, BaseFitter):
            raise TypeError("fitter is not a BaseFitter")

        self.source_cordinates = source_cordinates
        self.source_weights = source_weights
        self.target_coordinates = target_coordinates
        self.target_weights = target_weights

        self.fitter = fitter(source_cordinates, source_weights, target_coordinates, target_weights)


    def fit(self):
        return self.fitter.fit()


if __name__ == "__main__":
    Ac = np.array([
        [3513649.63170, 778954.53800, 5248201.78430], #BUDD
        [3611640.06026, 635936.17447, 5201014.66702], #FYHA
        [3446394.50233, 591712.93124, 5316383.25562], #SULD
        [3628427.91179, 562059.09356, 5197872.21496], #MOJN
    ])
    Aw = np.array([1.0, 1.0, 1.0, 1.0])

    Bc = np.array([
        [3513649.50350, 778954.59460, 5248201.86730], #BUDD
        [3611639.59221, 635936.55217, 5201014.95257], #FYHA
        [3446393.99783, 591713.34725, 5316383.58572], #SULD
        [3628427.41567, 562059.50896, 5197872.52439], #MOJN

    ])
    Bw = np.array([1.0, 1.0, 1.0, 1.0])

    try:
        if sys.argv[1] == "--fitter":
            fitter = sys.argv[2]
    except IndexError:
        fitter = "helmert"

    fit_engine = FITTERS[fitter]

    t = Transformo(Ac, Aw, Bc, Bw, fit_engine)
    print(t.fit())