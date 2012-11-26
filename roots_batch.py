#!/usr/bin/python
#
# Copyright (C) 2008 Marcel Tunnissen
#
# License: GNU Public License version 2
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not,
# check at http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# or write to the Free Software Foundation,
#
# $Log$
#


import pygsl._numobj as numx
from pygsl  import multiroots, errno
import pygsl
import copy
import math
import threading
import gc
import Queue

import glue
import Geom3D
import GeomTypes
import Heptagons

import string
import time
import random

H         = numx.sin(  numx.pi / 7)
RhoH      = numx.sin(2*numx.pi / 7)
SigmaH    = numx.sin(3*numx.pi / 7)
Rho       = RhoH / H
Sigma     = SigmaH / H

eqFloatMargin = 1.0e-12

V2 = numx.sqrt(2.)
V5 = numx.sqrt(5)
hV2 = V2/2
V3 = numx.sqrt(3.)
hV3 = V3/2
tV3 = V3/3
V2dV3 = V2/V3

tau = (1.0 + V5)/2
dtau = 1.0/tau
tau2 = tau + 1

def eq(a, b, precision = eqFloatMargin):
    """
    Check if 2 floats 'a' and 'b' are close enough to be called equal.

    a: a floating point number.
    b: a floating point number.
    margin: if |a - b| < margin then the floats will be considered equal and
            True is returned.
    """
    return abs(a - b) < precision

def Veq(a, b, precision = eqFloatMargin, log = False):
    """
    Check if 2 floats vectors 'a' and 'b' are close enough to be called equal.

    Note both vectors should have the same dimension, otherwise an assert will
    be generated.
    a: a floating point vector.
    b: a floating point vector.
    margin: if |a - b| < margin then the floats will be considered equal and
            True is returned.
    """
    assert len(a) == len(b),\
        'vecors have different dimenstions: len(a) = %d, len(b) == %d' % (
            len(a), len(b)
        )
    is_eq = True
    for i in range(len(a)):
        if not eq(a[i], b[i], precision):
            if log:
                print '---> index %s difference too big: %.13f (margin: %.13f)\n' % (
                                            i, abs(a[i]-b[i]), precision)
            is_eq = False
            break;
    return is_eq

# since GeomTypes.quat doesn't work well with multiroots...
def quatRot(axis, angle):
    assert not (GeomTypes.eq(axis[0], 0) and
            GeomTypes.eq(axis[1], 0) and
            GeomTypes.eq(axis[2], 0)
        ), 'Axis cannot be (0, 0, 0) %s ' % str(axis)
    norm = numx.sqrt(axis[0]*axis[0] + axis[1]*axis[1] + axis[2]*axis[2])
    sa = numx.sin(angle/2)
    ca = numx.cos(angle/2)
    q0 = [sa*a/norm for a in axis]
    q1 = [-q for q in q0]
    q0.insert(0, ca)
    q1.insert(0, ca)
    return (q0, q1)

def quatMult(v, w):
    return [
        v[0]*w[0] - v[1]*w[1] - v[2] * w[2] - v[3] * w[3],
        v[0]*w[1] + v[1]*w[0] + v[2] * w[3] - v[3] * w[2],
        v[0]*w[2] - v[1]*w[3] + v[2] * w[0] + v[3] * w[1],
        v[0]*w[3] + v[1]*w[2] - v[2] * w[1] + v[3] * w[0]
    ]

def rotate(v, q):
    w = [0, v[0], v[1], v[2]]
    r = quatMult(q[0], w)
    r = quatMult(r, q[1])
    return GeomTypes.Vec(r[1:])

class Symmetry:
        # not efficient for comparing, but not a bottleneck
        A4xI = "A4xI"
        S4A4 = "S4A4"
        A4   = "A4"
        S4xI = "S4xI"
        S4   = "S4"
        A5   = "A5"
        A5xI = "A5xI"

D_Dom =  {
    Symmetry.A4xI: [0, 0],
    Symmetry.S4A4: [numx.pi/4, numx.pi/4],
    Symmetry.A4  : [0, numx.pi/4],
    Symmetry.S4xI: [0, numx.pi/2],
    Symmetry.S4  : [0, numx.pi/2],
    Symmetry.A5  : [0, numx.pi/2],
    Symmetry.A5xI: [0, numx.pi/2],
}

T_Dom =  {
    Symmetry.A4xI: [-2., 3.],
    Symmetry.S4A4: [-2., 3.],
    Symmetry.A4  : [-2., 3.],
    Symmetry.S4xI: [-4., 4.8],
    Symmetry.S4  : [-4., 4.8],
    Symmetry.A5  : [-5., 6.0],
    Symmetry.A5xI: [-5., 6.0],
}

class Param:
    tri_fill       = 0
    opp_fill       = 1
    edge_len       = 2
    h_fold         = 3
    t_fill_pos     = 4
    opp_t_fill_pos = 5
    n_7_turn       = 6

refl1_bas  = 0
strip1_bas = 1
strip2_bas = 2
star_bas   = 3
refl2_bas  = 4
loose_bit  = 8
alt_bit    = 16
rot_bit    = 32
twist_bit  = 64
class TriangleAlt:
    refl_1           = refl1_bas
    refl_2           = refl2_bas
    stripI           = strip1_bas
    strip1loose      = strip1_bas | loose_bit
    alt_stripI       = strip1_bas             | alt_bit
    alt_strip1loose  = strip1_bas | loose_bit | alt_bit
    stripII          = strip2_bas
    alt_stripII      = strip2_bas             | alt_bit
    star             = star_bas
    star1loose       = star_bas   | loose_bit
    rot_strip1loose  = strip1_bas | loose_bit           | rot_bit
    arot_strip1loose = strip1_bas | loose_bit | alt_bit | rot_bit
    rot_star1loose   = star_bas   | loose_bit           | rot_bit
    arot_star1loose  = star_bas   | loose_bit | alt_bit | rot_bit
    twisted          =                                    twist_bit
    def __iter__(t):
        return iter([
            t.refl_1,
            t.refl_2,
            t.stripI,
            t.strip1loose,
            t.alt_stripI,
            t.alt_strip1loose,
            t.stripII,
            t.alt_stripII,
            t.star,
            t.star1loose,
            t.rot_strip1loose,
            t.arot_strip1loose,
            t.rot_star1loose,
            t.arot_star1loose,
            t.twisted
        ])

Stringify = {
    TriangleAlt.refl_1          : 'refl 1',
    TriangleAlt.refl_2          : 'refl 2',
    TriangleAlt.strip1loose     : 'strip 1 loose',
    TriangleAlt.stripI          : 'strip I',
    TriangleAlt.stripII         : 'strip II',
    TriangleAlt.star            : 'shell',
    TriangleAlt.star1loose      : 'shell 1 loose',
    TriangleAlt.alt_strip1loose : 'alt strip 1 loose',
    TriangleAlt.alt_stripI      : 'alt strip I',
    TriangleAlt.alt_stripII     : 'alt strip II',
    TriangleAlt.rot_strip1loose : 'rot strip 1 loose',
    TriangleAlt.arot_strip1loose: 'alt rot strip 1 loose',
    TriangleAlt.rot_star1loose  : 'rot shell 1 loose',
    TriangleAlt.arot_star1loose : 'alt rot shell 1 loose',
    TriangleAlt.twisted         : 'twisted',
}

class Fold:
    parallel  = 0
    trapezium = 1
    w         = 2
    triangle  = 3
    star      = 4

    def __init__(this, f = 0):
        this.set(f)

    def set(this, f):
        assert (f >= this.parallel and f <= this.star)
        this.fold = f

    def __str__(this):
        if (this.fold == this.parallel):
            return 'parallel'
        elif (this.fold == this.trapezium):
            return 'trapezium'
        elif (this.fold == this.w):
            return 'w'
        elif (this.fold == this.triangle):
            return 'triangle'
        elif (this.fold == this.star):
            return 'shell'
        else:
            return None

fold = Fold()

def GetBaseHeptagon(T, alpha, beta0, beta1, gamma0, gamma1, delta, fold_type):
    """Returns the positioned base heptagon indepent on symmetry

    Returns the array of 7 coordinates, which are tuples.
    T: translation of the heptagon
    alpha: half of the dihedral angle
    beta0: first fold left
    beta1: first fold right
    gamma0: second fold left
    gamma0: second fold right
    delta: rotation around the z-axis
    fold_type: expresses how the heptagon is folded, ie over which diagonals
    """
    # before rotating, with heptagon centre = origin
    R = 1.0 / (2*H)       # radius
    x0, y0, z0 = (H + SigmaH + RhoH, 0.0,     0.)
    x1, y1, z1 = (    SigmaH + RhoH, Rho/2,   0.)
    x2, y2, z2 = (             RhoH, Sigma/2, 0.)
    x3, y3, z3 = (              0.0, 1.0/2,   0.)
    x4, y4, z4 = (               x3, -y3,     z3)
    x5, y5, z5 = (               x2, -y2,     z2)
    x6, y6, z6 = (               x1, -y1,     z1)

    Tx = R - x0   # translate in X to centre on origin
    cosa  = numx.cos(alpha)
    sina  = numx.sin(alpha)
    cosb0 = numx.cos(beta0)
    sinb0 = numx.sin(beta0)
    cosg0 = numx.cos(gamma0)
    sing0 = numx.sin(gamma0)
    cosb1 = numx.cos(beta1)
    sinb1 = numx.sin(beta1)
    cosg1 = numx.cos(gamma1)
    sing1 = numx.sin(gamma1)
    if (fold_type == Fold.parallel):
        # this code I wrote first only for the parallel case.
        # I didn't remove the code since it so much faster then the newer code.
        #
        #             0
        #
        #      6 ----------- 1    axis b
        #
        #
        #
        #    5 --------------- 2  axis a
        #
        #
        #         4       3
        #  ^ x
        #  |
        #  +--> y
        x0__ = cosg0 * (H) + SigmaH + RhoH
        z0__ = sing0 * (H)

        x0   = cosb0 * (x0__ - RhoH) - sinb0 * (z0__       ) + RhoH
        z0   = cosb0 * (z0__       ) + sinb0 * (x0__ - RhoH)

        x1   = cosb0 * (SigmaH) + RhoH
        z1   = sinb0 * (SigmaH)

        x6, y6, z6 = x1, -y1, z1

    elif (fold_type == Fold.triangle):
        #
        #             0
        #            _^_
        #      1   _/   \_   6
        #        _/       \_
        #      _/  axes  b  \_
        #     /               \
        #    2 --------------- 5  axis a
        #
        #
        #         3       4
        #                                ^ X
        #                                |
        #                                |
        #                       Y <------+
        #
        # rotate gamma around b
        # rotate beta  around a
        #
        # ROTATE V1 around axis b: angle gamma
        # ------------------------------------
        # refer to V1 as if centre i origon:
        # rotate around axis b as if centre -> V1 is x-axis:
        x = (R - H) + cosg0 * H
        z =           sing0 * H
        # now correct for V1 not on x-axis: rotate d around z-axis
        # with d: angle of heptagon centre to V1 with x-as
        # and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
        cosd = (x1 + Tx) / R
        sind = y1 / R
        x1, y1, z1 = (cosd * x - Tx, sind * x, z)
        # ROTATE V0 and V1 around axis a: angle beta
        # ------------------------------------
        x = H + SigmaH
        x0, y0, z0 = (RhoH + cosb0 * x, y0, sinb0 * x)
        x = x1 - RhoH
        x1, y1, z1 = (RhoH + cosb0 * x - sinb0 * z1, y1, sinb0 * x + cosb0 * z1)

        x6, y6, z6 = x1, -y1, z1
        x5, y5, z5 = x2, -y2, z2

    elif (fold_type == Fold.star):
        #
        #               0
        #              .^.
        #        1   _/| |\_   6
        #          _/ /   \ \_
        # axis g0_/  |     |  \_ axis g1
        #       /    |a   a|    \
        #      2    / x   x \    5
        #          |  i   i  |
        #          "  s   s  "
        #          3         4
        #             b   b
        #             0   1              ^ X
        #                                |
        #                                |
        #                       Y <------+
        #
        # rotate gamma around b
        # rotate beta  around a
        #
        # ROTATE V1 around axis g
        # ------------------------------------
        # refer to V1 as if centre is origon:
        # rotate around axis g as if centre -> V1 is x-axis:
        x = (R - H) + cosg0 * H
        z =           sing0 * H
        # now correct for V1 not on x-axis: rotate d around z-axis
        # with d: angle of heptagon centre to V1 with x-as
        cosd = (x1 + Tx) / R
        sind = RhoH # = sin(2pi/7)
        x1, y1, z1 = (cosd * x, sind * x, z)

        # use similar calc for different angle and x6, y6, z6 = x1, -y1, z1
        x = (R - H) + cosg1 * H
        z =           sing1 * H
        x6, y6, z6 = (cosd * x, sind * x, z)

        # ROTATE V1 and V2 around axis b
        # ------------------------------------
        # correction for V5 not on -x: rotate d around z-axis
        # with d: angle of heptagon centre to V2 with -x-as
        cosd = -(x2 + Tx) / R
        sind = SigmaH # = sin(3pi/7)
        # refer to V2 as if centre in origon and as if V5 in -x:
        x2, y2, z2 = (x0 - R, 0.5, 0.0)
        d0_3 = x2 - RhoH
        # rotate around axis b:
        # TODO: above: rm x2, y2 assignment, mv y2 assignment down.
        x2, z2 = (d0_3 + cosb0 * RhoH, sinb0 * RhoH)
        # correct for V5 not on -x: rotate d around z-axis
        # and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
        x2, y2 = (cosd * x2 - sind * y2 - Tx, sind * x2 + cosd * y2)
        # Similarly for V1:
        # for V1 rotate V5 into -x: * (cosd, -sind)
        x1, y1 = (cosd * x1 + sind * y1, -sind * x1 + cosd * y1)
        # rotate around axis b:
        dx = x1 - d0_3
        x1, z1 = (d0_3 + cosb0 * dx - sinb0 * z1, sinb0 * dx + cosb0 * z1)
        # correct for V5 not on -x: rotate d around z-axis
        # and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
        x1, y1 = (cosd * x1 - sind * y1 - Tx, sind * x1 + cosd * y1)

        # use similar calc for different angle for
        # x5, y5, z5 = x2, -y2, z2
        # x6, y6, z6 = x1, -y1, z1
        y5 = 0.5
        x5, z5 = (d0_3 + cosb1 * RhoH, sinb1 * RhoH)
        x5, y5 = (cosd * x5 - sind * y5 - Tx, sind * x5 + cosd * y5)
        x6, y6 = (cosd * x6 + sind * y6, -sind * x6 + cosd * y6)
        dx = x6 - d0_3
        x6, z6 = (d0_3 + cosb1 * dx - sinb1 * z6, sinb1 * dx + cosb1 * z6)
        x6, y6 = (cosd * x6 - sind * y6 - Tx, sind * x6 + cosd * y6)
        # x5, y5, z5 = x2, -y2, z2  and  x6, y6, z6 = x1, -y1, z1
        y5, y6 = -y5, -y6

    elif (fold_type == Fold.trapezium):
        #
        #               0
        #
        #        1 ----------- 6    axis b0
        #        .             .
        # axis g0 \           / axis g1
        #          \         /
        #      2   |         |   5
        #          \        /
        #           "       "
        #           3       4
        #
        #                                ^ X
        #                                |
        #                                |
        #                       Y <------+
        #
        # rotate gamma around b
        # rotate beta  around a
        #
        # ROTATE V2 around axis g0: angle gamma
        # ------------------------------------
        # refer to V2 as if centre is origon:
        # rotate around axis g0 as if centre -> V2 is x-axis:
        x = (R - H) + cosg0 * H
        z =           sing0 * H
        # now correct for V2 not on x-axis: rotate d around z-axis
        # with d: angle of heptagon centre to V2 with x-as
        # and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
        cosd = (x2 + Tx) / R
        #TODO: change into SigmaH and retest
        sind = y2 / R
        x2, y2, z2 = (cosd * x - Tx, sind * x, z)

        # use similar calc for different angle for x5, -y5, z5 = x2, y2, z2
        x = (R - H) + cosg1 * H
        z =           sing1 * H
        x5, y5, z5 = (cosd * x - Tx, -sind * x, z)

        # ROTATE V0 around axis b0: angle beta
        # ------------------------------------
        # refer to V0 as if centre is origon:
        #   - rotate around axis b0
        # Then translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
        x0 = (R - H) + cosb0 * H - Tx
        z0 =           sinb0 * H

    elif (fold_type == Fold.w):
        #
        #               0
        #              .^.
        #        1     | |     6
        #        .    /   \    .
        # axis g0 \  |     |  / axis g1
        #          " |a   a| "
        #      2   |/ x   x \|   5
        #          V  i   i  V
        #          "  s   s  "
        #          3         4
        #             b   b              ^ X
        #             0   1              |
        #                                |
        #                       Y <------+
        #
        # ROTATE V2 around axis g:
        # ------------------------------------
        # refer to V2 as if centre is origon:
        # rotate around axis b as if centre -> V2 is x-axis:
        x = (R - H) + cosg0 * H
        z =           sing0 * H
        # prepare for next: rotate V5 onto -x with angle d0
        cosd0 = -Tx / R
        sind0 = H # = sin(pi/7)
        # Then later: correction for V5 not on -x: rotate d around z-axis
        # with d: angle of heptagon centre to V2 with -x-as
        cosd1 = -(x2 + Tx) / R
        sind1 = SigmaH # = sin(3pi/7)
        x2, y2, z2 = (cosd0 * x, sind0 * x, z)

        # use similar calc for different angle for x5, -y5, z5 = x2, y2, z2
        x = (R - H) + cosg1 * H
        z =           sing1 * H
        x5, y5, z5 = (cosd0 * x, sind0 * x, z)

        # ROTATE V1 and V2 around axis b
        # ------------------------------------
        # refer to V1 as if centre in origon and as if V5 in -x:
        d0_3 = x0 - R - RhoH
        # rotate around axis b:
        x1, y1, z1 = (d0_3 + cosb0 * RhoH, -0.5, sinb0 * RhoH)
        # correct for V5 not on -x: rotate d around z-axis
        # and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
        x1, y1 = (cosd1 * x1 - sind1 * y1 - Tx, sind1 * x1 + cosd1 * y1)
        # Similarly for V2:
        # rotate around axis b:
        dx = x2 - d0_3
        x2, z2 = (d0_3 + cosb0 * dx - sinb0 * z2, sinb0 * dx + cosb0 * z2)
        # correct for V5 not on -x: rotate d around z-axis
        # and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
        x2, y2 = (cosd1 * x2 - sind1 * y2 - Tx, sind1 * x2 + cosd1 * y2)

        # use similar calc for different angle for
        # x5, y5, z5 = x2, -y2, z2
        # x6, y6, z6 = x1, -y1, z1
        x6, y6, z6 = (d0_3 + cosb1 * RhoH, -0.5, sinb1 * RhoH)
        x6, y6 = (cosd1 * x6 - sind1 * y6 - Tx, sind1 * x6 + cosd1 * y6)
        dx = x5 - d0_3
        x5, z5 = (d0_3 + cosb1 * dx - sinb1 * z5, sinb1 * dx + cosb1 * z5)
        x5, y5 = (cosd1 * x5 - sind1 * y5 - Tx, sind1 * x5 + cosd1 * y5)
        # x5, y5, z5 = x2, -y2, z2  and  x6, y6, z6 = x1, -y1, z1
        y5, y6 = -y5, -y6

    # rotate around 3-4; angle a
    # ------------------------------------
    # since half dihedral angle is used instead of angle with x-axis:
    # TODO don't copy the code...
    cos_a = sina
    sin_a = -cosa
    x0, y0, z0, = (cos_a * x0 - sin_a * z0, y0, sin_a * x0 + cos_a * z0)
    x1, y1, z1, = (cos_a * x1 - sin_a * z1, y1, sin_a * x1 + cos_a * z1)
    x2, y2, z2, = (cos_a * x2 - sin_a * z2, y2, sin_a * x2 + cos_a * z2)
    x5, y5, z5, = (cos_a * x5 - sin_a * z5, y5, sin_a * x5 + cos_a * z5)
    x6, y6, z6, = (cos_a * x6 - sin_a * z6, y6, sin_a * x6 + cos_a * z6)
    # and translate
    # ------------------------------------
    z0 = z0 + T
    z1 = z1 + T
    z2 = z2 + T
    z3 = z3 + T
    z4 = z4 + T
    z5 = z5 + T
    z6 = z6 + T

    cosd = numx.cos(delta)
    sind = numx.sin(delta)
    x0, y0 = x0 * cosd - y0 * sind, x0 * sind + y0 * cosd
    x1, y1 = x1 * cosd - y1 * sind, x1 * sind + y1 * cosd
    x2, y2 = x2 * cosd - y2 * sind, x2 * sind + y2 * cosd
    x3, y3 = x3 * cosd - y3 * sind, x3 * sind + y3 * cosd
    x4, y4 = x4 * cosd - y4 * sind, x4 * sind + y4 * cosd
    x5, y5 = x5 * cosd - y5 * sind, x5 * sind + y5 * cosd
    x6, y6 = x6 * cosd - y6 * sind, x6 * sind + y6 * cosd

    # comment out the return below if you want to see the prints
    return [
        (x0, y0, z0),
        (x1, y1, z1),
        (x2, y2, z2),
        (x3, y3, z3),
        (x4, y4, z4),
        (x5, y5, z5),
        (x6, y6, z6)
    ]

    print 'v0 =', [x0, y0, z0]
    print 'v1 =', [x1, y1, z1]
    print 'v2 =', [x2, y2, z2]
    print 'v3 =', [x3, y3, z3]
    print 'v4 =', [x4, y4, z4]
    print 'v5 =', [x5, y5, z5]
    print 'v6 =', [x6, y6, z6]

    return [
        (x0, y0, z0),
        (x1, y1, z1),
        (x2, y2, z2),
        (x3, y3, z3),
        (x4, y4, z4),
        (x5, y5, z5),
        (x6, y6, z6)
    ]

