#! /usr/bin/python

import math
import GeomTypes
from copy import copy

X = GeomTypes.ux
Y = GeomTypes.uy
Z = GeomTypes.uz

hTurn = math.pi         # half turn
qTurn = math.pi/2       # quarter turn
eTurn = qTurn/2         # one eighth turn
tTurn = 2*math.pi/3     # third turn

acos_1_V3  = math.acos(1.0 / math.sqrt(3))
asin_1_V3  = math.asin(1.0 / math.sqrt(3))
asin_V2_V3 = acos_1_V3
acos_V2_V3 = asin_1_V3

# halfturn around x-, y-, and z-axis
Hx = GeomTypes.Hx
Hy = GeomTypes.Hy
Hz = GeomTypes.Hz

I  = GeomTypes.I       # central inversion

class ImproperSubgroup(ValueError):
    "Raised when subgroup is not really a subgroup"

class Set(set):

    def __init__(this, *args):
        set.__init__(this, *args)

    def __eq__(this, o):
        eq = (len(this) == len(o))
        if eq:
            for e in this:
                eq = e in o
                if not eq: break
        return eq

    def __mul__(this, o):
        if isinstance(o, Set):
            # Set(this) * Set(o)
            new = Set([])
            for d in o:
                new.update(this * d)
            return new
        else:
            # Set * GeomTypes.Transform3
            return Set([e * o for e in this])

    def __rmul__(this, o):
        # Note rotation Set * Set is caught by __mul__
        # rotation Rot * Set
        return Set([o * e for e in this])

    def subgroup(this, o):
        try:
            if isinstance(o, GeomTypes.Transform3):
                # generate the quotient set THIS / o
                assert o in this
                subgroup = Set([o])
                subgroup.group()
                return subgroup
            else:
                for e in o:
                    assert e in this
                subgroup = copy(o)
                subgroup.group()
                return subgroup
        except AssertionError:
            raise ImproperSubgroup

    def __div__(this, o):
        # this * subgroup: right quotient set
        # make sure o is a subgroup:
        if (len(o) > len(this)): return o.__div__(this)
        o = this.subgroup(o)
        assert len(o) <= len(this)
        # use a list of sets, since sets are unhashable
        quotientSet = []
        # use a big set for all elems found so for
        foundSoFar = Set([])
        for te in this:
            q = te * o
            if q.getOne() not in foundSoFar:
                quotientSet.append(q)
                foundSoFar = foundSoFar.union(q)
        return quotientSet

    quotientSet = __div__

    def __rdiv__(this, o):
        #  subgroup * this: left quotient set
        pass # TODO

    def __contains__(this, o):
        # Needed for 'in' relationship: default doesn't work, it seems to
        # compare the elements id.
        #print this.__class__.__name__, '__contains__'
        for e in this:
            if e == o:
                #print 'e == o'
                #print '  - with e:', e
                #print '           ', e.__repr__()
                #print '  - with o:', o
                #print '           ', o.__repr__()
                return True
        return False

    def add(this, e):
        l = len(this)
        if e not in this:
            set.add(this, e)

    def update(this, o):
        for e in o:
            this.add(e)

    def getOne(this):
        for e in this: return e

    def __str__(this):
        s = '%s = {' % this.__class__.__name__
        for d in this:
            s = '%s\n  %s,' % (s, str(d))
        s = '%s\n}' % s
        # TODO if there is an opposite isometry...
        return s

    def group(this, maxIter = 50):
        """
        Tries to make a group out of the set of isometries

        If it succeeds within maxiter step this set is closed, contains the unit
        element and the set contains for every elements its inverse
        """
        result = copy(this)
        for e in this:
            result.add(e.inverse())
        result.add(GeomTypes.E)
        this.clear()
        this.update(result.close(maxIter))

    def close(this, maxIter = 50):
        """
        Return a set that is closed, if it can be generated within maxIter steps.
        """
        result = copy(this)
        for i in range(maxIter):
            lPrev = len(result)
            # print 'close step', i, 'len:', lPrev
            result.update(result * result)
            l = len(result)
            if l == lPrev:
                break
            # print '  --> new group with len', l, ':\n', result
        assert (l == lPrev), "couldn't close group after %d iterations"% maxIter
        return result

