#! /usr/bin/python

import math
#import re
import GeomTypes
import isometry
#from copy import copy

def setup(**kwargs): return kwargs

class Orbit(list):
    def __new__(this, v):
        assert len(v) == 2
        assert isinstance(v[0], isometry.Set)
        assert isinstance(v[1], isometry.Set)
        this.final = v[0]
        this.stabiliser = v[1]
        return list.__new__(this, v)

    def __repr__(v):
        s = '%s([\n'
        s = '%s  %s\n' % repr(v[0])
        s = '%s  %s\n' % repr(v[1])
        s = '%s])\n'
        if __name__ != '__main__':
            s = '%s.%s' % (__name__, s)
        return s

    def __str__(v):
        s = '%s([\n'
        s = '%s  final = %s\n' % str(v[0])
        s = '%s  stabiliser = %s\n' % str(v[1])
        s = '%s])\n'
        if __name__ != '__main__':
            s = '%s.%s' % (__name__, s)
        return s

    @property
    def higherOrderStabiliserProps(v):
        """Get possible sub orbit classes for higher order stabilisers

        A sub-orbit is used if a group of isometries are used on the
        stabiliser to obtain a higher order stabiliser. This higher order
        stabiliser requires a sub orbit. Practically this is used for colouring
        of polyhedra. E.g. The polyhedra is defined by one face with some
        symmetry. Then the higher order stabiliser is the set of faces with the
        same colour. SUch a set has there own symmetry. The different groups of
        coloured faces are mapped onto each other by a sub orbit. The norm of
        this sub-orbit equals to the amount of colours used. With this a list of
        dictionaries is obtained. Each dictionary holds:
            'class': higher order stabiliser classes is obtained.
            'index': the length of the subgroups in the final group, or the
                     norme of the coset.
        """
        try:
            assert v.__hoscCalled == True, 'if this exists it should be true'
        except AttributeError:
            v.__hosProps = v.__hosp()
            v.__hosPropsCalled = True
        print 'higherOrderStabiliserProps', v.__hosProps
        return v.__hosProps


    def __hosp(v):
        """See higherOrderStabiliserProps"""

        print '%s.getSubOrbitClasses' % v.__class__.__name__
        higherOrderStabiliserProps   = []
        v.hoStabs                    = []
        v.indexCovered               = {}
        for subGroup in v.final.subgroups:
            #print 'subGroup', subGroup.__class__.__name__
            #print '...contains stabiliser', v.stabiliser, '...??..',
            assert subGroup.order != 0
            if v.stabiliser.__class__ in subGroup.subgroups:
                #print 'yes'

                # Check if the stabiliser can really be a subgroup for this
                # orientation.
                # E.g.
                # final symmetry S4xI
                # stabiliser: D2C2 with principle axis: one 2-fold from S4xI
                #                                       (ie not a 4-fold axis)
                # Now A4xI is a subgroup of S4xI
                # and D2C2 is a subgroup of A4xI,
                # However the D2C2 that is a subgroup of the A4xI subgroup of
                # S4xI has a principle axis that is a 4-fold axis of S4xI.

                hoStabs = v.final.realiseSubgroups(subGroup)
                #print 'check list of len:', len(hoStabs)
                # from end to beginning, because elements will be filtered out:
                for i in range(len(hoStabs)-1, -1, -1):
                    #print 'isSubgroup', v.stabiliser, hoStabs[i]
                    if v.stabiliser.isSubgroup(hoStabs[i]):
                        #print 'yes, break at index', i
                        break
                    else:
                        # remove this from the list, this is part of the work of
                        # filtering the list. This is not done completely here
                        # since it costs time, and the user might not choose
                        # this sub orbit anyway (hence the break above). But to
                        # save time later, remove it already.
                        #print 'no'
                        #print 'higher order stabiliser:'
                        #print '%s' % (str(hoStabs[i]))
                        #print 'has no subgroup:'
                        #print '%s' % (str(v.stabiliser))
                        del hoStabs[i]
                index = v.final.order/subGroup.order
                if hoStabs != []:
                    #print 'add True'
                    higherOrderStabiliserProps.append({
                            'class': subGroup, 'index': index, 'filtered': i
                        }
                    )
                    v.hoStabs.append(hoStabs)
                    v.indexCovered[index] = True
                    #print 'subOrbitsLengths, finalSymClass', v.final.__class__
                #else:
                #    print 'filetered out subgroup', subGroup
                #    print 'add False'
            #else:
            #    print 'no'
        return higherOrderStabiliserProps

    def higherOrderStabiliser(v, n):
        """Get possible sub orbits for higher order stabilisers

        With this a list of higher order stabilisers of one class is obtained.
        n: the list index in higherOrderStabiliserProps representing the class.
        see also higherOrderStabiliserProps.
        """

        # Make sure the list is initialised.
        props = v.higherOrderStabiliserProps

        # filter rest if needed:
        if (props[n]['filtered'] > 0):
            # Now filter out the stabilisers that are not a subgroup for this
            # orientation.
            # (part of this is done in __hosp)
            # E.g.
            # final symmetry S4xI
            # stabiliser: D2C2 with principle axis: one 2-fold from S4xI
            #                                       (ie not a 4-fold axis)
            # Now D4xI is a subgroup of S4xI
            # and D2C2 is a subgroup of D4xI,
            # but not necessarily this orientation. In fact only one of the
            # three possible D4xI will have this D2C2 as subgroup.
            for i in range(props[n]['filtered']-1, -1, -1):
                if not v.stabiliser.isSubgroup(v.hoStabs[n][i]):
                    del v.hoStabs[n][i]
            assert len(v.hoStabs[n]) != 0, (
                "This case should have been checked in __hosp"
            )
            props[n]['filtered'] = 0
        return v.hoStabs[n]

    @property
    def lowerOrderStabiliserProps(v):
        """Get possible sub orbit classes for alternative higher order stabilisers

        TODO
        """
        try:
            assert v.__losPropsCalled == True, 'if this exists it should be true'
        except AttributeError:
            v.__losProps = v.__losp()
            v.__losPropsCalled = True
        return v.__losProps


    def __losp(v):
        """See lowerOrderStabiliserProps"""

        lowerOrderStabiliserProps = []
        v.loStabs                 = []
        if v.stabiliser.mixed == True:
            # alternative way of colouring by using the direct parents.
            # TODO explain more
            assert v.final.mixed
            print '__losp: final class', v.final.__class__.__name__
            if v.final.generator != {}:
                v.altFinal = v.final.directParent(
                        setup = v.final.directParentSetup
                    )
            else:
                v.altFinal = v.final.directParent(isometries = [
                        isom for isom in v.final if isom.isDirect()
                    ])
            if v.stabiliser.generator != {}:
                v.altStab = v.stabiliser.directParent(setup =
                        v.stabiliser.directParentSetup
                    )
            else:
                v.altStab = v.stabiliser.directParent(isometries = [
                        isom for isom in v.stabiliser if isom.isDirect()
                    ])

            # TODO: fix; don't copy above code...
            for subGroup in v.altFinal.subgroups:
                assert subGroup.order != 0
                if v.altStab.__class__ in subGroup.subgroups:
                    loStabs = v.altFinal.realiseSubgroups(subGroup)
                    for i in range(len(loStabs)-1, -1, -1):
                        if v.altStab.isSubgroup(loStabs[i]):
                            break
                        else:
                            del loStabs[i]
                    index = v.altFinal.order/subGroup.order
                    try:
                        if v.indexCovered[index]:
                            pass
                    except KeyError:
                        if loStabs != []:
                            lowerOrderStabiliserProps.append({
                                    'class': subGroup,
                                    'index': index, 'filtered': i
                                }
                            )
                            v.loStabs.append(loStabs)
                            # don't add to v.indexCovered, it means covered by
                            # ho, really

        return lowerOrderStabiliserProps

    def lowerOrderStabiliser(v, n):
        """Get possible sub orbits for higher order stabilisers

        With this a list of higher order stabilisers of one class is obtained.
        n: the list index in lowerOrderStabiliserProps representing the class.
        see also lowerOrderStabiliserProps.
        """

        # Make sure the list is initialised.
        props = v.lowerOrderStabiliserProps

        # filter rest if needed:
        if (props[n]['filtered'] > 0):
            for i in range(props[n]['filtered']-1, -1, -1):
                if not v.altStab.isSubgroup(v.loStabs[n][i]):
                    del v.loStabs[n][i]
            assert len(v.loStabs[n]) != 0, (
                "This case should have been checked in __losp"
            )
            props[n]['filtered'] = 0
        return v.loStabs[n]