def FoldedRegularHeptagonsA4xI(c, params):
    """Calculates the 4 variable edge lengths - 1 for the simplest A4xI case of
    folded heptagons.

    The case contains
    c[3]: a translation (towards the viewer)
    c[1]: half the angle between the 2 heptagons 0,1,2,3,4,5,6 and 7,8,9,3,4,10,11
    c[2]: the angle of the first fold around 2-5 (9, 10)
    c[3]: the angle of the first fold around 1-6 (8, 11)
    The vertices are positioned as follows:
    #          19                      18
    #                      ^ y-axis
    #                      |
    #             16                14             . [1, 1, 1] o3 axis
    #                      12
    #
    #               9             2
    #      8                               1
    #
    #                      3
    #
    #   7                  . z-axis           0        --> x-axis
    #
    #                      4
    #
    #     11                               6
    #              10             5
    #
    #                      13
    #             17                15

    And the relevant vertices are defined as follows:
    [ x1,    y1,    z1], # V1
    [ x2,    y2,    z2], # V2
    [ x3,    y3,    z3], # V3

    [-x2,    y2,    z2], # V9 = V2'

    [ y0,    z0,    x0], # V12 =(              0.0, 1.0/2,   0.) V0'

    [ y1,    z1,    x1], # V14 = V1'

    The heptagons are regular, so
    |0-1| = |1-2| = |2-3| = |3-4| = |4-5| = |5-6| = |6-0| = |12 - 14| = 1
    The alternatives for creatings triangles leads to the following possible
    variable edge lengths:
    params{'0'} | edge a | edge b | edge c | edge d
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 14 - 1     strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 14 - 1     strip I
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 14 - 1     strip II
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 12 - 1 | 14 - 1     star
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 12 - 1 | 14 - 1     star 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 18 - 2     strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 18 - 2     alt strip II
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 18 - 2     alt strip I
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 19 - 2 | 1 - 16 | 12 - 0     twisted

    For the param{'0'} the following constant names can be used, see
    TriangleAlt.

    params{'1'} steers which the edge lengths. It is a vector of 4 floating
    point numbers that expresses the edge lengths of [a, b, c, d]. If params 1
    is not given, the edge lengths are supposed to be 1.

    params{'2'} defines which heptagon folding method is used.
    """

    T     = c[0]
    alpha = c[1]
    beta  = c[2]
    gamma = c[3]
    delta = 0

    par_tri_fill = Param.tri_fill
    par_edge_len = Param.edge_len
    par_fold     = Param.h_fold

    edgeAlternative = params[par_tri_fill]
    if edgeAlternative & twist_bit == twist_bit:
        delta = D_Dom[Symmetry.A4][1]

    coords = GetBaseHeptagon(
            T, alpha, beta, beta, gamma, gamma, delta, params[par_fold])
    x0, y0, z0 = coords[0]
    x1, y1, z1 = coords[1]
    x2, y2, z2 = coords[2]
    x3, y3, z3 = coords[3]
    x4, y4, z4 = coords[4]
    x5, y5, z5 = coords[5]
    x6, y6, z6 = coords[6]

    #print 'v0', x0, y0, z0
    #print 'v1', x1, y1, z1
    #print 'v2', x2, y2, z2
    #print 'v3', x3, y3, z3
    cp = [0, 0, 0, 0]
    #
    # EDGE A
    #
    edgeLengths = [1., 1., 1., 1.]
    try:
        edgeLengths = params[Param.edge_len]
    except IndexError:
        pass
    if edgeAlternative & loose_bit:
        # V2 - V9:[-x2,    y2,    z2], # V9 = V2'
        cp[0] = numx.sqrt(4*x2*x2) - edgeLengths[0]
    elif edgeAlternative & twist_bit == twist_bit:
        # V2 - V9 = V2 - V5':  V5' = [-x5, -y5, z5]
        cp[0] = numx.sqrt((x2+x5)*(x2+x5) + (y2+y5)*(y2+y5) + (z2-z5)*(z2-z5)) - edgeLengths[0]
    else:
        # V3 - V12:[ y0,    z0,    x0], # V12 = V0'
        cp[0] = numx.sqrt((x3-y0)*(x3-y0) + (y3-z0)*(y3-z0) + (z3-x0)*(z3-x0)) - edgeLengths[0]
    #
    # EDGE B
    #
    plain_edge_alt = edgeAlternative & ~alt_bit
    if plain_edge_alt == TriangleAlt.stripII:
        # V3 - V14:[ y1,    z1,    x1], # V14 = V1'
        cp[1] = numx.sqrt((x3-y1)*(x3-y1) + (y3-z1)*(y3-z1) + (z3-x1)*(z3-x1)) - edgeLengths[1]
    elif edgeAlternative & twist_bit == twist_bit:
        # V2 - V19: V19 = V5' = [y5, z5, x5]
        cp[1] = numx.sqrt((x2-y5)*(x2-y5) + (y2-z5)*(y2-z5) + (z2-x5)*(z2-x5)) - edgeLengths[1]
    else:
        #V2 - V12:[ y0,    z0,    x0], # V12 = V0'
        cp[1] = numx.sqrt((x2-y0)*(x2-y0) + (y2-z0)*(y2-z0) + (z2-x0)*(z2-x0)) - edgeLengths[1]
    #
    # EDGE C
    #
    if edgeAlternative & twist_bit == twist_bit:
        # V1 - V16: V16 = V6' = [y6, z6, x6]
        cp[2] = numx.sqrt((x1-y6)*(x1-y6) + (y1-z6)*(y1-z6) + (z1-x6)*(z1-x6)) - edgeLengths[2]
    elif (
        edgeAlternative != TriangleAlt.star
        and edgeAlternative != TriangleAlt.star1loose
    ):
        # V2 - V14:[ y1,    z1,    x1], # V14 = V1'
        cp[2] = numx.sqrt((x2-y1)*(x2-y1) + (y2-z1)*(y2-z1) + (z2-x1)*(z2-x1)) - edgeLengths[2]
    else:
        # V1 - V12:[ y0,    z0,    x0], # V12 = V0'
        cp[2] = numx.sqrt((x1-y0)*(x1-y0) + (y1-z0)*(y1-z0) + (z1-x0)*(z1-x0)) - edgeLengths[2]
    #
    # EDGE D
    #
    if edgeAlternative & twist_bit == twist_bit:
        # V0 - V12 = V0 - V0': V0' = [ y0,    z0,    x0]
        cp[3] = numx.sqrt((x0-y0)*(x0-y0) + (y0-z0)*(y0-z0) + (z0-x0)*(z0-x0)) - edgeLengths[3]
    elif (edgeAlternative & alt_bit == 0):
        cp[3] = numx.sqrt((x1-y1)*(x1-y1) + (y1-z1)*(y1-z1) + (z1-x1)*(z1-x1)) - edgeLengths[3]
    else:
        # V2 - V18:[ y2,    z2,    x2], # V18 = V2'
        cp[3] = numx.sqrt((x2-y2)*(x2-y2) + (y2-z2)*(y2-z2) + (z2-x2)*(z2-x2)) - edgeLengths[3]

    #print cp
    return cp

def FoldedRegularHeptagonsA4(c, params):
    """Calculates the 4 variable edge lengths - 1 for the simplest A4 case of
    folded heptagons.

    The case contains
    c[0]: a translation (towards the viewer)
    c[1]: half the angle between the 2 heptagons 0,1,2,3,4,5,6 and 7,8,9,3,4,10,11
    c[2]: the angle of the first fold (left)
    c[3]: the angle of the second fold (left)
    c[4]: rotation angle around z-axis
    c[5]: the angle of the first fold (right)
    c[6]: the angle of the second fold (right)
    The vertices are positioned as follows:
    #          19                      18
    #
    #
    #             16                14
    #                      12
    #
    #               9             2
    #      8                               1
    #
    #                      3
    #
    #   7                                     0
    #
    #                      4
    #
    #     11                               6
    #              10             5
    #
    #                      13
    #             17                15

    And the relevant vertices are defined as follows:
    [ x1,    y1,    z1], # V1
    [ x2,    y2,    z2], # V2
    [ x3,    y3,    z3], # V3

    [-x5,   -y5,    z5], # V9 = V2'
    [ y0,    z0,    x0], # V12 = V0'
    [ y1,    z1,    x1], # V14 = V1'

    The heptagons are regular, so
    |0-1| = |1-2| = |2-3| = |3-4| = |4-5| = |5-6| = |6-0| = |12 - 14| = 1

    For the param[0] the following constant names can be used:
    The alternatives for creatings triangles leads to the following possible
    variable edge lengths:
    params{'0'} | edge a | edge b | edge c | edge d
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 8 - 16     strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 8 - 16     strip I
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 8 - 16     strip II
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 12 - 1 | 8 - 16     star
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 12 - 1 | 8 - 16     star 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 9 - 19     alt strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 9 - 19     alt strip II
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 9 - 19     alt strip I
    ------------+--------+--------+--------+-------

    only valid for opposites alternatives:
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 9 - 16 | 8 - 16     rot strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 9 - 16 | 9 - 19     alt rot strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 2 -  8 | 8 - 16     rot star 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 2 - 19 | 9 - 19     alt rot star 1 loose
    ------------+--------+--------+--------+-------

    params{'1'} alternatives for the opposite triangle fill.

    params{'2'} steers which the edge lengths. It is a vector of 7 floating
    point numbers that expresses the edge lengths of [a, b0, c0, d, b1, c1]. If
    this params is not given, the edge lengths are supposed to be 1.

    params{'3'} defines which heptagon folding method is used.

    params{'4'} start position of the triangle fill

    params{'5'} start position of the opposite triangle fill

    params{'6'} rotate the folding with n/7 turn
    """

    T      = c[0]
    alpha  = c[1]
    beta0  = c[2]
    gamma0 = c[3]
    delta  = c[4]
    beta1  = c[5]
    gamma1 = c[6]

    par_tri_fill = Param.tri_fill
    par_opp_fill = Param.opp_fill
    par_edge_len = Param.edge_len
    par_fold     = Param.h_fold
    n_7_turn     = Param.n_7_turn

    coords = GetBaseHeptagon(
            T, alpha, beta0, beta1, gamma0, gamma1, delta, params[par_fold])
    x0, y0, z0 = coords[0]
    x1, y1, z1 = coords[1]
    x2, y2, z2 = coords[2]
    x3, y3, z3 = coords[3]
    x4, y4, z4 = coords[4]
    x5, y5, z5 = coords[5]
    x6, y6, z6 = coords[6]

    cp = copy.copy(c)
    edgeAlternative = params[par_tri_fill]
    oppAlternative = params[par_opp_fill]
    #
    # EDGE A: only one for A4
    #
    try:
        edgeLengths = params[par_edge_len]
    except IndexError:
        edgeLengths = [1., 1., 1., 1., 1., 1., 1.]

    if edgeAlternative & loose_bit:
        # V2 - V9:[-x5,   -y5,    z5], # V9 = V5'
        cp[0] = numx.sqrt((x2+x5)*(x2+x5) + (y2+y5)*(y2+y5) + (z2-z5)*(z2-z5)) - edgeLengths[0]
    else:
        # V3 - V12:[ y0,    z0,    x0], # V12 = V0'
        cp[0] = numx.sqrt((x3-y0)*(x3-y0) + (y3-z0)*(y3-z0) + (z3-x0)*(z3-x0)) - edgeLengths[0]

    #
    # EDGE B: 2 different B's for A4
    #
    plain_edge_alt = edgeAlternative & ~alt_bit
    if plain_edge_alt == TriangleAlt.stripII:
        # V3 - V14:[y1, z1, x1], # V14 = V1'
        cp[1] = numx.sqrt((x3-y1)*(x3-y1) + (y3-z1)*(y3-z1) + (z3-x1)*(z3-x1)) - edgeLengths[1]
    else:
        #V2 - V12:[y0, z0, x0], # V12 = V0'
        cp[1] = numx.sqrt((x2-y0)*(x2-y0) + (y2-z0)*(y2-z0) + (z2-x0)*(z2-x0)) - edgeLengths[1]

    #
    # EDGE C
    #
    if (
        edgeAlternative != TriangleAlt.star
        and edgeAlternative != TriangleAlt.star1loose
    ):
        # V2 - V14:[ y1, z1, x1], # V14 = V1'
        cp[2] = numx.sqrt((x2-y1)*(x2-y1) + (y2-z1)*(y2-z1) + (z2-x1)*(z2-x1)) - edgeLengths[2]
    else:
        # V1 - V12:[y0,    z0,    x0], # V12 = V0'
        cp[2] = numx.sqrt((x1-y0)*(x1-y0) + (y1-z0)*(y1-z0) + (z1-x0)*(z1-x0)) - edgeLengths[2]

    #
    # EDGE D
    #
    if (edgeAlternative & alt_bit == 0):
        # V1 - V14:[ y1,    z1,    x1], # V14 = V1'
        cp[3] = numx.sqrt((x1-y1)*(x1-y1) + (y1-z1)*(y1-z1) + (z1-x1)*(z1-x1)) - edgeLengths[3]
    else:
        # V2 - V18:[ y2,    z2,    x2], # V18 = V2'
        cp[3] = numx.sqrt((x2-y2)*(x2-y2) + (y2-z2)*(y2-z2) + (z2-x2)*(z2-x2)) - edgeLengths[3]

    # opposite alternative edges, similar as above
    #
    # OPPOSITE EDGE B
    #
    plain_edge_alt = oppAlternative & ~alt_bit
    if plain_edge_alt == TriangleAlt.stripII:
        # V3 - V16:[y6, z6, x6], # V16 = V6'
        cp[4] = numx.sqrt((x3-y6)*(x3-y6) + (y3-z6)*(y3-z6) + (z3-x6)*(z3-x6)) - edgeLengths[4]
    elif plain_edge_alt & rot_bit == rot_bit:
        # V2 - V16:[y6, z6, x6], # V16 = V6'
        cp[4] = numx.sqrt((x2-y6)*(x2-y6) + (y2-z6)*(y2-z6) + (z2-x6)*(z2-x6)) - edgeLengths[4]
    else:
        #V9:[-x5, -y5, z5] - V12, # V9 = V5'
        cp[4] = numx.sqrt((-x5-y0)*(-x5-y0) + (-y5-z0)*(-y5-z0) + (z5-x0)*(z5-x0)) - edgeLengths[4]
    #
    # OPPOSITE EDGE C
    #
    if oppAlternative == TriangleAlt.arot_star1loose:
        # V2 - V19: V19 = V5' = [y5, z5, x5]
        cp[5] = numx.sqrt((x2-y5)*(x2-y5) + (y2-z5)*(y2-z5) + (z2-x5)*(z2-x5)) - edgeLengths[5]
    elif oppAlternative == TriangleAlt.rot_star1loose:
        # V2 - V8: V8 = V6' = [-x6, -y6, z6]
        cp[5] = numx.sqrt((x2+x6)*(x2+x6) + (y2+y6)*(y2+y6) + (z2-z6)*(z2-z6)) - edgeLengths[5]
    elif (
        oppAlternative != TriangleAlt.star
        and oppAlternative != TriangleAlt.star1loose
    ):
        # V9 - V16: V9 = V5' = [-x5, -y5, z5], V16 = V6' = [ y6, z6, x6]
        cp[5] = numx.sqrt((y6+x5)*(y6+x5) + (z6+y5)*(z6+y5) + (x6-z5)*(x6-z5)) - edgeLengths[5]
    else:
        # V8: [-x6, -y6, z6] - V12, # V8 = V6'
        cp[5] = numx.sqrt((x6+y0)*(x6+y0) + (y6+z0)*(y6+z0) + (x0-z6)*(x0-z6)) - edgeLengths[5]
    #
    # OPPOSITE EDGE D
    #
    if (oppAlternative & alt_bit == 0):
        # V8 - V16: V8 = V6' = [-x6, -y6, z6]; V16 = V6' = [y6, z6, x6]
        cp[6] = numx.sqrt((y6+x6)*(y6+x6) + (z6+y6)*(z6+y6) + (x6-z6)*(x6-z6)) - edgeLengths[6]
    else:
        # V9 - V19: V9 = V5' = [-x5, -y5, z5]; V19 = V5' = [y5, z5, x5]
        cp[6] = numx.sqrt((y5+x5)*(y5+x5) + (z5+y5)*(z5+y5) + (x5-z5)*(x5-z5)) - edgeLengths[6]

    #print cp
    return cp

def S4_Q_turn_o4(x, y, z):
    """Rotate [x, y, z] a quarter turn around the S4 o4 axis [1, 0, 1]

    Returns the tuple [x', y', z']
    """
    # Rotation is obtained by
    # 1. rotate one eight turn around positive y-axis
    # 1. rotate quarter turn around positive z-axis
    # 3. rotate one eight turn around negative y-axis
    # TODO: optimise me

    # 1: x_, y_, z_ =  hV2x - hV2z, y,  hV2x + hV2z
    # 2: x_, y_     = -y_, x_
    # so 1 & 2:
    hV2x = hV2 * x
    hV2z = hV2 * z
    y_, x_, z_ = hV2x - hV2z, -y, hV2x + hV2z
    # 3: x_, y_, z_ =  hV2x + hV2z, y, -hV2x + hV2z
    hV2x = hV2 * x_
    hV2z = hV2 * z_
    x_, z_ =  hV2x + hV2z, -hV2x + hV2z
    return (x_, y_, z_)

def S4_T_turn_o3(x, y, z):
    """Rotate [x, y, z] a 1/3 turn around the S4 o3 axis [0, 1/V3, V2/V3]

    Note this is for a right handed system.
    Returns the tuple [x', y', z']
    """
    # Rotations is obtained by
    # 1. rotate alpha turn around positive x-axis
    # 1. rotate third turn around positive z-axis
    # 3. rotate alpha turn around negative x-axis

    # TODO: optimise me
    # Note this is for a right handed system.
    # 1:
    cosa = V2dV3
    sina = -tV3
    x_, y_, z_ = x, sina * z + cosa * y,  cosa * z - sina * y
    # 2:
    cosb = -0.5
    sinb = hV3
    #if not positive:
    #    sinb = -sinb
    x_, y_ = cosb * x_ + sinb * y_, cosb * y_ - sinb * x_
    # 3:
    y_, z_ = -sina * z_ + cosa * y_,  cosa * z_ + sina * y_
    return (x_, y_, z_)

def v_delta(x0, y0, z0, x1, y1, z1):
    return numx.sqrt((x1-x0)*(x1-x0) + (y1-y0)*(y1-y0) + (z1-z0)*(z1-z0))

