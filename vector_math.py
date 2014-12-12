"""
Description
-----------
Crossbeams Modeller vector_math library--a collection of vector_math
routines not in numpy.

See cbmodel.py for a description of the package and its history.

Author
------
Charles Sharman

License
-------
Distributed under the GNU GENERAL PUBLIC LICENSE Version 3.  View
LICENSE for details.
"""

import numpy as np

import math

def cross(v1, v2):
    """
    Returns the cross product of v1 and v2 (now in numpy)
    """
    v3 = np.array([0.0, 0.0, 0.0])
    v3[0] = v1[1] * v2[2] - v1[2] * v2[1]
    v3[1] = -v1[0] * v2[2] + v1[2] * v2[0]
    v3[2] = v1[0] * v2[1] - v1[1] * v2[0]
    return v3

def mag(v1):
    """
    Returns the magnitude of v1
    """
    return np.sqrt(np.sum(v1*v1, -1))

def normalize(v1):
    """
    Normalizes vector v1
    """
    absv1 = mag(v1)
    return v1/absv1

def acos_care(x):
    """
    Returns the arc cosine of x; corrects for beyond 1.
    """
    if x < -1.0: r = -1.0
    elif x > 1.0: r = 1.0
    else: r = x
    if x < -1.0 or x > 1.0:
        print 'acos error ' + repr(x) + ' corrected to ' + repr(r)
    return math.acos(r)

def angle_normal(norm):
    """
    Returns the unit circle angle (0 to 2*pi) a 2D normal's direction
    takes.
    """
    a0 = math.acos(min(max(-1.0, float(norm[0])), 1.0))
    if norm[1] < 0.0: # bottom half plane
        return 2*math.pi - a0
    else:
        return a0

def offsets(r2, r1 = -1):
    """
    Returns a list of offsets for a pixel-based offsetting algorithm
    by drawing a filled circle from radius r1 to radius r2.
    """
    mesh = np.zeros((2*r2 + 1, 2*r2 + 1), np.uint8)
    r2sq = r2**2
    if r1 > 0:
        r1sq = r1**2
    else:
        r1sq = r1
    for x in range(r2 + 1):
        for y in range(r2 + 1):
            pos2 = x**2 + y**2
            if pos2 <= r2sq and pos2 > r1sq:
                mesh[x+r2, y+r2] = 1
                mesh[-x+r2, y+r2] = 1
                mesh[x+r2, -y+r2] = 1
                mesh[-x+r2, -y+r2] = 1
    #print mesh
    coords = np.transpose(np.nonzero(mesh)) - np.array([r2, r2])
    return coords
