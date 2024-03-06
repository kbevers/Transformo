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
from pyproj import Transformer


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
            if not (
                hasattr(subclass, abstract_method)
                and callable(eval(f"subclass.{abstract_method}"))
            ):
                raise NotImplemented

        return True


class BaseReader(TransformoAbstractClass):
    """
    Basis for all reader classes
    """

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
    """
    https://www.tandfonline.com/doi/full/10.1080/10095020.2022.2138569
    """


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Translations [m]
        self.tx = None
        self.ty = None
        self.tz = None
        # Rotations [radians]
        self.rx = None
        self.ry = None
        self.rz = None
        # Scale factor
        self.s =  None

    def fit(self):
        """
        Determine the 7 parameters of a regular Helmert transformation.

        With inspiration from https://www.tandfonline.com/doi/full/10.1080/10095020.2022.2138569

        shape(Ac) = shape(Bc) = (N,1)

        """
        Ac = self.Ac
        Bc = self.Bc
        N = Ac.shape[0]

        L = Ac.reshape(-1) - Bc.reshape(-1)
        print(L) # eq.

        A = np.zeros((N*3,7))
        for i in range(N):
            xi = Ac[i,0]
            yi = Ac[i,1]
            zi = Ac[i,2]

            A[i*3,0] = 1
            A[i*3,4] = -zi
            A[i*3,5] = yi
            A[i*3,6] = xi
            A[i*3+1,1] = 1
            A[i*3+1,3] = zi
            A[i*3+1,5] = -xi
            A[i*3+1,6] = yi
            A[i*3+2,2] = 1
            A[i*3+2,3] = -yi
            A[i*3+2,4] = xi
            A[i*3+2,6] = zi

        print(A)
        P = np.cov(Ac, Bc)

        X = np.invert(A.T*P*A) * (A.T*P*L)

        print(X)


    def forward_operation(self):
        """
        Apply determined transformation parameters to input coordinates
        """
        fwd = Transformer.from_pipeline("+proj=helmert +x=-81.1 +y=-89.4 +z=-115.8 +rx=0.485 +ry=0.024 +rz=0.413 +s=-0.54 +convention=position_vector")
        for pt in fwd.itransform(self.Aw):
            print(pt)



class AffineFitter(BaseFitter):
    """."""

    def __init__(self, *args, **kwargs):
        """."""
        super().__init__(*args, **kwargs)

    def fit(self):
        """Fit.."""
        pass

    def forward_operation(self):
        """."""
        pass


class ChainFitter(BaseFitter):
    """
    Combine Fitters in a chain.
    """

    def __init__(self, *args, fitter_chain: Iterable = None, **kwargs):
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


class Transformo:
    """Transformation engine"""

    def __init__(
        self,
        source_coordinates: np.array,
        source_weights: np.array,
        target_coordinates: np.array,
        target_weights: np.array,
        fitter: BaseFitter,
    ):
        """
        Instatiate a transformation engine.

        source_coordinates: Nx3 numpy array
        source_weights: Nx1
        target_coordinates: Nx3
        target_weights: Nx1
        """

        if not issubclass(fitter, BaseFitter):
            raise TypeError("fitter is not a BaseFitter")

        self.source_coordinates = source_coordinates
        self.source_weights = source_weights
        self.target_coordinates = target_coordinates
        self.target_weights = target_weights

        self.fitter = fitter(
            source_coordinates, source_weights, target_coordinates, target_weights
        )

        self.fitter.forward_operation()

    def fit(self):
        return self.fitter.fit()


if __name__ == "__main__":
    # Try to replicate the Helmert transformation ED50 -> ETRS89 (EPSG:1626).
    #
    # +proj=helmert +x=-81.1 +y=-89.4 +z=-115.8
    # +rx=0.485 +ry=0.024 +rz=0.413 +s=-0.54 +convention=position_vector


    Ac = np.array(
        [
            [3513649.63170, 778954.53800, 5248201.78430],  # BUDD
            [3611640.06026, 635936.17447, 5201014.66702],  # FYHA
            [3446394.50233, 591712.93124, 5316383.25562],  # SULD
            [3628427.91179, 562059.09356, 5197872.21496],  # MOJN
            [3586538.66500, 762342.32690, 5201484.2788],   # (12,55,123)
        ]
    )
    Aw = np.array([1.0, 1.0, 1.0, 1.0])

    Bc = np.array(
        [
            [3513565.68530, 778859.41234, 5248084.57303],  # BUDD
            [3611556.34182, 635841.43320, 5200897.13354],  # FYHA
            [3446310.97509, 591617.61171, 5316265.57509],  # SULD
            [3628344.33184, 561964.43318, 5197754.50752],  # MOJN
            [3586454.70710, 762247.46600, 5201367.04520], # (12,55,123)
        ]
    )
    Bw = np.array([1.0, 1.0, 1.0, 1.0])

    print(Aw.shape)

    try:
        if sys.argv[1] == "--fitter":
            fitter = sys.argv[2]
    except IndexError:
        fitter = "helmert"

    fit_engine = FITTERS[fitter]

    t = Transformo(Ac, Aw, Bc, Bw, fit_engine)
    t.fit()