def FoldedRegularHeptagonsS4(c, params):
    """Calculates the 4 variable edge lengths for the simplest S4 case of
    folded heptagons.

    The case contains
    c[0]: a translation (towards the viewer)
    c[1]: half the angle between the 2 heptagons 0,1,2,3,4,5,6 and 7,8,9,3,4,10,11
    c[2]: the angle of the first fold (left)
    c[3]: the angle of the second fold (left)
    c[4]: rotation angle around z-axis
    c[5]: the angle of the first fold (right)
    c[6]: the angle of the second fold (right)
    The vertices are positioned as follows:

    #
    #              10             5
    #     11                               6
    #
    #                      4
    #
    #   7           z-axis . o2-axis          0       . o4-axis: [1, 0, 1]
    #
    #                      3
    #
    #      8                               1          +---> x
    #               9             2                   |
    #                                                 v y
    #
    #                      . o3 axis: [0, 1/V3, V2/V3]
    #
    #
    #             12 = o3(0)
    #
    #   13 = o3(6)        14 = o3(1)
    #
    # 15 = o3(5)             16 = o3(2)

    And the relevant vertices are defined as follows:

    The heptagons are regular, so
    |0-1| = |1-2| = |2-3| = |3-4| = |4-5| = |5-6| = |6-0| = |12 - 14| = 1

    For the param[0] the following constant names can be used:
    The alternatives for creatings triangles leads to the following possible
    variable edge lengths:
    params{'0'} | edge a | edge b | edge c | edge d
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 1 - 14     strip 1 loose
          opp.  |        | 12 - 9 | 9 - 13 | 8 - 13
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 1 - 14     strip I
          opp.  |        | 12 - 9 | 9 - 13 | 8 - 13
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 1 - 14     strip II
          opp.  |        | 3 - 13 | 9 - 13 | 8 - 13
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 12 - 1 | 1 - 14     star
          opp.  |        | 12 - 9 | 12 - 8 | 8 - 13
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 12 - 1 | 1 - 14     star 1 loose
          opp.  |        | 12 - 9 | 12 - 8 | 8 - 13
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 2 - 16     alt strip 1 loose
          opp.  |        | 12 - 9 | 9 - 13 | 9 - 15
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 2 - 16     alt strip II
          opp.  |        | 3 - 13 | 9 - 13 | 9 - 15
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 2 - 16     alt strip I
          opp.  |        | 12 - 9 | 9 - 13 | 9 - 15
    ------------+--------+--------+--------+-------

    only valid for opposites alternatives:
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 9 - 16 | 8 - 16     rot strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 9 - 16 | 9 - 19     alt rot strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 2 -  8 | 8 - 16     rot star 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 2 - 19 | 9 - 19     alt rot star 1 loose
    ------------+--------+--------+--------+-------

    params{'1'} alternatives for the opposite triangle fill.

    params{'2'} steers the edge lengths. It is a vector of 4 or 7 floating point
    numbers that expresses the edge lengths of [a, b, c, d] or
    [a, b0, c0, d, b1, c1] resp. If length 4, then c[5] = c[2] and c[6] = c[3];
    the value of c[4] is either 0 or pi/2 rad, depending on params[5].
    If this params[2] is not given, the edge lengths are supposed to be 1.

    params{'3'} defines which heptagon folding method is used.

    params{'4'} start position of the triangle fill

    params{'5'} start position of the opposite triangle fill

    params{'6'} rotate the folding with n/7 turn
    """

    # params indices in text:

    T      = c[0]
    alpha  = c[1]
    beta0  = c[2]
    gamma0 = c[3]

    par_tri_fill       = Param.tri_fill
    par_opp_fill       = Param.opp_fill
    par_edge_len       = Param.edge_len
    par_fold           = Param.h_fold

    incl_reflections = len(params[par_edge_len]) == 4
    if incl_reflections:
        beta1  = beta0
        gamma1 = gamma0
        if params[par_tri_fill] == TriangleAlt.refl_2:
            delta = D_Dom[Symmetry.S4xI][1]
        else:
            delta = D_Dom[Symmetry.S4xI][0]
        oppAlternative = params[par_tri_fill]
    else:
        delta  = c[4]
        beta1  = c[5]
        gamma1 = c[6]
        oppAlternative = params[par_opp_fill]

    coords = GetBaseHeptagon(
            T, alpha, beta0, beta1, gamma0, gamma1, delta, params[par_fold])
    x0, y0, z0 = coords[0]
    x1, y1, z1 = coords[1]
    x2, y2, z2 = coords[2]
    x3, y3, z3 = coords[3]
    x4, y4, z4 = coords[4]
    x5, y5, z5 = coords[5]
    x6, y6, z6 = coords[6]

    # print (y, 1x, z) to compare with Orbitit
    #print '[y0, x0, z0] =', y0, x0, z0
    #print '[y1, x1, z1] =', y1, x1, z1
    #print '[y2, x2, z2] =', y2, x2, z2
    #print '[y3, x3, z3] =', y3, x3, z3
    #print '[y4, x4, z4] =', y4, x4, z4
    #print '[y5, x5, z5] =', y5, x5, z5
    #print '[y6, x6, z6] =', y6, x6, z6

    cp = copy.copy(params[par_edge_len])
    edgeAlternative = params[par_tri_fill]
    x12, y12, z12 = S4_T_turn_o3(x0, y0, z0)
    x14, y14, z14 = S4_T_turn_o3(x1, y1, z1)
    #
    # EDGE A: only one for A4
    #
    try:
        edgeLengths = params[par_edge_len]
    except IndexError:
        edgeLengths = [1., 1., 1., 1., 1., 1., 1.]

    #if ((edgeAlternative & loose_bit) != 0 or
    #   (edgeAlternative & twist_bit) != 0
    #):
    if (edgeAlternative == TriangleAlt.refl_1 or
                                edgeAlternative == TriangleAlt.refl_2 or
                                (edgeAlternative & loose_bit) != 0
    ):
        # V2 - V9:[-x5,   -y5,    z5], # V9 = V5'
        cp[0] = numx.sqrt((x2+x5)*(x2+x5) + (y2+y5)*(y2+y5) + (z2-z5)*(z2-z5)) - edgeLengths[0]
    else:
        cp[0] = v_delta(x3, y3, z3, x12, y12, z12) - edgeLengths[0]

    #
    # EDGE B:
    #
    plain_edge_alt = edgeAlternative & ~alt_bit
    #if (edgeAlternative & twist_bit) != 0:
    if (edgeAlternative == TriangleAlt.refl_1):
        # V5 - Q-turn-around-o4(V2)
        V2_o4_x, V2_o4_y, V2_o4_z = S4_Q_turn_o4(x2, y2, z2)
        cp[1] = v_delta(x5, y5, z5, V2_o4_x, V2_o4_y, V2_o4_z) - edgeLengths[1]
    elif (edgeAlternative == TriangleAlt.refl_2):
        # V10 - Q-turn-around-o4(V5), V10 = V2' = [-x2, -y2, z2]
        V_o4_x, V_o4_y, V_o4_z = S4_Q_turn_o4(x5, y5, z5)
        cp[1] = v_delta(-x2, -y2, z2, V_o4_x, V_o4_y, V_o4_z) - edgeLengths[1]
    elif plain_edge_alt == TriangleAlt.stripII:
        cp[1] = v_delta(x3, y3, z3, x14, y14, z14) - edgeLengths[1]
    else:
        cp[1] = v_delta(x2, y2, z2, x12, y12, z12) - edgeLengths[1]

    #
    # EDGE C
    #
    #if (edgeAlternative & twist_bit) != 0:
    if (edgeAlternative == TriangleAlt.refl_1):
        # V6 - Q-turn-around-o4(V1)
        V1_o4_x, V1_o4_y, V1_o4_z = S4_Q_turn_o4(x1, y1, z1)
        cp[2] = v_delta(x6, y6, z6, V1_o4_x, V1_o4_y, V1_o4_z) - edgeLengths[2]
    elif (edgeAlternative == TriangleAlt.refl_2):
        # V11 - Q-turn-around-o4(V6), V11 = V1' = [-x1, -y1, z1]
        V_o4_x, V_o4_y, V_o4_z = S4_Q_turn_o4(x6, y6, z6)
        cp[2] = v_delta(-x1, -y1, z1, V_o4_x, V_o4_y, V_o4_z) - edgeLengths[2]
    elif (
        edgeAlternative != TriangleAlt.star
        and edgeAlternative != TriangleAlt.star1loose
    ):
        cp[2] = v_delta(x2, y2, z2, x14, y14, z14) - edgeLengths[2]
    else:
        cp[2] = v_delta(x1, y1, z1, x12, y12, z12) - edgeLengths[2]

    #
    # EDGE D
    #
    #if (edgeAlternative & twist_bit) != 0:
    if (edgeAlternative == TriangleAlt.refl_1):
        # V0 - T-turn-around-o4(V9:[x0,   y0,    z0])
        V0_o4_x, V0_o4_y, V0_o4_z = S4_Q_turn_o4(x0, y0, z0)
        cp[3] = v_delta(x0, y0, z0, V0_o4_x, V0_o4_y, V0_o4_z) - edgeLengths[3]
    elif (edgeAlternative == TriangleAlt.refl_2):
        # V7 - Q-turn-around-o4(V0), V7 = o2(v0) = [-x0, -y0, z0]
        cp[3] = v_delta(-x0, -y0, z0, V_o4_x, V_o4_y, V_o4_z) - edgeLengths[3]
    elif (edgeAlternative & alt_bit == 0):
        cp[3] = v_delta(x1, y1, z1, x14, y14, z14) - edgeLengths[3]
    else:
        x16, y16, z16 = S4_T_turn_o3(x2, y2, z2)
        cp[3] = v_delta(x2, y2, z2, x16, y16, z16) - edgeLengths[3]

    if not incl_reflections:
        x9,  y9,  z9  = -x5, -y5, z5
        x13, y13, z13 = S4_T_turn_o3(x6, y6, z6)
        #
        # OPPOSITE EDGE B
        #
        plain_edge_alt = oppAlternative & ~alt_bit
        if plain_edge_alt == TriangleAlt.stripII:
            cp[4] = v_delta(x3, y3, z3, x13, y13, z13) - edgeLengths[4]
        elif plain_edge_alt & rot_bit == rot_bit:
            # V2 - V16:[y6, z6, x6], # V16 = V6'
            cp[4] = numx.sqrt((x2-y6)*(x2-y6) + (y2-z6)*(y2-z6) + (z2-x6)*(z2-x6)) - edgeLengths[4]
        else:
            cp[4] = v_delta(x9, y9, z9, x12, y12, z12) - edgeLengths[4]

        #
        # OPPOSITE EDGE C
        #
        if oppAlternative == TriangleAlt.arot_star1loose:
            # TODO
            # V2 - V19: V19 = V5' = [y5, z5, x5]
            cp[5] = numx.sqrt((x2-y5)*(x2-y5) + (y2-z5)*(y2-z5) + (z2-x5)*(z2-x5)) - edgeLengths[5]
        elif oppAlternative == TriangleAlt.rot_star1loose:
            # TODO
            # V2 - V8: V8 = V6' = [-x6, -y6, z6]
            cp[5] = numx.sqrt((x2+x6)*(x2+x6) + (y2+y6)*(y2+y6) + (z2-z6)*(z2-z6)) - edgeLengths[5]
        elif (
            oppAlternative != TriangleAlt.star
            and oppAlternative != TriangleAlt.star1loose
        ):
            cp[5] = v_delta(x9, y9, z9, x13, y13, z13) - edgeLengths[5]
        else:
            # x8,  y8,  z8  = -x6, -y6, z6
            cp[5] = v_delta(-x6, -y6, z6, x12, y12, z12) - edgeLengths[5]

        #
        # OPPOSITE EDGE D
        #
        if (oppAlternative & alt_bit == 0):
            # x8,  y8,  z8  = -x6, -y6, z6
            cp[6] = v_delta(-x6, -y6, z6, x13, y13, z13) - edgeLengths[6]
        else:
            x15, y15, z15 = S4_T_turn_o3(x5, y5, z5)
            cp[6] = v_delta(x9, y9, z9, x15, y15, z15) - edgeLengths[6]

    #print cp
    return cp

# For A5:
# o3axis = GeomTypes.Vec([1/tau, 0, tau]
# o5axis = GeomTypes.Vec([0, -1, tau])
# o5axis = GeomTypes.Vec([0, 1, tau])

A5_o3_l = numx.sqrt(tau2 + 1/tau2)
A5_o3_cosa = tau/A5_o3_l
A5_o3_sina = dtau/A5_o3_l

def A5_T_turn_o3(x, y, z, positive = True):
    """Rotate [x, y, z] a third turn around the A4 o3 axis [1/tau, 0, tau]

    If positive == False, then a third turn around the negative axis is
    returned.
    Returns the tuple [x', y', z']
    """
    # Rotations is obtained by
    # 1. rotate (tau, 1/tau) / l around positive x-axis, l = V(tau^2 + 1/tau^2)
    # 1. rotate third turn around positive = <positive> z-axis
    # 3. rotate opposite of step 1.

    cosa = A5_o3_cosa
    sina = A5_o3_sina

    # 1:
    x_, y_, z_ =  cosa * x - sina * z, y, sina * x + cosa * z
    # 2:
    cosb = -0.5
    sinb = hV3
    if not positive:
        sinb = -sinb
    x_, y_ = cosb * x_ - sinb * y_, sinb * x_ + cosb * y_
    # 3:
    x_, z_ =  cosa * x_ + sina * z_, -sina * x_ + cosa * z_
    return (x_, y_, z_)

A5_o5_l = numx.sqrt(tau2 + 1)
A5_o5_cosa_1 = tau/A5_o5_l
A5_o5_sina_1 = 1/A5_o5_l
A5_o5_cosa_2 = math.cos(72 * Geom3D.Deg2Rad)
A5_o5_sina_2 = math.sin(72 * Geom3D.Deg2Rad)

def A5_F_turn_o5(x, y, z, positive = True):
    """Rotate [x, y, z] a fifth turn around the A5 o5 axis [0, 1, tau]

    Returns the tuple [x', y', z']
    """
    # Rotation is obtained by
    # 1. rotate positive x-axis, by complex multiplying with (tau/l, 1/l)
    # 1. rotate quarter turn around positive z-axis
    # 3. rotate the opposite of 1.
    # TODO: optimise me

    # 1:
    x_ = x
    y_ = A5_o5_cosa_1 * y - A5_o5_sina_1 * z
    z_ = A5_o5_sina_1 * y + A5_o5_cosa_1 * z
    # 2:
    if positive:
        sinb = A5_o5_sina_2
    else:
        sinb = -A5_o5_sina_2
    x_, y_ = A5_o5_cosa_2 * x_ - sinb * y_, sinb * x_ + A5_o5_cosa_2 * y_
    # 3:
    y_, z_ =  A5_o5_cosa_1 * y_ + A5_o5_sina_1 * z_, -A5_o5_sina_1 * y_ + A5_o5_cosa_1 * z_
    return (x_, y_, z_)

def FoldedRegularHeptagonsA5_t_fill_pos_0(c,
    incl_reflections,
    par_tri_fill,
    par_opp_fill,
    par_edge_len,
    par_fold,
    hept_coords
):
    """Calculates the edge lengths for the A5 case of folded heptagons.

    This calculates for the triangle fill position 0 and refl_1 and refl_2.
    c           : see FoldedRegularHeptagonsA5
    incl_reflections: whether this is a model that includes reflections.
    par_tri_fill: params[0], see FoldedRegularHeptagonsA5
    par_opp_fill: params[1], see FoldedRegularHeptagonsA5
    par_edge_len: params[2], see FoldedRegularHeptagonsA5
    par_fold    : params[3], see FoldedRegularHeptagonsA5
    hept_coords : an array of tuples: [(x0, y0, z0), (x1, y1, y2),..] with the
                  heptagon coordinates.
    """
    x0, y0, z0 = hept_coords[0]
    x1, y1, z1 = hept_coords[1]
    x2, y2, z2 = hept_coords[2]
    x3, y3, z3 = hept_coords[3]
    x4, y4, z4 = hept_coords[4]
    x5, y5, z5 = hept_coords[5]
    x6, y6, z6 = hept_coords[6]
    cp = copy.copy(par_edge_len)
    edgeAlternative = par_tri_fill
    try:
        edgeLengths = par_edge_len
    except IndexError:
        edgeLengths = [1., 1., 1., 1., 1., 1., 1.]

    # False, for right-hand coord. system
    x12, y12, z12 = A5_F_turn_o5(x0, y0, z0, False)
    x14, y14, z14 = A5_F_turn_o5(x1, y1, z1, False)

    #
    # EDGE A: only one for A5xI
    #
    #if ((edgeAlternative & loose_bit) != 0 or
    #   (edgeAlternative & twist_bit) != 0
    #):
    if (edgeAlternative == TriangleAlt.refl_1 or
                                edgeAlternative == TriangleAlt.refl_2 or
                                (edgeAlternative & loose_bit) != 0
    ):
        # V2 - V9:[-x5,   -y5,    z5], # V9 = V5'
        cp[0] = numx.sqrt((x2+x5)*(x2+x5) + (y2+y5)*(y2+y5) + (z2-z5)*(z2-z5)) - edgeLengths[0]
    else:
        # V3 - V12, V12 = V0'
        cp[0] = v_delta(x3, y3, z3, x12, y12, z12) - edgeLengths[0]

    #
    # EDGE B:
    #
    plain_edge_alt = edgeAlternative & ~alt_bit
    if (edgeAlternative == TriangleAlt.refl_1):
        # V5 - Third-turn-around-o3(V2)
        # True: opposite turn and right-hand coord system
        V2_o4_x, V2_o4_y, V2_o4_z = A5_T_turn_o3(x2, y2, z2)
        cp[1] = v_delta(x5, y5, z5, V2_o4_x, V2_o4_y, V2_o4_z) - edgeLengths[1]
    elif (edgeAlternative == TriangleAlt.refl_2):
        # V10 - Third-turn-around-o3(V5), V10 = V2' = [-x2, -y2, z2]
        # True: opposite turn and right-hand coord system
        V_o4_x, V_o4_y, V_o4_z = A5_T_turn_o3(x5, y5, z5)
        cp[1] = v_delta(-x2, -y2, z2, V_o4_x, V_o4_y, V_o4_z) - edgeLengths[1]
    elif plain_edge_alt == TriangleAlt.stripII:
        cp[1] = v_delta(x3, y3, z3, x14, y14, z14) - edgeLengths[1]
    else:
        cp[1] = v_delta(x2, y2, z2, x12, y12, z12) - edgeLengths[1]

    #
    # EDGE C
    #
    if (edgeAlternative == TriangleAlt.refl_1):
        # V6 - Q-turn-around-o4(V1)
        # True: opposite turn and right-hand coord system
        V1_o4_x, V1_o4_y, V1_o4_z = A5_T_turn_o3(x1, y1, z1)
        cp[2] = v_delta(x6, y6, z6, V1_o4_x, V1_o4_y, V1_o4_z) - edgeLengths[2]
    elif (edgeAlternative == TriangleAlt.refl_2):
        # V11 - Q-turn-around-o4(V6), V11 = V1' = [-x1, -y1, z1]
        # True: opposite turn and right-hand coord system
        V_o4_x, V_o4_y, V_o4_z = A5_T_turn_o3(x6, y6, z6)
        cp[2] = v_delta(-x1, -y1, z1, V_o4_x, V_o4_y, V_o4_z) - edgeLengths[2]
    #TODO:
    elif (
        edgeAlternative != TriangleAlt.star
        and edgeAlternative != TriangleAlt.star1loose
    ):
        cp[2] = v_delta(x2, y2, z2, x14, y14, z14) - edgeLengths[2]
    else:
        cp[2] = v_delta(x1, y1, z1, x12, y12, z12) - edgeLengths[2]

    #
    # EDGE D
    #
    #if (edgeAlternative & twist_bit) != 0:
    if (edgeAlternative == TriangleAlt.refl_1):
        # V0 - T-turn-around-o4(V9:[x0,   y0,    z0])
        # True: opposite turn and right-hand coord system
        V0_o4_x, V0_o4_y, V0_o4_z = A5_T_turn_o3(x0, y0, z0)
        cp[3] = v_delta(x0, y0, z0, V0_o4_x, V0_o4_y, V0_o4_z) - edgeLengths[3]
    elif (edgeAlternative == TriangleAlt.refl_2):
        # V7 - Q-turn-around-o4(V0), V7 = o2(v0) = [-x0, -y0, z0]
        # True: opposite turn and right-hand coord system
        V_o4_x, V_o4_y, V_o4_z = A5_T_turn_o3(x0, y0, z0)
        cp[3] = v_delta(-x0, -y0, z0, V_o4_x, V_o4_y, V_o4_z) - edgeLengths[3]
    elif (edgeAlternative & alt_bit == 0):
        cp[3] = v_delta(x1, y1, z1, x14, y14, z14) - edgeLengths[3]
    else:
        x16, y16, z16 = A5_F_turn_o5(x2, y2, z2)
        cp[3] = v_delta(x2, y2, z2, x16, y16, z16) - edgeLengths[3]

    if not incl_reflections:
        # True: opposite turn and right-hand coord system
        x13, y13, z13 = A5_T_turn_o3(x6, y6, z6)
        #
        # OPPOSITE EDGE B
        #
        if plain_edge_alt == TriangleAlt.stripII:
            cp[4] = v_delta(x4, y4, z4, x13, y13, z13) - edgeLengths[4]
        elif plain_edge_alt & rot_bit == rot_bit:
            # TODO TODO TODO
            # V2 - V16:[y6, z6, x6], # V16 = V6'
            cp[4] = numx.sqrt((x2-y6)*(x2-y6) + (y2-z6)*(y2-z6) + (z2-x6)*(z2-x6)) - edgeLengths[4]
        else:
            # V9 = O2(V5)
            cp[4] = v_delta(-x5, -y5, z5, x12, y12, z12) - edgeLengths[4]

        #
        # OPPOSITE EDGE C
        #
        #
        if par_opp_fill == TriangleAlt.arot_star1loose:
            # TODO
            # V2 - V19: V19 = V5' = [y5, z5, x5]
            cp[5] = numx.sqrt((x2-y5)*(x2-y5) + (y2-z5)*(y2-z5) + (z2-x5)*(z2-x5)) - edgeLengths[5]
        elif par_opp_fill == TriangleAlt.rot_star1loose:
            # TODO
            # V2 - V8: V8 = V6' = [-x6, -y6, z6]
            cp[5] = numx.sqrt((x2+x6)*(x2+x6) + (y2+y6)*(y2+y6) + (z2-z6)*(z2-z6)) - edgeLengths[5]
        elif (
            par_opp_fill != TriangleAlt.star
            and par_opp_fill != TriangleAlt.star1loose
        ):
            cp[5] = v_delta(x5, y5, z5, x13, y13, z13) - edgeLengths[5]
        else:
            # x8,  y8,  z8  = -x6, -y6, z6
            cp[5] = v_delta(-x6, -y6, z6, x12, y12, z12) - edgeLengths[5]

        #
        # OPPOSITE EDGE D
        #
        if (par_opp_fill & alt_bit == 0):
            cp[6] = v_delta(x6, y6, z6, x13, y13, z13) - edgeLengths[6]
        else:
            x15, y15, z15 = A5_T_turn_o3(x5, y5, z5)
            cp[6] = v_delta(x5, y5, z5, x15, y15, z15) - edgeLengths[6]

    #print cp
    return cp

