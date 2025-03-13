# type: ignore

from enum import Enum
from typing import Optional, Tuple

import numpy as np
from scipy.linalg import LinAlgError, inv


class TransformationType(Enum):
    STANDARD_7P = "7p"
    STANDARD_10P = "10p"
    IERS_7P = "-7p"
    IERS_10P = "-10p"


def derive_parameters(
    datum1: np.ndarray,
    datum2: np.ndarray,
    transformation_type: TransformationType = TransformationType.STANDARD_7P,
    constraints: Optional[np.ndarray] = None,
) -> Tuple[
    float,
    float,
    float,
    float,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    int,
    TransformationType,
    str,
]:
    """
    Derive transformation parameters for 7-parameter Helmert transformation.
    """

    print("\n--> Defining transformation parameters...")

    # Argument checking and defaults
    if constraints is None:
        constraints = np.array([1, 1, 1, 1, 1, 1, 1])

    if transformation_type not in TransformationType:
        raise ValueError(
            f"ERROR: transformation type {transformation_type} not recognized. "
            "Must be 7p or 10p for standard rotations or in case of opposite rotations -7p or -10p..."
        )

    s1 = datum1.shape
    s2 = datum2.shape

    # Check that there are equal number of points in each set
    if s1 != s2:
        raise ValueError("The datum sets are not of equal size")
    # Check that each point has three coordinate values, i.e. 3D
    if s1[1] < 3 or s2[1] < 3:
        raise ValueError("At least one of the datum sets is not 3D")
    # Check the number of points, at least three required
    if s1[0] < 3 or s2[0] < 3:
        raise ValueError(
            "At least 3 points in each datum are necessary for calculating"
        )
    # Check that each point has either three or nine coordinate components: X,Y,Z[,varX,varY,varZ,covX,covY,covZ]
    if s1[1] not in [3, 9] or s2[1] not in [3, 9]:
        raise ValueError(
            "Datum points must have either three or nine coordinate components: "
            "X,Y,Z[,varX,varY,varZ,covX,covY,covZ]"
        )

    # If points have only three coordinate values, add equal variances and covariances
    if s1[1] == 3 and s2[1] == 3:
        datum1 = np.hstack((datum1, np.ones((s1[0], 6))))
        datum2 = np.hstack((datum2, np.ones((s2[0], 6))))

    # Message about used rotations: standard or IERS
    if transformation_type in [
        TransformationType.STANDARD_7P,
        TransformationType.STANDARD_10P,
    ]:
        print("Using standard rotations (opposite to IERS rotations)")
        Rtype = "standard"
    elif transformation_type in [
        TransformationType.IERS_7P,
        TransformationType.IERS_10P,
    ]:
        print("Using IERS rotations (opposite to standard rotations)")
        Rtype = "iers"

    # Approximate a priori values
    ex = 0.0
    ey = 0.0
    ez = 0.0
    Y0 = (constraints[4:7] * np.mean(datum2[:, :3], axis=0)).T
    X0 = (constraints[4:7] * np.mean(datum1[:, :3], axis=0)).T
    T = Y0

    # Coordinate values minus centre of mass: X-X0
    Y1 = datum2[:, :3] - np.tile(Y0, (datum2.shape[0], 1))
    X1 = datum1[:, :3] - np.tile(X0, (datum1.shape[0], 1))

    # First approximate for scale
    k = constraints[0] * np.sqrt(
        np.sum(np.diag(Y1.T @ Y1)) / np.sum(np.diag(X1.T @ X1))
    ) + (1 - constraints[0])

    # Compute affine parameters Baff=[x0,Y0,Z0;ax,ay,az;bx,by,bz;cx,cy,cz]
    X1 = np.hstack((np.ones((X1.shape[0], 1)), X1))
    try:
        Baff = inv(X1.T @ X1) @ X1.T @ datum2[:, :3]
    except LinAlgError:
        raise ValueError(
            "ERROR: Singular matrix in affine parameter computation. Check input data."
        )

    # Start iterating transformation parameters
    Limits = np.array([1e-5, 1e-12])  # 1e-12 in rotation is roughly ~0.01mm
    r = 0
    while r <= 1000:
        r += 1
        N1 = 0
        t1 = 0
        deltax = 0
        for i in range(datum1.shape[0]):
            X = datum1[i, :3].T - X0
            Y = datum2[i, :3].T

            # Covariance matrices for both datums
            CX = np.array(
                [
                    [datum1[i, 3] ** 2, datum1[i, 6], datum1[i, 7]],
                    [datum1[i, 6], datum1[i, 4] ** 2, datum1[i, 8]],
                    [datum1[i, 7], datum1[i, 8], datum1[i, 5] ** 2],
                ]
            )

            CY = np.array(
                [
                    [datum2[i, 3] ** 2, datum2[i, 6], datum2[i, 7]],
                    [datum2[i, 6], datum2[i, 4] ** 2, datum2[i, 8]],
                    [datum2[i, 7], datum2[i, 8], datum2[i, 5] ** 2],
                ]
            )

            Cl = np.block([[CX, np.zeros((3, 3))], [np.zeros((3, 3)), CY]])

            A = 0
            y = 0
            v = 0

            # Rotations
            if transformation_type in [
                TransformationType.STANDARD_7P,
                TransformationType.STANDARD_10P,
            ]:
                R1 = np.array(
                    [
                        [1, 0, 0],
                        [0, np.cos(ex), np.sin(ex)],
                        [0, -np.sin(ex), np.cos(ex)],
                    ]
                )
                R2 = np.array(
                    [
                        [np.cos(ey), 0, -np.sin(ey)],
                        [0, 1, 0],
                        [np.sin(ey), 0, np.cos(ey)],
                    ]
                )
                R3 = np.array(
                    [
                        [np.cos(ez), np.sin(ez), 0],
                        [-np.sin(ez), np.cos(ez), 0],
                        [0, 0, 1],
                    ]
                )
                R = R3 @ R2 @ R1
                dR1 = (
                    R3
                    @ R2
                    @ np.array(
                        [
                            [0, 0, 0],
                            [0, -np.sin(ex), np.cos(ex)],
                            [0, -np.cos(ex), -np.sin(ex)],
                        ]
                    )
                )
                dR2 = (
                    R3
                    @ np.array(
                        [
                            [-np.sin(ey), 0, -np.cos(ey)],
                            [0, 0, 0],
                            [np.cos(ey), 0, -np.sin(ey)],
                        ]
                    )
                    @ R1
                )
                dR3 = (
                    np.array(
                        [
                            [-np.sin(ez), np.cos(ez), 0],
                            [-np.cos(ez), -np.sin(ez), 0],
                            [0, 0, 0],
                        ]
                    )
                    @ R2
                    @ R1
                )
            elif transformation_type in [
                TransformationType.IERS_7P,
                TransformationType.IERS_10P,
            ]:
                R1 = np.array(
                    [
                        [1, 0, 0],
                        [0, np.cos(ex), -np.sin(ex)],
                        [0, np.sin(ex), np.cos(ex)],
                    ]
                )
                R2 = np.array(
                    [
                        [np.cos(ey), 0, np.sin(ey)],
                        [0, 1, 0],
                        [-np.sin(ey), 0, np.cos(ey)],
                    ]
                )
                R3 = np.array(
                    [
                        [np.cos(ez), -np.sin(ez), 0],
                        [np.sin(ez), np.cos(ez), 0],
                        [0, 0, 1],
                    ]
                )
                R = R3 @ R2 @ R1
                dR1 = (
                    R3
                    @ R2
                    @ np.array(
                        [
                            [0, 0, 0],
                            [0, -np.sin(ex), -np.cos(ex)],
                            [0, np.cos(ex), -np.sin(ex)],
                        ]
                    )
                )
                dR2 = (
                    R3
                    @ np.array(
                        [
                            [-np.sin(ey), 0, np.cos(ey)],
                            [0, 0, 0],
                            [-np.cos(ey), 0, -np.sin(ey)],
                        ]
                    )
                    @ R1
                )
                dR3 = (
                    np.array(
                        [
                            [-np.sin(ez), -np.cos(ez), 0],
                            [np.cos(ez), -np.sin(ez), 0],
                            [0, 0, 0],
                        ]
                    )
                    @ R2
                    @ R1
                )

            # Model of observation equations (i.e. Helmert transformation)
            Yc = k * R @ X + T
            y = Y - Yc

            # Linearization:
            A = np.hstack((R @ X, k * dR1 @ X, k * dR2 @ X, k * dR3 @ X, np.eye(3)))
            B = np.hstack((k * R, -np.eye(3)))
            Py = inv(B @ Cl @ B.T)
            N = A.T @ Py @ A
            t = A.T @ Py @ y
            N1 += N
            t1 += t

        # Solution for normal equations (x=inv(A'PA)*A'Py=inv(N1)*t1), i.e. corrections for transformation parameters
        Q = inv(N1)
        if np.linalg.det(N1) != 0:
            deltax = (np.linalg.lstsq(N1, t1, rcond=None)[0] * constraints).T
        else:
            raise ValueError(
                "ERROR: NEQ matrix is singular - cannot determine transformation parameters... Aborting..."
            )

        # New values for unknown parameters
        k += deltax[0]
        ex += deltax[1]
        ey += deltax[2]
        ez += deltax[3]
        T += deltax[4:7]
        TMB = T - X0
        TBW = T - k * R @ X0

        # Test corrections against limits
        testv = np.sqrt(
            (deltax[4] ** 2 + deltax[5] ** 2 + deltax[6] ** 2) / 3
        )  # Translation increments
        testd = np.sqrt(
            (deltax[1] ** 2 + deltax[2] ** 2 + deltax[3] ** 2) / 3
        )  # Rotation increments

        if constraints[0] == 0 and (k + deltax[0]) > 1e-15:
            k += deltax[0]

        # Test if increments for translations and rotations are below set limits
        if abs(testv) < Limits[0] and abs(testd) < Limits[1]:
            break
        # Test if maximum residual in all points/coordinate components is below limit
        elif np.max(np.abs(y)) < 1e-5:
            break
        # Test if iteration rounds exceed the limit
        elif r >= 1000:
            print(
                "Helmert3D:Too_many_iterations. Calculation not converging after 1000 iterations. I am aborting. Results may be inaccurate."
            )
            break

    print(f" {r} iteration rounds")

    return k, ex, ey, ez, T, TMB, TBW, R, Q, r, transformation_type, Rtype