#class E(Set):
#    initPars = []
#    order = 1
#    def __init__(this, isometries = None, setup = {}):
#            this.checkSetup(setup)
#            Set.__init__(this, [GeomTypes.E])
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        return [E()]
#
#E.subgroups = [E]
#C1 = E
#
#class ExI(Set):
#    initPars = []
#    order = 2
#    def __init__(this, isometries = None, setup = {}):
#            this.checkSetup(setup)
#            Set.__init__(this, [GeomTypes.E, GeomTypes.I])
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if sg == ExI:
#            return [this]
#        elif sg == E:
#            return [E()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
#ExI.subgroups = [ExI, E]
#
#class MetaCn(type):
#    def __init__(this, classname, bases, classdict):
#        type.__init__(this, classname, bases, classdict)
#class Cn(Set):
#    __metaclass__ = MetaCn
#    initPars = [
#        {'type': 'int', 'par': 'n',    'lab': "order"},
#        {'type': 'vec3', 'par': 'axis', 'lab': "n-fold axis"}
#    ]
#    defaultSetup = {'n': 2, 'axis': Z[:]}
#    order = 0
#    n = 0
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group Cn, consisting of n rotations
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
#        """
#        #print 'isometries', isometries, 'setup', setup
#        if isometries != None:
#            # TODO: add some asserts
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            keys = setup.keys()
#            if 'axis' in keys: axis = setup['axis']
#            else:              axis = this.defaultSetup['axis'][:]
#            if this.n != 0   : n = this.n
#            else:
#                if 'n' in keys: n = setup['n']
#                else:           n = this.defaultSetup['n']
#                if n == 0: n = 1
#                this.n = n
#
#            angle = 2 * math.pi / n
#            try:   r = GeomTypes.Rot3(axis = axis, angle = angle)
#            except TypeError:
#                # assume axis has Rot3 type
#                r = GeomTypes.Rot3(axis = axis.axis(), angle = angle)
#
#            isometries = [r]
#            for i in range(n-1):
#                isometries.append(r * isometries[-1])
#            Set.__init__(this, isometries)
#            this.order = n
#            this.rotAxes = {'n': axis}
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if isinstance(sg, MetaCn):
#            if sg.n == this.n: # Cn
#                return [this]
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif sg == E:
#            return [E()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
## dynamically create Cn classes:
#CnMetas = {}
#def C(n):
#    try:
#        return CnMetas[n]
#    except KeyError:
#        if n == 1:
#            CnMetas[n] = E
#        else:
#            C_n = MetaCn('C%d' % n, (Cn,),
#                    {
#                        'n'    : n,
#                        'order': n,
#                        'initPars': [{
#                                'type': 'vec3',
#                                'par': 'axis',
#                                'lab': "%d-fold axis" % n
#                            }],
#                        'defaultSetup': {'axis': Cn.defaultSetup['axis']}
#                    }
#                )
#            # TODO: fix subgroups depending on n:
#            C_n.subgroups = [C_n, E]
#            CnMetas[n] = C_n
#        return CnMetas[n]
#
#C2 = C(2)
#C3 = C(3)
#C4 = C(4)
#C5 = C(5)
#
#class MetaC2nCn(MetaCn):
#    def __init__(this, classname, bases, classdict):
#        type.__init__(this, classname, bases, classdict)
#class C2nCn(Cn):
#    __metaclass__ = MetaC2nCn
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group C2nCn, consisting of n rotations and of n rotary
#        inversions (reflections)
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
#        - n rotary inversions around one n-fold axis (angle: pi(1 + 2i)/n, with 
#          0 <= i < n)
#        """
#        #print 'isometries', isometries, 'setup', setup
#        if isometries != None:
#            # TODO: add some asserts
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            s = copy(setup)
#            if 'n' not in s and this.n != 0:
#                s['n'] = this.n
#            cn = Cn(setup = s)
#            this.n = cn.n
#            s['n'] = 2 * s['n']
#            c2n = Cn(setup = s)
#            Set.__init__(this, cn | ((c2n-cn) * GeomTypes.I))
#            this.rotAxes = {'n': cn.rotAxes['n']}
#            this.order = c2n.order
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if isinstance(sg, MetaC2nCn):
#            if sg.n == this.n: # C2cCn
#                return [this]
#            elif sg.n == 1: # C2C1 = {E, Reflection}
#                assert this.n % 2 == 1, 'Improper subgroup'
#                # only one orientation: reflection normal parallel to n-fold
#                # axis.
#                return [sg(setup = {'axis': this.rotAxes['n']})]
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif isinstance(sg, MetaCn):
#            if sg.n == this.n: # C2cCn
#                # only one orientation:
#                return [sg(setup = {'axis': this.rotAxes['n']})]
#            else:
#                TODO
#        elif sg == E:
#            return [E()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
## dynamically create C2nCn classes:
#C2nCnMetas = {}
#def C2nC(n):
#    try:
#        return C2nCnMetas[n]
#    except KeyError:
#        C_2n_C_n = MetaC2nCn('C%dC%d' % (2*n, n), (C2nCn,),
#                {
#                    'n'    : n,
#                    'order': 2 * n,
#                    'initPars': [{
#                            'type': 'vec3',
#                            'par': 'axis',
#                            'lab': "%d-fold axis" % n
#                        }],
#                    'defaultSetup': {'axis': C2nCn.defaultSetup['axis']}
#                }
#            )
#        C_2n_C_n.subgroups = [C_2n_C_n, C(n), E]
#        # Add subgroup {E, reflection}
#        if n % 2 == 1:
#            if n != 1:
#                C_2n_C_n.subgroups.insert(-1, C2C1)
#        # TODO: fix more subgroups depending on n, e.g.:
#        #else:
#        #    if n != 2:
#        #        C_2n_C_n.subgroups.insert(-2, C2nC(2))
#        C2nCnMetas[n] = C_2n_C_n
#        return C2nCnMetas[n]
#
#C2C1 = C2nC(1)
#C4C2 = C2nC(2)
#C6C3 = C2nC(3)
#C8C4 = C2nC(4)
#
#class MetaCnxI(MetaCn):
#    def __init__(this, classname, bases, classdict):
#        type.__init__(this, classname, bases, classdict)
#class CnxI(Cn):
#    __metaclass__ = MetaCnxI
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group CnxI, consisting of n rotations and of n rotary
#        inversions (reflections)
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
#        - n rotary inversions around one n-fold axis (angle: i * 2pi/n, with 
#          0 <= i < n)
#        """
#        #print 'isometries', isometries, 'setup', setup
#        if isometries != None:
#            # TODO: add some asserts
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            s = copy(setup)
#            if 'n' not in s and this.n != 0:
#                s['n'] = this.n
#            cn = Cn(setup = s)
#            this.n = cn.n
#            Set.__init__(this, cn * ExI())
#            this.rotAxes = {'n': cn.rotAxes['n']}
#            this.order = 2 * cn.order
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if isinstance(sg, MetaCnxI):
#            if sg.n == this.n: # CnxI
#                return [this]
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif isinstance(sg, MetaC2nCn):
#            if sg.n == 1: # C2C1
#                # only one orientation:
#                return [sg(setup = {'axis': this.rotAxes['n']})]
#            else:
#                TODO
#        elif isinstance(sg, MetaCn):
#            if sg.n == this.n: # Cn
#                # only one orientation:
#                return [sg(setup = {'axis': this.rotAxes['n']})]
#            else:
#                print sg, sg.n, this.n
#                TODO
#        elif sg == ExI:
#            return [ExI()]
#        elif sg == E:
#            return [E()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
## dynamically create CnxI classes:
#CnxIMetas = {}
#def CxI(n):
#    try:
#        return CnxIMetas[n]
#    except KeyError:
#        if n == 1:
#            CnxIMetas[n] = ExI
#        else:
#            C_nxI = MetaCnxI('C%dxI' % n, (CnxI,),
#                    {
#                        'n'    : n,
#                        'order': 2 * n,
#                        'initPars': [{
#                                'type': 'vec3',
#                                'par': 'axis',
#                                'lab': "%d-fold axis" % n
#                            }],
#                        'defaultSetup': {'axis': CnxI.defaultSetup['axis']}
#                    }
#                )
#            # TODO: fix subgroups depending on n:
#            C_nxI.subgroups = [C_nxI, C(n), C1xI, E]
#            # Add subgroup {E, reflection}
#            if n % 2 == 0:
#                if n != 0:
#                    C_nxI.subgroups.insert(-2, C2C1)
#            CnxIMetas[n] = C_nxI
#        return CnxIMetas[n]
#
#C1xI = ExI
#C2xI = CxI(2)
#C3xI = CxI(3)
#C4xI = CxI(4)
#C5xI = CxI(5)
#
#class MetaDnCn(MetaCn):
#    def __init__(this, classname, bases, classdict):
#        type.__init__(this, classname, bases, classdict)
#class DnCn(Cn):
#    __metaclass__ = MetaDnCn
#    initPars = [
#        {'type': 'int',  'par': 'n',    'lab': "order"},
#        {'type': 'vec3', 'par': 'axis_n', 'lab': "n-fold axis"},
#        {'type': 'vec3', 'par': 'normal_r', 'lab': "normal of reflection"}
#    ]
#    defaultSetup = {'n': 2, 'axis_n': Z[:], 'normal_r': X[:]}
#
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group DnCn, consisting of n rotations and of n rotary
#        inversions (reflections)
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
#        - n reflections in planes that share the n-fold axis.
#        """
#        #print 'isometries', isometries, 'setup', setup
#        if isometries != None:
#            # TODO: add some asserts
#            Set.__init__(this, isometries)
#        else:
#            s = {}
#            this.checkSetup(setup)
#            if 'n' not in setup:
#                if this.n != 0:
#                    s['n'] = this.n
#                else:
#                    s['n'] = this.defaultSetup['n']
#            else:
#                s['n'] = setup['n']
#            if 'axis_n' in setup:
#                s['axis'] = setup['axis_n']
#            else:
#                s['axis'] = this.defaultSetup['axis_n'][:]
#            cn = Cn(setup = s)
#            if 'normal_r' in setup:
#                s['axis_2'] = setup['normal_r']
#            else:
#                s['axis_2'] = this.defaultSetup['normal_r'][:]
#            s['axis_n'] = s['axis']
#            del s['axis']
#            dn = Dn(setup = s)
#            Set.__init__(this, cn | ((dn-cn) * GeomTypes.I))
#            this.n = s['n']
#            this.rotAxes = {'n': cn.rotAxes['n']}
#            this.reflNormals = dn.rotAxes[2]
#            this.order = dn.order
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if isinstance(sg, MetaDnCn):
#            if sg.n == this.n:
#                return [this]
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif isinstance(sg, MetaC2nCn):
#            if sg.n == 1: # C2C1
#                return [sg(setup = {'axis': rn}) for rn in this.reflNormals]
#            else:
#                TODO
#        elif isinstance(sg, MetaCn):
#            if sg.n == this.n:
#                return [sg(setup = {'axis': this.rotAxes['n']})]
#            else:
#                TODO
#        elif sg == E:
#            return [E()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
## dynamically create DnCn classes:
#DnCnMetas = {}
#def DnC(n):
#    try:
#        return DnCnMetas[n]
#    except KeyError:
#        if n == 1:
#            DnCnMetas[n] = C2C1
#        else:
#            D_n_C_n = MetaDnCn('D%dC%d' % (n, n), (DnCn,),
#                    {
#                        'n'    : n,
#                        'order': 2 * n,
#                        'initPars': [{
#                                'type': 'vec3',
#                                'par': 'axis_n',
#                                'lab': "%d-fold axis" % n
#                            }, {
#                                'type': 'vec3',
#                                'par': 'normal_r',
#                                'lab': "normal of reflection"
#                            }],
#                        'defaultSetup': {
#                                'axis_n': DnCn.defaultSetup['axis_n'],
#                                'normal_r': DnCn.defaultSetup['normal_r']
#                            }
#                    }
#                )
#            D_n_C_n.subgroups = [D_n_C_n, C(n), C2C1, E]
#            # TODO: fix more subgroups depending on n, e.g.:
#            DnCnMetas[n] = D_n_C_n
#        return DnCnMetas[n]
#
#D1C1 = DnC(1)
#D2C2 = DnC(2)
#D3C3 = DnC(3)
#D4C4 = DnC(4)
#D5C5 = DnC(5)
#
#class MetaDn(type):
#    def __init__(this, classname, bases, classdict):
#        type.__init__(this, classname, bases, classdict)
#class Dn(Set):
#    __metaclass__ = MetaDn
#    initPars = [
#        {'type': 'int',  'par': 'n',    'lab': "order"},
#        {'type': 'vec3', 'par': 'axis_n', 'lab': "n-fold axis"},
#        {'type': 'vec3', 'par': 'axis_2', 'lab': "axis of halfturn"}
#    ]
#    defaultSetup = {'n': 2, 'axis_n': Z[:], 'axis_2': X[:]}
#    order = 0
#    n = 0
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group Dn, consisting of 2n rotations
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
#        - n halfturns around axes perpendicular to the n-fold axis
#        """
#        #print 'isometries', isometries, 'setup', setup
#        if isometries != None:
#            # TODO: add some asserts
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            keys = setup.keys()
#            if 'axis_n' in keys: axis_n = setup['axis_n']
#            else:                axis_n = this.defaultSetup['axis_n'][:]
#            if 'axis_2' in keys: axis_2 = setup['axis_2']
#            else:                axis_2 = this.defaultSetup['axis_2'][:]
#            if this.n != 0     : n = this.n
#            else:
#                if 'n' in keys: n = setup['n']
#                else:           n = 2
#                if n == 0: n = 1
#
#            h = GeomTypes.HalfTurn3(axis_2)
#            cn = Cn(setup = {'axis': axis_n, 'n': n})
#            isometries = [isom for isom in cn]
#            hs = [isom * h for isom in cn]
#            #for isom in hs: print isom
#            isometries.extend(hs)
#            this.rotAxes = {'n': axis_n, 2: [h.axis() for h in hs]}
#            Set.__init__(this, isometries)
#            this.n     = n
#            this.order = 2 * n
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if isinstance(sg, MetaDn):
#            if sg.n == this.n:
#                return [this]
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif isinstance(sg, MetaCn):
#            if sg.n == this.n:
#                return [sg(setup = {'axis': this.rotAxes['n']})]
#            elif sg.n == 2: # sg = C2
#                isoms = [
#                    sg(setup = {'axis':this.rotAxes[2][i]})
#                    for i in range(len(this.rotAxes[2]))
#                ]
#                if this.n % 2 == 0: # if D2, D4, etc
#                    isoms.append(
#                        sg(setup = {'axis': this.rotAxes['n']})
#                    )
#                return isoms
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif sg == E:
#            return [E()]
#
## dynamically create Dn classes:
#DnMetas = {}
#def D(n):
#    try:
#        return DnMetas[n]
#    except KeyError:
#        if n == 1:
#            DnMetas[n] = C2
#        else:
#            D_n = MetaDn('D%d' % n, (Dn,),
#                    {
#                        'n'    : n,
#                        'order': 2 * n,
#                        'initPars': [
#                                {
#                                    'type': 'vec3',
#                                    'par': 'axis_n',
#                                    'lab': "%d-fold axis" % n
#                                }, {
#                                    'type': 'vec3',
#                                    'par': 'axis_2',
#                                    'lab': "axis of halfturn"
#                                }
#                            ],
#                        'defaultSetup': {
#                                'axis_n': Dn.defaultSetup['axis_n'],
#                                'axis_2': Dn.defaultSetup['axis_2']
#                            }
#                    }
#                )
#            # TODO: fix subgroups depending on n:
#            D_n.subgroups = [D_n, C2, E]
#            if n != 2:
#                D_n.subgroups.insert(-2, C(n))
#            DnMetas[n] = D_n
#        return DnMetas[n]
#
#D1 = D(1)
#D2 = D(2)
#D3 = D(3)
#D4 = D(4)
#D5 = D(5)
#
#class MetaDnxI(MetaDn):
#    def __init__(this, classname, bases, classdict):
#        type.__init__(this, classname, bases, classdict)
#class DnxI(Dn):
#    __metaclass__ = MetaDnxI
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group DnxI, of order 4n.
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
#        - n halfturns around axes perpendicular to the n-fold axis
#        - n rotary inversions around one n-fold axis (angle: i * 2pi/n, with
#          0 <= i < n). For n even one of these becomes a reflection in a plane
#          perpendicular to the n-fold axis.
#        - n reflections in planes that contain the n-fold axis. The normals of
#          the reflection planes are perpendicular to the halfturn axes.
#        """
#        #print 'isometries', isometries, 'setup', setup
#        if isometries != None:
#            # TODO: add some asserts
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            s = copy(setup)
#            if 'n' not in s and this.n != 0:
#                s['n'] = this.n
#            dn = Dn(setup = s)
#            Set.__init__(this, dn * ExI())
#            this.rotAxes = {'n': dn.rotAxes['n'], 2: dn.rotAxes[2][:]}
#            this.n     = dn.n
#            this.order = 2 * dn.order
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        #print 'realiseSubgroups', sgName
#        if isinstance(sg, MetaDnxI):
#            if sg.n == this.n:
#                return [this]
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif isinstance(sg, MetaDn):
#            if sg.n == this.n:
#                return [
#                    sg(setup = {
#                        'axis_n': this.rotAxes['n'],
#                        'axis_2': this.rotAxes[2][0]
#                    })
#                    # choosing other 2-fold axes leads essentially to the same.
#                ]
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif isinstance(sg, MetaDnCn):
#            if sg.n == this.n and this.n > 1: # DnCn
#                return [
#                    sg(setup = {'axis_n':this.rotAxes['n'],
#                            'normal_r': this.rotAxes[2][0]
#                        }
#                    )
#                ]
#            else:
#                TODO
#        elif isinstance(sg, MetaC2nCn):
#            if sg.n == 1: # C2C1: {E, Reflection}
#                isoms = [
#                    sg(setup = {'axis':this.rotAxes[2][i]})
#                    for i in range(len(this.rotAxes[2]))
#                ]
#                if this.n % 2 == 0: # if D2xI, D4xI, etc
#                    isoms.append(
#                        sg(setup = {'axis': this.rotAxes['n']})
#                    )
#                return isoms
#            else:
#                TODO
#        elif isinstance(sg, MetaCnxI) or type(sg) == MetaCn:
#            if sg.n == this.n:
#                return [sg(setup = {'axis': this.rotAxes['n']})]
#            elif sg.n == 2: # C2xI or C2
#                isoms = [
#                    sg(setup = {'axis':this.rotAxes[2][i]})
#                    for i in range(len(this.rotAxes[2]))
#                ]
#                if this.n % 2 == 0: # if D2xI, D4xI, etc
#                    isoms.append(sg(setup = {'axis': this.rotAxes['n']}))
#                return isoms
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif sg == ExI:
#            return [ExI()]
#        elif sg == E:
#            return [E()]
#        else: raise ImproperSubgroupError, '%s ! <= %s(%s)' % (
#                this.__class__.__name__, sg.__name__, sg.__class__.__name__)
#
## dynamically create DnxI classes:
#DnxIMetas = {}
#def DxI(n):
#    assert n != 0
#    try:
#        return DnxIMetas[n]
#    except KeyError:
#        if n == 1:
#            DnxIMetas[n] = C2xI
#        else:
#            D_nxI = MetaDnxI('D%dxI' % n, (DnxI,),
#                    {
#                        'n'    : n,
#                        'order': 4 * n,
#                        'initPars': [
#                                {
#                                    'type': 'vec3',
#                                    'par': 'axis_n',
#                                    'lab': "%d-fold axis" % n
#                                }, {
#                                    'type': 'vec3',
#                                    'par': 'axis_2',
#                                    'lab': "axis of halfturn"
#                                }
#                            ],
#                        'defaultSetup': {
#                                'axis_n': DnxI.defaultSetup['axis_n'],
#                                'axis_2': DnxI.defaultSetup['axis_2']
#                            }
#                    }
#                )
#            D_nxI.subgroups = [D_nxI, DnC(n), D(n), CxI(n), C2, C2C1, ExI, E]
#            if n != 2:
#                D_nxI.subgroups.insert(-4, C(n))
#            if n % 2 == 0:
#                D_nxI.subgroups.insert(-4, D2C2)
#            # TODO: fix more subgroups depending on n:
#            DnxIMetas[n] = D_nxI
#        return DnxIMetas[n]
#
#D1xI = DxI(1)
#D2xI = DxI(2)
#D3xI = DxI(3)
#D4xI = DxI(4)
#D5xI = DxI(5)
#
#class MetaD2nDn(MetaDn):
#    def __init__(this, classname, bases, classdict):
#        type.__init__(this, classname, bases, classdict)
#class D2nDn(Dn):
#    __metaclass__ = MetaD2nDn
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group D2nDn, consisting of n rotations, n half turns, n
#        rotary inversions (reflections) and n reflections.
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
#        - n halfturns around axes perpendicular to the n-fold axis
#        - n rotary inversions around one n-fold axis (angle: pi(1 + 2i)/n, with
#          0 <= i < n). For n odd one of these becomes a reflection in a plane
#          perpendicular to the n-fold axis.
#        - n reflections in planes that contain the n-fold axis. The normal of
#          the reflection planes lie in the middle between two halfturns.
#        """
#        #print 'isometries', isometries, 'setup', setup
#        if isometries != None:
#            # TODO: add some asserts
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            s = copy(setup)
#            if 'n' not in s and this.n != 0:
#                s['n'] = this.n
#            dn = Dn(setup = s)
#            this.n = dn.n
#            s['n'] = 2 * s['n']
#            d2n = Dn(setup = s)
#            Set.__init__(this, dn | ((d2n-dn) * GeomTypes.I))
#            this.rotAxes = dn.rotAxes
#            this.reflNormals = []
#            for isom in this:
#                if isom.isRefl():
#                    this.reflNormals.append(isom.planeN())
#            this.order = d2n.order
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if isinstance(sg, MetaD2nDn):
#            if sg.n == this.n: # D2cDn
#                return [this]
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif isinstance(sg, MetaDn):
#            if sg.n == this.n:
#                return [sg(setup = {'axis': this.rotAxes['n']})]
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif isinstance(sg, MetaDnCn):
#            if sg.n == this.n and this.n > 1: # DnCn
#                return [sg(setup = {'axis_n':this.rotAxes['n'],
#                        'normal_r': this.reflNormals[0]
#                    }
#                )]
#            else:
#                TODO
#        elif isinstance(sg, MetaC2nCn):
#            if sg.n == this.n: # D2nDn
#                return [sg(setup = {'axis': this.rotAxes['n']})]
#            elif sg.n == 1: # C2C1 = {E, Reflection}
#                isoms = [
#                    sg(setup = {'axis':this.reflNormals[i]})
#                    for i in range(len(this.reflNormals))
#                ]
#                # included in previous:
#                #if this.n % 2 == 1 and this.n > 1: # if D3xI, D5xI, etc
#                #    isoms.append(
#                #        sg(setup = {'axis': this.rotAxes['n']})
#                #    )
#                return isoms
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif isinstance(sg, MetaCn):
#            if sg.n == this.n:
#                return [sg(setup = {'axis': this.rotAxes['n']})]
#            elif sg.n > this.n:
#                return []
#            else:
#                TODO
#        elif sg == E:
#            return [E()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
## dynamically create C2nCn classes:
#D2nDnMetas = {}
#def D2nD(n):
#    assert n != 0
#    try:
#        return D2nDnMetas[n]
#    except KeyError:
#        D_2n_D_n = MetaD2nDn('D%dD%d' % (2*n, n), (D2nDn,),
#                {
#                    'n'    : n,
#                    'order': 4 * n,
#                    'initPars': [
#                            {
#                                'type': 'vec3',
#                                'par': 'axis_n',
#                                'lab': "%d-fold axis" % n
#                            }, {
#                                'type': 'vec3',
#                                'par': 'axis_2',
#                                'lab': "axis of halfturn"
#                            }
#                        ],
#                    'defaultSetup': {
#                            'axis_n': D2nDn.defaultSetup['axis_n'],
#                            'normal_r': D2nDn.defaultSetup['axis_2']
#                        }
#                }
#            )
#        D_2n_D_n.subgroups = [D_2n_D_n, DnC(n), D(n), C2nC(n), C(n), C2C1, E]
#        if n % 2 == 1 and n > 1:
#            D_2n_D_n.subgroups.insert(-2, D2C2)
#        # TODO: fix more subgroups depending on n, e.g.:
#        D2nDnMetas[n] = D_2n_D_n
#        return D2nDnMetas[n]
#
#D2D1 = D2nD(1)
#D4D2 = D2nD(2)
#D6D3 = D2nD(3)
#D8D4 = D2nD(4)
#
#class A4(Set):
#    initPars = [
#        {'type': 'vec3', 'par': 'o2axis0', 'lab': "half turn axis"},
#        {'type': 'vec3', 'par': 'o2axis1', 'lab': "half turn of orthogonal axis"}
#    ]
#    defaultSetup = {'o2axis0': X[:], 'o2axis1': Y[:]}
#    order = 12
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group A4, consisting of 12 rotations
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - the identity E, and 3 orthogonal halfturns
#        - 8 order 3 isometries.
#        The group can be generated by the axes of 2 half turns, but this will
#        not generate the group uniquely: There are 2 possibilities: the two
#        tetrahedra in a Stella Octagula. The order of the 2 axes of the 2 half
#        turns decides which position is obtained.
#        """
#        # A4 consists of:
#        # 1. A subgroup D2: E, and half turns H0, H1, H2
#        #print 'isometries', isometries, 'setup', setup
#        if isometries != None:
#            assert len(isometries) == this.order, "%d != %d" % (
#                                                this.order, len(isometries))
#            # TODO: more asserts?
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            axes = setup.keys()
#            if 'o2axis0' in axes: o2axis0 = setup['o2axis0']
#            else:                 o2axis0 = this.defaultSetup['o2axis0'][:]
#            if 'o2axis1' in axes: o2axis1 = setup['o2axis1']
#            else:                 o2axis1 = this.defaultSetup['o2axis1'][:]
#            d2 = generateD2(o2axis0, o2axis1)
#            H0, H1, H2 = d2
#            R1_1, R1_2, R2_1, R2_2, R3_1, R3_2, R4_1, R4_2 = generateA4O3(d2)
#
#            Set.__init__(this, [
#                    GeomTypes.E,
#                    H0, H1, H2,
#                    R1_1, R1_2, R2_1, R2_2, R3_1, R3_2, R4_1, R4_2
#                ])
#
#            this.rotAxes = {
#                    2: [H0.axis(), H1.axis(), H2.axis()],
#                    3: [R1_1.axis(), R2_1.axis(), R3_1.axis(), R4_1.axis()],
#                }
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if sg == A4:
#            return [this]
#        elif sg == D2:
#            o2a = this.rotAxes[2]
#            return [D2(setup = {'axis_n': o2a[0], 'axis_2': o2a[1]})]
#        elif sg == C2:
#            o2a = this.rotAxes[2]
#            return [C2(setup = {'axis': a}) for a in o2a]
#        elif sg == C3:
#            o3a = this.rotAxes[3]
#            return [C3(setup = {'axis': a}) for a in o3a]
#        elif sg == E:
#            return [E()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
## Dn = D2, (D1~C2)
## Cn = C3, C2
#A4.subgroups = [A4,
#        D2, # D1
#        C3, C2, E
#    ]
#
#class S4A4(A4):
#    order = 24
#
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group A4, consisting of 24 isometries, 12 direct, 12
#        opposite.
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - the identity E, and 3 orthogonal halfturns
#        - 8 order 3 isometries.
#        - 6 reflections
#        - 6 rotary inversions
#        The group can be generated by the axes of 2 half turns, but this will
#        not generate the group uniquely: There are 2 possibilities: the two
#        tetrahedra in a Stella Octagula. The order of the 2 axes of the 2 half
#        turns decides which position is obtained.
#        """
#        # A4 consists of:
#        # 1. A subgroup D2: E, and half turns H0, H1, H2
#        #print 'isometries', isometries, 'setup', setup
#        if isometries != None:
#            assert len(isometries) == this.order, "%d != %d" % (
#                                                this.order, len(isometries))
#            # TODO: more asserts?
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            axes = setup.keys()
#            if 'o2axis0' in axes: o2axis0 = setup['o2axis0']
#            else:                 o2axis0 = this.defaultSetup['o2axis0'][:]
#            if 'o2axis1' in axes: o2axis1 = setup['o2axis1']
#            else:                 o2axis0 = this.defaultSetup['o2axis1'][:]
#            d2 = generateD2(o2axis0, o2axis1)
#            h0, h1, h2 = d2
#            r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2 = generateA4O3(d2)
#
#            ax0 = h0.axis()
#            ax1 = h1.axis()
#            ax2 = h2.axis()
#            ri0_1 = GeomTypes.RotInv3(axis = ax0, angle = qTurn)
#            ri0_3 = GeomTypes.RotInv3(axis = ax0, angle = 3*qTurn)
#            ri1_1 = GeomTypes.RotInv3(axis = ax1, angle = qTurn)
#            ri1_3 = GeomTypes.RotInv3(axis = ax1, angle = 3*qTurn)
#            ri2_1 = GeomTypes.RotInv3(axis = ax2, angle = qTurn)
#            ri2_3 = GeomTypes.RotInv3(axis = ax2, angle = 3*qTurn)
#            pn0 = GeomTypes.Rot3(axis = ax0, angle = eTurn) * ax1
#            pn1 = GeomTypes.Rot3(axis = ax0, angle = 3*eTurn) * ax1
#            pn2 = GeomTypes.Rot3(axis = ax1, angle = eTurn) * ax0
#            pn3 = GeomTypes.Rot3(axis = ax1, angle = 3*eTurn) * ax0
#            pn4 = GeomTypes.Rot3(axis = ax2, angle = eTurn) * ax0
#            pn5 = GeomTypes.Rot3(axis = ax2, angle = 3*eTurn) * ax0
#            s0 = GeomTypes.Refl3(planeN = pn0)
#            s1 = GeomTypes.Refl3(planeN = pn1)
#            s2 = GeomTypes.Refl3(planeN = pn2)
#            s3 = GeomTypes.Refl3(planeN = pn3)
#            s4 = GeomTypes.Refl3(planeN = pn4)
#            s5 = GeomTypes.Refl3(planeN = pn5)
#            Set.__init__(this, [
#                    GeomTypes.E,
#                    h0, h1, h2,
#                    r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2,
#                    s0, s1, s2, s3, s4, s5,
#                    ri0_1, ri0_3, ri1_1, ri1_3, ri2_1, ri2_3,
#                ])
#
#            this.reflNormals = [pn0, pn1, pn2, pn3, pn4, pn5]
#            this.rotAxes = {
#                    2: [h0.axis(), h1.axis(), h2.axis()],
#                    3: [r1_1.axis(), r2_1.axis(), r3_1.axis(), r4_1.axis()],
#                }
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        #S4A4, A4, D2nDn, DnCn, C2nCn, Dn, Cn
#        #C3, C2, E
#        if sg == S4A4:
#            return [this]
#        elif sg == A4:
#            o2a = this.rotAxes[2]
#            return [sg(setup = {'o2axis0': o2a[0], 'o2axis1': o2a[1]})]
#        elif sg == D4D2:
#            o2a = this.rotAxes[2]
#            l = len(o2a)
#            return [sg(setup = {'axis_n': o2a[i], 'axis_2': o2a[(i+1)%l]})
#                    for i in range(l)
#                ]
#        elif sg == D3C3:
#            isoms = []
#            for o3 in this.rotAxes[3]:
#                for rn in this.reflNormals:
#                    if GeomTypes.eq(rn*o3, 0):
#                        isoms.append(sg(setup = {'axis_n': o3, 'normal_r': rn}))
#                        break
#            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
#            return isoms
#        elif sg == C4C2:
#            return [C4C2(setup = {'axis': a}) for a in this.rotAxes[2]]
#        elif sg == C3:
#            return [sg(setup = {'axis': a}) for a in this.rotAxes[3]]
#        elif sg == C2:
#            return [sg(setup = {'axis': a}) for a in this.rotAxes[2]]
#        elif sg == C2C1:
#            return [sg(setup = {'axis': normal}) for normal in this.reflNormals]
#        elif sg == E:
#            return [E()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
## Dn = D2, (D1~C2)
## Cn = C3, C2
## D2nDn = D4D2
## DnCn  = D3C3, D2C2
## C2nCn = C4C2, C2C1
## Diagram 1.
#S4A4.subgroups = [S4A4,
#        A4, D4D2, D3C3,
#        C4C2,
#        C3,
#        C2C1, C2,
#        E
#    ]
#
#class A4xI(A4):
#    order = 24
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group A4xI, consisting of 12 rotations and 12 rotary
#        inversions.
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - the identity E, and 3 orthogonal halfturns
#        - 8 order 3 rotations.
#        - the central inversion I, 3 reflections
#        - 8 order rotary inversions
#        The group can be generated by the axes of 2 half turns
#        """
#        if isometries != None:
#            assert len(isometries) == this.order, "%d != %d" % (
#                                                this.order, len(isometries))
#            # TODO: more asserts?
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            a4 = A4(setup = setup)
#            Set.__init__(this, a4 * ExI())
#            this.rotAxes = a4.rotAxes
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if sg == A4xI:
#            return [this]
#        elif sg == A4:
#            # other ways of orienting A4 into A4xI don't give anything new
#            return [ A4( setup = {
#                        'o2axis0': this.rotAxes[2][0],
#                        'o2axis1': this.rotAxes[2][1]
#                    }
#                )
#            ]
#        elif sg == D2xI:
#            o2a = this.rotAxes[2]
#            return [sg(setup = {'axis_n': o2a[0], 'axis_2': o2a[1]})]
#        elif sg == C3xI:
#            o3a = this.rotAxes[3]
#            return [sg(setup = {'axis': a}) for a in o3a]
#        elif sg == D2:
#            o2a = this.rotAxes[2]
#            return [sg(setup = {'axis_n': o2a[0], 'axis_2': o2a[1]})]
#        elif sg == D2C2:
#            isoms = []
#            for o2 in this.rotAxes[2]:
#                for rn in this.rotAxes[2]:
#                    if GeomTypes.eq(rn*o2, 0):
#                        isoms.append(sg(setup = {'axis_n': o2, 'normal_r': rn}))
#                        break
#            assert len(isoms) == 3, 'len(isoms) == %d != 3' % len(isoms)
#            return isoms
#        if sg == C2xI:
#            o2a = this.rotAxes[2]
#            return [sg(setup = {'axis': a}) for a in o2a]
#        elif sg == C3:
#            o3a = this.rotAxes[3]
#            return [sg(setup = {'axis': a}) for a in o3a]
#        elif sg == C2:
#            o2a = this.rotAxes[2]
#            return [sg(setup = {'axis': a}) for a in o2a]
#        elif sg == C2C1:
#            o2a = this.rotAxes[2]
#            return [sg(setup = {'axis': a}) for a in o2a]
#        elif sg == ExI:
#            return [sg()]
#        elif sg == E:
#            return [sg()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
## Diagram 4, 14
## 24            A4xI
##            _.-'| |'-._
##         .-'    | |    '-._
## 12     A4      |  \       '-.._
##         |\     |   |           '-._
##  8      | |    |   |               D2xI
##         | \    |    \         ____/ |
##  6      |  |  C3xI   |   to D2      |
##         |  \   /\    |              |
##  4     D2   | /  | D2C2      __----C2xI
##         |   \/  to   |  to C2  _.--'|
##  3      |   C3  ExI  |     _.-'     |
##         |   |        | _.-'         |
##  2     C2   |      C2C1          __ExI
##         '-._|__..--' ____....''''
##  1          E----''''
#A4xI.subgroups = [A4xI, A4,
#        D2xI, C3xI,
#        D2, D2C2, C2xI,
#        C3,
#        C2, C2C1, ExI, E
#    ]
#
#class S4(Set):
#    initPars = [
#        {'type': 'vec3', 'par': 'o4axis0', 'lab': "4-fold axis"},
#        {'type': 'vec3', 'par': 'o4axis1', 'lab': "orthogonal 4-fold axis"}
#    ]
#    defaultSetup = {'o4axis0': X[:], 'o4axis1': Y[:]}
#    order = 24
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group S4, consisting of 24 rotations
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - the identity E,
#        - and 9 orthogonal turns based on quarter turns (1/4, 1/2, 3/4)
#        - 8 turns based on third turns (1/3, 2/3).
#        - 6 halfturns
#        The group can be generated by the axes of 2 quarter turns,
#        """
#        if isometries != None:
#            assert len(isometries) == this.order, "%d != %d" % (
#                                                this.order, len(isometries))
#            # TODO: more asserts?
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            axes = setup.keys()
#            if 'o4axis0' in axes: o4axis0 = setup['o4axis0']
#            else:                 o4axis0 = this.defaultSetup['o4axis0'][:]
#            if 'o4axis1' in axes: o4axis1 = setup['o4axis1']
#            else:                 o4axis1 = this.defaultSetup['o4axis1'][:]
#            d2 = generateD2(o4axis0, o4axis1)
#            r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2 = generateA4O3(d2)
#            q0_2, q1_2, q2_2 = d2
#            ax0 = q0_2.axis()
#            ax1 = q1_2.axis()
#            ax2 = q2_2.axis()
#            q0_1 = GeomTypes.Rot3(axis = ax0, angle = qTurn)
#            q0_3 = GeomTypes.Rot3(axis = ax0, angle = 3*qTurn)
#            q1_1 = GeomTypes.Rot3(axis = ax1, angle = qTurn)
#            q1_3 = GeomTypes.Rot3(axis = ax1, angle = 3*qTurn)
#            q2_1 = GeomTypes.Rot3(axis = ax2, angle = qTurn)
#            q2_3 = GeomTypes.Rot3(axis = ax2, angle = 3*qTurn)
#            h0 = GeomTypes.Rot3(
#                    axis = GeomTypes.Rot3(axis = ax0, angle = eTurn) * ax1,
#                    angle = hTurn
#                )
#            h1 = GeomTypes.Rot3(
#                    axis = GeomTypes.Rot3(axis = ax0, angle = 3*eTurn) * ax1,
#                    angle = hTurn
#                )
#            h2 = GeomTypes.Rot3(
#                    axis = GeomTypes.Rot3(axis = ax1, angle = eTurn) * ax0,
#                    angle = hTurn
#                )
#            h3 = GeomTypes.Rot3(
#                    axis = GeomTypes.Rot3(axis = ax1, angle = 3*eTurn) * ax0,
#                    angle = hTurn
#                )
#            h4 = GeomTypes.Rot3(
#                    axis = GeomTypes.Rot3(axis = ax2, angle = eTurn) * ax0,
#                    angle = hTurn
#                )
#            h5 = GeomTypes.Rot3(
#                    axis = GeomTypes.Rot3(axis = ax2, angle = 3*eTurn) * ax0,
#                    angle = hTurn
#                )
#            Set.__init__(this, [
#                    GeomTypes.E,
#                    q0_1, q0_2, q0_3, q1_1, q1_2, q1_3, q2_1, q2_2, q2_3,
#                    r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2,
#                    h0, h1, h2, h3, h4, h5
#                ])
#            this.rotAxes = {
#                    2: [h0.axis(), h1.axis(), h2.axis(),
#                            h3.axis(), h4.axis(), h5.axis()
#                        ],
#                    3: [r1_1.axis(), r2_1.axis(), r3_1.axis(), r4_1.axis()],
#                    4: [ax0, ax1, ax2]
#                }
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if sg == S4:
#            return [this]
#        elif sg == A4:
#            # other ways of orienting A4 into S4 don't give anything new
#            return [
#                A4(
#                    setup = {
#                        'o2axis0': this.rotAxes[4][0],
#                        'o2axis1': this.rotAxes[4][1]
#                    }
#                )
#            ]
#        elif sg == D4:
#            o4a = this.rotAxes[4]
#            l = len(o4a)
#            return [sg(
#                    setup = {'axis_n': o4a[i], 'axis_2': o4a[(i+1)%l]}
#                ) for i in range(l)
#            ]
#        elif sg == D3:
#            isoms = []
#            for o3 in this.rotAxes[3]:
#                for o2 in this.rotAxes[2]:
#                    if GeomTypes.eq(o2*o3, 0):
#                        isoms.append(sg(setup = {'axis_n': o3, 'axis_2': o2}))
#                        break
#            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
#            return isoms
#        elif sg == D2:
#            isoms = []
#            # There are 2 kinds of D2:
#            # 1. one consisting of the three 4-fold axes
#            # 2. 3 consisting of a 4 fold axis and two 2-fold axes.
#            o4a = this.rotAxes[4]
#            l = len(o4a)
#            isoms = [sg(setup = {'axis_n': o4a[0], 'axis_2': o4a[1]})]
#            for o4 in this.rotAxes[4]:
#                for o2 in this.rotAxes[2]:
#                    if GeomTypes.eq(o2*o4, 0):
#                        isoms.append(sg(setup = {'axis_n': o4, 'axis_2': o2}))
#                        break
#            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
#            return isoms
#        elif sg == C4:
#            o4a = this.rotAxes[4]
#            return [sg(setup = {'axis': a}) for a in o4a]
#        elif sg == C3:
#            o3a = this.rotAxes[3]
#            return [sg(setup = {'axis': a}) for a in o3a]
#        elif sg == C2:
#            o4a = this.rotAxes[4]
#            isoms = [sg(setup = {'axis': a}) for a in o4a]
#            o2a = this.rotAxes[2]
#            isoms.extend([sg(setup = {'axis': a}) for a in o2a])
#            return isoms
#        elif sg == E:
#            return [E()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
## Dn = D4, D3, D2 (2x), D1 (~C2)
## Cn = C4, C3, C2 (2x @ 2-fold and 4-fold axes)
#S4.subgroups = [S4, A4,
#        D4, D3,
#        D2, C4,
#        C3,
#        C2,
#        E
#    ]
#
#class S4xI(S4):
#    order = 48
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group S4xI, consisting of 12 rotations and 12 rotary
#        inversions.
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - the identity E,
#        - and 9 orthogonal turns based on quarter turns (1/4, 1/2, 3/4)
#        - 8 turns based on third turns (1/3, 2/3).
#        - 6 halfturns
#        - the central inversion I
#        - 6 rotary inversions, derived from the 6 quarter turns.
#        - 8 rotary inversions, derived from the 8 third turns.
#        - 9 reflections, of which 6 are based on (ie orthogonal to) the 2 fold
#          axes and 3 on the 4-fold axes.
#        The group can be generated by the axes of 2 quarter turns,
#        """
#        if isometries != None:
#            assert len(isometries) == this.order, "%d != %d" % (
#                                                this.order, len(isometries))
#            # TODO: more asserts?
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            s4 = S4(setup = setup)
#            Set.__init__(this, s4 * ExI())
#            this.rotAxes = s4.rotAxes
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if sg == S4xI:
#            return [this]
#        elif sg == S4:
#            # other ways of orienting S4 into S4xI don't give anything new
#            return [ sg( setup = {
#                        'o4axis0': this.rotAxes[4][0],
#                        'o4axis1': this.rotAxes[4][1]
#                    }
#                )
#            ]
#        elif sg == A4xI or sg == A4 or sg == S4A4:
#            return [ sg( setup = {
#                        'o2axis0': this.rotAxes[4][0],
#                        'o2axis1': this.rotAxes[4][1]
#                    }
#                )
#            ]
#        elif sg == D4xI or sg == D8D4 or sg == D4:
#            o4a = this.rotAxes[4]
#            l = len(o4a)
#            return [sg(
#                    setup = {'axis_n': o4a[i], 'axis_2': o4a[(i+1)%l]}
#                ) for i in range(l)
#            ]
#        elif sg == D3xI or sg == D3:
#            isoms = []
#            for o3 in this.rotAxes[3]:
#                for o2 in this.rotAxes[2]:
#                    if GeomTypes.eq(o2*o3, 0):
#                        isoms.append(sg(setup = {'axis_n': o3, 'axis_2': o2}))
#                        break
#            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
#            return isoms
#        elif sg == D4C4:
#            isoms = []
#            for a4 in this.rotAxes[4]:
#                for rn in this.rotAxes[2]:
#                    if GeomTypes.eq(rn*a4, 0):
#                        isoms.append(sg(setup = {'axis_n': a4, 'normal_r': rn}))
#                        break
#            return isoms
#        elif sg == D4D2:
#            o4a = this.rotAxes[4]
#            l = len(o4a)
#            isoms = [sg(setup = {'axis_n': o4a[i], 'axis_2': o4a[(i+1)%l]})
#                    for i in range(l)
#                ]
#            o2a = this.rotAxes[2]
#            for a4 in o4a:
#                for a2 in o2a:
#                    if GeomTypes.eq(a2*a4, 0):
#                        isoms.append(sg(setup = {'axis_n': a4, 'axis_2': a2}))
#                        break
#            return isoms
#        elif sg == D2xI or sg == D2:
#            o4a = this.rotAxes[4]
#            isoms = [sg(setup = {'axis_n': o4a[0], 'axis_2': o4a[1]})]
#            o2a = this.rotAxes[2]
#            for a4 in o4a:
#                for a2 in o2a:
#                    if GeomTypes.eq(a2*a4, 0):
#                        isoms.append(sg(setup = {'axis_n': a4, 'axis_2': a2}))
#                        break
#            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
#            return isoms
#        elif sg == D3C3:
#            isoms = []
#            for o3 in this.rotAxes[3]:
#                for rn in this.rotAxes[2]:
#                    if GeomTypes.eq(rn*o3, 0):
#                        isoms.append(sg(setup = {'axis_n': o3, 'normal_r': rn}))
#                        break
#            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
#            return isoms
#        elif sg == C3xI or sg == C3:
#            o3a = this.rotAxes[3]
#            return [sg(setup = {'axis': a}) for a in o3a]
#        elif sg == D2C2:
#            o4a = this.rotAxes[4]
#            l = len(o4a)
#            isoms = [sg(setup = {'axis_n': o4a[i], 'normal_r': o4a[(i+1)%l]})
#                    for i in range(l)
#                ]
#            o2a = this.rotAxes[2]
#            for a4 in o4a:
#                for a2 in o2a:
#                    if GeomTypes.eq(a2*a4, 0):
#                        isoms.append(sg(setup = {'axis_n': a4, 'normal_r': a2}))
#                        break
#            for o2 in this.rotAxes[2]:
#                for rn in this.rotAxes[4]:
#                    if GeomTypes.eq(rn*o2, 0):
#                        isoms.append(sg(setup = {'axis_n': o2, 'normal_r': rn}))
#                        break
#            assert len(isoms) == 12, 'len(isoms) == %d != 12' % len(isoms)
#            return isoms
#        elif sg == C4xI or sg == C4 or sg == C4C2:
#            o4a = this.rotAxes[4]
#            return [sg(setup = {'axis': a}) for a in o4a]
#        elif sg == C2xI or sg == D1xI or sg == C2 or sg == D1:
#            o2a = this.rotAxes[4]
#            o2a.extend(this.rotAxes[2])
#            return [sg(setup = {'axis': a}) for a in o2a]
#        elif sg == C2C1:
#            isoms = [sg(setup = {'axis': a}) for a in this.rotAxes[2]]
#            isoms.extend([sg(setup = {'axis': a}) for a in this.rotAxes[4]])
#            return isoms
#        elif sg == ExI:
#            return [sg()]
#        elif sg == E:
#            return [sg()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
#S4xI.subgroups = [S4xI,                 # 48
#        S4, S4A4, A4xI,                 # 24
#        D4xI,                           # 18
#        D8D4,                           # 16
#        A4, D3xI,                       # 12
#        D4D2, D2xI, D4, C4xI, D4C4,     #  8
#        D3, D3C3, C3xI,                 #  6
#        D2, D2C2, C2xI, C4, C4C2,       #  4
#        C3,                             #  3
#        C2, C2C1, ExI,                  #  2
#        E
#    ]
#
#def generateD2(o2axis0, o2axis1):
#    """
#    Returns 3 orthogonal halfturns for D2
#    """
#    # if axes is specified as a transform:
#    if isinstance(o2axis0, GeomTypes.Transform3):
#        o2axis0 = o2axis0.axis()
#    if isinstance(o2axis1, GeomTypes.Transform3):
#        o2axis1 = o2axis1.axis()
#    assert GeomTypes.eq(GeomTypes.Vec3(o2axis0) * GeomTypes.Vec3(o2axis1), 0), (
#            "Error: axes not orthogonal")
#    H0 = GeomTypes.HalfTurn3(o2axis0)
#    H1 = GeomTypes.Rot3(axis = o2axis1, angle = hTurn)
#    return (H0, H1, H1 * H0)
#
#def generateA4O3(D2HalfTurns):
#    """
#    Returns a tuple (R1_1_3, R1_2_3, R2_1_3, R2_2_3, R3_1_3, R3_2_3, R4_1_3,
#    R4_2_3)
#
#    D2HalfTurns: tuple containing H0, H1, H2
#    """
#    H0, H1, H2 = D2HalfTurns
#
#    # the one order 3 rotation axis, is obtained as follows:
#    # imagine A4 is part of S4 positioned in a cube
#    # H0, H1, H2 go through the cube face centres
#    # define a quarter turn around H2
#    Q = GeomTypes.Rot3(axis = H2.axis(), angle = qTurn)
#    # h0 and h1 go through cube edge centres
#    h0 = Q * H0
#    h1 = Q * H1
#    # o3axis goes through 1 of the 2 cube vertices that form the edge
#    # between the faces which centres are on H0 and H1
#    o3axis = GeomTypes.Rot3(
#            axis = h0.axis(), angle = asin_1_V3
#        ) * h1.axis()
#    # R1_1_3: 1/3 rotation around the first order 3 axis
#    # R1_2_3: 2/3 rotation around the first order 3 axis
#    R1_1_3 = GeomTypes.Rot3(axis = o3axis, angle = tTurn)
#    R1_2_3 = GeomTypes.Rot3(axis = o3axis, angle = 2*tTurn)
#    R4_1_3 = R1_1_3 * H0
#    R3_1_3 = R1_1_3 * H1
#    R2_1_3 = R1_1_3 * H2
#    R2_2_3 = R1_2_3 * H0
#    R4_2_3 = R1_2_3 * H1
#    R3_2_3 = R1_2_3 * H2
#    # print 'R1_1_3', R1_1_3
#    # print 'R1_2_3', R1_2_3
#    # print 'R2_1_3', R2_1_3
#    # print 'R2_2_3', R2_2_3
#    # print 'R3_1_3', R3_1_3
#    # print 'R3_2_3', R3_2_3
#    # print 'R4_1_3', R4_1_3
#    # print 'R5_2_3', R4_2_3
#    return (R1_1_3, R1_2_3, R2_1_3, R2_2_3, R3_1_3, R3_2_3, R4_1_3, R4_2_3)
#
#class A5(Set):
#    initPars = [
#        {'type': 'vec3', 'par': 'o3axis', 'lab': "3-fold axis"},
#        {'type': 'vec3', 'par': 'o5axis', 'lab': "5-fold axis (nearest)"}
#    ]
#    defaultSetup = {
#        'o3axis': GeomTypes.Vec3([1, 1, 1]),
#        'o5axis': GeomTypes.Vec3([0, (1.0 + math.sqrt(5))/2, 1])
#    }
#    order = 60
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group A5, consisting of 60 rotations
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - the identity E,
#        - 24 turns based on the  6  5-fold turns (1/5, 2/5, 3/5, 4/5)
#        - 20 turns based on the 10  3-fold turns (1/3, 2/3)
#        - 15 halfturns
#        The group can be generated by the axes of 2 quarter turns,
#        """
#        if isometries != None:
#            assert len(isometries) == this.order, "%d != %d" % (
#                                                this.order, len(isometries))
#            # TODO: more asserts?
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            axes = setup.keys()
#            if 'o3axis' in axes: o3axis = setup['o3axis']
#            else: o3axis = this.defaultSetup['o3axis'][:]
#            if 'o5axis' in axes: o5axis = setup['o5axis']
#            else: o5axis = this.defaultSetup['o5axis'][:]
#
#            turn5 = 2 * math.pi / 5
#            turn3 = 2 * math.pi / 3
#            R0_1_5 = GeomTypes.Rot3(axis = o5axis, angle = turn5)
#            R0_1_3 = GeomTypes.Rot3(axis = o3axis, angle = turn3)
#            o3axes = [o3axis]                           # o3[0]
#            o5axes = [R0_1_3 * o5axis]                  # o5[0]
#            for i in range(4):
#                o3axes.append(R0_1_5 * o3axes[-1])      # o3[1:5]
#                o5axes.append(R0_1_5 * o5axes[-1])      # o5[1:5]
#            o5axes.append(o5axis)                       # o5[5] ... done
#            o2axes = [
#                    (o5axis + o5axes[i]) / 2
#                    for i in range(5)
#                ]                                       # o2[0:5]
#            o2axes.extend([
#                    (o5axes[i] + o5axes[(i+4) % 5]) / 2
#                    for i in range(5)
#                ])                                      # o2[5:10]
#            o3axes.extend([
#                    GeomTypes.HalfTurn3(axis = o2axes[i+5]) * o3axes[i]
#                    for i in range(5)
#                ])                                      # o3[5:10] ... done
#            o2axes.extend([
#                    GeomTypes.HalfTurn3(axis = o2axes[i]) * o2axes[(i+2) % 5]
#                    for i in range(5)
#                ])                                      # o2[10:15] ... done
#            transforms = [GeomTypes.E]
#            for a in o5axes:
#                transforms.extend([
#                    GeomTypes.Rot3(axis = a, angle = i * turn5)
#                    for i in range(1, 5)
#                ])
#            for a in o3axes:
#                transforms.extend([
#                    GeomTypes.Rot3(axis = a, angle = i * turn3)
#                    for i in range(1, 3)
#                ])
#
##        ___---.__
##      .L     / \_""__
##     /  \ _14 9  \   "\
##  10/ 5  4----9___|_13-.
##   /  5/  \  4    3  8 |
##   |/"  0  4   3-" \  /
##   0__     \_-"  3  8 |
##   \  "0--_5__       \/
##    \      |  ""2--__2
##     \_ 1  1   2  _.-" <--- o2_e12
##    _ 6\_   |  _7" __
##    /|   "-_1-"    |\
##   6     ^           7
##         |
##       o2_11
#
#            transforms.extend([GeomTypes.HalfTurn3(axis = a) for a in o2axes])
#            Set.__init__(this, transforms)
#            #for i in range(len(transforms)):
#            #    print 'transform %d: %s' % (i, transforms[i])
#            this.rotAxes = { 2: o2axes, 3: o3axes, 5: o5axes }
#            #for i in range(len(this.rotAxes[2])):
#            #    print i, this.rotAxes[2][i]
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if sg == A5:
#            return [this]
#        elif sg == A4:
#            return [
#                # Essentially these lead to 3 different colourings, of which 2
#                # pairs are mirrors images.
#                sg(setup = {
#                    'o2axis0': this.rotAxes[2][i],
#                    'o2axis1': this.rotAxes[2][((i+3) % 5) + 5]
#                })
#                for i in range(5)
#            ]
#        elif sg == D5:
#            isoms = [
#                sg(setup = {
#                    'axis_n': this.rotAxes[5][i],
#                    'axis_2': this.rotAxes[2][(i+2) % 5]
#                })
#                for i in range(5)
#            ]
#            isoms.append(
#                sg(setup = {
#                    'axis_n': this.rotAxes[5][5],
#                    'axis_2': this.rotAxes[2][10]
#                })
#            )
#            return isoms
#        elif sg == D3:
#            isoms = [
#                sg(setup = {
#                    'axis_n': this.rotAxes[3][i],
#                    'axis_2': this.rotAxes[2][((i+3) % 5) + 5]
#                })
#                for i in range(5)
#            ]
#            isoms.extend([
#                sg(setup = {
#                    'axis_n': this.rotAxes[3][i + 5],
#                    'axis_2': this.rotAxes[2][(i+3) % 5]
#                })
#                for i in range(5)
#            ])
#            return isoms
#        elif sg == D2:
#            return [
#                sg(setup = {
#                    'axis_n': this.rotAxes[2][i],
#                    'axis_2': this.rotAxes[2][((i+3) % 5) + 5]
#                })
#                for i in range(5)
#            ]
#        elif sg == C5:
#            return [ sg(setup = {'axis': a}) for a in this.rotAxes[5] ]
#        elif sg == C3:
#            return [ sg(setup = {'axis': a}) for a in this.rotAxes[3] ]
#        elif sg == C2:
#            return [ sg(setup = {'axis': a}) for a in this.rotAxes[2] ]
#        elif sg == E:
#            return [sg()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
## Diagram 15
#A5.subgroups = [A5,
#        A4,     # 12
#        D5,     # 10
#        D3,     #  6
#        C5,     #  5
#        D2,     #  4
#        C3,     #  3
#        C2,     #  2
#        E
#    ]
#
#class A5xI(A5):
#    order = 120
#    def __init__(this, isometries = None, setup = {}):
#        """
#        The algebraic group A5xI, which is the complete symmetry of an
#        icosahedron, It consists of 120 isometries.
#
#        either provide the complete set or provide setup that generates
#        the complete group. For the latter see the class initPars argument.
#        Contains:
#        - the identity E,
#        - 24 turns based on the  6  5-fold turns (1/5, 2/5, 3/5, 4/5)
#        - 20 turns based on the 10  3-fold turns (1/3, 2/3)
#        - 15 halfturns
#        - the central inversion I
#        - 24 rotary inversions based on the  6  5-fold axes (1/5, 2/5, 3/5, 4/5)
#        - 20 rotary inversions based on the 10  3-fold axes (1/3, 2/3)
#        - 15 reflections
#        """
#        if isometries != None:
#            assert len(isometries) == this.order, "%d != %d" % (
#                                                this.order, len(isometries))
#            # TODO: more asserts?
#            Set.__init__(this, isometries)
#        else:
#            this.checkSetup(setup)
#            a5 = A5(setup = setup)
#            Set.__init__(this, a5 * ExI())
#            this.rotAxes = a5.rotAxes
#
#    def realiseSubgroups(this, sg):
#        """
#        realise an array of possible oriented subgroups for non-oriented sg
#        """
#        assert isinstance(sg, type)
#        if sg == A5xI:
#            return [this]
#        elif sg == A5:
#            # other ways of orienting A5 into A5xI don't give anything new
#            return [ sg( setup = {
#                        'o3axis': this.rotAxes[3][0],
#                        'o5axis': this.rotAxes[5][0]
#                    }
#                )
#            ]
#        elif sg == A4xI or sg == S4A4 or sg == A4:
#            return [
#                # Essentially these lead to 3 different colourings, of which 2
#                # pairs are mirrors images. For A4xI the mirrors should lead to
#                # to equal solutions.
#                sg(setup = {
#                    'o2axis0': this.rotAxes[2][i],
#                    'o2axis1': this.rotAxes[2][((i+3) % 5) + 5]
#                })
#                for i in range(5)
#            ]
#        elif sg == D5xI or sg == D5:
#            isoms = [
#                sg(setup = {
#                    'axis_n': this.rotAxes[5][i],
#                    'axis_2': this.rotAxes[2][(i+2) % 5]
#                })
#                for i in range(5)
#            ]
#            isoms.append(
#                sg(setup = {
#                    'axis_n': this.rotAxes[5][5],
#                    'axis_2': this.rotAxes[2][10]
#                })
#            )
#            return isoms
#        elif sg == D5C5:
#            isoms = [
#                sg(setup = {
#                    'axis_n': this.rotAxes[5][i],
#                    'normal_r': this.rotAxes[2][(i+2) % 5]
#                })
#                for i in range(5)
#            ]
#            isoms.append(
#                sg(setup = {
#                    'axis_n': this.rotAxes[5][5],
#                    'normal_r': this.rotAxes[2][10]
#                })
#            )
#            return isoms
#        elif sg == D3xI or sg == D3:
#            isoms = [
#                sg(setup = {
#                    'axis_n': this.rotAxes[3][i],
#                    'axis_2': this.rotAxes[2][((i+3) % 5) + 5]
#                })
#                for i in range(5)
#            ]
#            isoms.extend([
#                sg(setup = {
#                    'axis_n': this.rotAxes[3][i + 5],
#                    'axis_2': this.rotAxes[2][(i+3) % 5]
#                })
#                for i in range(5)
#            ])
#            return isoms
#        elif sg == D3C3:
#            isoms = [
#                sg(setup = {
#                    'axis_n': this.rotAxes[3][i],
#                    'normal_r': this.rotAxes[2][((i+3) % 5) + 5]
#                })
#                for i in range(5)
#            ]
#            isoms.extend([
#                sg(setup = {
#                    'axis_n': this.rotAxes[3][i + 5],
#                    'normal_r': this.rotAxes[2][(i+3) % 5]
#                })
#                for i in range(5)
#            ])
#            return isoms
#        elif sg == D2xI or sg == D2:
#            return [
#                sg(setup = {
#                    'axis_n': this.rotAxes[2][i],
#                    'axis_2': this.rotAxes[2][((i+3) % 5) + 5]
#                })
#                for i in range(5)
#            ]
#        elif sg == D2C2:
#            return [
#                sg(setup = {
#                    'axis_n': this.rotAxes[2][i],
#                    'normal_r': this.rotAxes[2][((i+3) % 5) + 5]
#                })
#                for i in range(5)
#            ]
#        elif sg == C5xI or sg == C5:
#            return [ sg(setup = {'axis': a}) for a in this.rotAxes[5] ]
#        elif sg == C3xI or sg == C3:
#            return [ sg(setup = {'axis': a}) for a in this.rotAxes[3] ]
#        elif sg == C2xI or sg == C2 or sg == C2C1 or sg == D1xI or sg == D1:
#            return [ sg(setup = {'axis': a}) for a in this.rotAxes[2] ]
#        elif sg == ExI:
#            return [sg()]
#        elif sg == E:
#            return [sg()]
#        else: raise ImproperSubgroupError, '%s ! <= %s' % (
#                this.__class__.__name__, sg.__class__.__name__)
#
#A5xI.subgroups = [A5xI,                 # 120
#        A5,                             #  60
#        A4xI, S4A4,                     #  24
#        D5xI,                           #  20
#        A4, D3xI,                       #  12
#        D5, D5C5, C5xI,                 #  10
#        D3, D3C3, C3xI,                 #   6
#        C5,                             #   5
#        D2, D2C2, C2xI,                 #   4
#        C3,                             #   3
#        C2, C2C1, ExI,                  #   2
#        E
#    ]
#
#def order(isometry):
#    return isometry.order
#
#Cn.subgroups = [Cn, E]
#CnxI.subgroups = [CnxI, Cn, ExI, E]
#C2nCn.subgroups = [C2nCn, Cn, E]
#Dn.subgroups = [Dn, Cn, C2, E]
#DnxI.subgroups = [DnxI, Dn, CnxI, Cn, C2xI, C2, ExI, E]
#
#if __name__ == '__main__':
#
#    print 'testing creation of set',
#    g = Set([Hx, Hy])
#    print '....ok'
#    #print 'Initialised set g:', g
#    print "testing 'in' relation",
#    assert GeomTypes.Rot3(axis = [1, 0, 0], angle = hTurn) in g
#    assert GeomTypes.Rot3(axis = [-1, 0, 0], angle = -hTurn) in g
#    print '......ok'
#    print "testing 'close' function",
#    cg = g.close()
#    #print 'Set g after closing:'
#    #print cg
#    assert len(cg) == 4
#    assert Hx in cg
#    assert Hy in cg
#    assert Hz in cg
#    assert GeomTypes.E in cg
#    print '...ok'
#
#    print 'testing creation of set',
#    g = Set([GeomTypes.Rot3(axis = X, angle = qTurn)])
#    print '....ok'
#    print "testing 'in' relation",
#    GeomTypes.Rot3(axis =  X, angle = qTurn)  in g
#    GeomTypes.Rot3(axis = -X, angle = -qTurn) in g
#    print '......ok'
#    print "testing 'close' function",
#    cg = g.close()
#    #print 'Set g after closing:'
#    #print cg
#    assert len(cg) == 4
#    GeomTypes.Rot3(axis =  GeomTypes.Vec3([1, 0, 0]), angle = qTurn)  in cg
#    GeomTypes.Rot3(axis = -GeomTypes.Vec3([1, 0, 0]), angle = -qTurn) in cg
#    assert Hx in cg
#    assert GeomTypes.E in cg
#    print '...ok'
#
#    print 'testing creation of A4',
#    a4 = A4(setup = setup(o2axis0 = X, o2axis1= Y))
#    print '.....ok'
#    print 'checking result',
#    assert len(a4) == 12
#    assert GeomTypes.E in a4
#    assert Hx in a4
#    assert Hy in a4
#    assert Hz in a4
#    t0 = GeomTypes.Rot3(axis = [1,  1,  1], angle =   tTurn)
#    assert t0 in a4
#    t1 = GeomTypes.Rot3(axis = [1,  1,  1], angle = 2*tTurn)
#    assert t1 in a4
#    t2 = GeomTypes.Rot3(axis = [1, -1,  1], angle =   tTurn)
#    assert t2 in a4
#    t3 = GeomTypes.Rot3(axis = [1, -1,  1], angle = 2*tTurn)
#    assert t3 in a4
#    t4 = GeomTypes.Rot3(axis = [1, -1, -1], angle =   tTurn)
#    assert t4 in a4
#    t5 = GeomTypes.Rot3(axis = [1, -1, -1], angle = 2*tTurn)
#    assert t5 in a4
#    t6 = GeomTypes.Rot3(axis = [1,  1, -1], angle =   tTurn)
#    assert t6 in a4
#    t7 = GeomTypes.Rot3(axis = [1,  1, -1], angle = 2*tTurn)
#    assert t7 in a4
#    print '............ok'
#
#    print 'testing creation of A4',
#    a4 = A4(
#            setup = setup(
#                # try list argument
#                o2axis0 = [1, 1, 1],
#                # try Rot3 argument
#                o2axis1 = GeomTypes.HalfTurn3([1, -1, 0])
#            )
#        )
#    #print 'A4(o2axis0 = [1, 1, 1], o2axis1 = [1, -1, 0])'
#    print '.....ok'
#    # this a4 is the above a4 repositioned as follows:
#    r0 = GeomTypes.Rot3(axis = Z, angle = eTurn)
#    r1 = GeomTypes.Rot3(axis = [1, -1, 0], angle = math.atan(1/math.sqrt(2)))
#    r = r1 * r0
#    print 'checking result',
#    assert len(a4) == 12
#    assert GeomTypes.E in a4
#    assert GeomTypes.HalfTurn3(r*X) in a4
#    assert GeomTypes.HalfTurn3(r*Y) in a4
#    assert GeomTypes.HalfTurn3(r*Z) in a4
#    assert GeomTypes.Rot3(axis = r * t0.axis(), angle =   tTurn) in a4
#    assert GeomTypes.Rot3(axis = r * t1.axis(), angle = 2*tTurn) in a4
#    assert GeomTypes.Rot3(axis = r * t2.axis(), angle =   tTurn) in a4
#    assert GeomTypes.Rot3(axis = r * t3.axis(), angle = 2*tTurn) in a4
#    assert GeomTypes.Rot3(axis = r * t4.axis(), angle =   tTurn) in a4
#    assert GeomTypes.Rot3(axis = r * t5.axis(), angle = 2*tTurn) in a4
#    assert GeomTypes.Rot3(axis = r * t6.axis(), angle =   tTurn) in a4
#    assert GeomTypes.Rot3(axis = r * t7.axis(), angle = 2*tTurn) in a4
#    print '............ok'
#    #print a4
#    print 'test grouping this',
#    ca4 = copy(a4)
#    a4.group(2)
#    assert a4 == ca4
#    print '.........ok'
#
#    ########################################################################
#    # Quotient Set:
#    a4 = A4(setup = setup(o2axis0 = X, o2axis1= Y))
#    assert len(a4) == 12
#    # print 'group a4:'
#    # print a4
#    d2 = Set([Hx, Hy])
#    d2.group()
#    assert len(d2) == 4
#    # print 'has a subgroup D2:'
#    # print d2
#    print 'test quotient set: A4/D2',
#    q = a4 / d2
#    # print 'which defines a right quotient set s = ['
#    for s in q:
#    #     print '  set('
#    #     for e in s:
#    #         print '    ', e
#    #     print '  )'
#        assert len(s) == 4
#    # print ']'
#    assert len(q) == 3
#    # check if A4 / D2 is a partition of A4:
#    for i in range(len(q)-1):
#        s = q[i]
#        for transform in s:
#            for j in range(i+1, len(q)):
#                assert not transform in q[j]
#    print '...ok'
#
#    ########################################################################
#    # Quotient Set:
#    print 'test isSubgroup: A4, S4',
#    s4 = S4()
#    a4 = A4()
#    assert a4.isSubgroup(s4)
#    assert not s4.isSubgroup(a4)
#    a4.add(GeomTypes.I)
#    assert not a4.isSubgroup(s4)
#    print '....ok'
#
#    print 'success!'