def FoldedRegularHeptagonsA5_t_fill_pos_1(c,
    incl_reflections,
    par_tri_fill,
    par_opp_fill,
    par_edge_len,
    par_fold,
    hept_coords
):
    """Calculates the edge lengths for the A5 case of folded heptagons.

    This calculates for the triangle fill position 0 and refl_1 and refl_2.
    c           : see FoldedRegularHeptagonsA5
    incl_reflections: whether this is a model that includes reflections.
    par_tri_fill: params[0], see FoldedRegularHeptagonsA5
    par_opp_fill: params[1], see FoldedRegularHeptagonsA5
    par_edge_len: params[2], see FoldedRegularHeptagonsA5
    par_fold    : params[3], see FoldedRegularHeptagonsA5
    hept_coords : an array of tuples: [(x0, y0, z0), (x1, y1, y2),..] with the
                  heptagon coordinates.
    """
    x0, y0, z0 = hept_coords[0]
    x1, y1, z1 = hept_coords[1]
    x2, y2, z2 = hept_coords[2]
    x3, y3, z3 = hept_coords[3]
    x4, y4, z4 = hept_coords[4]
    x5, y5, z5 = hept_coords[5]
    x6, y6, z6 = hept_coords[6]
    cp = copy.copy(par_edge_len)
    try:
        edgeLengths = par_edge_len
    except IndexError:
        edgeLengths = [1., 1., 1., 1., 1., 1., 1.]

    # Use nrs from Orbitit:
    # False, for right-hand coord. system
    x40, y40, z40 = A5_F_turn_o5(x6, y6, z6, False)
    x11, y11, z11 = A5_F_turn_o5(x0, y0, z0, False)
    # True: opposite turn and right-hand coord system
    x23, y23, z23 = A5_T_turn_o3(x5, y5, z5)
    x17, y17, z17 = A5_T_turn_o3(x6, y6, z6)

    #
    # EDGE A: only one for A5xI
    #
    cp[0] = v_delta(x2, y2, z2, x40, y40, z40) - edgeLengths[0]

    #
    # EDGE B:
    #
    if (par_tri_fill == TriangleAlt.stripII):
        cp[1] = v_delta(x2, y2, z2, x11, y11, z11) - edgeLengths[1]
    else:
        cp[1] = v_delta(x1, y1, z1, x40, y40, z40) - edgeLengths[1]

    #
    # EDGE C
    #
    if (par_tri_fill == TriangleAlt.star):
        cp[2] = v_delta(x0, y0, z0, x40, y40, z40) - edgeLengths[2]
    else:
        cp[2] = v_delta(x1, y1, z1, x11, y11, z11) - edgeLengths[2]

    #
    # EDGE D
    #
    cp[3] = v_delta(x0, y0, z0, x11, y11, z11) - edgeLengths[3]

    # always: not incl_reflections:
    #
    # OPPOSITE EDGE B
    #
    if (par_opp_fill & loose_bit) == loose_bit:
        cp[4] = v_delta(-x5, -y5, z5, x2, y2, z2) - edgeLengths[4]
    elif par_opp_fill == TriangleAlt.stripI:
        cp[4] = v_delta(x4, y4, z4, x17, y17, z17) - edgeLengths[4]
    elif par_opp_fill == TriangleAlt.stripII:
        cp[4] = v_delta(-x2, -y2, z2, x23, y23, z23) - edgeLengths[4]
    else:
        cp[4] = v_delta(x4, y4, z4, x17, y17, z17) - edgeLengths[4]

    #
    # OPPOSITE EDGE C
    #
    #
    if par_opp_fill == TriangleAlt.strip1loose:
        cp[5] = v_delta(-x2, -y2, z2, x23, y23, z23) - edgeLengths[5]
    elif (par_opp_fill & star_bas) == star_bas:
        # star and star_1_loose
        cp[5] = v_delta(x5, y5, z5, x17, y17, z17) - edgeLengths[5]
    else:
        # strip I and strip II
        cp[5] = v_delta(x4, y4, z4, x23, y23, z23) - edgeLengths[5]

    #
    # OPPOSITE EDGE D
    #
    cp[6] = v_delta(x5, y5, z5, x23, y23, z23) - edgeLengths[6]

    #print cp
    return cp

def FoldedRegularHeptagonsA5(c, params):
    """Calculates the edge lengths for the A5 case of folded heptagons.

    The case contains
    c[0]: a translation (towards the viewer)
    c[1]: half the angle between the 2 heptagons 0,1,2,3,4,5,6 and 7,8,9,3,4,10,11
    c[2]: the angle of the first fold (left)
    c[3]: the angle of the second fold (left)
    c[4]: rotation angle around z-axis
    c[5]: the angle of the first fold (right)
    c[6]: the angle of the second fold (right)
    The vertices are positioned as follows:

    #
    #              10             5
    #     11                               6
    #
    #                      4
    #
    #   7           z-axis . o2-axis          0       . o3-axis: [1/tau, 0, tau]
    #
    #                      3
    #
    #      8                               1          +---> x
    #               9             2                   |
    #                                                 v y
    #
    #                      . o5-axis: [0, 1, tau]
    #
    #
    #             12 = o5(0)
    #
    #   13 = o5(6)        14 = o5(1)
    #
    # 15 = o5(5)             16 = o5(2)

    And the relevant vertices are defined as follows:

    The heptagons are regular, so
    |0-1| = |1-2| = |2-3| = |3-4| = |4-5| = |5-6| = |6-0| = |12 - 14| = 1

    For the param[0] constant TriangleAlt names can be used:
    The alternatives for creatings triangles lead to the possible variable edge
    lengths: refl_1, refl_2, which are for the A5xI symmetry.
    The alternatives for creatings triangles for A5 leads to the following
    possible variable edge lengths:
    params{'0'} | edge a | edge b | edge c | edge d
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 1 - 14     strip 1 loose
          opp.  |        | 12 - 9 | 9 - 13 | 8 - 13
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 1 - 14     strip I
          opp.  |        | 12 - 9 | 9 - 13 | 8 - 13
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 1 - 14     strip II
          opp.  |        | 3 - 13 | 9 - 13 | 8 - 13
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 12 - 1 | 1 - 14     star
          opp.  |        | 12 - 9 | 12 - 8 | 8 - 13
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 12 - 1 | 1 - 14     star 1 loose
          opp.  |        | 12 - 9 | 12 - 8 | 8 - 13
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 2 - 16     alt strip 1 loose
          opp.  |        | 12 - 9 | 9 - 13 | 9 - 15
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 2 - 16     alt strip II
          opp.  |        | 3 - 13 | 9 - 13 | 9 - 15
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 2 - 16     alt strip I
          opp.  |        | 12 - 9 | 9 - 13 | 9 - 15
    ------------+--------+--------+--------+-------

    only valid for opposites alternatives:
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 9 - 16 | 8 - 16     rot strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 9 - 16 | 9 - 19     alt rot strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 2 -  8 | 8 - 16     rot star 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 2 - 19 | 9 - 19     alt rot star 1 loose
    ------------+--------+--------+--------+-------

    params{'1'} alternatives for the opposite triangle fill.

    params{'2'} steers the edge lengths. It is a vector of 4 or 7 floating point
    numbers that expresses the edge lengths of [a, b, c, d] or
    [a, b0, c0, d, b1, c1] resp. If length 4, then c[5] = c[2] and c[6] = c[3];
    the value of c[4] is either 0 or pi/2 rad, depending on params[5].
    If this params[2] is not given, the edge lengths are supposed to be 1.

    params{'3'} defines which heptagon folding method is used.

    params{'4'} start position of the triangle fill

    params{'5'} start position of the opposite triangle fill

    params{'6'} rotate the folding with n/7 turn
    """

    # params indices in text:

    T      = c[0]
    alpha  = c[1]
    beta0  = c[2]
    gamma0 = c[3]

    par_tri_fill = Param.tri_fill
    par_opp_fill = Param.opp_fill
    par_edge_len = Param.edge_len
    par_fold     = Param.h_fold

    incl_reflections = len(params[par_edge_len]) == 4
    if incl_reflections:
        beta1  = beta0
        gamma1 = gamma0
        if params[par_tri_fill] == TriangleAlt.refl_2:
            delta = D_Dom[Symmetry.A5xI][1]
        else:
            delta = D_Dom[Symmetry.A5xI][0]
        oppAlternative = params[par_tri_fill]
    else:
        delta  = c[4]
        beta1  = c[5]
        gamma1 = c[6]
        oppAlternative = params[par_opp_fill]

    hept_coords = GetBaseHeptagon(
            T, alpha, beta0, beta1, gamma0, gamma1, delta, params[par_fold])
    #print '[y0, x0, z0] = (%.4f, %.4f, %.4f)' % (hept_coords[0][1], hept_coords[0][0], hept_coords[0][2])
    #print '[y1, x1, z1] = (%.4f, %.4f, %.4f)' % (hept_coords[1][1], hept_coords[1][0], hept_coords[1][2])
    #print '[y2, x2, z2] = (%.4f, %.4f, %.4f)' % (hept_coords[2][1], hept_coords[2][0], hept_coords[2][2])
    #print '[y3, x3, z3] = (%.4f, %.4f, %.4f)' % (hept_coords[3][1], hept_coords[3][0], hept_coords[3][2])
    #print '[y4, x4, z4] = (%.4f, %.4f, %.4f)' % (hept_coords[4][1], hept_coords[4][0], hept_coords[4][2])
    #print '[y5, x5, z5] = (%.4f, %.4f, %.4f)' % (hept_coords[5][1], hept_coords[5][0], hept_coords[5][2])
    #print '[y6, x6, z6] = (%.4f, %.4f, %.4f)' % (hept_coords[6][1], hept_coords[6][0], hept_coords[6][2])

    if len(params) <= Param.t_fill_pos or params[Param.t_fill_pos] == 0:
        return FoldedRegularHeptagonsA5_t_fill_pos_0(c,
            incl_reflections,
            params[par_tri_fill],
            oppAlternative,
            params[par_edge_len],
            params[par_fold],
            hept_coords
        )
    else:
        return FoldedRegularHeptagonsA5_t_fill_pos_1(c,
            incl_reflections,
            params[par_tri_fill],
            oppAlternative,
            params[par_edge_len],
            params[par_fold],
            hept_coords
        )

class Method:
    hybrids = 0
    dnewton = 1
    broyden = 2
    hybrid  = 3

def FindMultiRoot(initialValues,
        symmetry,
        edgeAlternative,
        edgeLengths = [1., 1., 1., 1.],
        fold = Fold.parallel,
        method = 1,
        cleanupF  = None,
        prec_delta = 1e-15,
        maxIter = 100,
        printIter = False,
        quiet     = False,
        oppEdgeAlternative = None,
        triangle_fill_pos = 0
    ):
    if oppEdgeAlternative == None:
        oppEdgeAlternative = edgeAlternative
    if not quiet:
        print '[|a|, |b|, |c|, |d|] =', edgeLengths, 'for',
        if edgeAlternative == 0:
            print 'triangle strip, 1 loose:'
        elif edgeAlternative == 1:
            print 'triangle strip I:'
        elif edgeAlternative == 2:
            print 'triangle strip II:'
        elif edgeAlternative == 3:
            print 'triangle star:'
        elif edgeAlternative == 4:
            print 'triangle star, 1 loose:'

    nrOfIns = len(initialValues)
    params = {
            Param.tri_fill: edgeAlternative,
            Param.opp_fill: oppEdgeAlternative,
            Param.edge_len: edgeLengths,
            Param.h_fold:   fold,
        }
    if triangle_fill_pos > 0:
        params[Param.t_fill_pos] = triangle_fill_pos
    if symmetry == Symmetry.A5 or symmetry == Symmetry.A5xI:
        mysys = multiroots.gsl_multiroot_function(
            FoldedRegularHeptagonsA5,
            params,
            nrOfIns
        )
    elif symmetry == Symmetry.S4 or symmetry == Symmetry.S4xI:
        mysys = multiroots.gsl_multiroot_function(
            FoldedRegularHeptagonsS4,
            nrOfIns
        )
    elif symmetry == Symmetry.A4xI or symmetry == Symmetry.S4A4:
        if nrOfIns == 5:
            # the last value is a constant:
            nrOfIns = 4
            initialValues = initialValues[0:4]
        assert (nrOfIns == 4)
        mysys = multiroots.gsl_multiroot_function(
            FoldedRegularHeptagonsA4xI,
            {
                Param.tri_fill: edgeAlternative,
                Param.edge_len: edgeLengths,
                Param.h_fold:   fold
            },
            nrOfIns
        )
    elif symmetry == Symmetry.A4:
        assert (nrOfIns == 7)
        mysys = multiroots.gsl_multiroot_function(
            FoldedRegularHeptagonsA4,
            params,
            nrOfIns
        )
    else:
        assert False, "error: wrong dimension: %d" % nrOfIns

    if method == Method.hybrids:
        solver = multiroots.hybrids(mysys, nrOfIns)
    elif method == Method.dnewton:
        solver = multiroots.dnewton(mysys, nrOfIns)
    elif method == Method.broyden:
        solver = multiroots.broyden(mysys, nrOfIns)
    else:
        solver = multiroots.hybrid(mysys, nrOfIns)

    solver.set(initialValues)
    if printIter:
        print "# Using solver ", solver.name(), 'with edge alternative:', edgeAlternative
        print "# %5s %9s %9s %9s %9s  %9s  %10s  %9s  %10s" % (
            "iter",
            "x[0]", "x[1]", "x[2]", "x[3]",
            "f[0]", "f[1]", "f[2]", "f[3]"
        )
        # Get and print initial values
        r = solver.root()
        x = solver.getx()
        f = solver.getf()
        print "  %5d % .7f % .7f % .7f % .7f  % .7f  % .7f  % .7f  % .7f" %(
            0,
            x[0], x[1], x[2], x[3],
            f[0], f[1], f[2], f[3]
        )
    result = None
    for iter in range(maxIter):
        try:
            status = solver.iterate()
            r = solver.root()
            x = solver.getx()
            f = solver.getf()
            status = multiroots.test_residual(f, prec_delta)
            if status == errno.GSL_SUCCESS and not quiet:
                print "# Converged after %5d iterations" % (iter + 1)
            if printIter:
                print "  %5d % .15f % .15f % .15f % .15f" %(
                    iter+1,
                    x[0], x[1], x[2], x[3])
                print "  ----> % .15f % .15f % .15f % .15f" %(
                    f[0], f[1], f[2], f[3]
                )
            if status == errno.GSL_SUCCESS:
                # Now print solution with high precision
                if not quiet:
                    for i in range(nrOfIns):
                        print "x[%d] = %.15f" % (i, x[i])
                result = [x[i] for i in range(nrOfIns)]
                break
            else:
                if not quiet:
                    print "# not converged... :("
        except pygsl.errors.gsl_SingularityError:
            #print 'gsl_Singularity Error exception', maxIter
            del(solver)
            break
            pass
        except pygsl.errors.gsl_NoProgressError:
            #print 'gsl_NoProgress Error exception', maxIter
            del(solver)
            break
            pass
        except pygsl.errors.gsl_JacobianEvaluationError:
            #print 'gsl_JacobianEvaluation Error exception', maxIter
            del(solver)
            break
            pass
    if result != None and cleanupF != None:
        result = cleanupF(result, nrOfIns)
    return result