def analyze_results(
    datum1: np.ndarray,
    datum2: np.ndarray,
    k: float,
    ex: float,
    ey: float,
    ez: float,
    T: np.ndarray,
    R: np.ndarray,
    Q: np.ndarray,
    transformation_type: TransformationType,
    X0: np.ndarray,
) -> Tuple[np.ndarray, float, np.ndarray, float]:
    """
    Analyze the results of the Helmert transformation.
    """

    print("\n--> Analyzing results...")

    vtpv = 0
    jv = np.zeros((datum1.shape[0], 3))
    jv2 = np.zeros((datum1.shape[0], 3))

    for i in range(datum1.shape[0]):
        X = datum1[i, :3].T - X0
        Y = datum2[i, :3].T

        CX = np.array(
            [
                [datum1[i, 3] ** 2, datum1[i, 6], datum1[i, 7]],
                [datum1[i, 6], datum1[i, 4] ** 2, datum1[i, 8]],
                [datum1[i, 7], datum1[i, 8], datum1[i, 5] ** 2],
            ]
        )

        CY = np.array(
            [
                [datum2[i, 3] ** 2, datum2[i, 6], datum2[i, 7]],
                [datum2[i, 6], datum2[i, 4] ** 2, datum2[i, 8]],
                [datum2[i, 7], datum2[i, 8], datum2[i, 5] ** 2],
            ]
        )

        Cl = np.block([[CX, np.zeros((3, 3))], [np.zeros((3, 3)), CY]])

        A = 0
        y = 0
        v = 0

        # Rotations
        if transformation_type in [
            TransformationType.STANDARD_7P,
            TransformationType.STANDARD_10P,
        ]:
            R1 = np.array(
                [[1, 0, 0], [0, np.cos(ex), np.sin(ex)], [0, -np.sin(ex), np.cos(ex)]]
            )
            R2 = np.array(
                [[np.cos(ey), 0, -np.sin(ey)], [0, 1, 0], [np.sin(ey), 0, np.cos(ey)]]
            )
            R3 = np.array(
                [[np.cos(ez), np.sin(ez), 0], [-np.sin(ez), np.cos(ez), 0], [0, 0, 1]]
            )
            R = R3 @ R2 @ R1
        elif transformation_type in [
            TransformationType.IERS_7P,
            TransformationType.IERS_10P,
        ]:
            R1 = np.array(
                [[1, 0, 0], [0, np.cos(ex), -np.sin(ex)], [0, np.sin(ex), np.cos(ex)]]
            )
            R2 = np.array(
                [[np.cos(ey), 0, np.sin(ey)], [0, 1, 0], [-np.sin(ey), 0, np.cos(ey)]]
            )
            R3 = np.array(
                [[np.cos(ez), -np.sin(ez), 0], [np.sin(ez), np.cos(ez), 0], [0, 0, 1]]
            )
            R = R3 @ R2 @ R1

        # Design matrix
        A = np.hstack((R @ X, k * dR1 @ X, k * dR2 @ X, k * dR3 @ X, np.eye(3)))
        B = np.hstack((k * R, -np.eye(3)))
        Py = inv(B @ Cl @ B.T)
        Yc = k * R @ X + T
        y = Y - Yc
        v = Cl @ B.T @ Py @ (np.eye(3) - A @ Q @ A.T @ Py) @ y
        vtpv += v.T @ inv(Cl) @ v
        jv[i, :] = v.T
        jv2[i, :] = y.T

    vv = jv2.flatten()
    vtpv2 = vv.T @ vv

    # Standard error of unit weights in both residual cases
    m0 = np.sqrt(vtpv / (3 * datum1.shape[0] - 7))
    m02 = np.sqrt(vtpv2 / (3 * datum1.shape[0] - 7))

    print("\n<-- Transformation parameters defined...")

    return jv, m0, vv, m02