def setup(**kwargs): return kwargs

class E(Set):
    initPars = []
    def __init__(this, isometries = None, setup = {}):
            Set.__init__(this, [GeomTypes.E])

C1 = E

class ExI(Set):
    initPars = []
    def __init__(this, isometries = None, setup = {}):
            Set.__init__(this, [GeomTypes.E, GeomTypes.I])


C1xI = ExI

class Cn(Set):
    initPars = [
        {'type': 'int', 'par': 'n',    'lab': "order"},
        {'type': 'vec3', 'par': 'axis', 'lab': "n-fold axis"}
    ]
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group Cn, consisting of n rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        """
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(this, isometries)
        else:
            keys = setup.keys()
            if 'axis' in keys: axis = setup['axis']
            else:              axis = Z[:]
            if 'n' in keys: n = setup['n']
            else:           n = 2
            if n == 0: n = 1

            angle = 2 * math.pi / n
            try:   r = GeomTypes.Rot3(axis = axis, angle = angle)
            except TypeError:
                # assume axis has Rot3 type
                r = GeomTypes.Rot3(axis = axis.axis(), angle = angle)

            isometries = [r]
            for i in range(n-1):
                isometries.append(r * isometries[-1])
            Set.__init__(this, isometries)

def generateD2(o2axis0, o2axis1):
    """
    Returns 3 orthogonal halfturns for D2
    """
    # if axes is specified as a transform:
    if isinstance(o2axis0, GeomTypes.Transform3):
        o2axis0 = o2axis0.axis()
    if isinstance(o2axis1, GeomTypes.Transform3):
        o2axis1 = o2axis1.axis()
    assert GeomTypes.Vec3(o2axis0) * GeomTypes.Vec3(o2axis1) == 0, (
            "Error: axes not orthogonal")
    H0 = GeomTypes.HalfTurn3(o2axis0)
    H1 = GeomTypes.Rot3(axis = o2axis1, angle = hTurn)
    return (H0, H1, H1 * H0)

def generateA4O3(D2HalfTurns):
    """
    Returns a tuple (R1_1_3, R1_2_3, R2_1_3, R2_2_3, R3_1_3, R3_2_3, R4_1_3,
    R4_2_3)

    D2HalfTurns: tuple containing H0, H1, H2
    """
    H0, H1, H2 = D2HalfTurns

    # the one order 3 rotation axis, is obtained as follows:
    # imagine A4 is part of S4 positioned in a cube
    # H0, H1, H2 go through the cube face centres
    # define a quarter turn around H2
    Q = GeomTypes.Rot3(axis = H2.axis(), angle = qTurn)
    # h0 and h1 go through cube edge centres
    h0 = Q * H0
    h1 = Q * H1
    # o3axis goes through 1 of the 2 cube vertices that form the edge
    # between the faces which centres are on H0 and H1
    o3axis = GeomTypes.Rot3(
            axis = h0.axis(), angle = asin_1_V3
        ) * h1.axis()
    # R1_1_3: 1/3 rotation around the first order 3 axis
    # R1_2_3: 2/3 rotation around the first order 3 axis
    R1_1_3 = GeomTypes.Rot3(axis = o3axis, angle = tTurn)
    R1_2_3 = GeomTypes.Rot3(axis = o3axis, angle = 2*tTurn)
    R4_1_3 = R1_1_3 * H0
    R3_1_3 = R1_1_3 * H1
    R2_1_3 = R1_1_3 * H2
    R2_2_3 = R1_2_3 * H0
    R4_2_3 = R1_2_3 * H1
    R3_2_3 = R1_2_3 * H2
    # print 'R1_1_3', R1_1_3
    # print 'R1_2_3', R1_2_3
    # print 'R2_1_3', R2_1_3
    # print 'R2_2_3', R2_2_3
    # print 'R3_1_3', R3_1_3
    # print 'R3_2_3', R3_2_3
    # print 'R4_1_3', R4_1_3
    # print 'R5_2_3', R4_2_3
    return (R1_1_3, R1_2_3, R2_1_3, R2_2_3, R3_1_3, R3_2_3, R4_1_3, R4_2_3)

class A4(Set):
    initPars = [
        {'type': 'vec3', 'par': 'o2axis0', 'lab': "half turn axis"},
        {'type': 'vec3', 'par': 'o2axis1', 'lab': "half turn of orthogonal axis"}
    ]
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group A4, consisting of 12 rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - the identity E, and 3 orthogonal halfturns
        - 8 order 3 isometries.
        The group can be generated by the axes of 2 half turns, but this will
        not generate the group uniquely: There are 2 possibilities: the two
        tetrahedra in a Stella Octagula. The order of the 2 axes of the 2 half
        turns decides which position is obtained.
        """
        # A4 consists of:
        # 1. A subgroup D2: E, and half turns H0, H1, H2
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            assert len(isometries) == 12, "12 != %d" % (len(isometries))
            # TODO: more asserts?
            Set.__init__(this, isometries)
        else:
            axes = setup.keys()
            if 'o2axis0' in axes: o2axis0 = setup['o2axis0']
            else:                 o2axis0 = X[:]
            if 'o2axis1' in axes: o2axis1 = setup['o2axis1']
            else:                 o2axis1 = Y[:]
            d2 = generateD2(o2axis0, o2axis1)
            H0, H1, H2 = d2
            R1_1, R1_2, R2_1, R2_2, R3_1, R3_2, R4_1, R4_2 = generateA4O3(d2)

            Set.__init__(this, [
                    GeomTypes.E,
                    H0, H1, H2,
                    R1_1, R1_2, R2_1, R2_2, R3_1, R3_2, R4_1, R4_2
                ])