class RandFindMultiRootOnDomain(threading.Thread):
    def __init__(this,
        domain,
        symmetry,
        threadId = 0,
        edgeAlternative = TriangleAlt.stripI,
        oppEdgeAlternative = None,
        method = 1,
        precision = 15,
        fold = Fold.parallel,
        dynSols = None,
        edgeLengths = [1., 1., 1., 1., 1., 1., 1.],
        outDir = "frh-roots",
        exceptQueue = None,
        triangle_fill_pos = 0
    ):
        this.domain = domain
        this.symmetry = symmetry
        this.threadId = threadId
        this.method = method
        this.exceptQueue = exceptQueue
        this.triangle_fill_pos = triangle_fill_pos

        # Amount of digits to write the input values (of the formula) with
        this.precision = precision
        # how much the caculated edge length may differ:
        # write with a bit higher precision, to prevent throwing solutions after
        # reading these again because of rounding problems.
        # e.g. for this one:
        # python roots_batch.py -i 100 -p 12 -o ./ -l 9 -a 4 -f 0  A4xI
        this.prec_delta = pow(10, -(precision - 1))
        # Any delta of this size or bigger in the input vector should mean a
        # different solution:
        # Choose this quite bigger than the precision margin, to prevent getting
        # doublets.
        if precision > 5:
            this.eq_margin = this.prec_delta * 100
        else:
            this.eq_margin = this.prec_delta
        # This means that we will write the final values with a higher precision
        # than valid, ie. it is a fake precision, we fool the user.
        # However to request a precision of 15 digits, to make sure that you
        # don't have doublets, you need to require that the edgelengths don't
        # differ more than 1e-18, which is not possible. Instead we will write
        # 15 digits af the the floating point and interpred all solution that
        # differ less the 1.e-12 as equal solutions.

        this.fold = fold
        this.edgeAlternative = edgeAlternative
        this.oppEdgeAlternative = oppEdgeAlternative
        this.edgeLengths = edgeLengths
        this.dynamicSols = dynSols
        this.stopAfter = 100000
        this.outDir = outDir
        if not outDir[-1] == '/':
            this.outDir = "%s/" % outDir
        if not os.path.isdir(outDir):
            os.mkdir(outDir, 0755)
        random.seed()
        threading.Thread.__init__(this)

    def sol_str(this, r, n):
        digs = this.precision
        s = '    [%s' % glue.f2s(r[0], digs)
        for i in range(1, n):
            s = '%s, %s' % (s, glue.f2s(r[i], digs))
        s = '%s],\n' % s
        return s

    changeIterLimits = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    maxIters = [2 ** (6+8-i) for i in range(9)]
    def setMaxIter(this):
        """return nr of trials of 1 value depending on amount of solutions

        If there is no solution yet, you could just continue, since there is no
        chance that if you continue that you'll find a solution that is already
        found. Towards more solutions it is probably better to start with
        another random value if it doesn't develop.
        """
        nrSols = len(this.results)
        # note for performance it is better to start with [8]
        if nrSols >= this.changeIterLimits[8]:
            return this.maxIters[8]
        elif nrSols == this.changeIterLimits[7]:
            return this.maxIters[7]
        elif nrSols == this.changeIterLimits[6]:
            return this.maxIters[6]
        elif nrSols == this.changeIterLimits[5]:
            return this.maxIters[5]
        elif nrSols == this.changeIterLimits[4]:
            return this.maxIters[4]
        elif nrSols == this.changeIterLimits[3]:
            return this.maxIters[3]
        elif nrSols == this.changeIterLimits[2]:
            return this.maxIters[2]
        elif nrSols == this.changeIterLimits[1]:
            return this.maxIters[1]
        elif nrSols <= this.changeIterLimits[0]:
            return this.maxIters[0]

    dpi = 2*numx.pi
    def cleanupResult(this, v, l = 4):
        lim = this.dpi
        hLim = numx.pi
        for i in range(1, l):
            v[i] = v[i] % lim
            # move interval from [0, lim] to [-lim/2, lim/2]:
            if v[i] > hLim:
                v[i] = v[i] - lim
            if eq(v[i], -hLim, this.eq_margin):
                # float rounding:
                v[i] = v[i] + lim
            # shouldn't happen:
            #elif v[i] < -hLim:
            #    v[i] = v[i] + lim
        # If the position angle equals 180 degrees, reconstruct the solution to
        # a pos angle = 0 by:
        # - using a negative translation
        # - an opposite dihedral angle
        # - negative folding angles
        # TODO check if this is valid for symmetries other than A4
        if (
            len(v) >= 5
            and
            eq(v[4], numx.pi, this.eq_margin)
        ):
            v[4] = 0                    # set pos angle to 0 instead
            v[0] = -v[0]                # -translate
            if v[1] < 0:
                v[1] = -numx.pi - v[1]  # oppsite dihedral angle
            else:
                v[1] = numx.pi - v[1]   # oppsite dihedral angle
            v[2] = -v[2]                # opposite folds
            v[3] = -v[3]
            if len(v) >= 6:
                v[5] = -v[5]            # opposite folds
                if len(v) >= 7:
                    v[6] = -v[6]
        return v

    def randTestvalue(this):
        dLen = len(this.domain)
        return [
            random.random() * (this.domain[i][1] - this.domain[i][0]) + this.domain[i][0]
            for i in range(dLen)
        ]

    # This can be optimised
    def solutionAlreadyFound(this, sol):
        found = False
        lstRange = range(len(sol))
        for old in this.results:
            allElemsEqual = True
            for i in lstRange:
                if len(old) < len(sol):
                    print 'Oops'
                    print 'old', old
                    print 'sol', sol
                if abs(old[i] - sol[i]) > this.eq_margin:
                    allElemsEqual = False
                    break # for i loop, not for old
            if allElemsEqual:
                found = True
                break # for old loop
        return found

    def isDynamicSol(this, sol):
        if this.dynamicSols != None:
            for d in this.dynamicSols:
                ea_ok = False
                for ea in d['edgeAlternative']:
                    ea_ok = (this.edgeAlternative == ea) or ea_ok
                if ea_ok:
                    oa_ok = False
                    for oa in d['oppEdgeAlternative']:
                        oa_ok = (this.oppEdgeAlternative == oa) or oa_ok
                    if oa_ok:
                        fld_ok = False
                        for fld in d['fold']:
                            fld_ok = (this.fold == fld) or fld_ok
                        if fld_ok:
                            for vs in d['sol_vector']:
                                sol_isEq = True
                                for i in range(len(vs)):
                                    if not eq(vs[i], this.edgeLengths[i],
                                                            this.eq_margin):
                                        sol_isEq = False
                                        break # don't check other (i, v)
                                if sol_isEq:
                                    break # from vs in d['sol_vector']
                            if sol_isEq:
                                for vs in d['set_vector']:
                                    isEq = True
                                    for k, v in vs.iteritems():
                                        if not eq(sol[k], v, this.eq_margin):
                                            isEq = False
                                            break
                                    if isEq:
                                        return isEq
        return False

    def _symmetricEdges(this):
        el = this.edgeLengths
        return (
            len(el) > 5 and (
                this.edgeAlternative == this.oppEdgeAlternative and
                eq(el[1], el[4], this.eq_margin) and
                eq(el[2], el[5], this.eq_margin) and
                eq(el[3], el[6], this.eq_margin)
            )
        )

    def symmetricEdges(this):
        if this.symmetry == Symmetry.A4:
            return this._symmetricEdges()
        elif this.symmetry == Symmetry.S4:
            return this._symmetricEdges() and (
                        this.edgeAlternative == TriangleAlt.refl_1 or
                        this.edgeAlternative == TriangleAlt.refl_2
                    )
        elif this.symmetry == Symmetry.A5:
            return this._symmetricEdges() and (
                        this.edgeAlternative == TriangleAlt.refl_1 or
                        this.edgeAlternative == TriangleAlt.refl_2
                    )
        else:
            return False

    def getOutName(this):
        if len(this.edgeLengths) == 4:
            return this.getOutReflName()
        # else:
        es = ''
        for l in this.edgeLengths:
            # TODO move to func and reuse in getOutReflName
            if l == 1 or l == 0:
                es = '%s_%d' % (es, l)
            elif eq(l, V2):
                es = '%s_V2' % (es)
            else:
                es = '%s_%.1f' % (es, l)
        es = es[1:]
        return '%sfrh-roots-%s-fld_%s.0-%s_%d-opp_%s_%d.py' % (
                this.outDir,
                es, Fold(this.fold),
                string.join(Stringify[this.edgeAlternative].split(), '_'),
                triangle_fill_pos,
                string.join(Stringify[this.oppEdgeAlternative].split(), '_'),
                triangle_fill_pos
            )

    def getOutReflName(this):
        es = ''
        for i in range(0, 4):
            l = this.edgeLengths[i]
            if l == 1 or l == 0:
                es = '%s_%d' % (es, l)
            elif eq(l, V2):
                es = '%s_V2' % (es)
            else:
                es = '%s_%.1f' % (es, l)
        es = es[1:]
        return '%sfrh-roots-%s-fld_%s.0-%s.py' % (
                this.outDir,
                es, Fold(this.fold),
                string.join(Stringify[this.edgeAlternative].split(), '_')
            )

    def _extend_refl_results(this, refl_results):
        for r in refl_results:
            if len(r) == 4:
                r.extend([0.0, r[2], r[3]])
            elif len(r) == 5:
                r.extend([r[2], r[3]])

    def run(this):
        try:
            this._run()
        except:
            if (this.exceptQueue != None):
                this.exceptQueue.put(sys.exc_info())
            raise

    def tst_solutions_exist(this):
        this.solutions_exist = this._tst_solutions_exist()

    def _run(this):
        if this.oppEdgeAlternative == None:
            this.oppEdgeAlternative = this.edgeAlternative
        # changeIterLimits depends a bit on the amount of solutions.
        # 1. if you don't have a solution: just jump around until you get a
        #    hit.
        # 2. But you don't want to jump around a long time, just to find out
        #    it was a solution you already had.
        # Nr 2 will happen, when you are looking for the last solution,
        # especially if solutions are rare.

        filename = this.getOutName()

        # read previous file
        try:
            f = open(filename, 'r')
            ed = {'__name__': 'readPyFile'}
            exec f in ed
            # TODO check settings
            try:
                this.results = ed['results']
            except KeyError:
                this.results = []
                pass
            try:
                # TODO: remove; Note: some files still have them)
                results_refl = ed['results_refl']
                this._extend_refl_results(results_refl)
                this.results.extend(results_refl)
            except KeyError:
                pass
            try:
                prev_iterations = ed['iterations']
            except KeyError:
                prev_iterations = 0
                pass
            f.close()

        except IOError:
            this.results = []
            prev_iterations = 0

        if len(this.edgeLengths) > 4 and this.symmetricEdges():
            refl_filename = this.getOutReflName()

            # read previous file with reflective sols
            try:
                f = open(refl_filename, 'r')
                ed = {'__name__': 'readPyFile'}
                exec f in ed
                # TODO check settings
                try:
                    results_refl = ed['results']
                    this._extend_refl_results(results_refl)
                    this.results.extend(results_refl)
                except KeyError:
                    pass
                try:
                    results_refl = ed['results_refl']
                    this._extend_refl_results(results_refl)
                    this.results.extend(results_refl)
                except KeyError:
                    pass
                try:
                    prev_refl_iterations = ed['iterations']
                except KeyError:
                    prev_refl_iterations = 0
                    pass
                f.close()

            except IOError:
                prev_refl_iterations = 0

        # all solutions that are read might have less precision, check them
        # here and possibly increase precision (or reject them)
        reiterated_input_results = []
        maxIter = 1000 # this can be high assuming it is a solution
        for solution in this.results:
            result = FindMultiRoot(solution,
                    this.symmetry,
                    this.edgeAlternative,
                    this.edgeLengths,
                    this.fold,
                    this.method,
                    lambda v,l: this.cleanupResult(v, l),
                    this.prec_delta,
                    maxIter,
                    printIter = False,
                    quiet     = True,
                    oppEdgeAlternative = this.oppEdgeAlternative,
                    triangle_fill_pos = this.triangle_fill_pos
                )
            # write the previous solution if the difference is smaller than the
            # precision (this since we write with one digit more)
            if result == None:
                print 'Oops, dropping solution', solution
            elif Veq(result, solution, this.prec_delta, log=False) or (
                                                    this.isDynamicSol(result)):
                reiterated_input_results.append(solution)
            else:
                print 'Note, better precison for:\n-->', solution
                #print '-->', result
                reiterated_input_results.append(result)
        if (len(reiterated_input_results) != len(this.results)):
            print 'Warning: %d solution(s) thrown after increasing the precision'\
                % (len(this.results) - len(reiterated_input_results))
        this.results = reiterated_input_results

        nrOfIters = 0
        # TODO: why is trapezium handled differently?
        # TODO: why not use 50 always? will give better loop performance
        if this.fold == Fold.trapezium:
            maxIter = 50
        else:
            maxIter = this.setMaxIter()

        while True:
            try:
                result = FindMultiRoot(this.randTestvalue(),
                        this.symmetry,
                        this.edgeAlternative,
                        this.edgeLengths,
                        this.fold,
                        this.method,
                        lambda v,l: this.cleanupResult(v, l),
                        this.prec_delta,
                        maxIter,
                        printIter = False,
                        quiet     = True,
                        oppEdgeAlternative = this.oppEdgeAlternative,
                        triangle_fill_pos = this.triangle_fill_pos
                    )
                if (
                    result != None
                    and not this.solutionAlreadyFound(result)
                    and not this.isDynamicSol(result)
                ):
                    this.results.append(result)
                    maxIter = this.setMaxIter()
                    print '(thread %d) %s:' % (
                            this.threadId,
                            time.strftime("%y%m%d %H%M%S", time.localtime())
                        ),
                    print 'added new result nr %d (after %d new iterations)' % (
                            len(this.results),
                            nrOfIters
                        )
            except pygsl.errors.gsl_SingularityError:
                pass
            except pygsl.errors.gsl_NoProgressError:
                pass
            except pygsl.errors.gsl_JacobianEvaluationError:
                pass
            nrOfIters = nrOfIters + 1
            if nrOfIters >= this.stopAfter:
                # always write the result, even when empty, so it is known how
                # many iterations were done (without finding a result)
                f = open(filename, 'w')
                f.write('# edgeLengths = %s\n' % str(this.edgeLengths))
                f.write('# edgeAlternative = %s\n' % Stringify[this.edgeAlternative])
                if len(this.edgeLengths) > 4:
                    f.write('# oppEdgeAlternative = %s\n' % Stringify[this.oppEdgeAlternative])
                f.write('# fold = %s\n' % Fold(this.fold))

                # filter results. This is needed since the filter changed after
                # having found many solutions.
                # Also split in results and results_refl:
                cp_results = this.results[:]
                this.results = [] # for this.solutionAlreadyFound(result)
                results      = []
                results_refl = []
                for result in cp_results:
                    this.cleanupResult(result, len(result))
                    #print 'sols checked', len(this.results)
                    if not this.solutionAlreadyFound(result):
                        # register result handled for this.solutionAlreadyFound
                        this.results.append(result)
                        # check if this value is (still) valid. This check is
                        # done since the script is under development all the
                        # time.  It is easier to throw an solution that appeared
                        # to be invalid, then to start over the whole search
                        # again...
                        try:
                            if len(this.edgeLengths) == 4:
                                if this.symmetry == Symmetry.A4xI or\
                                                this.symmetry == Symmetry.S4A4:
                                    chk = FoldedRegularHeptagonsA4xI(result,
                                        {
                                            Param.tri_fill: this.edgeAlternative,
                                            Param.edge_len: this.edgeLengths,
                                            Param.h_fold:   this.fold
                                        }
                                    )
                                elif this.symmetry == Symmetry.A5xI:
                                    chk = FoldedRegularHeptagonsA5(result,
                                        {
                                            Param.tri_fill: this.edgeAlternative,
                                            Param.edge_len: this.edgeLengths,
                                            Param.h_fold:   this.fold
                                        }
                                    )
                                else:
                                    chk = FoldedRegularHeptagonsS4(result,
                                        {
                                            Param.tri_fill: this.edgeAlternative,
                                            Param.edge_len: this.edgeLengths,
                                            Param.h_fold:   this.fold,
                                        }
                                    )
                            elif this.symmetry == Symmetry.A4:
                                chk = FoldedRegularHeptagonsA4(result,
                                    {
                                        Param.tri_fill: this.edgeAlternative,
                                        Param.opp_fill: this.oppEdgeAlternative,
                                        Param.edge_len: this.edgeLengths,
                                        Param.h_fold:   this.fold
                                    }
                                )
                            elif this.symmetry == Symmetry.S4:
                                chk = FoldedRegularHeptagonsS4(result,
                                    {
                                        Param.tri_fill: this.edgeAlternative,
                                        Param.opp_fill: this.oppEdgeAlternative,
                                        Param.edge_len: this.edgeLengths,
                                        Param.h_fold:   this.fold,
                                        Param.t_fill_pos: triangle_fill_pos
                                    }
                                )
                            else: # A5
                                chk = FoldedRegularHeptagonsA5(result,
                                    {
                                        Param.tri_fill: this.edgeAlternative,
                                        Param.opp_fill: this.oppEdgeAlternative,
                                        Param.edge_len: this.edgeLengths,
                                        Param.h_fold:   this.fold,
                                        Param.t_fill_pos: triangle_fill_pos
                                    }
                                )
                        except IndexError:
                            print 'Ooops while working on', filename
                            raise

                        isEq = True
                        # check if the solution is valid (a solution)
                        for i in range(len(chk)):
                            if not eq(chk[i], 0., this.prec_delta):
                                print '|chk[%d]| = |' % i, chk[i], '| >', this.prec_delta
                                isEq = False
                                break
                        if isEq:
                            if len(this.edgeLengths) <= 4:
                                results_refl.append(result)
                            elif (
                                (
                                    eq(result[4], 0.0) or
                                    eq(result[4], D_Dom[this.symmetry][1]) or
                                    eq(result[4], -D_Dom[this.symmetry][1]) or
                                    eq(result[4], numx.pi/2) or
                                    eq(result[4], -numx.pi/2) or
                                    eq(result[4], numx.pi) or
                                    eq(result[4], -numx.pi)
                                ) and (
                                    len(result) == 5 or (
                                        len(result) == 7 and
                                        eq(result[2], result[5], 1e-12) and
                                        eq(result[3], result[6], 1e-12)
                                    )
                                )
                            ):
                                results_refl.append(result)
                            else:
                                results.append(result)
                        else:
                            print 'Throwing invalid solution:', result
                    else:
                        print 'Throwing doublet:', result

                f.write('# %s: ' % time.strftime(
                        "%y%m%d %H%M%S", time.localtime())
                    )
                f.write('%d (+%d) solutions found\n' % (
                                len(results), len(results_refl)))
                f.write('iterations = %d\n' % (nrOfIters + prev_iterations))
                if len(this.edgeLengths) != 4:
                    f.write('results = [\n')
                    for r in results:
                        f.write('%s' % this.sol_str(r, 7))
                if len(this.edgeLengths) == 4:
                    if this.edgeAlternative == TriangleAlt.refl_1:
                        angle = D_Dom[this.symmetry][0]
                    else:
                        angle = D_Dom[this.symmetry][1]
                    f.write('results = [\n')
                    for r in results_refl:
                        if eq(angle, 0):
                            f.write(this.sol_str(r, 4))
                        else:
                            try:
                                r[4] = angle
                            except IndexError:
                                r.append(angle)
                            f.write(this.sol_str(r, 5))
                elif this.symmetricEdges():
                    f.write(']\n')
                    # close this file open the relective file:
                    f.write('# for results_refl, see %s\n' % refl_filename)
                    f.close()
                    f = open(refl_filename, 'w')
                    f.write('# edgeLengths = %s\n' % str(this.edgeLengths))
                    f.write('# edgeAlternative = %s\n' % Stringify[this.edgeAlternative])
                    f.write('# fold = %s\n' % Fold(this.fold))
                    f.write('# %s: ' % time.strftime(
                            "%y%m%d %H%M%S", time.localtime())
                        )
                    f.write('%d solutions found\n' % (len(results_refl)))
                    f.write('iterations = %d\n' % (nrOfIters + prev_refl_iterations))
                    f.write('results = [\n')
                    for r in results_refl:
                        if eq(r[4], 0):
                            f.write(this.sol_str(r, 4))
                        else:
                            f.write(this.sol_str(r, 5))
                else:
                    for r in results_refl:
                        f.write(this.sol_str(r, 7))
                f.write(']\n')
                f.close()
                print '(thread %d) %s:' % (
                        this.threadId,
                        time.strftime("%y%m%d %H%M%S", time.localtime())
                    ),
                if len(this.edgeLengths) == 4:
                    print len(results_refl),
                else:
                    print len(results),
                    print '(+%d)' % (len(results_refl)),
                print 'results written to',
                if len(this.edgeLengths) == 4:
                    print filename
                elif this.symmetricEdges():
                    print '%s (%s)' % (filename, refl_filename)
                else:
                    print filename
                break

    def _tst_solutions_exist(this):
        nrOfIters = 0
        maxIter = 5000
        while True:
            try:
                result = FindMultiRoot(this.randTestvalue(),
                        this.symmetry,
                        this.edgeAlternative,
                        this.edgeLengths,
                        this.fold,
                        this.method,
                        lambda v,l: this.cleanupResult(v, l),
                        this.prec_delta,
                        maxIter,
                        printIter = False,
                        quiet     = True,
                        oppEdgeAlternative = this.oppEdgeAlternative,
                        triangle_fill_pos = this.triangle_fill_pos
                    )
                if (result != None):
                    break
            except pygsl.errors.gsl_SingularityError:
                pass
            except pygsl.errors.gsl_NoProgressError:
                pass
            except pygsl.errors.gsl_JacobianEvaluationError:
                pass
            nrOfIters = nrOfIters + 1
            if nrOfIters >= this.stopAfter:
                break
        return result != None

