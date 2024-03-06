""""
Simple implementation of

    2013, Sjöberg, L.E., "Closed-form and iterative weighted least squares
        solutions of Helmert transformation parameters",
        https://www.degruyter.com/document/doi/10.2478/jogs-2013-0002/html


x, 1 x n
y, 1 x n
P, n x n

"""
import numpy as np

# Step 1
X = np.array(
    [
        [3513649.63170, 778954.53800, 5248201.78430],  # BUDD
        [3611640.06026, 635936.17447, 5201014.66702],  # FYHA
        [3446394.50233, 591712.93124, 5316383.25562],  # SULD
        [3628427.91179, 562059.09356, 5197872.21496],  # MOJN
        [3586538.66500, 762342.32690, 5201484.2788],   # (12,55,123)
    ]
).T

Xw = np.array([1.0, 1.0, 1.0, 1.0, 1.0])

Y = np.matrix(
    [
        [3513565.68530, 778859.41234, 5248084.57303],  # BUDD
        [3611556.34182, 635841.43320, 5200897.13354],  # FYHA
        [3446310.97509, 591617.61171, 5316265.57509],  # SULD
        [3628344.33184, 561964.43318, 5197754.50752],  # MOJN
        [3586454.70710, 762247.46600, 5201367.04520], # (12,55,123)
    ]
).T
Yw = np.array([1.0, 1.0, 1.0, 1.0, 1.0])

print("X:")
print(X)
print("Y:")
print(Y)
print()

(m, n) = X.shape
assert n > m

assert Xw.shape == Yw.shape
assert Xw.shape[0] == n and Yw.shape[0] == n

P = np.diag(Xw) @ np.diag(Yw)
print("P")
print(P)
print()


# Step 2 - Row mean values
Xbar = X @ np.ones((n,n)) / n
Ybar = Y @ np.ones((n,n)) / n

print("Xbar:")
print(Xbar)
print("Ybar:")
print(Ybar)
print()

# Step 3
Xtilde = X - Xbar
Ytilde = Y - Ybar

print("Xtilde:")
print(Xtilde)
print("Ytilde:")
print(Ytilde)
print()

# Step 4
sx2 = np.trace(Xtilde @ P @ Xtilde.T) / n
sy2 = np.trace(Ytilde @ P @ Ytilde.T) / n

print(f"{sx2=}, {sy2=}\n")

# Step 5
C = Xtilde @ P @ Ytilde.T
print("C:")
print(C)
print()

U, D, V = np.linalg.svd(C)

print("U:")
print(U)
print(U.shape)
print()

print("D:")
print(D)
print(D.shape)
print()

print("V:")
print(V)
print(V.shape)
print()

Sigma = [1, 1, np.linalg.det(U)*np.linalg.det(V)] # eq. 3b

R = U @ np.diag(Sigma) @ V.T
print("R:")
print(R)
print()

sxy = np.trace(R@C) / n
k = sxy / sx2

print(f"\n{k=}\n")

T = Ybar - k*R@Xbar
t = T*np.ones((n,1))/n

print("t:")
print(t)
print()

YY = t + k * R @ X

print(YY)
print()

print("Residuals")
print(Y - YY)
print()

# rotations
rx = np.arctan(-R[1,2]/R[2,2])
ry = np.arctan(R[0,2] / np.sqrt(R[0,0]**2 + R[0,1]**2))
rz = np.arctan(-R[0,1]/R[0,0])
print(f"{rx=}, {ry=}, {rz=}")