class A4xI(A4):
    initPars = [
        {'type': 'vec3', 'par': 'o2axis0', 'lab': "half turn axis"},
        {'type': 'vec3', 'par': 'o2axis1', 'lab': "half turn of orthogonal axis"}
    ]
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group A4xI, consisting of 12 rotations and 12 rotary
        inversions.

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - the identity E, and 3 orthogonal halfturns
        - 8 order 3 rotations.
        - the central inversion I, 3 reflections
        - 8 order rotary inversions
        The group can be generated by the axes of 2 half turns
        """
        if isometries != None:
            assert len(isometries) == 24, "24 != %d" % (len(isometries))
            # TODO: more asserts?
            Set.__init__(this, isometries)
        else:
            a4 = A4(setup = setup)
            Set.__init__(this, a4 * ExI())

class S4(Set):
    initPars = [
        {'type': 'vec3', 'par': 'o4axis0', 'lab': "half turn axis"},
        {'type': 'vec3', 'par': 'o4axis1', 'lab': "half turn of orthogonal axis"}
    ]
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group S4, consisting of 24 rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - the identity E,
        - and 9 orthogonal turns based on quarter turns (1/4, 1/2, 3/4)
        - 8 turns based on third turns (1/3, 2/3).
        - 6 halfturns
        The group can be generated by the axes of 2 quarter turns,
        """
        if isometries != None:
            assert len(isometries) == 24, "24 != %d" % (len(isometries))
            # TODO: more asserts?
            Set.__init__(this, isometries)
        else:
            axes = setup.keys()
            if 'o4axis0' in axes: o4axis0 = setup['o4axis0']
            else:                 o4axis0 = X[:]
            if 'o4axis1' in axes: o4axis1 = setup['o4axis1']
            else:                 o4axis1 = Y[:]
            d2 = generateD2(o4axis0, o4axis1)
            R1_1, R1_2, R2_1, R2_2, R3_1, R3_2, R4_1, R4_2 = generateA4O3(d2)
            q0_2, q1_2, q2_2 = d2
            ax0 = q0_2.axis()
            ax1 = q1_2.axis()
            ax2 = q2_2.axis()
            q0_1 = GeomTypes.Rot3(axis = ax0, angle = qTurn)
            q0_3 = GeomTypes.Rot3(axis = ax0, angle = 3*qTurn)
            q1_1 = GeomTypes.Rot3(axis = ax1, angle = qTurn)
            q1_3 = GeomTypes.Rot3(axis = ax1, angle = 3*qTurn)
            q2_1 = GeomTypes.Rot3(axis = ax2, angle = qTurn)
            q2_3 = GeomTypes.Rot3(axis = ax2, angle = 3*qTurn)
            h0 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax0, angle = eTurn) * ax1,
                    angle = hTurn
                )
            h1 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax0, angle = 3*eTurn) * ax1,
                    angle = hTurn
                )
            h2 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax1, angle = eTurn) * ax0,
                    angle = hTurn
                )
            h3 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax1, angle = 3*eTurn) * ax0,
                    angle = hTurn
                )
            h4 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax2, angle = eTurn) * ax0,
                    angle = hTurn
                )
            h5 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax2, angle = 3*eTurn) * ax0,
                    angle = hTurn
                )
            Set.__init__(this, [
                    GeomTypes.E,
                    q0_1, q0_2, q0_3, q1_1, q1_2, q1_3, q2_1, q2_2, q2_3,
                    R1_1, R1_2, R2_1, R2_2, R3_1, R3_2, R4_1, R4_2,
                    h0, h1, h2, h3, h4, h5
                ])