if __name__ == '__main__':
    import sys
    import os

    def testOneSolution(symGrp):

        if symGrp == Symmetry.A4xI:
            T  = 2.45
            a  = Geom3D.Deg2Rad * 40
            b0 = Geom3D.Deg2Rad * 25
            g0 = Geom3D.Deg2Rad * 27
            tmp = numx.array((T, a, b0, g0))
            print 'input values: \n [',
            for t in tmp: print t, ',',
            print ']'
            print FoldedRegularHeptagonsA4xI(tmp,
                    {
                        Param.tri_fill: TriangleAlt.star1loose,
                        Param.edge_len: [0., 0., 0., 0.],
                        Param.h_fold:   Fold.parallel
                    }
                )

        elif symGrp == Symmetry.S4A4:
            T  = 0.72
            a  = Geom3D.Deg2Rad * 180
            b0 = Geom3D.Deg2Rad * 101
            g0 = Geom3D.Deg2Rad * -53
            tmp = numx.array((T, a, b0, g0))
            #tmp = numx.array((3., 0., 0.0, 0.0))
            tmp = numx.array((0.01259577502021, 3.14159265358979, 1.76486301105478, -0.94170721928212, 0.78539816339745))
            tmp = numx.array((0.01259577502021, 1.57, 0.0, 0.1, 0.78539816339745))
            tmp = numx.array((0.01259577502021, 1.57, 0.2, 0.0, 0.78539816339745))
            print 'input values: \n [',
            for t in tmp: print t, ',',
            print ']'
            print FoldedRegularHeptagonsA4xI(tmp,
                    {
                        Param.tri_fill: TriangleAlt.twisted,
                        Param.edge_len: [0., 0., 0., 0.],
                        Param.h_fold:   Fold.parallel
                    }
                )

        elif symGrp == Symmetry.A4:
            T  = 2.3
            a  = Geom3D.Deg2Rad * 30
            b0 = Geom3D.Deg2Rad * 60
            g0 = Geom3D.Deg2Rad * 50
            d  = Geom3D.Deg2Rad * 40
            b1 = Geom3D.Deg2Rad * 50
            g1 = Geom3D.Deg2Rad * 100
            tmp = numx.array((T, a, b0, g0, d, b1, g1))
            tmp = [2.42367662112328, 0.73523867591239, -0.95915637221717, -1.30440374966920, 0.00000000000000, -0.95915637221717, g1]
            print 'input values: \n [',
            for t in tmp: print t, ',',
            print ']'
            print FoldedRegularHeptagonsA4(tmp,
                    {
                        Param.tri_fill: TriangleAlt.star1loose,
                        Param.opp_fill: TriangleAlt.strip1loose,
                        Param.edge_len: [0., 0., 0., 0., 0., 0., 0.],
                        Param.h_fold:   Fold.w
                    }
                )

        elif symGrp == Symmetry.S4xI:
            #T  = 3.
            #a  = Geom3D.Deg2Rad * 30
            #b0 = Geom3D.Deg2Rad * 60
            #g0 = Geom3D.Deg2Rad * 50
            #d  = Geom3D.Deg2Rad * 40
            #b1 = Geom3D.Deg2Rad * 50
            #g1 = Geom3D.Deg2Rad * 100
            #tmp = numx.array((T, a, b0, g0, d, b1, g1))
            tmp = numx.array((3., 0., 0., 0.))
            print 'input values: \n [',
            for t in tmp: print t, ',',
            print ']'
            print FoldedRegularHeptagonsS4(tmp,
                {
                    Param.tri_fill: TriangleAlt.refl_2,
                    Param.edge_len: [0., 0., 0., 0.],
                    Param.h_fold:   Fold.trapezium,
                }
            )

        elif symGrp == Symmetry.S4:
            T  = 3.9
            a  = 1.2#Geom3D.Deg2Rad * 68
            b0 = 0.5236#Geom3D.Deg2Rad * 60
            g0 = 0.5236#Geom3D.Deg2Rad * 50
            d  = 0.5236#Geom3D.Deg2Rad * 40
            b1 = 0.5236#Geom3D.Deg2Rad * 50
            g1 = 0.5236#Geom3D.Deg2Rad * 100
            tmp = numx.array((T, a, b0, g0, d, b1, g1))
            print 'input values: \n [',
            for t in tmp: print t, ',',
            print ']'
            print FoldedRegularHeptagonsS4(tmp,
                {
                    Param.tri_fill: TriangleAlt.stripI,
                    Param.opp_fill: TriangleAlt.stripI,
                    Param.edge_len: [0., 0., 0., 0., 0., 0., 0.],
                    Param.h_fold:   Fold.star,
                }
            )

        elif symGrp == Symmetry.A5xI:
            T  = 8.38
            a  = Geom3D.Deg2Rad * 60
            b0 = Geom3D.Deg2Rad * 10
            g0 = Geom3D.Deg2Rad * 20
            tmp = numx.array((T, a, b0, g0))
            print 'input values: \n [',
            for t in tmp: print t, ',',
            print ']'
            print FoldedRegularHeptagonsA5(tmp,
                {
                    Param.tri_fill: TriangleAlt.refl_2,
                    Param.edge_len: [0., 0., 0., 0.],
                    Param.h_fold:   Fold.triangle,
                }
            )

        elif symGrp == Symmetry.A5:
            T  = 5.1 #8.38
            a  = 119 * Geom3D.Deg2Rad# * 60
            b0 = 0*Geom3D.Deg2Rad * 36
            g0 = 0*Geom3D.Deg2Rad * 72
            d  = Geom3D.Deg2Rad * 72
            b1 = 0*Geom3D.Deg2Rad * 36
            g1 = 0*Geom3D.Deg2Rad * -36
            tmp = numx.array((T, a, b0, g0, d, b1, g1))
            print 'input values: \n [',
            for t in tmp: print t, ',',
            print ']'
            print FoldedRegularHeptagonsA5(tmp,
                {
                    Param.tri_fill: TriangleAlt.stripI,
                    Param.opp_fill: TriangleAlt.star,
                    Param.edge_len: [0., 0., 0., 0., 0., 0., 0.],
                    Param.h_fold:   Fold.star,
                    Param.t_fill_pos: 1
                }
            )

        else:
            printError('Error: Unkown symmetry group: %s' % symGrp)

    def tstDynamicSolutions():
        passed = True
        symGrp = Symmetry.A4,
        tst = RandFindMultiRootOnDomain(
            [
                    T_Dom[symGrp],         # Translation
                    [-numx.pi, numx.pi],   # angle alpha
                    [-numx.pi, numx.pi],   # fold 1 beta0
                    [-numx.pi, numx.pi],   # fold 2 gamma0
                    D_Dom[symGrp],         # delta: around z-axis
                    [-numx.pi, numx.pi],   # fold 1 beta1
                    [-numx.pi, numx.pi],   # fold 2 gamma1
                ],
            symGrp,
            edgeAlternative    = TriangleAlt.star1loose,
            oppEdgeAlternative = TriangleAlt.star1loose,
            fold               = Fold.w,
            edgeLengths        = [0, 1, 0, 1, 1, 0, 1],
            dynSols            = dynamicSols,
        )
        chkDynSols = [
            [2.59691495774690, 0.37180029203870, -0.99159844699067, 0.0, 0.0, -0.99159844699067, 1.90],
            [-2.39662854867090, -2.76044142453588, -2.28962724865982, 0.0, 0.0, -2.28962724865982, 4.30],
            [-1.32969344523106, 2.93729908156380, 0.47840318769040, 0.3, 0.0, 0.47840318769040, -1.24666979460112],
            [1.56791889743089, 0.07044231686021, -3.01397582234294, 0.3, 0.0, -3.01397582234294, -0.617],
            [-1.48353635258086, 3.14159265358979, -2.17789038635323, 0.3, 2.00286242147445, 2.17789038635323, -0.3],
            [1.48353635258086, 0.0, -2.17789038635323, 6.0, 1.13873023211535, 2.17789038635323, -6.0],
            [-1.48353635258086, 3.14159265358979, 2.17789038635323, 0.0, -2.00286242147445, -2.17789038635323, -0.0],
            [1.48353635258086, 0.0, 2.17789038635323, 0.3, -1.13873023211535, -2.17789038635323, -0.3],
            [-1.79862645974663, 2.89384136702916, 2.66115365118573, 0.0, 2.22084886403160, 2.66115365118573, 1.16715894682047],
            [1.79862645974663, 0.24775128656063, -2.66115365118573, 0.3, 0.92074378955819, -2.66115365118573, -1.46715894682047],
            [-1.79862645974663, 2.89384136702916, 2.66115365118573, 0.3, -2.22084886403160, 2.66115365118573, 0.86715894682047],
            [1.79862645974663, 0.24775128656063, -2.66115365118573, 0.0, -0.92074378955819, -2.66115365118573, -1.16715894682047],
            [-1.93838678986755, -2.82756860983026, -0.78734965896067, 0.0, 1.35463810886690, -0.78734965896067, +1.53424315674435],
            [1.93838678986755, -0.31402404375953, 0.78734965896067, 0.3, 1.78695454472289, 0.78734965896067, -1.83424315674435],
            [-1.93838678986755, -2.82756860983026, -0.78734965896067, 0.0, -1.35463810886690, -0.78734965896067, +1.53424315674435],
            [1.93838678986755, -0.31402404375953, 0.78734965896067, 0.0, -1.78695454472289, 0.78734965896067, -1.53424315674435],
        ]
        for ds in chkDynSols:
            if not tst.isDynamicSol(ds):
                print 'oops', ds, 'should be a dynamic solution'
                passed = False
        chkDynSols = [
            [1.73117867469463, 0.46014030244326, -1.75383477143902, 3,4, -1.75383477143902, 6],
            [1.73117867469463, -0.46014030244326, 1.75383477143902, 3,4, 1.75383477143902, 6],
            [-1.73117867469463, -2.68145235114654, -1.75383477143902, 3,4, -1.75383477143902, 6],
            [-1.73117867469463, 2.68145235114654, 1.75383477143902, 3,4, 1.75383477143902, 6],
        ]
        tst.edgeLengths = [0, V2, 1, 0, V2, 1, 0]
        for ds in chkDynSols:
            if not tst.isDynamicSol(ds):
                print 'oops', ds, 'should be a dynamic solution'
                passed = False
        tst.edgeLengths = [0, 1, 1, 0, 1, 1, 0]
        for ds in chkDynSols:
            if not tst.isDynamicSol(ds):
                print 'oops', ds, 'should be a dynamic solution'
                passed = False
        chkDynSols = [
            [1.48353635258086, 0, 2, 3, 4, 5, 6],
            [-1.48353635258086, 3.14159265358979, 2, 3, 4, 5, 6],
            [1.48353635258086, 0.0, 2.177, 0.3, -1.1387, -2.17789, -0.3],
        ]
        tst.edgeLengths = [0, 1, 0, 1, 1, 0, 1]
        tst.fold = Fold.star
        for ds in chkDynSols:
            if not tst.isDynamicSol(ds):
                print 'oops', ds, 'should be a dynamic solution'
                passed = False
        tst.fold = Fold.w
        chkNoDynSols = [
            [1.48353635258086, 0.0, 2.177, 0.3, -1.1387, -2.17789, -0.3],
            [-2.59691495774690, 0.37180029203870, -0.99159844699067, 0.0, 0.0, -0.99159844699067, 1.90],
            [-1.73117867469463, 0.46014030244326, -1.75383477143902, 3,4, -1.75383477143902, 6],
            [-1.73117867469463, -0.46014030244326, 1.75383477143902, 3,4, 1.75383477143902, 6],
            [-1.73117867469463, 2.68145235114654, -1.75383477143902, 3,4, -1.75383477143902, 6],
            [-1.73117867469463, 2.68145235114654, 1.75383477143902, 3,4, -1.75383477143902, 6],
        ]
        for edgeL in [[0, V2, 1, 0, V2, 1, 0], [0, 1, 1, 0, 1, 1, 0]]:
            tst.edgeLengths = edgeL
            for ds in chkNoDynSols:
                if tst.isDynamicSol(ds):
                    print 'oops', ds, "shouldn't be a dynamic solution"
                    passed = False
        return passed

    def setup_ok_Y(symGrp, edgeLs, edgeAlts, folds, oppEdgeAlts = None):
        dom = [
            T_Dom[symGrp],         # Translation
            [-numx.pi, numx.pi],   # angle alpha
            [-numx.pi, numx.pi],   # fold 1 beta0
            [-numx.pi, numx.pi],   # fold 2 gamma0
            D_Dom[symGrp],         # delta: around z-axis
            [-numx.pi, numx.pi],   # fold 1 beta1
            [-numx.pi, numx.pi],   # fold 2 gamma1
        ]
        if edgeLs == [] or folds == [] or edgeAlts ==[] or oppEdgeAlts == []:
            print 'Warning: empty search specified!'
            return None
        else:
            return dom

    def tst_if_solutions_exist_Y(symGrp, edgeLs, edgeAlts, folds,
                    continueAfter = 100, precision = 14, oppEdgeAlts = None,
                    triangle_fill_pos = 0):
        if oppEdgeAlts == None:
            oppEdgeAlts = edgeAlts[:]
        dom = setup_ok_Y(symGrp, edgeLs, edgeAlts, folds, oppEdgeAlts)
        if dom == None:
            return []
        trd = None
        has_solutions = []
        for edges in edgeLs:
            print 'investigating', edges
            edgeLs_has_solutions = False
            for fold in folds:
                print '  fold', str(Fold(fold))
                for ea in edgeAlts:
                    for oea in oppEdgeAlts:
                        print '    edge alt', Stringify[ea], Stringify[oea]
                        # loose_bit must be the same for both:
                        if (
                            ea & loose_bit == loose_bit and
                            oea & loose_bit == loose_bit
                        ) or (
                            ea & loose_bit == 0 and
                            oea & loose_bit == 0
                        ):
                            trd = RandFindMultiRootOnDomain(dom,
                                symGrp,
                                edgeAlternative    = ea,
                                oppEdgeAlternative = oea,
                                edgeLengths        = edges,
                                fold               = fold,
                                precision          = precision,
                                method             = Method.hybrids,
                                triangle_fill_pos  = triangle_fill_pos
                            )
                            trd.stopAfter = continueAfter
                            # we aren't using threads for this.
                            trd.tst_solutions_exist()
                            edgeLs_has_solutions = trd.solutions_exist
                            if edgeLs_has_solutions: break
                        if edgeLs_has_solutions: break
                    if edgeLs_has_solutions: break
                if edgeLs_has_solutions: break
            if edgeLs_has_solutions:
                has_solutions.append(edges)
        return has_solutions

    def randBatchY(symGrp, edgeLs, edgeAlts, folds, continueAfter = 100,
                nrThreads = 1, dynSols = None, precision = 14, outDir = "./",
                loop = True, oppEdgeAlts = None, triangle_fill_pos = 0):
        if oppEdgeAlts == None:
            oppEdgeAlts = edgeAlts[:]
        dom = setup_ok_Y(symGrp, edgeLs, edgeAlts, folds, oppEdgeAlts)
        if dom == None:
            return []
        rndT = [None for j in range(nrThreads)]
        i = 0
        while True:
            for edges in edgeLs:
                for fold in folds:
                    for ea in edgeAlts:
                        for oea in oppEdgeAlts:
                            # loose_bit must be the same for both:
                            if (
                                ea & loose_bit == loose_bit and
                                oea & loose_bit == loose_bit
                            ) or (
                                ea & loose_bit == 0 and
                                oea & loose_bit == 0
                            ):
                                print '====set up thread %d===' % i
                                exceptionQueue = Queue.Queue()
                                rndT[i] = RandFindMultiRootOnDomain(dom,
                                    symGrp,
                                    threadId           = i,
                                    edgeAlternative    = ea,
                                    oppEdgeAlternative = oea,
                                    edgeLengths        = edges,
                                    dynSols            = dynSols,
                                    fold               = fold,
                                    precision          = precision,
                                    method             = Method.hybrids,
                                    outDir             = outDir,
                                    exceptQueue        = exceptionQueue,
                                    triangle_fill_pos  = triangle_fill_pos
                                )
                                rndT[i].stopAfter = continueAfter
                                rndT[i].start()
                                i = i + 1
                                if (i == nrThreads):
                                    for j in range(nrThreads):
                                        rndT[j].join()
                                    print '===threads finished===='
                                    i = 0
                                assert (exceptionQueue.empty()),\
                                    "An exception occurred in a child thread"
                                del exceptionQueue
            if not loop:
                break

    pre_edgeLs_all_1s_opposite_syms = [
        [
            (i/2**3)%2,
            (i/2**2)%2,
            (i/2)%2,
            i%2
        ] for i in range(2**4)
    ]

    pre_edgeLs_all_1s_direct_syms = [
        [
            (i/2**6)%2,
            (i/2**5)%2,
            (i/2**4)%2,
            (i/2**3)%2,
            (i/2**2)%2,
            (i/2)%2,
            i%2
        ] for i in range(2**7)
    ]

    pre_edgeLs_A4 = [
        #[0., 0., 0., 0., 0., 0., 0.],

        #[0., 0., 0., 1., 0., 0., 1.],

        [0., 0., 1., 0., 0., 1., 0.],

        [0., 0., 1., 1., 0., 1., 1.],

        #[0., 1., 0., 0., 1., 0., 0.],

        [0., 1., 0., 1., 0., 1., 0.], # no sols. Check again..
        [0., 1., 0., 1., 1., 0., 1.],

        [0., 1., 1., 0., 1., 1., 0.],

        #[1., 0., 0., 0., 0., 0., 0.],

        [1., 0., 0., 1., 0., 0., 1.],

        [1., 0., 1., 0., 0., 1., 0.], # only hepts
                # it seems that
                # frh-roots-1_0_1_0_0_1_0-fld_w.0-shell-opp_shell.py
                # needs to find nr 11 (has 10 now)
        [1., 0., 1., 0., 0., 1., 0.],
        [1., 0., 1., 0., 0., 1., 1.], # 16 triangles (0)
        [1., 0., 1., 0., 1., 0., 0.], # no sols
        [1., 0., 1., 0., 1., 0., 1.], # 16 triangles (1)
        [1., 0., 1., 0., 1., 1., 0.], # 24 triangles (0)
        [1., 0., 1., 0., 1., 1., 1.], # 40 triangles (0)

        [1., 0., 1., 1., 0., 1., 0.], # 16 triangles (3)
        [1., 0., 1., 1., 0., 1., 1.], # 32 triangles (1)
        [1., 0., 1., 1., 1., 1., 0.], # 40 triangles (2)

        [1., 1., 0., 0., 1., 0., 0.],

        [1., 1., 0., 1., 0., 0., 0.], # for rot 0
        [1., 1., 0., 1., 0., 0., 1.], # for rot 0
        [1., 1., 0., 1., 0., 1., 0.], # 16 triangles (1)
        [1., 1., 0., 1., 0., 1., 1.], # 32 triangles (0)

        [1., 1., 1., 0., 0., 1., 0.], # 24 triangles (1)
        [1., 1., 1., 0., 0., 1., 1.], # 40 triangles (3)
        [1., 1., 1., 0., 1., 0., 0.], # no sols
        [1., 1., 1., 0., 1., 1., 0.], # no O3's: 48 triangles

        [1., 1., 1., 1., 0., 1., 0.], # 40 triangles (1)
        [1., 1., 1., 1., 1., 1., 0.], # 64 triangles (0)
        [1., 1., 1., 1., 1., 1., 1.], # all equilateral

        [0., V2, 1., 0., V2, 1., 0.], # 12 folded squares
        [1., V2, 1., 0., V2, 1., 0.], # 24 folded squares
    ]

    dynamicSol_A4_S4 = {
        'edgeAlternative': [TriangleAlt.alt_strip1loose],
        'oppEdgeAlternative': [TriangleAlt.alt_strip1loose],
        'fold': [Fold.w],
        'sol_vector': [[0, V2, 1, 0, V2, 1, 0]],
        'set_vector': [
                {
                    0: -0.86602540378444,
                    1: -2.77997947392212,
                    2: -1.28052911995042,
                    3: -2.06457033281442,
                    5: -1.28052911995042,
                    6: -2.06457033281442
                },{
                    0: -0.86602540378444,
                    1: -2.77997947392212,
                    2: -1.28052911995042,
                    3: -2.06457033281442,
                    5:  2.84861154567842,
                    6:  2.06457033281442
                },{
                    0: -0.86602540378444,
                    1: -2.77997947392212,
                    2:  2.84861154567842,
                    3:  2.06457033281442,
                    5: -1.28052911995042,
                    6: -2.06457033281442
                },{
                    0: -0.86602540378444,
                    1: -2.77997947392212,
                    2:  2.84861154567842,
                    3:  2.06457033281442,
                    5:  2.84861154567842,
                    6:  2.06457033281442
                },{
                    0: -0.86602540378444,
                    1: -2.77997947392212,
                    2:  2.84861154567842,
                    3:  2.06457033281442,
                    5:  2.84861154567842,
                    6:  2.06457033281442
                },{
                    0: -0.86602540378444,
                    1:  2.77997947392212,
                    2: -2.84861154567842,
                    3: -2.06457033281442,
                    5: -2.84861154567842,
                    6: -2.06457033281442
                },{
                    0: -0.86602540378444,
                    1:  2.77997947392212,
                    2: -2.84861154567842,
                    3: -2.06457033281442,
                    5:  1.28052911995042,
                    6:  2.06457033281442
                },{
                    0: -0.86602540378444,
                    1:  2.77997947392212,
                    2:  1.28052911995042,
                    3:  2.06457033281442,
                    5: -2.84861154567842,
                    6: -2.06457033281442
                },{
                    0: -0.86602540378444,
                    1:  2.77997947392212,
                    2:  1.28052911995042,
                    3:  2.06457033281442,
                    5:  1.28052911995042,
                    6:  2.06457033281442
                },{
                    0:  0.86602540378444,
                    1: -0.36161317966767,
                    2: -2.84861154567842,
                    3: -2.06457033281442,
                    5: -2.84861154567842,
                    6: -2.06457033281442
                },{
                    0:  0.86602540378444,
                    1: -0.36161317966767,
                    2: -2.84861154567842,
                    3: -2.06457033281442,
                    5:  1.28052911995042,
                    6:  2.06457033281442
                },{
                    0:  0.86602540378444,
                    1: -0.36161317966767,
                    2:  1.28052911995042,
                    3:  2.06457033281442,
                    5: -2.84861154567842,
                    6: -2.06457033281442
                },{
                    0:  0.86602540378444,
                    1: -0.36161317966767,
                    2:  1.28052911995042,
                    3:  2.06457033281442,
                    5:  1.28052911995042,
                    6:  2.06457033281442
                },{
                    0:  0.86602540378444,
                    1:  0.36161317966767,
                    2: -1.28052911995042,
                    3: -2.06457033281442,
                    5: -1.28052911995042,
                    6: -2.06457033281442
                },{
                    0:  0.86602540378444,
                    1:  0.36161317966767,
                    2: -1.28052911995042,
                    3: -2.06457033281442,
                    5:  2.84861154567842,
                    6:  2.06457033281442
                },{
                    0:  0.86602540378444,
                    1:  0.36161317966767,
                    2:  2.84861154567842,
                    3:  2.06457033281442,
                    5: -1.28052911995042,
                    6: -2.06457033281442
                },{
                    0:  0.86602540378444,
                    1:  0.36161317966767,
                    2:  2.84861154567842,
                    3:  2.06457033281442,
                    5:  2.84861154567842,
                    6:  2.06457033281442
                }
            ]
    }
    dynamicSols_A4 = [
        # TODO: important add edge lengths!!!
        {
            # here is an example of where it is important to define the
            # sol_vector. Since it can be that solutions with different edge
            # lengths have non-dynamic solutions for which the translation
            # and the dihedral angle have the values below.
            'edgeAlternative': [TriangleAlt.star1loose],
            'oppEdgeAlternative': [TriangleAlt.star1loose],
            'fold': [Fold.star],
            'sol_vector': [[0, 1, 0, 1, 1, 0, 1]],
            'set_vector': [
                    {
                        0: 1.48353635258086,
                        1: 0.0,
                    },{
                        0: -1.48353635258086,
                        1: 3.14159265358979,
                    }
                ]
        },{
            'edgeAlternative': [TriangleAlt.star1loose],
            'oppEdgeAlternative': [TriangleAlt.star1loose],
            'fold': [Fold.w],
            'sol_vector': [[0, 1, 0, 1, 1, 0, 1]],
            'set_vector': [
                {
                    0: 2.59691495774690,
                    1: 0.37180029203870,
                    2: -0.99159844699067,
                    4: 0.0,
                    5: -0.99159844699067,
                },{
                    0: -2.39662854867090,
                    1: -2.76044142453588,
                    2: -2.28962724865982,
                    4: 0.0,
                    5: -2.28962724865982,
                },{
                    0: -1.32969344523106,
                    1: 2.93729908156380,
                    2: 0.47840318769040,
                    4: 0.0,
                    5: 0.47840318769040,
                },{
                    0: 1.56791889743089,
                    1: 0.07044231686021,
                    2: -3.01397582234294,
                    4: 0.0,
                    5: -3.01397582234294,
                },{
                    0: -1.48353635258086,
                    1: 3.14159265358979,
                    2: -2.17789038635323,
                    4: 2.00286242147445,
                    5: 2.17789038635323,
                },{
                    0: 1.48353635258086,
                    1: 0.0,
                    2: -2.17789038635323,
                    4: 1.13873023211535,
                    5: 2.17789038635323,
                },{
                    0: -1.48353635258086,
                    1: 3.14159265358979,
                    2: 2.17789038635323,
                    4: -2.00286242147445,
                    5: -2.17789038635323,
                },{
                    0: 1.48353635258086,
                    1: 0.0,
                    2: 2.17789038635323,
                    4: -1.13873023211535,
                    5: -2.17789038635323,
                },{
                    0: -1.79862645974663,
                    1: 2.89384136702916,
                    2: 2.66115365118573,
                    4: 2.22084886403160,
                    5: 2.66115365118573,
                },{
                    0: 1.79862645974663,
                    1: 0.24775128656063,
                    2: -2.66115365118573,
                    4: 0.92074378955819,
                    5: -2.66115365118573,
                },{
                    0: -1.79862645974663,
                    1: 2.89384136702916,
                    2: 2.66115365118573,
                    4: -2.22084886403160,
                    5: 2.66115365118573,
                },{
                    0: 1.79862645974663,
                    1: 0.24775128656063,
                    2: -2.66115365118573,
                    4: -0.92074378955819,
                    5: -2.66115365118573,
                },{
                    0: -1.93838678986755,
                    1: -2.82756860983026,
                    2: -0.78734965896067,
                    4: 1.35463810886690,
                    5: -0.78734965896067,
                },{
                    0: 1.93838678986755,
                    1: -0.31402404375953,
                    2: 0.78734965896067,
                    4: 1.78695454472289,
                    5: 0.78734965896067,
                },{
                    0: -1.93838678986755,
                    1: -2.82756860983026,
                    2: -0.78734965896067,
                    4: -1.35463810886690,
                    5: -0.78734965896067,
                },{
                    0: 1.93838678986755,
                    1: -0.31402404375953,
                    2: 0.78734965896067,
                    4: -1.78695454472289,
                    5: 0.78734965896067,
                }
            ]
        },{
            'edgeAlternative': [
                TriangleAlt.star1loose, TriangleAlt.strip1loose],
            'oppEdgeAlternative': [
                TriangleAlt.star1loose, TriangleAlt.strip1loose],
            'fold': [Fold.w],
            'sol_vector': [
                    [0, 1, 1, 0, 1, 1, 0],
                    [0, V2, 1, 0, V2, 1, 0]
            ],
            'set_vector': [
                {
                    0: 1.73117867469463,
                    1: 0.46014030244326,
                    2: -1.75383477143902,
                    5: -1.75383477143902,
                },{
                    0: 1.73117867469463,
                    1: -0.46014030244326,
                    2: 1.75383477143902,
                    5: 1.75383477143902,
                },{
                    0: -1.73117867469463,
                    1: -2.68145235114654,
                    2: -1.75383477143902,
                    5: -1.75383477143902,
                },{
                    0: -1.73117867469463,
                    1: 2.68145235114654,
                    2: 1.75383477143902,
                    5: 1.75383477143902,
                }
            ]
        },
        dynamicSol_A4_S4
    ]
    dynamicSols_S4 = [
        {
            'edgeAlternative': [TriangleAlt.star1loose],
            'oppEdgeAlternative': [TriangleAlt.star1loose],
            'fold': [Fold.star],
            'sol_vector': [[0, 1, 0, 1, 1, 0, 1]],
            'set_vector': [
                    {
                        0: -1.190643133767,
                        1: 3.14159265359,
                    },{
                        0:  1.190643133767,
                        1: 0,
                    }
                ]
        },{
            'edgeAlternative': [TriangleAlt.star1loose],
            'oppEdgeAlternative': [TriangleAlt.star1loose],
            'fold': [Fold.w],
            'sol_vector': [[0, 1, 0, 1, 1, 0, 1]],
            'set_vector': [
                    {
                        0: -3.0466368148482,
                        1:  2.742948685126,
                        2:  1.1074899130379,
                        4: -2.3083673222932,
                        5:  1.1074899130379
                    },{
                        0: -2.8062737859459,
                        1: -2.7220636635727,
                        2: -2.1241516186627,
                        4:  0.8788481404661,
                        5: -2.1241516186627
                    },{
                        0: -2.1442205879459,
                        1: -2.8059606274723,
                        2: -0.8585846483971,
                        4:  2.0077652698193,
                        5: -0.858584648397
                    },{
                        0: -2.0821021848193,
                        1:  2.8110775119117,
                        2:  2.4527359602419,
                        4: -1.7049178642452,
                        5:  2.4527359602419
                    },{
                        0: -1.7309112237548,
                        1: -2.8546984508612,
                        2: -0.7040677186794,
                        4: -0.3756575042836,
                        5: -0.7040677186794
                    },{
                        0: -1.1906431337674,
                        1:  math.pi,
                        2: -0.9020989680997,
                        4:  1.4026364217199,
                        5:  0.9020989680997
                    },{
                        0: -1.1906431337674,
                        1:  math.pi,
                        2:  0.9020989680997,
                        4: -0.1716770043791,
                        5: -0.9020989680997
                    },{
                        0: -1.0698370978116,
                        1:  3.0691108767628,
                        2:  0.1636646541258,
                        4:  0.6662657794866,
                        5:  0.1636646541258
                    },{
                        0:  1.0698370978116,
                        1:  0.0724817768269,
                        2: -0.1636646541258,
                        4: -2.4753268741032,
                        5: -0.1636646541258
                    },{
                        0:  1.1906431337674,
                        1:  0.,
                        2: -0.9020989680997,
                        4:  2.9699156492107,
                        5:  0.9020989680997
                    },{
                        0:  1.1906431337674,
                        1:  0.,
                        2:  0.9020989680997,
                        4: -1.7389562318699,
                        5: -0.9020989680997
                    },{
                        0:  1.7309112237548,
                        1: -0.2868942027286,
                        2:  0.7040677186794,
                        4:  2.7659351493062,
                        5:  0.7040677186794
                    },{
                        0:  2.0821021848193,
                        1:  0.3305151416781,
                        2: -2.4527359602419,
                        4:  1.4366747893446,
                        5: -2.4527359602419
                    },{
                        0:  2.1442205879459,
                        1: -0.3356320261175,
                        2:  0.858584648397,
                        4: -1.1338273837704,
                        5:  0.858584648397
                    },{
                        0:  2.8062737859459,
                        1: -0.4195289900171,
                        2:  2.1241516186627,
                        4: -2.2627445131237,
                        5:  2.1241516186627
                    },{
                        0:  3.0466368148482,
                        1:  0.3986439684638,
                        2: -1.1074899130379,
                        4:  0.8332253312966,
                        5: -1.1074899130379
                    }
                ]
        },{
            'edgeAlternative': [TriangleAlt.star1loose],
            'oppEdgeAlternative': [TriangleAlt.strip1loose],
            'fold': [Fold.w],
            'sol_vector': [[0, 1, 1, 0, 1, 1, 0]],
            'set_vector': [
                    {
                        0: -1.7311786746946,
                        1: -2.6814523511465,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0: -1.7311786746946,
                        1:  2.6814523511465,
                        2:  1.753834771439,
                        5:  1.753834771439
                    },{
                        0:  1.7311786746946,
                        1:  0.4601403024433,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0:  1.7311786746946,
                        1: -0.4601403024433,
                        2:  1.753834771439,
                        5:  1.753834771439
                    }
                ]
        },{
            'edgeAlternative': [TriangleAlt.strip1loose],
            'oppEdgeAlternative': [TriangleAlt.star1loose],
            'fold': [Fold.w],
            'sol_vector': [[0, 1, 1, 0, 1, 1, 0]],
            'set_vector': [
                    {
                        0: -1.7311786746946,
                        1: -2.6814523511465,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0: -1.7311786746946,
                        1:  2.6814523511465,
                        2:  1.753834771439,
                        5:  1.753834771439
                    },{
                        0:  1.7311786746946,
                        1:  0.4601403024433,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0:  1.7311786746946,
                        1: -0.4601403024433,
                        2:  1.753834771439,
                        5:  1.753834771439
                    }
                ]
        },{
            'edgeAlternative': [TriangleAlt.strip1loose],
            'oppEdgeAlternative': [TriangleAlt.strip1loose],
            'fold': [Fold.w],
            'sol_vector': [[0, 1, 1, 0, 1, 1, 0]],
            'set_vector': [
                    {
                        0: -1.7311786746946,
                        1: -2.6814523511465,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0: -1.7311786746946,
                        1:  2.6814523511465,
                        2:  1.753834771439,
                        5:  1.753834771439
                    },{
                        0:  1.7311786746946,
                        1:  0.4601403024433,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0:  1.7311786746946,
                        1: -0.4601403024433,
                        2:  1.753834771439,
                        5:  1.753834771439
                    }
                ]
        },{
            'edgeAlternative': [TriangleAlt.star1loose],
            'oppEdgeAlternative': [TriangleAlt.star1loose],
            'fold': [Fold.w],
            'sol_vector': [[0, 1, 1, 0, 1, 1, 0]],
            'set_vector': [
                    {
                        0: -1.7311786746946,
                        1: -2.6814523511465,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0: -1.7311786746946,
                        1:  2.6814523511465,
                        2:  1.753834771439,
                        5:  1.753834771439
                    },{
                        0:  1.7311786746946,
                        1:  0.4601403024433,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0:  1.7311786746946,
                        1: -0.4601403024433,
                        2:  1.753834771439,
                        5:  1.753834771439
                    }
                ]
        },{
            'edgeAlternative': [TriangleAlt.star1loose],
            'oppEdgeAlternative': [TriangleAlt.star1loose],
            'fold': [Fold.w],
            'sol_vector': [[0, V2, 1, 0, V2, 1, 0]],
            'set_vector': [
                    {
                        0: -1.7311786746946,
                        1: -2.6814523511465,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0: -1.7311786746946,
                        1:  2.6814523511465,
                        2:  1.753834771439,
                        5:  1.753834771439
                    },{
                        0:  1.7311786746946,
                        1:  0.4601403024433,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0:  1.7311786746946,
                        1: -0.4601403024433,
                        2:  1.753834771439,
                        5:  1.753834771439
                    }
                ]
        },{
            'edgeAlternative': [TriangleAlt.strip1loose],
            'oppEdgeAlternative': [TriangleAlt.star1loose],
            'fold': [Fold.w],
            'sol_vector': [[0, V2, 1, 0, V2, 1, 0]],
            'set_vector': [
                    {
                        0: -1.7311786746946,
                        1: -2.6814523511465,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0: -1.7311786746946,
                        1:  2.6814523511465,
                        2:  1.753834771439,
                        5:  1.753834771439
                    },{
                        0:  1.7311786746946,
                        1:  0.4601403024433,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0:  1.7311786746946,
                        1: -0.4601403024433,
                        2:  1.753834771439,
                        5:  1.753834771439
                    }
                ]
        },{
            'edgeAlternative': [TriangleAlt.strip1loose],
            'oppEdgeAlternative': [TriangleAlt.strip1loose],
            'fold': [Fold.w],
            'sol_vector': [[0, V2, 1, 0, V2, 1, 0]],
            'set_vector': [
                    {
                        0: -1.7311786746946,
                        1: -2.6814523511465,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0: -1.7311786746946,
                        1:  2.6814523511465,
                        2:  1.753834771439,
                        5:  1.753834771439
                    },{
                        0:  1.7311786746946,
                        1:  0.4601403024433,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0:  1.7311786746946,
                        1: -0.4601403024433,
                        2:  1.753834771439,
                        5:  1.753834771439
                    }
                ]
        },{
            'edgeAlternative': [TriangleAlt.star1loose],
            'oppEdgeAlternative': [TriangleAlt.strip1loose],
            'fold': [Fold.w],
            'sol_vector': [[0, V2, 1, 0, V2, 1, 0]],
            'set_vector': [
                    {
                        0: -1.7311786746946,
                        1: -2.6814523511465,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0: -1.7311786746946,
                        1:  2.6814523511465,
                        2:  1.753834771439,
                        5:  1.753834771439
                    },{
                        0:  1.7311786746946,
                        1:  0.4601403024433,
                        2: -1.753834771439,
                        5: -1.753834771439
                    },{
                        0:  1.7311786746946,
                        1: -0.4601403024433,
                        2:  1.753834771439,
                        5:  1.753834771439
                    }
                ]

        },
        dynamicSol_A4_S4
    ]

    edgeAltOpts = {}
    edgeAltOpts[Symmetry.A4] = [
        [ # position 0
            [ # normal edge alternative
                TriangleAlt.stripI,
                TriangleAlt.strip1loose,
                TriangleAlt.alt_stripI,
                TriangleAlt.alt_strip1loose,
                TriangleAlt.stripII,
                TriangleAlt.alt_stripII,
                TriangleAlt.star,
                TriangleAlt.star1loose,
            ]
        ]
    ]
    # the same for the opposite edge alts
    edgeAltOpts[Symmetry.A4][0].append(edgeAltOpts[Symmetry.A4][0][0])
    edgeAltOpts[Symmetry.A4xI] = [
        [ # position 0
            [ # normal edge alternative
                    TriangleAlt.stripI,
                    TriangleAlt.strip1loose,
                    TriangleAlt.alt_stripI,
                    TriangleAlt.alt_strip1loose,
                    TriangleAlt.stripII,
                    TriangleAlt.alt_stripII,
                    TriangleAlt.star,
                    TriangleAlt.star1loose,
                    #TriangleAlt.rot_strip1loose,
                    #TriangleAlt.arot_strip1loose,
                    #TriangleAlt.rot_star1loose,
                    #TriangleAlt.arot_star1loose,
            ]
        ]
    ]
    # the same for the opposite edge alts
    edgeAltOpts[Symmetry.A4xI][0].append(edgeAltOpts[Symmetry.A4xI][0][0])
    edgeAltOpts[Symmetry.S4A4] = [
        [ # position 0
            [ # normal edge alternative
                    TriangleAlt.twisted,
            ]
        ]
    ]
    # the same for the opposite edge alts
    edgeAltOpts[Symmetry.S4A4][0].append(edgeAltOpts[Symmetry.S4A4][0][0])
    edgeAltOpts[Symmetry.S4xI] = [
        [ # position 0
            [ # normal edge alternative
                    TriangleAlt.refl_1,
                    TriangleAlt.refl_2,
            ]
        ]
    ]
    # the same for the opposite edge alts
    edgeAltOpts[Symmetry.S4xI][0].append(edgeAltOpts[Symmetry.S4xI][0][0])
    edgeAltOpts[Symmetry.S4] = [
        [ # position 0
            [ # normal edge alternative
                    # TODO: add refl? Might lead to folded squares? Investigate.
                    #TriangleAlt.refl_1,
                    #TriangleAlt.refl_2,
                    TriangleAlt.stripI,
                    TriangleAlt.strip1loose,
                    TriangleAlt.alt_stripI,
                    TriangleAlt.alt_strip1loose,
                    TriangleAlt.stripII,
                    TriangleAlt.alt_stripII,
                    TriangleAlt.star,
                    TriangleAlt.star1loose,
            ]
        ]
    ]
    # the same for the opposite edge alts
    edgeAltOpts[Symmetry.S4][0].append(edgeAltOpts[Symmetry.S4][0][0])
    edgeAltOpts[Symmetry.A5xI] = [
        [ # position 0
            [ # normal edge alternative
                    TriangleAlt.refl_1,
                    TriangleAlt.refl_2,
            ]
        ]
    ]
    # the same for the opposite edge alts
    edgeAltOpts[Symmetry.A5xI][0].append(edgeAltOpts[Symmetry.A5xI][0][0])
    edgeAltOpts[Symmetry.A5] = [
        [ # position 0
            [ # normal edge alternative
                    # TODO: add refl? Might lead to folded squares? Investigate.
                    #TriangleAlt.refl_1,
                    #TriangleAlt.refl_2,
                    TriangleAlt.stripI,
                    TriangleAlt.strip1loose,
                    TriangleAlt.alt_stripI,
                    TriangleAlt.alt_strip1loose,
                    TriangleAlt.stripII,
                    TriangleAlt.alt_stripII,
                    TriangleAlt.star,
                    TriangleAlt.star1loose,
            ]
        ]
    ]
    # the same for the opposite edge alts
    edgeAltOpts[Symmetry.A5][0].append(edgeAltOpts[Symmetry.A5][0][0])
    edgeAltOpts[Symmetry.A5].append(
        [
            [ # std edge alternative
                TriangleAlt.stripI,
                TriangleAlt.stripII,
                TriangleAlt.star,
            ],
            [ # opposite edge alternative
                TriangleAlt.strip1loose,
                TriangleAlt.stripI,
                TriangleAlt.stripII,
                TriangleAlt.star,
                TriangleAlt.star1loose,
            ]
        ]
    )

    def setup_ok_YxI(symGrp, edgeLs, edgeAlts, folds):
        dom = [
            T_Dom[symGrp],       # Translation
            [-numx.pi, numx.pi], # angle alpha
            [-numx.pi, numx.pi], # fold 1 beta
            [-numx.pi, numx.pi], # fold 2 gamma
        ]
        if edgeLs == [] or folds == [] or edgeAlts ==[]:
            print 'Warning: empty search specified!'
            return None
        else:
            return dom

    def tst_if_solutions_exist_YxI(symGrp, edgeLs, edgeAlts, folds,
                                        continueAfter = 100, precision = 14):
        dom = setup_ok_YxI(symGrp, edgeLs, edgeAlts, folds)
        if dom == None:
            return []
        trd = None
        has_solutions = []
        for edges in edgeLs:
            print 'investigating', edges
            edgeLs_has_solutions = False
            for fold in folds:
                print '  fold', str(Fold(fold))
                for ea in edgeAlts:
                    print '    edge alt', Stringify[ea]
                    trd = RandFindMultiRootOnDomain(dom,
                        symGrp,
                        edgeAlternative    = ea,
                        oppEdgeAlternative = ea,
                        edgeLengths        = edges,
                        fold               = fold,
                        precision          = precision,
                        method             = Method.hybrids,
                    )
                    trd.stopAfter = continueAfter
                    # we aren't using threads for this.
                    trd.tst_solutions_exist()
                    edgeLs_has_solutions = trd.solutions_exist
                    if edgeLs_has_solutions: break

                if edgeLs_has_solutions: break
            if edgeLs_has_solutions:
                has_solutions.append(edges)
        return has_solutions

    def randBatchYxI(symGrp, edgeLs, edgeAlts, folds, continueAfter = 100,
                            nrThreads = 1, precision = 14, outDir = "./",
                            loop = True):
        if not setup_ok_Y(symGrp, edgeLs, edgeAlts, folds):
            return
        rndT = [None for j in range(nrThreads)]
        i = 0
        while True:
            for edges in edgeLs:
                for fold in folds:
                    for ea in edgeAlts:
                        print '====set up thread %d===' % i
                        rndT[i] = RandFindMultiRootOnDomain(dom,
                            symGrp,
                            threadId           = i,
                            edgeAlternative    = ea,
                            oppEdgeAlternative = ea,
                            edgeLengths        = edges,
                            fold               = fold,
                            precision          = precision,
                            method             = Method.hybrids,
                            outDir             = outDir
                        )
                        rndT[i].stopAfter = continueAfter
                        rndT[i].start()
                        i = i + 1
                        if (i == nrThreads):
                            for j in range(nrThreads):
                                rndT[j].join()
                            print '===threads finished===='
                            i = 0
            if not loop:
                break

    pre_edgeLs_A4xI = [
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 1, 0, 1],
        [0, 1, 1, 0],
        [0, 1, 1, 1],
        [1, 0, 1, 0],
        [1, 0, 1, 1],
        [1, 1, 0, 1],
        [1, 1, 1, 0],
        [1, 1, 1, 1]
    ]
    pre_edgeLs_S4A4 = pre_edgeLs_all_1s_opposite_syms[:]
    pre_edgeLs_S4xI = pre_edgeLs_all_1s_opposite_syms[:]
    V_2p2V2_ = numx.sqrt(2 + 2*V2)
    V3p1     = 1 + V3
    dogram   = V3p1 / (2 + V3)
    pre_edgeLs_S4xI.extend([
                [0., 0., 0., V_2p2V2_], # squares become regular octagons
                                        # for a octagram this is 1 too.
                [0., 0., 1., V3p1],     # folded regular dodecagons
                                        # not interesting: dodecagram, since
                                        # there is no guarantee it will be
                                        # regular (more requirements needed)
        ])
    pre_edgeLs_S4 = pre_edgeLs_A4[:]
    pre_edgeLs_S4.extend([
        [1., 0., 1., 0., 0., 0., 1.], # 6 squares
        [1., 1., 1., 0., 1., 1., 1.], # 6 squares, 120 triangles.
    ])

    pre_edgeLs_A5xI = pre_edgeLs_all_1s_opposite_syms[:]
    pre_edgeLs_A5 = pre_edgeLs_A4[:]
    pre_edgeLs_A5_1 = [
        [0, 1, 0, 1, 1, 0, 1],
        [0, 1, 0, 1, 1, 1, 0],
        [0, 1, 0, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 0, 1],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1],
        [1, 0, 1, 0, 0, 1, 0],
        [1, 0, 1, 0, 0, 1, 1],
        [1, 0, 1, 0, 1, 1, 0],
        [1, 0, 1, 0, 1, 1, 1],
        [1, 0, 1, 1, 0, 1, 0],
        [1, 0, 1, 1, 0, 1, 1],
        [1, 0, 1, 1, 1, 1, 0],
        [1, 0, 1, 1, 1, 1, 1],
        [1, 1, 0, 1, 1, 0, 1],
        [1, 1, 0, 1, 1, 1, 0],
        [1, 1, 0, 1, 1, 1, 1],
        [1, 1, 1, 0, 0, 1, 0],
        [1, 1, 1, 0, 0, 1, 1],
        [1, 1, 1, 0, 1, 1, 0],
        [1, 1, 1, 0, 1, 1, 1],
        [1, 1, 1, 1, 0, 1, 0],
        [1, 1, 1, 1, 0, 1, 1],
        [1, 1, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1]
    ]

    pre_edgeLs = {
        Symmetry.A4xI: pre_edgeLs_A4xI,
        Symmetry.S4A4: pre_edgeLs_S4A4,
        Symmetry.A4  : pre_edgeLs_A4,
        Symmetry.S4xI: pre_edgeLs_S4xI,
        Symmetry.S4  : pre_edgeLs_S4,
        Symmetry.A5xI: pre_edgeLs_A5xI,
        Symmetry.A5  : pre_edgeLs_A5,
    }
    batch_YxI_folds = [
        Fold.w,
        Fold.star,
        Fold.triangle,
        Fold.trapezium,
        Fold.parallel,
    ]
    # TODO: howto: Fold.star, Fold.w, Fold.trapezium
    batch_Y_folds = [Fold.star, Fold.w]
    pre_folds = {
        Symmetry.A4xI: batch_YxI_folds[:],
        Symmetry.S4A4: batch_YxI_folds[:],
        Symmetry.A4  : batch_Y_folds[:],
        Symmetry.S4xI: batch_YxI_folds[:],
        Symmetry.S4  : batch_Y_folds[:],
        Symmetry.A5xI: batch_YxI_folds[:],
        Symmetry.A5  : batch_Y_folds[:]
    }
    dynamicSols = {
        Symmetry.A4xI: [],
        Symmetry.S4A4: [],
        Symmetry.A4  : dynamicSols_A4,
        Symmetry.S4xI: [],
        Symmetry.S4  : dynamicSols_S4,
        Symmetry.A5xI: [],
        Symmetry.A5  : [],
    }

    sym_sup = [
        Symmetry.A4xI, Symmetry.S4A4, Symmetry.A4,
        Symmetry.S4xI, Symmetry.S4,
        Symmetry.A5xI, Symmetry.A5,
    ]

    tstProg = False

    def printError(s):
        print '\n*** %s\n' % s

    def printUsage():
        print 'Usage:'
        print sys.argv[0], '[options] <symmetry group>'
        print 'Where options:'
        print '     -A      : list the edge alternatives. Depends on -v option.'
        print '     -a x    : edge alternative to search.'
        print '     -a [x:y]: slice of edge alternative list to search. If nothing is'
        print '               specified, then all alternatives from the -A option are'
        print '               searched.'
        print '     -B      : list the opposite edge alternatives. Depends on -v option.'
        print '     -b x    : opposite edge alternative to search, only for non-reflexive'
        print '               symmetries.'
        print '     -b [x:y]: slice of opposite edge alternative list to search. If nothing is'
        print '               specified, then all alternatives from the -B option are'
        print '               searched. Only for non-reflexive symmetries.'
        print '     -v x    : vertex position. Whether some triangle fills make sense depends'
        print '               a bit on the angle that positions a pair of heptagons. This'
        print '               decides how a certain triangle fill is positioned.'
        print '               Valid values are: 0 .. %d. Defaults to 0.' % (
            max_triangle_fill_pos - 1
        )
        print '     -f [x:y]: slice of heptagon fold list to search. If nothing is'
        print '               specified, then all folds from the -F option are searched.'
        print '     -F      : list available heptagon folds.'
        print '     -f x    : heptagon fold to search.'
        print '     -h      : prints this help.'
        print '     -i <num>: number of iterations to use; default %d.' % nr_iterations
        print '     -l [x:y]: slice of edge lengths list to search. If nothing is specified,'
        print '               then all lengths from the -L option are searched.'
        print '     -L      : list the edge lengths of the predefined list.'
        print '     -l x    : edge length to search.'
        print "     -o <out>: specifiy the output directory: don't use spaces; default"
        print '               %s.' % outDir
        print '     -p <num>: precision, specify the amount of digits after the point; default'
        print '               %d. Suggested to use 4 <= precision <= 13.' % precision
        print '     -s      : stop after having checked all. Default the program loops through'
        print '               all folds, edges, etc and starts over.'
        print '     -t      : Test all possible combinations of 1 and 0 for the edge lengths.'
        print '               This can be useful to investigate which edge lengths have'
        print '               solutions. It is suggested to use a little precision then, e.g.'
        print '               4 and a smaller amount of iterations, e.g. 100. This assumes -s'
        print '               and overrides -l. Other options aren\'t usually needed'
        print '     -1      : try one solution (for debugging/ testing): TODO: improve'
        print '               interface.'
        print 'And'
        print '    <symmetry group>: search solutions for the specified symmetry group. Valid'
        print '                      values are',
        for sym in sym_sup:
            print "%s" % sym,
        print

    # default values used by printUsage
    loop = True
    nr_iterations = 4000
    outDir = "tst/frh-roots"
    precision = 10
    max_triangle_fill_pos = 2 # TODO: fill in per symmetry

    # Handle command line arguments:
    if len(sys.argv) <= 1:
        printUsage()
        sys.exit(-1)
    else:
        skipNext = False # for options that take arguments
        symGrp = '' # which symmetry group to search: '' means not read yet
        # can be set to true by cmd line
        list_pre_edgeLs   = False
        list_edge_alts    = False
        list_opp_edge_alts= False
        list_fold_alts    = False
        set_fold_alts     = ''
        set_edge_alts     = ''
        set_opp_edge_alts = ''
        set_edge_Ls       = ''
        tst_all_combos    = False

        if sys.argv[1] == '-1':
            if len(sys.argv) <= 2:
                printError('Error: No symmetry group defined')
                printUsage()
                sys.exit(-1)
            testOneSolution(sys.argv[2])
            sys.exit(0)
        def errIfNoNxt(s, n):
            if len(sys.argv) <= n + 1: # note incl the cmd line also
                printError('Missing parameter for option: %s' % s)
                printUsage()
                sys.exit(-1)
        for n in range(1, len(sys.argv)):
            if skipNext:
                skipNext = False
            elif sys.argv[n] == '-a':
                errIfNoNxt('a', n)
                set_edge_alts = sys.argv[n + 1]
                skipNext = True
            elif sys.argv[n] == '-A':
                list_edge_alts = True
            elif sys.argv[n] == '-B':
                list_opp_edge_alts = True
            elif sys.argv[n] == '-b':
                errIfNoNxt('b', n)
                set_opp_edge_alts = sys.argv[n + 1]
                skipNext = True
            elif sys.argv[n] == '-v':
                errIfNoNxt('v', n)
                set_triangle_fill_pos = sys.argv[n + 1]
                skipNext = True
            elif sys.argv[n] == '-f':
                errIfNoNxt('f', n)
                set_fold_alts = sys.argv[n + 1]
                skipNext = True
            elif sys.argv[n] == '-F':
                list_fold_alts = True
            elif sys.argv[n] == '-h':
                printUsage()
                sys.exit(0)
            elif sys.argv[n] == '-i':
                errIfNoNxt('i', n)
                nr_iterations = int(sys.argv[n + 1])
                skipNext = True
            elif sys.argv[n] == '-l':
                errIfNoNxt('l', n)
                set_edge_Ls = sys.argv[n + 1]
                skipNext = True
            elif sys.argv[n] == '-L':
                list_pre_edgeLs = True
            elif sys.argv[n] == '-o':
                errIfNoNxt('o', n)
                outDir = sys.argv[n + 1]
                skipNext = True
            elif sys.argv[n] == '-p':
                errIfNoNxt('p', n)
                precision = int(sys.argv[n + 1])
                skipNext = True
            elif sys.argv[n] == '-s':
                loop = False
            elif sys.argv[n] == '-t':
                tst_all_combos = True
            elif sys.argv[n] == '-T':
                tstProg = True
            elif symGrp == '':
                if sys.argv[n] in sym_sup:
                    symGrp = sys.argv[n]
                else:
                    printError('Unknown symmetry group defined')
                    printUsage()
                    sys.exit(-1)
            else:
                printError('Unknown option: %s', sys.argv[n])
                printUsage()
                sys.exit(-1)

    if tstProg:
        if tstDynamicSolutions():
            print 'test PASSED'
        else:
            print 'test FAILED'
    elif symGrp == '':
        printError('Error: No symmetry group defined')
        printUsage()
        sys.exit(-1)
    else:
        if set_triangle_fill_pos == '':
            triangle_fill_pos = 0
        else:
            triangle_fill_pos = int(set_triangle_fill_pos)
            if (triangle_fill_pos >= max_triangle_fill_pos or
                triangle_fill_pos < 0
            ):
                print 'WARNING: illegal triangle fill position: %d' % (
                    triangle_fill_pos
                )
                print '         Valid are 0 .. %d' % (max_triangle_fill_pos - 1)
                printUsage()
                sys.exit(0)
        if (list_pre_edgeLs or
            list_edge_alts or
            list_opp_edge_alts or
            list_fold_alts
        ):
            if list_pre_edgeLs:
                print 'Possible edge lengths:'
                for (i, e) in zip(range(len(pre_edgeLs[symGrp])),
                                                        pre_edgeLs[symGrp]):
                    print '%3d:' % i, e
            if list_edge_alts:
                print 'Possible edge alternatives:'
                for (i, e) in zip(
                    range(len(edgeAltOpts[symGrp][triangle_fill_pos][0])),
                    edgeAltOpts[symGrp][triangle_fill_pos][0]
                ):
                    print '%3d: %s' % (i, Stringify[e])
            if list_opp_edge_alts:
                print 'Possible opposite edge alternatives:'
                for (i, e) in zip(
                    range(len(edgeAltOpts[symGrp][triangle_fill_pos][1])),
                    edgeAltOpts[symGrp][triangle_fill_pos][1]
                ):
                    print '%3d: %s' % (i, Stringify[e])
            if list_fold_alts:
                print 'Possible heptagon fold alternatives:'
                for (i, e) in zip(range(len(pre_folds[symGrp])),
                                                        pre_folds[symGrp]):
                    print '%3d: %s' % (i, str(Fold(e)))
            sys.exit(0)
        if tst_all_combos:
            loop = False
            if symGrp == Symmetry.A4 or symGrp == Symmetry.S4 or\
                                                        symGrp == Symmetry.A5:
                edgeLs = pre_edgeLs_all_1s_direct_syms[:]
            else:
                edgeLs = pre_edgeLs_all_1s_opposite_syms[:]
        elif set_edge_Ls == '':
            edgeLs = pre_edgeLs[symGrp]
        else:
            if set_edge_Ls[0] != '[':
                # try is slice is one element, ie an int
                try:
                    i = int(set_edge_Ls)
                except ValueError:
                    printError("value error for edge index %s\n", set_edge_Ls)
                edgeLs = pre_edgeLs[symGrp][i:i+1]
            else:
                try:
                    edgeLs = eval('pre_edgeLs[Symmetry.%s]%s' % (symGrp,
                                                                set_edge_Ls))
                    # if just an index was used instead of a slice:
                    if type(edgeLs) == int:
                        edgeLs = [edgeLs]
                except TypeError:
                    printError("type error for edge slice: '%s'\n" % set_edge_Ls)
                    printUsage()
                    sys.exit(0)
                except SyntaxError:
                    printError("syntax error for edge slice: '%s'\n" % set_edge_Ls)
                    printUsage()
                    sys.exit(0)
        if set_edge_alts == '':
            edgeAlts = edgeAltOpts[symGrp][triangle_fill_pos][0]
        else:
            if set_edge_alts[0] != '[':
                # try if slice is one element, ie an int
                try:
                    i = int(set_edge_alts)
                except ValueError:
                    printError("value error for edge index %s\n", set_edge_alts)
                edgeAlts = edgeAltOpts[symGrp][triangle_fill_pos][0][i:i+1]
            else:
                try:
                    edgeAlts = eval('edgeAltOpts[Symmetry.%s][%d][0]%s' % (
                            symGrp,
                            triangle_fill_pos,
                            set_edge_alts
                        )
                    )
                except TypeError:
                    printError("type error for edge slice: '%s'\n" % set_edge_alts)
                    printUsage()
                    sys.exit(0)
                except SyntaxError:
                    printError("syntax error for edge slice: '%s'\n" % set_edge_alts)
                    printUsage()
                    sys.exit(0)
        if set_opp_edge_alts == '':
            oppEdgeAlts = edgeAltOpts[symGrp][triangle_fill_pos][1][:]
        else:
            if set_opp_edge_alts[0] != '[':
                # try if slice is one element, ie an int
                try:
                    i = int(set_opp_edge_alts)
                except ValueError:
                    printError(
                        "value error for edge index %s\n", set_opp_edge_alts)
                oppEdgeAlts = edgeAltOpts[symGrp][triangle_fill_pos][1][i:i+1]
            else:
                try:
                    oppEdgeAlts = eval('edgeAltOpts[Symmetry.%s][%d][1]%s' % (
                            symGrp,
                            triangle_fill_pos,
                            set_opp_edge_alts
                        )
                    )
                except TypeError:
                    printError("type error for edge slice: '%s'\n" %
                                                            set_opp_edge_alts)
                    printUsage()
                    sys.exit(0)
                except SyntaxError:
                    printError("syntax error for edge slice: '%s'\n" %
                                                            set_opp_edge_alts)
                    printUsage()
                    sys.exit(0)

        if set_fold_alts == '':
            foldAlts = pre_folds[symGrp]
        else:
            if set_fold_alts[0] != '[':
                # try is slice is one element, ie an int
                try:
                    i = int(set_fold_alts)
                except ValueError:
                    printError("value error for edge index %s\n", set_fold_alts)
                foldAlts = pre_folds[symGrp][i:i+1]
            else:
                try:
                    foldAlts = eval('pre_folds[Symmetry.%s]%s' % (symGrp,
                                                                    set_fold_alts))
                    # if just an index was used instead of a slice:
                    if type(foldAlts) == int:
                        foldAlts = [foldAlts]
                except TypeError:
                    printError("type error for fold slice: '%s'\n" % set_fold_alts)
                    printUsage()
                    sys.exit(0)
                except SyntaxError:
                    printError("syntax error for fold slice: '%s'\n" % set_fold_alts)
                    printUsage()
                    sys.exit(0)

        print 'Search solutions for symmetry group %s' % symGrp
        print 'Switch setup after %d randomly selected begin values' % (
                                                            nr_iterations)
        print 'Save solutions in:', outDir
        # TODO: specify fold by command line...
        print 'heptagon folds = ['
        for f in foldAlts:
            print '  %s,' % str(Fold(f))
        print ']'
        print 'Edge lengths slice %s:' % (set_edge_Ls)
        for e in edgeLs:
            print '  -', e
        print 'edgeAlts = ['
        for e in edgeAlts:
            print '  %s,' % Stringify[e]
        print ']'
        if oppEdgeAlts != None:
            print 'oppEdgeAlts = ['
            for e in oppEdgeAlts:
                print '  %s,' % Stringify[e]
            print ']'

        if symGrp == Symmetry.A4xI or symGrp == Symmetry.S4A4 or\
                        symGrp == Symmetry.S4xI or symGrp == Symmetry.A5xI:
            if tst_all_combos:
                edges_with_solutons = tst_if_solutions_exist_YxI(symGrp, edgeLs,
                                edgeAlts, foldAlts, nr_iterations, precision)
                print 'Edges with solutions:'
                for e in edges_with_solutons:
                    print e
            else:
                randBatchYxI(symGrp, edgeLs, edgeAlts, foldAlts, nr_iterations,
                        nrThreads = 1, precision = precision, outDir = outDir,
                        loop = loop)
        elif symGrp == Symmetry.A4 or symGrp == Symmetry.S4 or\
                                                        symGrp == Symmetry.A5:
            if tst_all_combos:
                edges_with_solutons = tst_if_solutions_exist_Y(symGrp, edgeLs,
                    edgeAlts, foldAlts, nr_iterations, precision, oppEdgeAlts,
                    triangle_fill_pos = triangle_fill_pos)
                print 'Edges with solutions:'
                for e in edges_with_solutons:
                    print e
            else:
                randBatchY(symGrp, edgeLs, edgeAlts, foldAlts, nr_iterations,
                        nrThreads = 1, dynSols = dynamicSols[symGrp],
                        precision = precision, outDir = outDir, loop = loop,
                        oppEdgeAlts = oppEdgeAlts,
                        triangle_fill_pos = triangle_fill_pos)