# Test case
if __name__ == "__main__":
    # Example datum points (X, Y, Z, varX, varY, varZ, covXY, covXZ, covYZ)
    datum1 = np.array(
        [
            [
                3513637.97424,
                778956.66526,
                5248216.59809,
                0.003,
                0.023,
                0.323,
                0.23,
                0.42,
                0.32,
            ],
            [
                3582104.73000,
                532590.21590,
                5232755.16250,
                0.003,
                0.023,
                0.323,
                0.23,
                0.42,
                0.32,
            ],
            [
                3491111.17695,
                497995.12319,
                5296843.05030,
                0.003,
                0.023,
                0.323,
                0.23,
                0.42,
                0.32,
            ],
            [
                3611639.48454,
                635936.65951,
                5201015.01371,
                0.003,
                0.023,
                0.323,
                0.23,
                0.42,
                0.32,
            ],
        ]
    )

    datum2 = np.array(
        [
            [
                3513638.56046,
                778956.18389,
                5248216.24817,
                0.003,
                0.023,
                0.323,
                0.23,
                0.42,
                0.32,
            ],
            [
                3582105.29700,
                532589.72930,
                5232754.80840,
                0.003,
                0.023,
                0.323,
                0.23,
                0.42,
                0.32,
            ],
            [
                3491111.73600,
                497994.64800,
                5296842.69400,
                0.003,
                0.023,
                0.323,
                0.23,
                0.42,
                0.32,
            ],
            [
                3611640.06540,
                635936.17060,
                5201014.66830,
                0.003,
                0.023,
                0.323,
                0.23,
                0.42,
                0.32,
            ],
        ]
    )

    # Derive transformation parameters
    k, ex, ey, ez, T, TMB, TBW, R, Q, r, transformation_type, Rtype = derive_parameters(
        datum1, datum2
    )

    # Analyze results
    jv, m0, vv, m02 = analyze_results(
        datum1, datum2, k, ex, ey, ez, T, R, Q, transformation_type, X0
    )

    # Print results
    print(f"k: {k}")
    print(f"ex: {ex}")
    print(f"ey: {ey}")
    print(f"ez: {ez}")
    print(f"T: {T}")
    print(f"TMB: {TMB}")
    print(f"TBW: {TBW}")
    print(f"R: {R}")
    print(f"Q: {Q}")
    print(f"r: {r}")
    print(f"Transformation Type: {transformation_type}")
    print(f"Rtype: {Rtype}")
    print(f"jv: {jv}")
    print(f"m0: {m0}")
    print(f"vv: {vv}")
    print(f"m02: {m02}")