E.subgroups = [E]
ExI.subgroups = [ExI, E]
Cn.subgroups = [Cn, E]

# Dn = D2, D1
# Cn = C3
A4.subgroups = [A4,
        #Dn,
        Cn, E
    ]

# DnxI = D2xI, D1xI
# CnxI = C3xI, C2xI
# Dn = D2, D1
# Cn = C3
A4xI.subgroups = [A4xI, A4,
        #DnxI, CnxI, Dn,
        Cn, E
    ]

# Dn = D4, D3, D2 (2x), D1
# Cn = C4, C3, C2
S4.subgroups = [S4, A4,
        #Dn,
        Cn, E
    ]

if __name__ == '__main__':

    print 'testing creation of set',
    g = Set([Hx, Hy])
    print '....ok'
    #print 'Initialised set g:', g
    print "testing 'in' relation",
    assert GeomTypes.Rot3(axis = [1, 0, 0], angle = hTurn) in g
    assert GeomTypes.Rot3(axis = [-1, 0, 0], angle = -hTurn) in g
    print '......ok'
    print "testing 'close' function",
    cg = g.close()
    #print 'Set g after closing:'
    #print cg
    assert len(cg) == 4
    assert Hx in cg
    assert Hy in cg
    assert Hz in cg
    assert GeomTypes.E in cg
    print '...ok'

    print 'testing creation of set',
    g = Set([GeomTypes.Rot3(axis = X, angle = qTurn)])
    print '....ok'
    print "testing 'in' relation",
    GeomTypes.Rot3(axis =  X, angle = qTurn)  in g
    GeomTypes.Rot3(axis = -X, angle = -qTurn) in g
    print '......ok'
    print "testing 'close' function",
    cg = g.close()
    #print 'Set g after closing:'
    #print cg
    assert len(cg) == 4
    GeomTypes.Rot3(axis =  GeomTypes.Vec3([1, 0, 0]), angle = qTurn)  in cg
    GeomTypes.Rot3(axis = -GeomTypes.Vec3([1, 0, 0]), angle = -qTurn) in cg
    assert Hx in cg
    assert GeomTypes.E in cg
    print '...ok'

    print 'testing creation of A4',
    a4 = A4(setup = setup(o2axis0 = X, o2axis1= Y))
    print '.....ok'
    print 'checking result',
    assert len(a4) == 12
    assert GeomTypes.E in a4
    assert Hx in a4
    assert Hy in a4
    assert Hz in a4
    t0 = GeomTypes.Rot3(axis = [1,  1,  1], angle =   tTurn)
    assert t0 in a4
    t1 = GeomTypes.Rot3(axis = [1,  1,  1], angle = 2*tTurn)
    assert t1 in a4
    t2 = GeomTypes.Rot3(axis = [1, -1,  1], angle =   tTurn)
    assert t2 in a4
    t3 = GeomTypes.Rot3(axis = [1, -1,  1], angle = 2*tTurn)
    assert t3 in a4
    t4 = GeomTypes.Rot3(axis = [1, -1, -1], angle =   tTurn)
    assert t4 in a4
    t5 = GeomTypes.Rot3(axis = [1, -1, -1], angle = 2*tTurn)
    assert t5 in a4
    t6 = GeomTypes.Rot3(axis = [1,  1, -1], angle =   tTurn)
    assert t6 in a4
    t7 = GeomTypes.Rot3(axis = [1,  1, -1], angle = 2*tTurn)
    assert t7 in a4
    print '............ok'

    print 'testing creation of A4',
    a4 = A4(
            setup = setup(
                # try list argument
                o2axis0 = [1, 1, 1],
                # try Rot3 argument
                o2axis1 = GeomTypes.HalfTurn3([1, -1, 0])
            )
        )
    #print 'A4(o2axis0 = [1, 1, 1], o2axis1 = [1, -1, 0])'
    print '.....ok'
    # this a4 is the above a4 repositioned as follows:
    r0 = GeomTypes.Rot3(axis = Z, angle = eTurn)
    r1 = GeomTypes.Rot3(axis = [1, -1, 0], angle = math.atan(1/math.sqrt(2)))
    r = r1 * r0
    print 'checking result',
    assert len(a4) == 12
    assert GeomTypes.E in a4
    assert GeomTypes.HalfTurn3(r*X) in a4
    assert GeomTypes.HalfTurn3(r*Y) in a4
    assert GeomTypes.HalfTurn3(r*Z) in a4
    assert GeomTypes.Rot3(axis = r * t0.axis(), angle =   tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t1.axis(), angle = 2*tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t2.axis(), angle =   tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t3.axis(), angle = 2*tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t4.axis(), angle =   tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t5.axis(), angle = 2*tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t6.axis(), angle =   tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t7.axis(), angle = 2*tTurn) in a4
    print '............ok'
    #print a4
    print 'test grouping this',
    ca4 = copy(a4)
    a4.group()
    assert a4 == ca4
    print '.........ok'

    ########################################################################
    # Quotient Set:
    a4 = A4(setup = setup(o2axis0 = X, o2axis1= Y))
    assert len(a4) == 12
    # print 'group a4:'
    # print a4
    d2 = Set([Hx, Hy])
    d2.group()
    assert len(d2) == 4
    # print 'has a subgroup D2:'
    # print d2
    print 'test quotient set: A4/D2',
    q = a4 / d2
    # print 'which defines a right quotient set s = ['
    for s in q:
    #     print '  set('
    #     for e in s:
    #         print '    ', e
    #     print '  )'
        assert len(s) == 4
    # print ']'
    assert len(q) == 3
    # check if A4 / D2 is a partition of A4:
    for i in range(len(q)-1):
        s = q[i]
        for transform in s:
            for j in range(i+1, len(q)):
                assert not transform in q[j]
    print '...ok'

    print 'success!'
