#!/usr/bin/python
#
# Copyright (C) 2010 Marcel Tunnissen
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
# $Log: Scene_RegHeptS4A4Eg.py,v $
# Revision 1.4  2008/10/04 21:38:16  marcelteun
# fix canvas position of regular heptagons
#
# Revision 1.3  2008/10/04 21:13:29  marcelteun
# fix for undestroyed boxes in Ubuntu Hardy Heron
#
# Revision 1.2  2008/10/03 20:09:51  marcelteun
# Bridges2008 changes: window position
#
# Revision 1.1.1.1  2008/07/05 10:35:43  marcelteun
# Imported sources
#
# Revision 1.1  2008/06/18 05:31:54  teun
# Initial revision
#
#

import wx
import math
import rgb
import Heptagons
import isometry
import Geom3D
import Scenes3D
from OpenGL.GL import *

import GeomTypes
from GeomTypes import Rot3      as Rot
from GeomTypes import HalfTurn3 as HalfTurn
from GeomTypes import Vec3      as Vec

Title = 'Polyhedra with Folded Regular Heptagons A4xI'

V2 = math.sqrt(2)

#                0
#   13                      12
#         6             1
#
# 11                           9
#
#       5                 2
#
#
#   10       4       3        8
#
#
#                         7
# There are 4 different edges to separate the triangles:
# a (V2-V7), b (V2-V8), c (V2-V9), and d (V9-V1)
# the first three have opposite alternatives:
# a' (V3-V8), b' (V3-V9) and c' (V1-V8)
# (there's no (V2-V12): V1-V9-V12 is the O3 triangle)
# This leads to 2^3 possible combinations,
# however the edge configuration a b' does not occur
# neither does b' c'
# This leaves 5 possible edge configurations:
class TrisAlt:
    # Note nrs should be different from above
    strip_1_loose     = 100
    strip_I           = 101
    strip_II          = 102
    star              = 103
    star_1_loose      = 104
    alt_strip_I       = 105
    alt_strip_II      = 106
    alt_strip_1_loose = 107
    def get(this, str):
	for k,v in Stringify.iteritems():
	    if v == str:
		return k
	return None

trisAlt = TrisAlt()

dyn_pos		= -1
all_eq_tris	=  0
no_o3_tris	=  1
edge_1_1_V2_1	=  2
edge_1_V2_1_1	=  3
edge_V2_1_1_1	=  4
edge_V2_1_V2_1	=  5
squares_24	=  6
edge_0_1_1_1	=  7
edge_0_1_V2_1	=  8
tris_24		=  9
only_hepts	= 10
only_o3_tris	= 11
edge_1_1_0_1	= 12
edge_1_0_1_1	= 13
square_o3_tris	= 14
edge_V2_1_1_0	= 15
square_12	= 16

Stringify = {
    dyn_pos:		'Enable Sliders',
    no_o3_tris:		'48 Triangles',
    all_eq_tris:	'All 80 Triangles Equilateral',
    edge_1_1_V2_1:	'32 Triangles and 24 Folded Squares: I',
    edge_1_V2_1_1:	'32 Triangles and 24 Folded Squares: II',
    edge_V2_1_1_1:	'56 Triangles and 12 Folded Squares',
    edge_V2_1_V2_1:	'8 Triangles and 36 Folded Squares',
    tris_24:		'24 Triangles',
    squares_24:		'24 Folded Squares',
    edge_0_1_1_1:	'56 Triangles',
    edge_0_1_V2_1:	'8 Triangles and 24 Folded Squares',
    only_hepts:		'Just Heptagons',
    only_o3_tris:	'8 Triangles (O3)',
    edge_1_1_0_1:	'32 Triangles (24 + 8) I',
    edge_1_0_1_1:	'32 Triangles (24 + 8) II',
    square_o3_tris:	'8 Triangles and 12 Folded Squares',
    edge_V2_1_1_0:	'24 Triangles and 12 Folded Squares',
    square_12:		'12 Folded Squares',
    trisAlt.strip_1_loose:	'Strip, 1 Loose ',
    trisAlt.strip_I:		'Strip I',
    trisAlt.strip_II:		'Strip II',
    trisAlt.star:		'Shell',
    trisAlt.star_1_loose:	'Shell, 1 Loose',
    trisAlt.alt_strip_I:	'Alternative Strip I',
    trisAlt.alt_strip_II:	'Alternative Strip II',
    trisAlt.alt_strip_1_loose:	'Alternative Strip, 1 loose',
}

def Vlen(v0, v1):
    x = v1[0] - v0[0]
    y = v1[1] - v0[1]
    z = v1[2] - v0[2]
    return (math.sqrt(x*x + y*y + z*z))

class Shape(Geom3D.IsometricShape):
    def __init__(this, *args, **kwargs):
        Geom3D.IsometricShape.__init__(this,
            Vs = [], Fs = [],
            directIsometries = isometry.A4(),
            unfoldOrbit = True,
            name = 'FoldedRegHeptS4xI'
        )
        this.heptagon = Heptagons.RegularHeptagon()
        #this.dbgPrn = True
        this.theColors     = [
                rgb.oliveDrab[:],
                rgb.brown[:],
                rgb.yellow[:],
                rgb.cyan[:]
            ]
        this.angle = 1.2
        this.fold1 = 0.0
        this.fold2 = 0.0
	this.foldHeptagon = Heptagons.foldMethod.parallel
        this.height = 2.3
        this.applySymmetry = True
        this.addTriangles = True
        this.onlyO3Triangles = False
        this.useCulling = False
        this.edgeAlternative = trisAlt.strip_1_loose

        #this.lightPosition = [-50., 50., 200., 0.]
        #this.lightAmbient  = [0.25, 0.25, 0.25, 1.]
        #this.lightDiffuse  = [1., 1., 1., 1.]
        #this.materialSpec  = [0., 0., 0., 0.]
        #this.showBaseOnly  = True
        this.initArrs()
        this.setV()

    def glDraw(this):
        if this.updateShape: this.setV()
        Geom3D.IsometricShape.glDraw(this)

    def setEdgeAlternative(this, alt):
        this.edgeAlternative = alt
        this.updateShape = True

    def setFoldMethod(this, method):
	this.foldHeptagon = method
        this.updateShape = True

    def setAngle(this, angle):
        this.angle = angle
        this.updateShape = True

    def setFold1(this, angle):
        this.fold1 = angle
        this.updateShape = True

    def setFold2(this, angle):
        this.fold2 = angle
        this.updateShape = True

    def setHeight(this, height):
        this.height = height
        this.updateShape = True

    def edgeColor(this):
        glColor(0.5, 0.5, 0.5)

    def vertColor(this):
        glColor(0.7, 0.5, 0.5)

    def getStatusStr(this):
        #angle = Geom3D.Rad2Deg * this.angle
        s = 'Angle = %01.2f rad, fold1 = %01.2f rad, fold2 = %01.2f rad, T = %02.2f' % (
                this.angle,
                this.fold1,
                this.fold2,
                this.height
            )
        if this.updateShape:
            #print 'getStatusStr: forced setV'
            this.setV()
	#                                  14 = 2'
        #                0
        #   13                      12 = o3 centre
        #         6             1
        #
        # 11                           9 = 1'
        #
        #       5                 2
        #
        #
        #   10       4       3        8 = 0'
        #
        #
        #                         7 = 6'
        Vs = this.getBaseVertexProperties()['Vs']
        if this.edgeAlternative == trisAlt.strip_1_loose:
            aLen = Vlen(Vs[2], Vs[7])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[1], Vs[9])
        elif this.edgeAlternative == trisAlt.strip_I:
            aLen = Vlen(Vs[3], Vs[8])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[1], Vs[9])
        elif this.edgeAlternative == trisAlt.strip_II:
            aLen = Vlen(Vs[3], Vs[8])
            bLen = Vlen(Vs[3], Vs[9])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[1], Vs[9])
        elif this.edgeAlternative == trisAlt.star:
            aLen = Vlen(Vs[3], Vs[8])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[1], Vs[8])
            dLen = Vlen(Vs[1], Vs[9])
        elif this.edgeAlternative == trisAlt.star_1_loose:
            aLen = Vlen(Vs[2], Vs[7])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[1], Vs[8])
            dLen = Vlen(Vs[1], Vs[9])
        elif this.edgeAlternative == trisAlt.alt_strip_I:
            aLen = Vlen(Vs[3], Vs[8])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[2], Vs[14])
        elif this.edgeAlternative == trisAlt.alt_strip_II:
            aLen = Vlen(Vs[3], Vs[8])
            bLen = Vlen(Vs[3], Vs[9])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[2], Vs[14])
        elif this.edgeAlternative == trisAlt.alt_strip_1_loose:
            aLen = Vlen(Vs[2], Vs[7])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[2], Vs[14])
	else:
	    raise TypeError, 'Unknown edgeAlternative %s' % str(
		this.edgeAlternative)
        #tst:
        #aLen = Vlen(Vs[0], [(Vs[6][i] + Vs[1][i]) / 2 for i in range(3)])
        #bLen = Vlen([(Vs[5][i] + Vs[2][i]) / 2 for i in range(3)], [(Vs[6][i] + Vs[1][i]) / 2 for i in range(3)])
        s = '%s, |a|: %02.2f, |b|: %02.2f, |c|: %02.2f, |d|: %02.2f' % (
                s, aLen, bLen, cLen, dLen
            )

        return s

    def setV(this):
        #print this.name, "setV"
        #this.heptagon.foldParallel(this.fold1, this.fold2)
        #this.heptagon.foldTrapezium(this.fold1, this.fold2)
        # The angle has to be adjusted for historical reasons...
	# TODO: fix me
	if this.foldHeptagon == Heptagons.foldMethod.parallel:
	    this.heptagon.foldParallel(-this.fold1, -this.fold2, keepV0 = False)
	else:
	    this.heptagon.fold(this.fold1, this.fold2,
		    keepV0 = False, fold = this.foldHeptagon)
	#print 'norm V0-V1: ', (this.heptagon.Vs[1]-this.heptagon.Vs[0]).squareNorm()
	#print 'norm V1-V2: ', (this.heptagon.Vs[1]-this.heptagon.Vs[2]).squareNorm()
	#print 'norm V2-V3: ', (this.heptagon.Vs[3]-this.heptagon.Vs[2]).squareNorm()
	#print 'norm V3-V4: ', (this.heptagon.Vs[3]-this.heptagon.Vs[4]).squareNorm()
        this.heptagon.translate(Heptagons.H*GeomTypes.uy)
        # The angle has to be adjusted for historical reasons...
        this.heptagon.rotate(-GeomTypes.ux, GeomTypes.qTurn - this.angle)
        this.heptagon.translate(this.height*GeomTypes.uz)
        Vs = this.heptagon.Vs[:]
        #
	# 15                                 14 = 2'
        #                     0
        #    (17) 13                      12 = o3c (alt 16)
        #              6             1
        #
        #      11                           9 = 1'
        #
        #            5                 2
        #
        #
        #        10       4       3        8 = 0'
        #
        #
        #                              7 = 6'

        Rr = Rot(axis = Vec([ 1, 1, 1]), angle = GeomTypes.tTurn)
        Rl = Rot(axis = Vec([-1, 1, 1]), angle = -GeomTypes.tTurn)
        Vs.append(Vec([Vs[2][0], -Vs[2][1], Vs[2][2]]))        # Vs[7]
        Vs.append(Rr * Vs[0])                                  # Vs[8]
        Vs.append(Rr * Vs[1])                                  # Vs[9]
        Vs.append(Rl * Vs[0])                                  # Vs[10]
        Vs.append(Rl * Vs[6])                                  # Vs[11]
        # V12 and V13 are the centres of the triangle on the O3 axis.
        # for V12 the O3 axis is (1, 1, 1). So we need to find the n*(1, 1, 1)
        # that lies in the face. This can found by projecting V12 straight onto
        # this axis, or we can rotate 180 degrees and take the average:
        halfTurn = HalfTurn(Vec([1, 1, 1]))
        Vs.append((Vs[1] + halfTurn*Vs[1]) / 2)                # Vs[12]
        halfTurn = HalfTurn(Vec([-1, 1, 1]))
        Vs.append((Vs[6] + halfTurn*Vs[6]) / 2)                # Vs[13]
        this.setBaseVertexProperties(Vs = Vs)
        Vs.append(Rr * Vs[2])                                  # Vs[14]
        Vs.append(Rl * Vs[5])                                  # Vs[15]
        halfTurn = HalfTurn(Vec([1, 1, 1]))
        Vs.append((Vs[2] + halfTurn*Vs[2]) / 2)                # Vs[16]
        halfTurn = HalfTurn(Vec([-1, 1, 1]))
        Vs.append((Vs[5] + halfTurn*Vs[5]) / 2)                # Vs[17]
        Es = []
        Fs = []
        Fs.extend(this.heptagon.Fs) # use extend to copy the list to Fs
        Es.extend(this.heptagon.Es) # use extend to copy the list to Fs
        colIds = [0 for f in Fs]
        if this.addTriangles:
	    Fs.extend(this.o3triFs[this.edgeAlternative]) # eql triangles
	    Es.extend(this.o3triEs[this.edgeAlternative])
            colIds.extend([3, 3])
	    if (not this.onlyO3Triangles):
		Fs.extend(this.triFs[this.edgeAlternative])
		colIds.extend(this.triColIds[this.edgeAlternative])
		Es.extend(this.triEs[this.edgeAlternative])
        this.setBaseEdgeProperties(Es = Es)
        this.setBaseFaceProperties(Fs = Fs, colors = (this.theColors, colIds))
        this.showBaseOnly = not this.applySymmetry
        this.updateShape = False

    def initArrs(this):
        print this.name, "initArrs"
        this.triFs = {
                trisAlt.strip_1_loose: [
                    [2, 3, 7], [2, 7, 8],
                    [2, 8, 9], [5, 11, 10],
                    [1, 2, 9], [5, 6, 11],
                ],
                trisAlt.strip_I: [
                    [2, 3, 8], [4, 5, 10],
                    [2, 8, 9], [5, 11, 10],
                    [1, 2, 9], [5, 6, 11],
                ],

                trisAlt.strip_II: [
                    [3, 8, 9], [4, 11, 10],
                    [2, 3, 9], [4, 5, 11],
                    [1, 2, 9], [5, 6, 11],
                ],
                trisAlt.star: [
                    [2, 3, 8], [4, 5, 10],
                    [1, 2, 8], [5, 6, 10],
                    [1, 8, 9], [6, 11, 10]
                ],
                trisAlt.star_1_loose: [
                    [2, 3, 7], [2, 7, 8],
                    [1, 2, 8], [5, 6, 10],
                    [1, 8, 9], [6, 11, 10]
                ],
                trisAlt.alt_strip_I: [
                    [2, 3, 8], [4, 5, 10],
                    [2, 8, 9], [5, 11, 10],
                    [2, 9, 14], [5, 15, 11]
                ],
                trisAlt.alt_strip_II: [
                    [3, 8, 9], [4, 11, 10],
                    [2, 3, 9], [4, 5, 11],
                    [2, 9, 14], [5, 15, 11]
                ],
                trisAlt.alt_strip_1_loose: [
                    [2, 3, 7], [2, 7, 8],
                    [2, 8, 9], [5, 11, 10],
                    [2, 9, 14], [5, 15, 11]
                ],
            }
	# 15                                 14 = 2'
        #                     0
        #    (17) 13                      12 = o3c (alt 16)
        #              6             1
        #
        #      11                           9 = 1'
        #
        #            5                 2
        #
        #
        #        10       4       3        8 = 0'
        #
        #
        #                              7 = 6'
        this.o3triFs = {
                trisAlt.strip_1_loose:		[[1, 9, 12], [6, 13, 11]],
                trisAlt.strip_I:		[[1, 9, 12], [6, 13, 11]],
                trisAlt.strip_II:		[[1, 9, 12], [6, 13, 11]],
                trisAlt.star:			[[1, 9, 12], [6, 13, 11]],
                trisAlt.star_1_loose:		[[1, 9, 12], [6, 13, 11]],
                trisAlt.alt_strip_I:		[[2, 14, 16], [5, 17, 15]],
                trisAlt.alt_strip_II:		[[2, 14, 16], [5, 17, 15]],
                trisAlt.alt_strip_1_loose:	[[2, 14, 16], [5, 17, 15]],
	    }
        this.triColIds = {
                trisAlt.strip_1_loose:		[1, 2, 1, 1, 2, 2],
                trisAlt.strip_I:		[1, 2, 2, 1, 1, 2],
                trisAlt.strip_II:		[1, 2, 2, 1, 1, 2],
                trisAlt.star:			[1, 2, 2, 1, 1, 2],
                trisAlt.star_1_loose:		[1, 2, 1, 1, 2, 2],
                trisAlt.alt_strip_I:		[1, 2, 2, 1, 1, 2],
                trisAlt.alt_strip_II:		[1, 2, 2, 1, 1, 2],
                trisAlt.alt_strip_1_loose:	[1, 2, 1, 1, 2, 2],
            }
        this.triEs = {
                trisAlt.strip_1_loose: [
                    2, 7, 2, 8, 2, 9,
                    5, 10, 5, 11,
                ],
                trisAlt.strip_I: [
                    3, 8, 2, 8, 2, 9,
                    5, 10, 5, 11,
                ],
                trisAlt.strip_II: [
                    3, 8, 3, 9, 2, 9,
                    4, 11, 5, 11,
                ],
                trisAlt.star: [
                    3, 8, 2, 8, 1, 8,
                    5, 10, 6, 10,
                ],
                trisAlt.star_1_loose: [
                    2, 7, 2, 8, 1, 8,
                    5, 10, 6, 10,
                ],
                trisAlt.alt_strip_I: [
                    3, 8, 2, 8, 2, 9,
                    5, 10, 5, 11,
                ],
                trisAlt.alt_strip_II: [
                    3, 8, 3, 9, 2, 9,
                    4, 11, 5, 11,
                ],
                trisAlt.alt_strip_1_loose: [
                    2, 7, 2, 8, 2, 9,
                    5, 10, 5, 11,
                ],
            }
        this.o3triEs = {
                trisAlt.strip_1_loose:		[1, 9, 6, 11],
                trisAlt.strip_I:		[1, 9, 6, 11],
                trisAlt.strip_II:		[1, 9, 6, 11],
                trisAlt.star:			[1, 9, 6, 11],
                trisAlt.star_1_loose:		[1, 9, 6, 11],
                trisAlt.alt_strip_I:		[2, 14, 5, 15],
                trisAlt.alt_strip_II:		[2, 14, 5, 15],
                trisAlt.alt_strip_1_loose:	[2, 14, 5, 15],
            }

class CtrlWin(wx.Frame):
    def __init__(this, shape, canvas, *args, **kwargs):
        size = (745, 745)
        # TODO assert (type(shape) == type(RegHeptagonShape()))
        this.shape = shape
        this.canvas = canvas
        wx.Frame.__init__(this, *args, **kwargs)
        this.panel = wx.Panel(this, -1)
        this.statusBar = this.CreateStatusBar()
	#this.foldMethod = Heptagons.foldMethod.parallel
	this.foldMethod = Heptagons.foldMethod.triangle
	this.restoreTris = False
	this.restoreO3Tris = False
	this.shape.foldHeptagon = this.foldMethod
        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
        this.mainSizer.Add(
                this.createControlsSizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.setDefaultSize(size)
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()

        this.specPosIndex = 0
        this.specPos = {
	    only_hepts: {
		# Note: all triangle variants are the same:
		Heptagons.foldMethod.parallel: {
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.parallel],
		    trisAlt.strip_I:       OnlyHeptagons[Heptagons.foldMethod.parallel],
		    trisAlt.star:          OnlyHeptagons[Heptagons.foldMethod.parallel],
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.parallel],
                },
                Heptagons.foldMethod.w: {
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.w],
		    trisAlt.strip_I:       OnlyHeptagons[Heptagons.foldMethod.w],
		    trisAlt.star:          OnlyHeptagons[Heptagons.foldMethod.w],
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.w],
                },
		Heptagons.foldMethod.star: {
		    trisAlt.alt_strip_II: OnlyHeptagons[Heptagons.foldMethod.star],
                },
	    },
	    only_o3_tris:   OnlyO3Triangles,
	    edge_1_1_0_1:   Pos32TrianglesI,
	    edge_1_0_1_1:   Pos32TrianglesII,
	    square_o3_tris: FoldedSquareAndO3Triangle,
	    edge_V2_1_1_0:  FoldedSquareAnd1TriangleType,
	    square_12:      Squares12,
	    tris_24:        Tris24,
	    all_eq_tris:    AllEquilateralTris,
	    no_o3_tris:     NoO3Triangles,
	    squares_24:     FoldedSquares_0,
	    edge_1_1_V2_1:  E1_1_V2_1,
	    edge_1_V2_1_1: {
		Heptagons.foldMethod.parallel: E1_V2_1_1[Heptagons.foldMethod.parallel],
	    },
	    edge_V2_1_1_1: {
		Heptagons.foldMethod.parallel: EV2_1_1_1[Heptagons.foldMethod.parallel],
	    },
	    edge_V2_1_V2_1: {
		Heptagons.foldMethod.parallel: EV2_1_V2_1[Heptagons.foldMethod.parallel],
	    },
	    edge_0_1_1_1: {
		Heptagons.foldMethod.parallel: E0_1_1_1[Heptagons.foldMethod.parallel],
	    },
	    edge_0_1_V2_1: {
		Heptagons.foldMethod.parallel: E0_1_V2_1[Heptagons.foldMethod.parallel],
	    },
	}

    def createControlsSizer(this):
        this.heightF = 10 # slider step factor, or: 1 / slider step
        this.maxHeight = 3

        this.Guis = []

        # static adjustments
	l = this.edgeChoicesList = [
	    Stringify[trisAlt.strip_1_loose],
	    Stringify[trisAlt.strip_I],
	    Stringify[trisAlt.strip_II],
	    Stringify[trisAlt.star],
	    Stringify[trisAlt.star_1_loose],
	    Stringify[trisAlt.alt_strip_I],
	    Stringify[trisAlt.alt_strip_II],
	    Stringify[trisAlt.alt_strip_1_loose],
	]
	this.edgeChoicesListItems = [
	    trisAlt.get(l[i]) for i in range(len(l))
	]
        this.trisAltGui = wx.RadioBox(this.panel,
                label = 'Triangle Fill Alternative',
                style = wx.RA_VERTICAL,
                choices = this.edgeChoicesList
            )
        this.Guis.append(this.trisAltGui)
        this.trisAltGui.Bind(wx.EVT_RADIOBOX, this.onTriangleAlt)
        this.trisAlt = this.edgeChoicesListItems[0]
        this.shape.setEdgeAlternative(this.trisAlt)

        # View Settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        this.applySymGui = wx.CheckBox(this.panel, label = 'Apply Symmetry')
        this.Guis.append(this.applySymGui)
        this.applySymGui.SetValue(this.shape.applySymmetry)
        this.applySymGui.Bind(wx.EVT_CHECKBOX, this.onApplySym)
        this.addTrisGui = wx.CheckBox(this.panel, label = 'Show Triangles')
        this.Guis.append(this.addTrisGui)
        this.addTrisGui.SetValue(this.shape.addTriangles)
        this.addTrisGui.Bind(wx.EVT_CHECKBOX, this.onAddTriangles)

        # static adjustments
	l = this.foldMethodList = [
	    Heptagons.FoldName[Heptagons.foldMethod.parallel],
	    Heptagons.FoldName[Heptagons.foldMethod.triangle],
	    Heptagons.FoldName[Heptagons.foldMethod.star],
	    Heptagons.FoldName[Heptagons.foldMethod.w],
	    Heptagons.FoldName[Heptagons.foldMethod.trapezium],
	]
	this.foldMethodListItems = [
	    Heptagons.foldMethod.get(l[i]) for i in range(len(l))
	]
        this.foldMethodGui = wx.RadioBox(this.panel,
                label = 'Heptagon Fold Method',
                style = wx.RA_VERTICAL,
                choices = this.foldMethodList
            )
	for i in range(len(this.foldMethodList)):
	    if (this.foldMethodList[i] == Heptagons.FoldName[this.foldMethod]):
		this.foldMethodGui.SetSelection(i)
        this.Guis.append(this.foldMethodGui)
        this.foldMethodGui.Bind(wx.EVT_RADIOBOX, this.onFoldMethod)

	# predefined positions
        this.prePosLst = [
		Stringify[only_hepts],
		Stringify[only_o3_tris],
		Stringify[square_12],
		Stringify[square_o3_tris],
		Stringify[tris_24],
		Stringify[squares_24],
		Stringify[edge_1_1_0_1],
		Stringify[edge_1_0_1_1],
		Stringify[edge_0_1_V2_1],
		Stringify[edge_V2_1_1_0],
		Stringify[edge_V2_1_V2_1],
		Stringify[no_o3_tris],
		Stringify[edge_0_1_1_1],
		Stringify[edge_1_1_V2_1],
		Stringify[edge_1_V2_1_1],
		Stringify[edge_V2_1_1_1],
		Stringify[all_eq_tris],
		Stringify[dyn_pos],
            ]
        this.prePosGui = wx.RadioBox(this.panel,
                label = 'Only Regular Faces with:',
                style = wx.RA_VERTICAL,
                choices = this.prePosLst
            )
	# Don't hardcode which index is dyn_pos, I might reorder the item list
	# one time, and will probably forget to update the default selection..
	for i in range(len(this.prePosLst)):
	    if (this.prePosLst[i] == Stringify[dyn_pos]):
		this.prePosGui.SetSelection(i)
        this.Guis.append(this.prePosGui)
        this.prePosGui.Bind(wx.EVT_RADIOBOX, this.onPrePos)
        #wxPoint& pos = wxDefaultPosition, const wxSize& size = wxDefaultSize, int n = 0, const wxString choices[] = NULL, long style = 0, const wxValidator& validator = wxDefaultValidator, const wxString& name = "listBox")

        this.firstButton = wx.Button(this.panel, label = 'First')
        this.nextButton  = wx.Button(this.panel, label = 'Next')
        this.nrTxt       = wx.Button(this.panel, label = '0/0',  style=wx.NO_BORDER)
        this.prevButton  = wx.Button(this.panel, label = 'Prev')
        this.lastButton  = wx.Button(this.panel, label = 'Last')
        this.Guis.append(this.firstButton)
        this.Guis.append(this.nextButton)
        this.Guis.append(this.nrTxt)
        this.Guis.append(this.prevButton)
        this.Guis.append(this.lastButton)
        this.firstButton.Bind(wx.EVT_BUTTON, this.onFirst)
        this.nextButton.Bind(wx.EVT_BUTTON, this.onNext)
        this.prevButton.Bind(wx.EVT_BUTTON, this.onPrev)
        this.lastButton.Bind(wx.EVT_BUTTON, this.onLast)

        # dynamic adjustments
        this.angleGui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.angle,
                minValue = -180,
                maxValue =  180,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.angleGui)
        this.angleGui.Bind(wx.EVT_SLIDER, this.onAngle)
        this.fold1Gui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.fold1,
                minValue = -180,
                maxValue =  180,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.fold1Gui)
        this.fold1Gui.Bind(wx.EVT_SLIDER, this.onFold1)
        this.fold2Gui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.fold2,
                minValue = -180,
                maxValue =  180,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.fold2Gui)
        this.fold2Gui.Bind(wx.EVT_SLIDER, this.onFold2)
        this.heightGui = wx.Slider(
                this.panel,
                value = this.maxHeight - this.shape.height*this.heightF,
                minValue = -this.maxHeight * this.heightF,
                maxValue = this.maxHeight * this.heightF,
		style = wx.SL_VERTICAL
            )
        this.Guis.append(this.heightGui)
        this.heightGui.Bind(wx.EVT_SLIDER, this.onHeight)


        # Sizers
        this.Boxes = []

        # view settings
        this.Boxes.append(wx.StaticBox(this.panel, label = 'View Settings'))
        settingsSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        settingsSizer.Add(this.applySymGui, 0, wx.EXPAND)
        settingsSizer.Add(this.addTrisGui, 0, wx.EXPAND)
        settingsSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        statSizer = wx.BoxSizer(wx.HORIZONTAL)
        statSizer.Add(this.foldMethodGui, 0, wx.EXPAND)
        statSizer.Add(this.trisAltGui, 0, wx.EXPAND)
        statSizer.Add(settingsSizer, 0, wx.EXPAND)
        statSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        posSizerSubH = wx.BoxSizer(wx.HORIZONTAL)
        posSizerSubH.Add(this.firstButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.prevButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.nrTxt, 1, wx.EXPAND)
        posSizerSubH.Add(this.nextButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.lastButton, 1, wx.EXPAND)
        posSizerSubV = wx.BoxSizer(wx.VERTICAL)
        posSizerSubV.Add(this.prePosGui, 0, wx.EXPAND)
        posSizerSubV.Add(posSizerSubH, 0, wx.EXPAND)
        posSizerSubV.Add(wx.BoxSizer(), 1, wx.EXPAND)
        posSizerH = wx.BoxSizer(wx.HORIZONTAL)
        posSizerH.Add(posSizerSubV, 2, wx.EXPAND)

        # dynamic adjustments
        specPosDynamic = wx.BoxSizer(wx.VERTICAL)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Dihedral Angle (Degrees)'))
        angleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        angleSizer.Add(this.angleGui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Fold 1 Angle (Degrees)'))
        fold1Sizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        fold1Sizer.Add(this.fold1Gui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Fold 2 Angle (Degrees)'))
        fold2Sizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        fold2Sizer.Add(this.fold2Gui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Offset T'))
        heightSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        heightSizer.Add(this.heightGui, 1, wx.EXPAND)
        specPosDynamic.Add(angleSizer, 0, wx.EXPAND)
        specPosDynamic.Add(fold1Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(fold2Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(wx.BoxSizer(), 1, wx.EXPAND)
        posSizerH.Add(specPosDynamic, 3, wx.EXPAND)
        posSizerH.Add(heightSizer, 1, wx.EXPAND)

        mainVSizer = wx.BoxSizer(wx.VERTICAL)
        mainVSizer.Add(statSizer, 0, wx.EXPAND)
        mainVSizer.Add(posSizerH, 0, wx.EXPAND)
        mainVSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(mainVSizer, 6, wx.EXPAND)

        this.errorStr = {
                'PosEdgeCfg': "ERROR: Impossible combination of position and edge configuration!"
            }

        return mainSizer

    def rmControlsSizer(this):
        #print "rmControlsSizer"
        # The 'try' is necessary, since the boxes are destroyed in some OS,
        # while this is necessary for Ubuntu Hardy Heron.
        for Box in this.Boxes:
            try:
                Box.Destroy()
            except wx._core.PyDeadObjectError: pass
        for Gui in this.Guis:
            Gui.Destroy()

    # move to general class
    def setDefaultSize(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

    def onAngle(this, event):
	#print this.GetSize()
        this.shape.setAngle(Geom3D.Deg2Rad * this.angleGui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onFold1(this, event):
        this.shape.setFold1(Geom3D.Deg2Rad * this.fold1Gui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onFold2(this, event):
        this.shape.setFold2(Geom3D.Deg2Rad * this.fold2Gui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onHeight(this, event):
        this.shape.setHeight(float(this.maxHeight - this.heightGui.GetValue())/this.heightF)
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onApplySym(this, event):
        this.shape.applySymmetry = this.applySymGui.IsChecked()
        this.shape.updateShape = True
        this.canvas.paint()

    def onAddTriangles(this, event):
        this.shape.addTriangles  = this.addTrisGui.IsChecked()
        this.shape.updateShape = True
        this.canvas.paint()

    def onTriangleAlt(this, event):
        this.trisAlt = this.edgeChoicesListItems[this.trisAltGui.GetSelection()]
        this.shape.setEdgeAlternative(this.trisAlt)
        if this.prePosGui.GetSelection() != len(this.prePosLst) - 1:
            this.onPrePos()
        else:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()

    def onFoldMethod(this, event):
        this.foldMethod = this.foldMethodListItems[
		this.foldMethodGui.GetSelection()
	    ]
	this.shape.setFoldMethod(this.foldMethod)
        if this.prePosGui.GetSelection() != len(this.prePosLst) - 1:
            this.onPrePos()
        else:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()

    def onFirst(this, event = None):
        this.specPosIndex = 0
        this.onPrePos()

    def onLast(this, event = None):
        this.specPosIndex = -1
        this.onPrePos()

    def getPrePos(this):
        prePosStr = this.prePosLst[this.prePosGui.GetSelection()]
	for k,v in Stringify.iteritems():
	    if v == prePosStr:
		return k
	return dyn_pos

    def onPrev(this, event = None):
        prePosIndex = this.getPrePos()
        if prePosIndex != dyn_pos:
            if this.specPosIndex > 0:
                this.specPosIndex -= 1
	    elif this.specPosIndex == -1:
                this.specPosIndex = len(
			this.specPos[prePosIndex][this.foldMethod][this.trisAlt]
		    ) - 2
	    # else prePosIndex == 0 : first one selected don't scroll around
            this.onPrePos()

    def onNext(this, event = None):
        prePosIndex = this.getPrePos()
        if prePosIndex != dyn_pos:
	    try:
		maxI = len(
			this.specPos[prePosIndex][this.foldMethod][this.trisAlt]
		    ) - 1
		if this.specPosIndex >= 0:
		    if this.specPosIndex < maxI - 1:
			this.specPosIndex += 1
		    else:
		        this.specPosIndex = -1 # select last
	    except KeyError:
		pass
	    this.onPrePos()

    tNone = 1.0
    aNone = 0.0
    fld1None = 0.0
    fld2None = 0.0
    def onPrePos(this, event = None):
	#print "onPrePos"
        sel = this.getPrePos()
	# if only_hepts:
	# 1. don't show triangles
	# 2. disable triangle strip.
	if (sel == only_hepts):
	    this.shape.addTriangles = False
	    # if legal fold method select first fitting triangle alternative
	    if this.foldMethod in this.specPos[sel]:
		for k in this.specPos[sel][this.foldMethod].iterkeys():
		    for i in range(len(this.edgeChoicesListItems)):
			if this.edgeChoicesListItems[i] == k:
			    this.trisAltGui.SetSelection(i)
			    this.trisAlt = k
			    this.shape.setEdgeAlternative(k)
			    break
		    break
	    this.addTrisGui.Disable()
	    this.trisAltGui.Disable()
	    this.restoreTris = True
	elif (this.restoreTris):
	    this.restoreTris = False
	    this.trisAltGui.Enable()
	    this.addTrisGui.Enable()
	    this.shape.addTriangles  = this.addTrisGui.IsChecked()
	    # needed for sel == dyn_pos
	    this.shape.updateShape = True
	if (sel == only_o3_tris):
	    this.shape.onlyO3Triangles = True
	    this.restoreO3Tris = True
	elif (this.restoreO3Tris):
	    this.restoreO3Tris = False
	    this.shape.onlyO3Triangles = False
	    # needed for sel == dyn_pos
	    this.shape.updateShape = True
        aVal = this.aNone
        tVal = this.tNone
	c = this.shape
        if sel == dyn_pos:
	    this.angleGui.Enable()
	    this.fold1Gui.Enable()
	    this.fold2Gui.Enable()
	    this.heightGui.Enable()
	    this.angleGui.SetValue(Geom3D.Rad2Deg * c.angle)
	    this.fold1Gui.SetValue(Geom3D.Rad2Deg * c.fold1)
	    this.fold2Gui.SetValue(Geom3D.Rad2Deg * c.fold2)
	    this.heightGui.SetValue(
		this.maxHeight - this.heightF*c.height)
	    # enable all folding and triangle alternatives:
	    for i in range(len(this.foldMethodList)):
		this.foldMethodGui.ShowItem(i, True)
	    for i in range(len(this.edgeChoicesList)):
		this.trisAltGui.ShowItem(i, True)
	else:
            fld1 = this.fld1None
            fld2 = this.fld2None
	    nrPos = 0

	    # Ensure this.specPosIndex in range:
	    try:
		nrPos = len(this.specPos[sel][this.foldMethod][this.trisAlt])
		maxI = nrPos - 1
		if (this.specPosIndex > maxI):
		    this.specPosIndex = maxI
		# keep -1 (last) so switching triangle alternative will keep
		# last selection.
		elif (this.specPosIndex < -1):
		    this.specPosIndex = maxI - 1
	    except KeyError:
		pass

	    # Disable / enable appropriate folding methods.
	    for i in range(len(this.foldMethodList)):
		method = this.foldMethodListItems[i]
		this.foldMethodGui.ShowItem(i, method in this.specPos[sel])
		# leave up to the user to decide which folding method to choose
		# in case the selected one was disabled.

	    # Disable / enable appropriate triangle alternatives.
	    # if the selected folding has valid solutions anyway
	    if this.foldMethod in this.specPos[sel]:
		for i in range(len(this.edgeChoicesList)):
		    alt = this.edgeChoicesListItems[i]
		    this.trisAltGui.ShowItem(
			i, alt in this.specPos[sel][this.foldMethod])

	    try:
		if this.specPos[sel][this.foldMethod][this.trisAlt] != []:
		    tVal = this.specPos[sel][this.foldMethod][this.trisAlt][
			    this.specPosIndex][0]
		    aVal = this.specPos[sel][this.foldMethod][this.trisAlt][
			    this.specPosIndex][1]
		    fld1 = this.specPos[sel][this.foldMethod][this.trisAlt][
			    this.specPosIndex][2]
		    fld2 = this.specPos[sel][this.foldMethod][this.trisAlt][
			    this.specPosIndex][3]
	    except KeyError:
	        pass

            c.setAngle(aVal)
            c.setHeight(tVal)
            c.setFold1(fld1)
            c.setFold2(fld2)
	    this.angleGui.SetValue(0)
	    this.fold1Gui.SetValue(0)
	    this.fold2Gui.SetValue(0)
	    this.heightGui.SetValue(0)
	    this.angleGui.Disable()
	    this.fold1Gui.Disable()
	    this.fold2Gui.Disable()
	    this.heightGui.Disable()
            if ( tVal == this.tNone and aVal == this.aNone and
		fld1 == this.fld1None and fld2 == this.fld2None
                ):
		if (sel == only_hepts or sel == only_o3_tris):
		    txt = 'No solution for this folding method'
		else:
		    txt = 'No solution for this triangle alternative'
                this.statusBar.SetStatusText(txt)
	    elif (sel == squares_24 and (
		    this.trisAlt == trisAlt.strip_1_loose
		    #or
		    #this.trisAlt == trisAlt.star
		) or (this.foldMethod == Heptagons.foldMethod.parallel and (
		    (
			sel == edge_1_V2_1_1
			and (
			    this.trisAlt == trisAlt.strip_1_loose
			    or
			    this.trisAlt == trisAlt.star_1_loose
			)
		    )
		    or
		    (
			sel == edge_V2_1_1_1
			and not (
			    this.trisAlt == trisAlt.strip_1_loose
			    or
			    this.trisAlt == trisAlt.star_1_loose
			)
		    )
		    or
		    (
			(
			    sel == edge_0_1_1_1
			    or
			    sel == edge_0_1_V2_1
			    or
			    sel == tris_24
			) and (
			    this.trisAlt == trisAlt.strip_1_loose
			    or
			    this.trisAlt == trisAlt.star_1_loose
			)
		    )
		))
	    ):

		this.statusBar.SetStatusText('Doesnot mean anything special for this triangle alternative')
	    else:
		if this.specPosIndex == -1:
		    nr = nrPos
		else:
		    nr = this.specPosIndex + 1
		this.nrTxt.SetLabel('%d/%d' % (nr, nrPos))
		this.statusBar.SetStatusText(c.getStatusStr())
        this.canvas.paint()

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)

###############################################################################
OnlyHeptagons = {
    Heptagons.foldMethod.parallel: [
	[1.31032278994319, 0.0, -1.9628169332268968, -2.2110608867701069],
	[-0.2533401749928702, 3.1415926535897931, 1.1787757203628966, -2.2110608867701069],
	[0.49161494586164856, 3.1415926535897931, 1.9628169332268963, -0.93053176681968619],
	[2.0552779107977082, 0.0, -1.1787757203628972, -0.93053176681968619],
    ],
    Heptagons.foldMethod.star: [
	[-0.74461021372109015, -2.9818815182710203, 2.7722011165143075, -1.6269361079388478],
	[-0.62171047473743957, -2.3850856066677051, 2.9797255199248309, 2.2122365867684177],
	[-0.55610249451280391, -2.609660225893911, -1.5658217693927483, -2.6032863388083642],
	[-0.893811200268113, -2.1240091326797543, -2.2219575336393387, 0.79799125365158663],
	[1.0540892657192353, 1.0743008888823, -1.8744609728684303, -2.6184266217442596],
	[1.3845570493440107, 1.4469702342451671, -1.3161975058771898, -0.86544404605462155],
    ],
    Heptagons.foldMethod.w: [
	[-1.8868486799927435, -2.6758432135380379, -3.1283205574215183, 1.9544544516064626],
	[-1.322333216810468, -2.9671800030020141, -1.1832507472772251, 1.6683015362824891],
	[1.7889621671929601, 0.48746365476050291, -1.6930224693313676, -1.5136933696889994],
	[2.380384930679721, 0.693073733186942, -0.568746300899379, -0.882436236397252],
    ],
    # none found for the others,... :(
}

###############################################################################
star_strip_1loose_lst = [
    [0.84975071885400866, 0.032588654231672121, -3.123498735130565, -2.0824877592417561],
    [1.2031441726440764, 0.77985326936848609, -2.5087287534276497, 1.2484420071876301],
    [-1.3176570232737794, -2.646076217507114, -2.8309084651792102, -2.3232921432177327],
    [-1.5638880068752432, -2.2362876476989033, -2.1550378224617521, 0.68864756632487789],
    [1.6989771952452002, 0.79879405476155396, -1.1170030013948313, -2.407166580932016],
    [1.7337065257026629, 0.92947412884703773, -1.796816948510644, 0.076971744283598167],
]
w_strip_1loose_lst = [
    [-1.064771818820939, 2.7267644021703066, 1.7538347714390188, -1.7399218514133903],
    [-1.0647718188209392, -2.6361403001227632, -1.7538347714390188, 1.5336092971456683],
     [1.6011356814825821, -0.031110111270192142, 1.7538347714390188, 2.5107377958463428],
    [1.7315028897368459, 0.0084059713168738032, 1.7538347714390188, 2.9236661785462799],
     [-1.573689301641376, -2.263365835344846, -1.7538347714390179, -0.55232000947421955],
]
star_strip_lst = [
    [-1.2787114409728058, -2.5182959872317254, 2.6830500115396658, 0.0],
    [-1.278711440972806, -2.5182959872317263, -1.4154825122609482, 0.0],
    [1.7787114409728062, 0.94749966043682887, -1.7261101413288449, 0.0],
]
tria_strip_lst = [
    [1.6800854296744396, 0.47457010697125623, 0.74503485547995096, 2.2177947528033286],
]
star_star1loose_lst = [
    [-1.334613872421748, 2.9512496091446225, 0.19307629197798809, 0.4590088595264899],
    [1.5705053243944138, 0.07242369151187969, -3.101306121708379, 0.16426745878077501],
    [2.093519824678034, 0.33436073666791066, -2.946081737032368, 1.9143662046281982],
]
tria_star_lst = [
    [-0.30901699437494773, 1.4571902198029689, 2.5643831539870461, 1.7538347714390194],
    [0.80901699437494679, -0.84333376321889553, 2.5643831539870474, 1.753834771439019],
]
tria_star1loose_lst = [
    [0.25480766689806883, 0.0, 2.835431693293132, 0.72223516058419468],
    [-1.3088552980379908, 3.1415926535897927, -0.30616096029666107, 0.72223516058419501],
    [-1.8244175404836567, 3.1415926535897931, 0.39495269151491569, -2.6816890561620608],
]
# note, same as Heptagons.foldMethod.star, since last value = 0.0:
w_strip_lst = star_strip_lst
w_star1loose_lst = [
    [-1.3296934452310603, 2.9372990815638049, 0.47840318769039741, math.pi -0.47333489730055955],
    [-1.3296934452310603, 2.9372990815638049, 0.47840318769039741, -0.47333489730055955],
    [1.5679188974308946, 0.070442316860208021, -3.0139758223429416, 2.9827742626672333],
    [1.5679188974308944, 0.070442316860207979, -3.0139758223429425, -0.15881839092255845],
    [2.5969149577468986, 0.37180029203869963, -0.99159844699066557, -2.1865945414789412],
    [2.5969149577468986, 0.37180029203869974, -0.99159844699066557, 0.95499811211085195],
]
trap_strip_lst = [
    [1.6713285948103263, 0.78612999312594156, 0.94665778267419576, 2.2644932672720368],
    [1.603988045241469, 1.1791617966606149, -1.2247214682758774, 0.9875936306319586],
]

OnlyO3Triangles = {
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_I:           tria_strip_lst,
	trisAlt.strip_II:          tria_strip_lst,
	trisAlt.star:              tria_star_lst,
	trisAlt.star_1_loose:      tria_star1loose_lst,
	trisAlt.alt_strip_I:       tria_strip_lst,
	trisAlt.alt_strip_II:      tria_strip_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose:     star_strip_1loose_lst,
	trisAlt.strip_I:           star_strip_lst,
	trisAlt.strip_II:          star_strip_lst,
	trisAlt.star_1_loose:      star_star1loose_lst,
	trisAlt.alt_strip_I:       star_strip_lst,
	trisAlt.alt_strip_II:      star_strip_lst,
	trisAlt.alt_strip_1_loose: star_strip_1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose:     w_strip_1loose_lst,
	trisAlt.strip_I:           w_strip_lst,
	trisAlt.strip_II:          w_strip_lst,
	trisAlt.star_1_loose:      w_star1loose_lst,
	trisAlt.alt_strip_I:       w_strip_lst,
	trisAlt.alt_strip_II:      w_strip_lst,
	trisAlt.alt_strip_1_loose: w_strip_1loose_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_I:           trap_strip_lst,
	trisAlt.strip_II:          trap_strip_lst,
	trisAlt.alt_strip_I:       trap_strip_lst,
	trisAlt.alt_strip_II:      trap_strip_lst,
    },
}

###############################################################################
tria_xxx1loose_lst = [
    [-0.11812292720476, 3.14159265358979, -2.25211078574522, -2.74857920585919],
    [1.4455400377313, 0.0, 0.88948186784457, -2.74857920585919],
    [0.60832876085173, 0.0, 2.18208908059778, 2.64524163292458],
    [-0.95533420408433, 3.14159265358979, -0.95950357299201, 2.64524163292458],
    [-0.65691438551895, 3.14159265358979, -1.33576642918691, 1.15113391706111],
    [0.90674857941711, 0.0, 1.80582622440289, 1.15113391706111],
    [0.470619952462, 3.14159265358979, -2.78574929965068, 1.27136705090598],
    [2.03428291739806, 0.0, 0.35584335393911, 1.27136705090598],
]
star_xxx1loose_lst = [
    [-1.20673038862948, 2.64886420376349, 0.5462781256929, 1.90439829002018],
    [-1.18498720369744, -2.96422976968227, -3.04175401058713, 2.29107353121922],
    [1.40643063492408, -0.18662824019381, 3.03637594858021, -2.26817282625815],
    [-1.77553651955644, -3.05965207131176, -3.09598219587269, -0.99511607066055],
    [-0.93641732709054, 2.44038947886288, 0.88697014027351, -0.27366004937339],
    [0.66845709899032, -0.38564524697005, 2.91190778483334, 0.58930509814088],
    [1.58322408928141, 0.47390958631694, -0.52100418066513, -2.00342801113787],
    [2.06165966104283, 0.22254153134540, -0.2269414372901, 1.53832863733572],
]
w_xxx1loose_lst = [
    [-0.94335616235195, 2.44013969579958, 0.73690456127344, 0.30810337906002],
    [-0.95922328678987, 2.440178678853, 0.75676044346296, 1.31293341966707],
    [0.64680225032839, -0.40681413993508, -3.05394393909218, -0.67958538291447],
    [1.13519707160583, 0.12145522427178, -2.32977399889470, 2.79015830517702],
    [-1.88107579998874, 2.90399006683424, 2.15718006845097, -2.43143969177342],
    [-1.91374594457222, -3.11261665074828, 2.53474378035533, 1.16485045216552],
    [2.27969888995643, -0.041271922594255, 0.965002604413438, 2.994364834727],
    [2.33699202330841, 0.07199688786574, 0.78873100385447, -1.7264857472177],
]
w_alt_strip1loose_lst = [
    [0.86602540378444, 0.36161317966767, -1.28052911995042, -2.06457033281442],
    [0.86602540378444, -0.36161317966767, -2.84861154567842, -2.06457033281442],
]

Squares12 = {
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose:     tria_xxx1loose_lst,
	trisAlt.star_1_loose:      tria_xxx1loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose:     star_xxx1loose_lst,
	trisAlt.star_1_loose:      star_xxx1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose:     w_xxx1loose_lst,
	trisAlt.star_1_loose:      w_xxx1loose_lst,
	trisAlt.alt_strip_1_loose: w_alt_strip1loose_lst,
    },
}

###############################################################################
par_star_strip_list = [
    [1.0667369771505062, 0.17460360869707484, -2.0645703328144194, 1.8471533350794935],
    [0.73520075865433276, 0.53851116038768643, -2.0645703328144194, 2.9951020996341051],
    [0.7352007586543331, 2.9669890448927174, 2.0645703328144198, 1.2944393185102951],
    [1.066736977150506, 2.6030814932021062, 2.0645703328144198, 0.14649055395568578],
]
tri_xxx1loose_list = [
    [0.63050299381973984, 0.0, 2.5041510448900102, 3.041589524833173],
    [-0.93315997111631988, 3.1415926535897931, -0.63744160869978295, 3.0415895248331721],
    [-0.35740390266670324, 3.1415926535897931, -1.3160926994220183, 0.49280142622661316],
    [1.2062590622693561, 0.0, 1.8254999541677752, 0.49280142622661333],
    [0.055516207990148426, 3.1415926535897927, -2.0242070276959412, -2.3313527285220612],
    [0.52364405571113759, 3.1415926535897931, -2.4574426992577738, 0.7791328412932077],
    [1.6191791729262084, 1.5613106568963563e-16, 1.1173856258938517, -2.3313527285220608],
    [2.0873070206471973, 2.0183831730962393e-16, 0.68414995433201908, 0.77913284129320814],
]
tri_star_strip_list = [
    [1.1964935651638633, -0.27352488932327734, 1.8842755148636305, -2.6593078492130866],
    [1.3090169943749472, -0.12747672487732764, 1.6744710166353975, 0.75403191432758199],
    [1.0742687982864947, 2.5927093577804059, -2.1000230413726158, 0.081756270399801309],
]
star_xxx1loose_list = [
    [0.95264738519643499, -0.013099993947301769, 3.1343221484232502, 1.0909897838323435],
    [-1.0622718113099829, 2.7897194390593305, 0.37000886846079506, 2.5424623174433245],
    [1.4080522672616729, 0.022606830810786814, -3.1290439458136583, -2.7576574367378717],
    [-1.4338752643482093, -2.7668210517772076, -2.9193133880967941, 1.7433708204513012],
    [-1.8254827733838002, -2.8529760281613155, -2.975141096922937, -0.72367409453609],
    [-0.60854380787240481, 2.5277433838466874, 0.72745662990011084, -0.94677780974506831],
    [1.8300400997086879, 0.57551428856377007, -0.66609035739679623, -1.3854564783828289],
    [2.178705047834566, 0.40973095071997873, -0.43911928098022912, 1.2836398804110356],
]
w_xxx1loose_list = [
    [0.9595199220234929, -0.011610850474307099, -2.5117433470403845, -1.1812096388085243],
    [1.6582512009956858, 0.42460909911928374, -1.8279950936484965, 1.7781134561114862],
    [-1.9136041058937987, 3.111560489829178, 2.4560332339509943, -3.0565646706556415],
    [-1.8994500263477267, -2.8952627985338513, 2.8209817729539464, 0.92614367809317444],
]
trap_alt_strip_list = [
    [1.3275323674874255, 0.77825225940270326, 2.1444313561738131, -2.2777346479732303],
    [1.3864835428228344, 1.2492288355252124, -1.9513728231636893, -1.5790658625186547],
]
Tris24 = {
    # valid for all non-loose methods:
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_I:           par_star_strip_list,
	trisAlt.strip_II:          par_star_strip_list,
	trisAlt.star:              par_star_strip_list,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose:     tri_xxx1loose_list,
	trisAlt.strip_I:           tri_star_strip_list,
	trisAlt.strip_II:          tri_star_strip_list,
	trisAlt.star:              tri_star_strip_list,
	trisAlt.star_1_loose:      tri_xxx1loose_list,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose:     star_xxx1loose_list,
	trisAlt.star_1_loose:      star_xxx1loose_list,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose:     w_xxx1loose_list,
	trisAlt.star_1_loose:      w_xxx1loose_list,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.alt_strip_I:       trap_alt_strip_list,
	trisAlt.alt_strip_II:      trap_alt_strip_list,
    },
}

###############################################################################
# These lists are valid for stripI and stripII:
tri_strip1loose_lst = [
    [-0.2458627268578423, 2.4477137125144059, 1.4573873326240594, -1.7538347714390188],
    [0.95623621578898843, 0.69387894107538728, -3.0719632031165078, -1.7538347714390188],
    [0.9562362157889881, 0.69387894107538739, 2.0568031048575843, 1.753834771439017],
    [-0.24586272685784227, 2.4477137125144055, 0.3029683334185661, 1.7538347714390179],
    [0.66725358606974539, 2.4477137125144055, -1.6404257772681818, 1.7538347714390179],
    [1.8693525287165764, 0.69387894107538739, 0.11340899417083616, 1.753834771439017],
    [1.8693525287165764, 0.69387894107538728, 1.2678279933763301, -1.753834771439017],
    [0.66725358606974572, 2.4477137125144055, -0.48600677806268777, -1.753834771439017],
]
tri_strip_lst = [
    [0.39884399626845796, 1.4568403064826343, 2.5715853033334066, -0.88428111441002599],
    [-0.25245320098095386, 2.5254918903733907, 1.2927536380277551, -1.9009046158502372],
    [0.56477962526448244, 2.5170214708479355, -1.6342822146880849, 1.884160303072703],
    [1.1958969269857136, 0.47194194051049571, 1.874835153247457, 2.2245693304207181],
    [1.6815827381053527, 1.4534250712582302, -0.036979849859386071, -0.88545500812312916],
    [1.791390806850272, 1.275075487327636, 0.20309173616168485, -0.9899282873130506],
]
tri_star_lst = [
    [-1.1866225214120076, -2.1754881202325826, -1.2929614267210461, -1.4812543041546764],
    [-1.5259121713285926, 2.6612849675887378, 1.195692467905124, 2.9190560509451822],
    [1.7523502275943492, -0.46021993104649006, 1.4016157369553881, -3.1278212850333933],
    [-0.88119866022994153, 2.0451389616084743, 1.5424299051472092, 0.99335328707403114],
    [-0.18727644316624867, -2.289496425290201, -2.3168872464112451, 1.8246646968695863],
    [1.5885922462368838, -1.112605957020758, 2.3392903216454823, -0.91912350781113883],
]
tri_star1loose_lst = [
    [-0.60197575041065687, -2.4477137125144059, -1.7669644500014954, 1.2408151821744893],
    [0.60012319223617494, -0.69387894107538717, 2.7623860857390725, 1.240815182174491],
    [0.010599127576782552, 0.69387894107538728, 2.6566097782503277, 0.84170067739776755],
    [-0.087361666013098777, 0.69387894107538728, -3.0147170070186511, 2.5950746780203096],
    [0.19988847087339739, -2.4477137125144059, -2.6607140685283119, 2.6837035899230366],
    [-0.31030415059135763, -0.69387894107538717, -2.5725181409268796, -1.7944705657794051],
    [-1.1914998150700482, 2.4477137125144055, 0.90277500681130984, 0.84170067739776933],
    [-1.2894606086599301, 2.4477137125144055, 1.514633528721917, 2.5950746780203104],
    [1.401987413520229, -0.69387894107538717, 1.8686364672122555, 2.6837035899230384],
    [-1.5124030932381887, -2.4477137125144059, -0.81868336948786169, -1.7944705657794051],
    [0.86022804268662301, -2.4477137125144059, -2.8209724114818533, -1.0942175323961338],
    [2.062326985333454, -0.69387894107538806, 1.7083781242587148, -1.0942175323961347],
]
star_strip1loose_lst = [
    [-1.1218560392107615, -2.7629940667629986, -1.7718213909514624, 2.2567722795241298],
    [-1.3267612461683367, -2.5778529653405711, 2.7362124611005836, -0.28126669081465216],
    [-0.28922422512916357, 2.6718456414892255, -0.21375757704173282, 1.9914479371053699],
    [1.8724618970261588, 0.76451178362743311, -0.0724688081506768, 1.8409398419822915],
    [-1.1124714157602793, -2.0230027283437906, 2.8368103677052008, 1.0316703289486415],
    [0.46925383056107556, 1.8313682859304494, 1.0348362820959265, -2.4222351368105524],
    [2.0846486004668447, 1.2250086511365692, -0.78617831355469914, -0.51598138539488669],
    [0.60829171411896221, 2.0264126913595617, 0.5479286501894568, -2.2482115235445761],

]
star_strip_lst = [
    [1.3589033857968413, 0.57075868490494164, -1.854104152973628, -1.5872846507074385],
    [1.1510711142603265, 0.76345718622723957, -2.5719659710126268, 1.3787127661296772],
    [-0.83500624291190872, -3.0100387448217596, -1.2472158731015446, 1.9370891705806654],
    [-0.61728150693957284, -2.8798182278826023, -0.67139289769202648, -1.3539686423323598],
    [-1.5443915209996073, -2.1001904551266772, -2.5300662835391172, 0.86765835633091604],
    [-1.0961611397416087, -2.0658152219428132, 2.7790349062846875, 0.9745184453712924],
    [1.240760438271816, 1.4093511342004652, 0.64591225448264056, -1.2296559797224518],
    [1.6778075265519903, 1.4302900334802295, 0.028895874420926265, -0.91810534087753481],
]
star_star_1_loose_lst = [
    [-1.0527737270036117, -2.7621170326704987, -1.5559015047935532, 1.3708769641669489],
    [0.88738781263339805, 0.36402083383768363, 2.6598971655877373, 1.3953299609574565],
    [-0.82085407458240289, -2.8685781621664668, -1.138328420660323, 2.9105955375120245],
    [-0.76256050710239953, 2.8535980097302165, 1.1750690037362688, 1.7201598127191211],
    [1.1814128956066625, 0.13777824432097649, 2.5431793383159698, -1.771774315067729],
    [-1.2281222949625707, -2.4369697775256816, 2.7784103659019332, 2.7592774819442405],
    [-1.5409124405799919, -2.7205416589019009, 2.6838359497746245, -0.71579457014568071],
    [-0.210218959483496, 2.667892652802895, -0.21007825655306878, 2.3887528392777599],
    [-0.43517063489266972, 3.0845097452742527, 0.76723800508305651, -1.8861109315392497],
    [1.774543294888165, 1.018095661657576, -0.38600103766333138, -2.4707870190356465],
    [1.8184908857953361, 0.84277938922333695, -0.15830362136156495, 1.8287391576850895],
    [-0.14951248888139046, 2.7950600355205855, -0.32905572345441403, 0.40418528715569912],
]
star_star1loose_lst = [
    [1.6679948328878738, 0.14105225645065164, -2.3160595002314182, -1.0092744329458769],
    [-1.3641070020094475, 3.006915671433056, 0.87876830925151528, -1.0198621573103113],
    [-1.4205050459294255, 3.078717729185263, -0.61926122847437526, 1.455269343661648],
    [1.996836517254672, 0.30402635467674699, -1.2177879775501825, -1.8714445744558157],
]
w_strip1loose_lst = [
    [-1.1877980818382776, 3.0908140965136033, 2.5643831539870465, -1.7178783670933822],
    [-1.1877980818382778, -2.6151617110632355, -2.5643831539870456, -3.1056362492441583],
    [-1.3421828273353866, -2.5969300935689588, 2.5643831539870452, 0.30631407367199226],
    [-1.342182827335386, -2.0197205939662117, -2.5643831539870456, -1.0814438084787836],
    [1.6394224984499302, 0.12273044694942978, 1.0770223207753735, 1.9593075245191285],
    [1.6394224984499308, 0.90677165981343011, -1.0770223207753737, -2.2593074498460375],
    [2.0993392707370284, 0.42611693996126931, 1.0770223207753733, -1.5924703792971675],
    [2.0993392707370289, 1.2101581528252696, -1.0770223207753729, 0.4720999535172512],
]
w_strip_lst = [
    [-1.1862476804268163, -2.9994899812656386, 2.8263876295048935, -1.8915912003967748],
    [-1.5497210407978861, -2.8867778263039949, 2.1809990026242287, 1.3489777010932347],
    [-1.5841901109149064, -2.1118412402325202, -2.0696948161710793, -0.77601462834736079],
    [-1.2563814028011522, -2.0569680257939194, -2.7314370005527069, -1.1211494395117416],
    [1.6882306382363743, 0.48669510129948473, 0.48415173585818649, 1.9868324248931146],
    [2.0749106784006828, 0.53819543761494271, 0.93672429915381661, -1.2680892577785441],
]
Pos32TrianglesI = {
    # TODO: fill in more...
    # no solutions found for trapezium and parallel fold (for any triangles).
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip1loose_lst,
	trisAlt.strip_I: tri_strip_lst,
	trisAlt.strip_II: tri_strip_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.star_1_loose: tri_star1loose_lst,
	trisAlt.alt_strip_I: tri_strip_lst,
	trisAlt.alt_strip_II: tri_strip_lst,
	trisAlt.alt_strip_1_loose: tri_strip1loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: star_strip1loose_lst,
	trisAlt.strip_I: star_strip_lst,
	trisAlt.strip_II: star_strip_lst,
	trisAlt.star_1_loose: star_star1loose_lst,
	trisAlt.alt_strip_I: star_strip_lst,
	trisAlt.alt_strip_II: star_strip_lst,
	trisAlt.alt_strip_1_loose: star_strip1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip1loose_lst,
	trisAlt.strip_I: w_strip_lst,
	trisAlt.strip_II: w_strip_lst,
	trisAlt.alt_strip_I: w_strip_lst,
	trisAlt.alt_strip_II: w_strip_lst,
	trisAlt.alt_strip_1_loose: w_strip1loose_lst,
    },
}

###############################################################################
par_stripI_lst = [
    [0.63253059063857, 0.0, -2.98282064597178, -0.93327919097016],
    [-0.93113237429749, 3.14159265358979, 0.15877200761801, -0.93327919097016],
    [0.13688981744294, 3.14159265358979, 0.896004297407, 1.87419729891036],
    [1.700552782379, 0.0, -2.2455883561828, 1.87419729891036],
]
tri_stripI_lst = [
    [0.5208870126758, 0.0, -2.95529376164387, 2.2694172235287],
    [-1.04277595226026, 3.14159265358979, 0.18629889194593, 2.26941722352870],
    [0.5208870126758, 0.0, -2.95529376164387, -0.60785377735739],
    [-1.04277595226026, 3.14159265358979, 0.18629889194593, -0.60785377735739],
    [0.60260278918294, 3.14159265358979, -1.75709521874082, -2.53373887623240],
    [2.166265754119, 0.0, 1.38449743484897, -2.5337388762324],
    [0.60260278918294, 3.14159265358979, -1.75709521874082, 0.87217543006109],
    [2.166265754119, 0.0, 1.38449743484897, 0.87217543006109],
]
Pos32TrianglesII = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_I: par_stripI_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_I: tri_stripI_lst,
    },
}

###############################################################################
tri_strip_1_loose_lst = [
    [-0.02650967655387, 2.01156609697354, 2.03145116250301, -1.12794994868396],
    [0.64060490724162, 1.13002655661625, 2.91299070286029, -1.12794994868396],
    [0.64060490724162, 1.13002655661625, 2.02137772495892, 1.12794994868396],
    [-0.02650967655387, 2.01156609697354, 1.13983818460163, 1.12794994868396],
    [1.18999167580366, 2.01156609697354, -1.3421943760654, 1.12794994868396],
    [1.85710625959915, 1.13002655661625, -0.46065483570811, 1.12794994868396],
    [1.18999167580367, 2.01156609697354, -0.45058139816402, -1.12794994868396],
    [1.85710625959915, 1.13002655661625, 0.43095814219326, -1.12794994868396],
]
tri_strip_lst = [
    [0.76992497486360933, 0.94624022871632729, 3.0803702160830282, -1.3554280853678113],
    [-0.027892439365956069, 2.0135355382599829, 1.1365693454289998, 1.1300966239587744],
    [-0.17038567171338109, 2.692349840061993, 0.68719186423390977, -2.2850437463779456],
    [0.27367697466186752, 2.6735422903020791, -1.4278661736369687, 2.2346826212529747],
    [1.7889887751470579, 0.56584486671766454, 1.5850459818848297, -2.0045929968418328],
    [1.1391199990835519, 2.0596070208421637, -0.46567402798771518, -1.1822021274704628],
]
tri_star_lst = [
    [-0.68791496155213328, -2.495631829431924, -1.6419078311288882, 1.1433256399495644],
    [-1.1818027610722566, 2.4320010142774864, 0.92874590277388847, 0.84683804809139129],
    [2.2198614656215532, -0.096567017054908, 0.77956167705151769, -2.2491539403800163],
    [2.1029095361483163, -0.65195721245229965, 1.6431449954540396, -1.1190387484482498],
]
tri_star_1_loose_lst = [
    [-0.12190664938895671, 1.1300265566162546, 2.9129403918280805, 2.0059341963195623],
    [-0.18414110678214954, 1.1300265566162544, 2.4742247811307219, 1.0070777511188451],
    [-0.78902123318444584, 2.0115660969735392, 2.0314008514707957, 2.005934196319564],
    [-0.29824891637152512, -1.1300265566162544, -2.4481961533146572, -1.3233415223631617],
    [-0.85125569057763784, 2.0115660969735383, 1.5926852407734382, 1.0070777511188427],
    [-0.96536350016701444, -2.0115660969735387, -1.566656612957372, -1.3233415223631644],
    [0.90072312664293952, -2.0115660969735387, -3.0375722013401916, -0.91433273824831396],
]
star_strip_1_loose_lst = [
    [1.9059097830186296, 0.80649142107765925, 0.27608560811485156, 0.74755557501847036],
    [0.89781315887566426, 1.6079465028301179, 0.80430968907499489, -1.7428360613785676],
    [1.0191362328011477, 1.674854923558174, 0.56576556222028196, -1.6471597101417732],
    [1.9116955706405505, 1.3530078960808691, -0.29406763282292303, -0.72053597167619721],
]
star_strip_lst = [
    [1.1337834018831718, 0.3983033753431518, -2.1797039818918522, -1.5328428576100608],
    [0.90307327376725277, 0.63885212596863361, -2.8904845931275038, 2.0878012966188395],
    [-0.5420331566827894, 2.9979749183990561, -0.78779708747906696, 1.9216762369325204],
    [-0.30364010591499141, -3.129387164358028, -0.38799713202612018, -1.8798977866386348],
    [0.85606927913462993, 1.6261911991325377, 0.83086420958161999, -1.8031208657168927],
    [0.98417091688110503, 1.7002804053036806, 0.57313683688259065, -1.6982959819999621],
]
star_star_lst = [
    [-1.5736991265545797, -3.0667349493793918, -1.3224963640241336, 2.0645703328144185],
    [-1.5736991265545799, -3.0667349493793914, 0.83154827752661153, -2.0645703328144176],
    [-2.0171802376047618, -2.830548018756736, -2.9655222486233694, 2.0645703328144211],
    [-2.0171802376047623, -2.830548018756736, -0.81147760707262417, -2.0645703328144194],
]
star_star_1_loose_lst = [
    [-1.5737945477148021, -3.0666624419279898, -1.3229092592043097, 2.0648406080614592],
]
w_strip_1_loose_lst = [
    [1.6836334146307617, 0.32015374035989591, 0.72926498726807643, 1.944604590758332],
    [1.6836334146307614, 0.91077045415146374, -0.72926498726807676, -2.9129944714359173],
    [1.9818619620991027, 0.71754460954812993, 0.72926498726807565, -0.75587888626315891],
    [1.9818619620991023, 1.3081613233396971, -0.72926498726807587, 0.66970735872217591],
]
w_strip_lst = [
    [-1.1873278995710541, 3.0795212915489931, 2.5484729998858415, -1.7099925934432898],
    [-1.6002075589879676, -3.0554878503734844, 1.9505868416444843, 1.950374772184948],
    [1.6791195265785936, 0.28190668923148438, 0.7894679357209311, 1.9408382769201495],
    [2.0981469671043058, 0.35412999252799127, 1.17394892523243, -1.8111512922408615],
]

FoldedSquareAndO3Triangle = {
    # nothing found for parallel and trapezium fold (strip triangle alt)
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip_1_loose_lst,
	trisAlt.strip_I: tri_strip_lst,
	trisAlt.strip_II: tri_strip_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.star_1_loose: tri_star_1_loose_lst,
	trisAlt.alt_strip_I: tri_strip_lst,
	trisAlt.alt_strip_II: tri_strip_lst,
	trisAlt.alt_strip_1_loose: tri_strip_1_loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: star_strip_1_loose_lst,
	trisAlt.strip_I: star_strip_lst,
	trisAlt.strip_II: star_strip_lst,
	trisAlt.star: star_star_lst,
	trisAlt.star_1_loose: star_star_1_loose_lst,
	trisAlt.alt_strip_II: star_strip_lst,
	trisAlt.alt_strip_1_loose: star_strip_1_loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip_1_loose_lst,
	trisAlt.strip_I: w_strip_lst,
	trisAlt.strip_II: w_strip_lst,
	trisAlt.alt_strip_I: w_strip_lst,
	trisAlt.alt_strip_II: w_strip_lst,
	trisAlt.alt_strip_1_loose: w_strip_1_loose_lst,
    },
}

###############################################################################
star_x1loose_tri_lst = [
    [-1.2628164662835473, -3.0287646321582198, -1.6594292761916289, -2.4391112049649166],
    [-1.1854570877430721, -3.0266606464664583, -1.6136286683835692, 0.904928812656415],
    [-1.0253693623836726, 3.0374414336809767, -0.9520220342354806, -2.9806153253963243],
    [-0.91397300297180872, 3.0178673144808363, -0.92401304642001225, 0.38108659926911326],
]
w_x1loose_tri_lst = [
    [-1.0928890956439592, -3.1307789637073631, -0.91702207542335401, -0.82480405947614965],
    [-0.92982212002999942, 3.024591057000984, -0.71976731613330269, -0.42505107803618536],
    [-1.8952899113056829, -2.8467930549977187, 2.8874820712279763, -1.6197686093544466],
    [-1.8918815621841074, -2.8031349905706828, 2.9496796185696237, -1.4463061610643262],
    [2.4083780767783871, 0.48332799353581873, 0.11580368164733132, 2.3959095740410219],
    [2.4072575858674519, 0.60940947020623781, -0.18098227475252493, 1.0764558095943713],
]
triangle_x1loose_tri_lst = [
    [-0.55030286595056677, 2.0115660969735383, 2.1812590935692802, -2.0753593276938869],
    [0.1168117178449211, 1.1300265566162544, 3.0627986339265636, -2.0753593276938851],
    [-0.18888293454288321, 2.0115660969735387, 2.1723268073374027, 2.7912199209265327],
    [0.47823164925260536, 1.1300265566162548, 3.0538663476946861, 2.7912199209265314],
    [-0.48310085169005607, 2.0115660969735387, 1.2445292814054225, 2.3176277065430568],
    [0.18401373210543281, 1.1300265566162544, 2.1260688217627064, 2.3176277065430577],
    [0.23319250951046236, 1.1300265566162544, 2.0993664328269634, -0.54984536241775039],
    [-0.43392207428502627, 2.0115660969735387, 1.2178268924696791, -0.54984536241775128],
]
trapezium_x1loose_tri_lst = [
  [-0.60716198509448005, 2.6030814932021067, -2.8842475205596578, -2.5219565537882365],
  [-0.60716198509447983, 2.6030814932021067, 1.9973292316324089, -2.5219565537882369],
  [-0.60716198509447916, 2.6030814932021058, 2.7410053028930559, -0.88395775250525688],
  [-0.60716198509447983, 2.6030814932021067, 1.3393967479055353, -0.88395775250525688],
  [2.4090997208993179, 0.53851116038768643, 1.1442634219573844, 2.5219565537882365],
  [2.4090997208993179, 0.53851116038768687, -0.25734513303013706, 2.5219565537882378],
  [2.4090997208993179, 0.53851116038768665, 0.40058735069673668, 0.88395775250525643],
  [2.4090997208993179, 0.53851116038768665, 1.8021959056842567, 0.88395775250525666],
]
parallel_x1loose_tri_lst = [
    [0.27906714692447937, 1.1300265566162542, -1.8113841868964684, -2.2429670099657946],
    [-0.38804743687100995, 2.0115660969735392, -0.92984464653918408, -2.2429670099657937],
    [0.27906714692447904, 1.1300265566162542, -1.8113841868964693, -0.84135845497827422],
    [-0.38804743687100979, 2.0115660969735387, -0.92984464653918497, -0.84135845497827333],
    [1.5228705888803598, 2.0115660969735387, 1.8113841868964684, -2.3002341986115193],
    [1.5228705888803598, 2.0115660969735387, 1.8113841868964689, -0.89862564362399944],
    [2.1899851726758479, 1.1300265566162544, 0.92984464653918486, -0.89862564362399944],
    [2.1899851726758484, 1.1300265566162544, 0.92984464653918453, -2.3002341986115202],
]
star_stripI_star_tri_lst = [
    [-1.0248629078901548, 3.0367879503498347, -0.95004531859792607, -2.9819419706524459],
    [-0.90815984502062352, 3.0126250996311295, -0.91047126200357198, 0.37145275614090456],
    [1.5200936080774254, 0.28279384061834983, -1.7562793370655365, 2.9017993292662552],
    [1.4074958748480417, 0.29634532013454673, -1.8587346053407554, -0.37191199363966465],
]
FoldedSquareAnd1TriangleType = {
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: star_x1loose_tri_lst,
	trisAlt.star_1_loose: star_x1loose_tri_lst,
	trisAlt.star: star_stripI_star_tri_lst,
	trisAlt.strip_I: star_stripI_star_tri_lst,
    },
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: parallel_x1loose_tri_lst,
	trisAlt.star_1_loose: parallel_x1loose_tri_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_x1loose_tri_lst,
	trisAlt.star_1_loose: w_x1loose_tri_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: triangle_x1loose_tri_lst,
	trisAlt.star_1_loose: triangle_x1loose_tri_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_1_loose: trapezium_x1loose_tri_lst,
	trisAlt.star_1_loose: trapezium_x1loose_tri_lst,
    },
}

###############################################################################
par_1loose_lst = [
    [0.61336294993015139, 0.69387894107538739, -2.0238552489037858, -2.9635369142286225],
    [-0.5887359927166792, 2.4477137125144059, -0.27002047746476787, -2.9635369142286265],
    [-0.58873599271667931, 2.4477137125144055, -0.27002047746476787, -0.53505902972359287],
    [0.61336294993015195, 0.69387894107538739, -2.0238552489037858, -0.5350590297235911],
    [1.1885747858746869, 2.4477137125144059, 2.0238552489037858, -0.17805573936116925],
    [1.1885747858746867, 2.4477137125144059, 2.0238552489037858, -2.6065336238662007],
    [2.3906737285215178, 0.69387894107538739, 0.27002047746476765, -2.6065336238662007],
    [2.3906737285215178, 0.69387894107538739, 0.27002047746476748, -0.17805573936117014],
]
par_star_stripI_lst = [
    [-0.44916112192145868, 2.1122756168847676, -0.7901219832851325, -2.38655387121839],
    [-0.17280305940844282, 1.7081970333207814, -1.3032695012730278, -1.0165778617602879],
    [1.9747407952132805, 1.4333956202690123, 1.3032695012730287, -2.125014791829507],
    [2.2510988577262974, 1.0293170367050257, 0.7901219832851325, -0.75503878237140576],
]
tri_1loose_lst = [
    [0.37956950870979289, 0.69387894107538739, 2.3462528705670898, 2.4979607745861023],
    [-0.82252943393703848, 2.4477137125144055, 0.5924180991280722, 2.4979607745861014],
    [-0.6185882971665474, 2.4477137125144055, 0.46697885942260137, -0.39003731740480951],
    [0.58351064548028386, 0.69387894107538739, 2.2208136308616186, -0.39003731740480863],
    [0.79647217452131636, 2.4477137125144055, -1.8166927760056151, -1.5509008741736849],
    [1.9985711171681473, 0.69387894107538717, -0.062858004566597181, -1.5509008741736849],
    [1.1862152160835135, 2.4477137125144055, -1.9683107133329685, -0.1317534141689487],
    [2.3883141587303451, 0.69387894107538728, -0.21447594189395058, -0.13175341416894693],
]
tri_star_stripI_lst = [
    [0.34664617344104431, 0.86790421007680063, -2.9183524563195662, -2.5357131716593115],
    [0.44342922384400701, 1.2043971571230043, 2.9678152262457984, 2.733862482677079],
    [-0.13757996544884257, 1.6084570481928555, 1.7354925345426517, 2.2595854205169754],
    [-0.15948643486139244, 1.6226430978740538, 1.7262559226641492, -0.6211270320711888],
    [0.10521042922568168, -2.9211684805913882, -2.3228638659052492, 0.98904570975942896],
    [0.34713223891179412, 2.8450993122289434, -1.9905243346719468, -2.0195695653151535],
    [1.865501565526734, -0.14072763828438362, 0.97247958376766686, 0.92915754697574027],
    [2.2654707305709847, 0.91371298454315442, -0.43647863663936182, -0.53238197326078485],
]
tri_stripII_lst = [
    [-0.69362254088141972, 2.3837340341851765, 1.1254019588348196, 2.8035555441575717],
    [0.09629061756709166, -2.9109224843350177, -2.3538835609175552, 1.038374310605497],
    [1.1733246742281231, -0.24756466527240129, 1.1439536032835247, 2.8377184430643179],
    [1.3706977170512502, -0.3517691701944754, 1.190005722659377, 1.719526046231636],
    [1.3104947093083925, 1.1746350130155665, -1.0755532787950095, -2.0705582882918172],
    [0.47844907061730613, -3.1174177208505096, -1.8009878851693211, -0.52451906799578474],
    [0.5195960468845211, 0.76355637010840083, 1.8325229369164608, 0.46624698504758744],
    [1.3341087637964673, 2.0888137803893021, -2.3283421126882242, 0.8485925321395964],
]
star_1loose_lst = [
    [-0.81142273548841504, 2.8508340392863452, 1.1821602496530978, -2.7004737715146279],
    [-1.2150631571732222, 2.930066718671418, 1.0093708960546925, 2.4200589119837703],
    [-0.94465584247634504, 2.8763828539672271, -0.40718613561262629, 2.9658635199935985],
    [1.1941233866437073, 0.16137415712460745, -2.2926660678148885, 0.036628487339837257],
    [1.2037784863527474, 0.13386242322661238, 2.5407786079721917, 2.4394229948156165],
    [-1.3252358663291748, -2.8873433152533288, -2.1613890118628927, 1.329697667731047],
    [1.3681604086070356, 0.10811746779092324, -2.3511333777261538, -2.9888416412977299],
    [1.4710558097802924, 0.14753269846663145, 2.5490920903942116, -2.9148875538767927],
    [-1.4920762936112058, -2.9327712260677026, -2.2315284208018982, -1.8685230956260446],
    [1.5426055759626391, 0.38028370870508671, -1.5655325497615529, -0.64108898782938439],
    [-1.5511696522087874, -2.7239330767675836, 2.6824635604539662, 1.6956124002136272],
    [1.6515812629163171, 0.36187359223971838, -1.4292707661290027, 2.6105894530132998],
    [-1.8169852277814136, -2.7454551751310121, 2.6736060179090133, 0.74151399711279353],
    [-0.68546957884664905, 2.7812753831524839, -0.31603033027855965, -0.038301442338051217],
    [1.9993967505362247, 0.65298011622705887, 0.040397625879475686, -1.6007926047434831],
    [2.3955447954775768, 0.55231438005714073, 0.13662981090526655, -0.30328035155114197],
]
star_star_stripI_lst = [
    [-1.2226037175057429, -2.9920503841257089, -1.7343475784738542, 1.0012029614658839],
    [1.7036687157462407, 0.48617998982301736, -1.1336552735758829, -1.028655093133735],
    [-1.8074078896180805, -2.7431759290222559, 2.657771875181989, 0.7911784998171143],
    [2.2762805918685358, 0.62193558416884642, 0.28329365947415813, -0.95529926140710941],
]
w_1loose_lst = [
    [1.1942319584330798, 0.16141093995103512, -2.2722544084743985, -0.03635132578960576],
    [-1.1885380676330068, -3.0610248115044425, -1.0277997109937944, -1.5603407400774909],
    [1.4940970401409459, 0.33974563286371656, -1.9878164741848501, 0.60200250434108049],
    [-1.8891417412341949, -2.7602647238348843, 3.0138377656983444, -0.62198120129139323],
    [-1.9113714540647924, -3.050180727953578, 2.616718600132196, -2.1013644306710688],
    [-0.68551804530956328, 2.7812528882839227, -0.33722704582774199, 0.038253670958501296],
    [2.3984203038164815, 0.32870888413382504, 0.38947670319288008, 2.6530947918873418],
    [2.4090765221893227, 0.54777022088716831, -0.021088695850087547, 0.285536611668055],
]
w_altStripII_lst = [
    [1.2318509277494007, 0.6643160579801346, -2.744418646003985, 2.323920148061275],
    [-0.81465964210344155, -3.0054914029764239, -2.9266597991462309, -1.0134531893522061],
    [-0.55505340313710294, -2.6912521610564504, -1.0978232075774352, -0.81706838986078889],
    [1.3090851977339995, 0.60112461442647824, 0.32074052738904008, -2.6215687994030152],
    [1.0611747578635415, 0.99830847874257844, -1.4270594225790028, -0.8051188586396103],
    [1.066868042531105, 1.1968659256814389, -0.48555269009589797, 1.4418226589823266],
    [1.0553619665365643, 1.124746638283936, 1.124833667408607, -1.3391431043836333],
    [1.3759709132130249, 1.4459383635562011, -0.34025212696833673, -1.1232395462465981],
]
trap_1loose_lst = [
    [-0.60716198509447983, 2.6030814932021067, -2.2110608867701069, 3.1415926535897931],
    [-0.60716198509447983, 2.6030814932021067, 1.6436465359044474, 3.1415926535897931],
    [-0.60716198509447894, 2.6030814932021062, 3.0946879986210174, -0.26432165270370156],
    [-0.60716198509447916, 2.6030814932021058, 0.66621011411598585, -0.26432165270370156],
    [2.4090997208993179, 0.53851116038768621, -0.93053176681968619, 3.1415926535897927],
    [2.4090997208993179, 0.53851116038768632, 1.4979461176853448, 3.1415926535897927],
    [2.4090997208993179, 0.53851116038768665, 0.046904654968776709, 0.26432165270370095],
    [2.4090997208993183, 0.53851116038768676, 2.4753825394738072, 0.26432165270370078],
]
trap_altStripI_lst = [
    [1.2124023647597155, 0.27119539728104036, 1.3666060716728241, 3.1017062284243884],
    [1.3863262114938031, 0.17318734586590168, 1.6127779065788801, 1.9092451219713116],
    [1.3715160226244727, 0.39473270260020676, -2.9816530835874064, 1.4912612581938618],
    [1.3007690028269281, 0.69337056798703367, -1.3213595801817952, -2.4123285067265918],
    [-0.6559581408896904, 2.884004465695956, 1.430964506097764, -3.0693494546670199],
    [0.36574515632646992, 1.6253931431501165, 2.6750946776536777, 1.2698334581825153],
    [0.31828398151567305, 1.6608418416794877, 2.9483926407032182, 1.3043521740594883],
    [0.28966469975199982, 2.5970934449333467, -3.0111482939479641, -1.3261071338245802],
]
trap_altStrip1loose_lst = [
    [1.3660254037844386, 0.13157816916629891, -2.3575514407257927, 2.0645703328144203],
    [1.3660254037844388, 0.13157816916629861, 1.4971559819487616, 2.0645703328144194],
    [-0.36602540378443882, 3.0100144844234942, 2.3575514407257923, -2.0645703328144194],
    [-0.36602540378443893, 3.0100144844234946, -1.4971559819487616, -2.0645703328144194],
    [-0.36602540378443865, 2.2259732715594938, -2.3575514407257927, 2.0645703328144185],
    [-0.36602540378443837, 2.2259732715594942, 1.4971559819487621, 2.0645703328144185],
    [1.3660254037844384, 0.91561938203029858, 2.3575514407257927, -2.0645703328144211],
    [1.3660254037844388, 0.9156193820302988, -1.4971559819487608, -2.0645703328144203],
]
NoO3Triangles = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: par_1loose_lst,
	trisAlt.strip_I: par_star_stripI_lst,
	trisAlt.star: par_star_stripI_lst,
	trisAlt.star_1_loose: par_1loose_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_1loose_lst,
	trisAlt.strip_I: tri_star_stripI_lst,
	trisAlt.strip_II: tri_stripII_lst,
	trisAlt.star: tri_star_stripI_lst,
	trisAlt.star_1_loose: tri_1loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: star_1loose_lst,
	trisAlt.strip_I: star_star_stripI_lst,
	trisAlt.star: star_star_stripI_lst,
	trisAlt.star_1_loose: star_1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_1loose_lst,
	trisAlt.star_1_loose: w_1loose_lst,
	trisAlt.alt_strip_II: w_altStripII_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_1_loose: trap_1loose_lst,
	trisAlt.star_1_loose: trap_1loose_lst,
	trisAlt.alt_strip_I: trap_altStripI_lst,
	trisAlt.alt_strip_1_loose: trap_altStrip1loose_lst,
    },
}

###############################################################################
par_stripI_lst = [
    [-0.08705843892515, 1.59694187025424, -1.42186719773489, 2.99244917462248],
    [0.49431990960006, 0.84938187722147, -1.96438419341773, 0.66547727260192],
    [1.30761782620478, 2.29221077636832, 1.96438419341773, 2.47611538098787],
    [1.88899617472999, 1.54465078333555, 1.42186719773489, 0.14914347896731],
]
par_stripII_lst = [
    [-0.11267755272150, -3.08314500505623, 1.38775788215077, 1.84497131694611],
    [-0.11267755272150, -3.08314500505623, 1.38775788215077, -2.11536359084037],
    [-0.11267755272150, 1.62991562536377, -1.38775788215077, -0.90997250329841],
    [-0.11267755272150, 1.62991562536377, -1.38775788215077, 3.05036240448807],
    [1.91461528852634, -0.05844764853356, -1.38775788215077, 1.29662133664368],
    [1.91461528852634, -0.05844764853356, -1.38775788215077, -1.02622906274943],
    [1.91461528852634, 1.51167702822602, 1.38775788215077, -2.23162015029139],
    [1.91461528852634, 1.51167702822602, 1.38775788215077, 0.09123024910172],

]
tri_stripI_lst = [
    [0.25766456904200, 1.23370849975870, -2.88823619661503, -2.55090394983209],
    [0.37227438884523, 1.67003860855452, 2.91884346747981, 2.57168321468181],
    [0.05034522603356, -2.84141477449258, -2.72796058287286, 1.59467046494364],
    [0.39147088895531, 2.53782687789367, -2.06356261454296, -2.15294978396779],
    [1.42577972511488, -0.33679604065731, 1.16588964454869, 1.62899326768965],
    [0.20961214592661, 0.93160515044760, 1.93474923340972, 2.02846591163361],
    [0.51952198057739, 0.76902767459531, 1.83720793949263, 0.44126270894260],
    [1.89033377832022, 1.54063607626176, -1.46278122794071, 0.09760150131543],
]
tri_stripII_lst = [
    [-1.02088206579342, 2.92215615986198, 0.49874432369016, -2.27469172529300],
    [-0.30975269902860, 1.79044847695879, 1.62192662119917, -0.75561499170429],
    [1.92672214289072, -0.10378911932353, 0.94538490616541, 0.81967055842755],
    [1.91479704822392, 1.51052615552960, -1.41456430513121, 0.06151762464484],
]
star_stripI_lst = [
    [-1.11479786012615, -3.01136198833584, -2.54651752372087, 2.08855752521128],
    [-1.21826652797755, -2.99298511952277, 2.58417032463309, 2.46891518155374],
    [1.61481708939396, 0.49256598699692, -0.36015420508179, -2.08846039896341],
    [1.74404819266953, 0.48593702238864, 0.76207581689038, -2.35738396251911],
]
star_stripII_lst = [
    [-1.11461130570509, -3.01138793355110, -2.51934738959092, 2.06457033281442],
    [-1.11461130570509, -3.01138793355110, -0.36530274804017, -2.06457033281442],
    [-1.41754988476213, -2.93758682322695, -2.00684651699682, -2.06457033281442],
    [-1.41754988476213, -2.93758682322695, 2.12229414863202, 2.06457033281442],
    [1.61456486022518, 0.49259642882540, -2.54173379839552, 2.06457033281442],
    [1.61456486022518, 0.49259642882540, -0.38768915684478, -2.06457033281442],
    [1.88523668938655, 0.49674376007488, -1.21199946174003, 2.06457033281442],
    [1.88523668938655, 0.49674376007488, 0.94204517981071, -2.06457033281442],
]
w_alt_atripI_lst = [
    [-0.89547889748827, -3.01890952973987, 2.00192299941082, 2.06457033281442],
    [-0.89547889748827, -3.01890952973987, -2.12721766621801, -2.06457033281442],
    [-0.68153184629161, -2.94538811002813, -2.75594521707258, 2.06457033281442],
    [-0.68153184629161, -2.94538811002813, -0.60190057552184, -2.06457033281442],
    [1.18246612652976, 0.71940546828616, -2.77214313178643, 2.06457033281442],
    [1.18246612652976, 0.71940546828616, -0.61809849023568, -2.06457033281442],
    [1.39159603088392, 0.55424480380267, -0.60305675188567, 2.06457033281442],
    [1.39159603088392, 0.55424480380267, 1.55098788966507, -2.06457033281442],
]
w_alt_atripII_lst = [
    [-0.89515429888633, -3.01887822399782, -2.09960357585013, -2.08823628536480],
    [-0.80526172599003, -3.00308178439659, -0.98732926243628, -2.43419758675807],
    [1.34493627420240, 0.57859595525542, -1.88133557756927, 2.65837008086174],
    [1.39251471695486, 0.55381552638265, -0.62315016480008, 2.08557475421552],
]
trap_alt_atripI_lst = [
    [1.37513217304298, 0.38161199538121, 0.73933240627855, 1.50858819316313],
    [1.26728811420110, 0.64538993311463, -1.86221766328240, 1.24098803506008],
    [0.90922235933844, 1.14789375852737, 1.20694992843107, 1.04870138148561],
    [0.65127907401936, 1.39756313984052, -1.94580249342009, 1.10727914914277],
    [1.35874499282133, 1.35818756471779, 1.71045465055478, -1.44026580355118],
    [1.14208824990637, 1.72603787032894, -1.13965255265727, -1.11624198566344],
]
trap_alt_atripII_lst = [
    [-0.62733301528653, 2.98274108690679, -2.80119010201015, -2.77982863376248],
    [-0.62733301528653, 2.98274108690679, 1.15914480577633, -2.77982863376248],
    [1.21769219373579, 0.36925126784640, -2.91442530699528, -2.97299720740092],
    [1.21769219373579, 0.36925126784640, 1.04590960079119, -2.97299720740092],
    [1.38222572563533, 0.35279275358404, -3.12412713146115, 1.54871690731114],
    [1.38222572563533, 0.35279275358404, 0.83620777632532, 1.54871690731114],
    [-0.31314273379578, 2.98942711952296, 1.57190002582026, -1.97892254968544],
    [-0.31314273379578, 2.98942711952296, -2.38843488196622, -1.97892254968545],
    [0.65102616496660, 1.39778197282034, -1.94649757899530, 1.10738416257284],
    [0.65102616496660, 1.39778197282034, 2.01383732879118, 1.10738416257284],
    [1.14172874232229, 1.72649858941196, 2.81921140330005, -1.11600414739872],
    [1.14172874232229, 1.72649858941196, -1.14112350448642, -1.11600414739872],

]
FoldedSquares_0 = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_I: par_stripI_lst,
	trisAlt.strip_II: par_stripII_lst,
	trisAlt.star: par_stripI_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_I: tri_stripI_lst,
	trisAlt.strip_II: tri_stripII_lst,
	trisAlt.star: tri_stripI_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_I: star_stripI_lst,
	trisAlt.strip_II: star_stripII_lst,
	trisAlt.star: star_stripI_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.alt_strip_I: w_alt_atripI_lst,
	trisAlt.alt_strip_II: w_alt_atripII_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.alt_strip_I: trap_alt_atripI_lst,
	trisAlt.alt_strip_II: trap_alt_atripII_lst,
    },
}

###############################################################################
par_stripI_lst = [
    [-0.7567470429582589, -2.5576199555507575, 1.1795454244237868, 2.3059857893662681],
    [-1.1678661078471526, -2.8121029764287098, 0.68295574950813442, -2.7139655274915295],
    [-0.41297524742965674, -3.1174972074287144, 1.7516400761892816, 2.79576640194874],
    [0.077508458941164482, -3.1132425768136569, 2.5081433873465593, -1.0130287751739537],
    [1.3083497604815739, -0.1140786213581082, -1.285439266528412, 2.7129193530365638],
    [0.25783404055203479, -2.5546307363274132, 1.7636722787631758, -2.2647077563220268],
    [1.7906535720932244, 0.18641414197294012, -0.10475933583315822, -1.4181438292384954],
    [1.7043186392248841, 2.5563292347776989, 1.7243790607070171, -0.22076373594903842],
]
par_star_lst = [
    [0.16424126714814655, 2.9498362993661056, 2.3874240497328016, -1.1058248893059073],
    [-0.19882278292562994, 2.9032159671887756, 1.5610799938533146, 2.4783868428030944],
    [0.25790649607642102, -2.5549946510779682, 1.7632951187038364, -2.2653071966369556],
    [0.93204577472517836, 1.5477756634948827, -0.99061381559026351, 2.1311786323813067],
    [1.4034311724568889, 0.99681726039765606, -1.4331975048281924, 1.4674950784683738],
    [1.8605312748771268, 2.3066435603055355, 1.4909152805218127, -0.17100514406483569],
]
par_star_1_loose_lst = [
    [0.47092324271706787, 2.4477137125144059, 2.202048646419386, -1.6406340012575686],
    [0.46605546632809519, 2.4477137125144055, 1.6180811587323642, 2.1466265883588198],
    [-0.023098085998088189, 2.4477137125144059, -0.43468821406451319, 0.094928336006570621],
    [1.1790008566487422, 0.6938789410753875, -2.188522985503532, 0.094928336006570094],
    [1.6730221853638987, 0.6938789410753875, 0.44821387498036724, -1.6406340012575686],
    [1.6681544089749261, 0.6938789410753875, -0.13575361270665454, 2.1466265883588189],
    [0.35276606332980004, 2.4477137125144059, 0.013198617843297455, 0.76713308744683972],
    [1.5548650059766309, 0.69387894107538739, -1.7406361535957213, 0.76713308744683828],
    [1.6426004818639248, 2.4477137125144059, 1.4471492405143849, 0.831403385559082],
    [1.7634098860459992, 2.4477137125144059, 1.6101771888421501, -0.48553086554936442],
    [2.8446994245107557, 0.69387894107538739, -0.30668553092463391, 0.83140338555908322],
    [2.9655088286928302, 0.69387894107538739, -0.14365758259686778, -0.48553086554936353],
]
par_alt_stripI_lst = [
  [0.0047144028745294674, 2.7379903413104696, 2.3019027983841802, -2.1187588498957375],
  [-0.17436128088859995, 2.6894420333711286, 1.7141875439587961, 3.1247798251350067],
  [1.4396160191727976, 0.40355341653010723, -0.04013610323553074, 2.9983967846607156],
  [0.048561335512176722, 2.7351785156391344, -1.3946897245476517, 2.1212283205760323],
  [1.6545772510170484, 0.45992003113628765, 0.47265909450437693, -2.1788073638335046],
  [0.29960308976706956, 2.6625356986245183, -0.95458098169673544, 3.0854419263781132],
]
tri_strip_1_loose_lst = [
    [0.44754647931560976, -0.69387894107538717, 2.9283416339989277, 0.73546911098847945],
    [-0.75455246333122072, -2.4477137125144059, -1.6010089017416407, 0.73546911098847867],
    [0.38799249591741464, 0.69387894107538739, -2.7481934015040062, 1.9217305374713831],
    [-0.81410644672941612, 2.4477137125144059, 1.7811571342365617, 1.9217305374713831],
    [-0.00078144583645169618, -0.69387894107538806, -2.9105032748773145, 2.4817759393050522],
    [-1.2028803884832828, -2.4477137125144059, -1.1566685034382953, 2.4817759393050522],
    [-0.086883722775554978, 0.69387894107538728, 2.7871813057043346, 1.6142712147035869],
    [-1.2889826654223862, 2.4477137125144055, 1.0333465342653172, 1.6142712147035869],
    [0.35471767008943322, -2.4477137125144059, -2.7608709502900197, -2.9045268190967177],
    [1.5568166127362641, -0.69387894107538717, 1.7684795854505484, -2.9045268190967177],
    [0.62055916052969939, -2.4477137125144059, -2.8449818089911982, 1.385740962136718],
    [1.8226581031765303, -0.69387894107538806, 1.6843687267493701, 1.3857409621367169],
    [1.2368627691314991, 2.4477137125144055, -1.9640264730105983, -1.9996760072702218],
    [2.4389617117783304, 0.69387894107538728, -0.21019170157157951, -1.9996760072702209],
    [1.7865787995653386, 2.4477137125144055, -1.5073593882667398, -0.53632250360021327],
    [2.9886777422121695, 0.69387894107538728, 0.24647538317227813, -0.53632250360021239],
]
tri_strip_I_lst = [
    [0.3229916886147739, 0.81787517156584844, -2.8741358849685965, 1.8522540043177553],
    [-0.77636060799865281, -2.0814047540194585, -1.7395852994618313, 2.7327139497350528],
    [-0.047234873250024893, 0.062584607124783656, -2.3867114485882062, -1.4845398163390682],
    [-0.29248954348814288, -2.184433682880405, -2.221824098830032, 1.0663512807465978],
    [-1.0179992246247618, 2.1389419876824682, 1.5111635925907958, 1.5357216696993703],
    [-1.4423668580203781, 2.5474174247594599, 1.2899778817864502, -0.78592785211070204],
    [1.6689708457019785, -0.78128633249251678, 1.8328968077092904, 1.4217553695367278],
    [1.7238166448334697, -0.55602013972733566, 1.5285934807432371, -2.8219530729171161],
    [2.3725193365280375, 1.1912951724252547, -0.65696083790277093, -1.7189176159276407],
    [2.3859054963765121, 1.4371083333570338, -0.76500995390103821, -1.3932613525357089],
    [1.7220319138319975, 2.5355822994405028, -1.6398259210337107, -0.19008008335461657],
    [1.9368973957782367, 2.1917281735384373, -1.3319724630965899, -0.96931527394340833],
]
tri_strip_II_lst = [
    [0.31858957474878097, 1.1416604314471859, -2.9368327011596094, 1.6986710529044275],
    [0.13597220632768922, -0.51427349788053078, -2.3135303788528994, 2.9740547563648829],
    [-0.40803835417222334, 1.2856123625310785, -2.9685366621097917, -1.3164309201117295],
    [0.13409835406810244, 3.0016485658010548, -2.9693765422757559, 0.69562341531837191],
    [0.18538185465246507, 2.9844926025111178, -2.446284212107209, -0.51584488859612954],
    [0.59520985104517565, -0.76917621844761541, -2.7886091007968554, -0.70538824942030853],
    [-0.41715794679440416, -2.3261803383974979, -1.2680255115546339, -0.76488269498585737],
    [-0.19301695451948814, -2.3242717189703925, -2.0154625099814298, 0.69859799471544493],
    [1.2147491257078284, -0.12084562635447682, 0.98864515115733909, 0.77202589564432422],
    [1.04260475400867, 0.27798862722358297, 0.76229978633982465, -2.257570972989444],
    [-1.1814934404520314, -3.0213049544793984, 1.480277878088069, -2.7139255175547365],
    [0.77196244815248694, -1.3551550155325032, -2.7385999616191286, -2.3366977384978771],
    [-1.2859958497971042, -2.6289772474289359, -0.54837631731554026, 2.6832571873715736],
    [0.52783872759654749, 2.4740716928316417, -3.0953396413849674, 0.45861159649013017],
    [0.60540787695390219, 0.75782334028723675, 1.8189431132877809, -1.1120219962473392],
    [0.79713298491614881, 0.53938481768732549, 1.2064008212528377, 0.46661717099783395],
    [0.98163637024194672, -3.0438473575821745, -1.8911399980068104, -1.7343103181788386],
    [1.0305381692032605, 3.0774413285023008, -3.0879269943189191, 1.8394271734448513],
]
tri_star_1_loose_lst = [
    [0.53322110854060689, 0.69387894107538717, -2.7479182974140643, -1.1770857909594907],
    [-0.6688778341062237, 2.4477137125144055, 1.781432238326504, -1.1770857909594907],
    [-0.22830290855591914, 2.4477137125144055, 1.4245996616377861, 1.947055154940466],
    [0.97379603409091275, 0.69387894107538728, -3.1047508741027827, 1.9470551549404664],
    [-0.16496706510379489, 2.4477137125144055, 0.29120719670181305, 2.164158557344718],
    [1.0371318775430354, 0.69387894107538728, 2.0450419681408318, 2.1641585573447175],
    [0.3605222308863405, -2.4477137125144059, -1.5447921122705353, -1.2442956469610822],
    [1.5626211735331701, -0.69387894107538806, 2.9845584234700349, -1.244295646961084],
    [0.50088247512095307, -2.4477137125144059, -1.6816368461803526, -1.4994950396935502],
    [1.7029814177677853, -0.69387894107538806, 2.847713689560214, -1.4994950396935547],
    [0.48150779101396946, 2.4477137125144055, -1.0988160829941984, -3.0453085123952626],
    [1.6836067336607996, 0.69387894107538739, 0.65501868844482158, -3.0453085123952661],
    [0.5898105401782201, 2.4477137125144055, -1.4739282664024023, 1.626395763310283],
    [1.7919094828250504, 0.69387894107538728, 0.27990650503661829, 1.6263957633102812],
    [-0.025024155704480189, 2.4477137125144055, 0.40755107877418256, 0.065662929961773031],
    [1.1770747869423515, 0.69387894107538739, 2.1613858502131995, 0.065662929961773031],
]
tri_star_lst = [
    [0.44390704949173498, 1.2490317464942158, 2.901465258810874, -0.85699420749519817],
    [-0.15138062756317877, 2.354675572919362, 1.4852499848169414, 1.8870512347068988],
    [1.3096463663498759, 0.48679814368217156, 1.7473229845568854, 2.6129268965237582],
    [0.63228897865292277, 2.4310485038531433, -1.5206671038941337, 1.6319055277130801],
    [0.90223122416310098, 2.1352569152314835, -1.0705938491221438, -2.7194462380612547],
    [1.6293765050296745, 0.66790870605198516, 1.2410701935992261, 0.81936466242206762],
    [2.3239137835991142, 1.054850849036572, -0.56479739374247373, 1.1459786116198973],
    [1.8721649845276422, 2.2931652533858013, -1.4262202854167221, -0.13919943851841854],
]
tri_alt_stripII_lst = [
    [-0.2519793138232207, 2.4968140805625003, 2.7835132577369133, -0.47092963435338664],
    [-0.076072920249210529, 2.7313496676005689, 2.2140423373196594, -0.79687434593069373],
    [-0.13780439608927375, 2.7113684739610235, 1.7314460412346691, 0.5076951362847506],
    [0.16675695221047909, 2.7112099155583604, -3.058923770578768, 0.74975905213282046],
    [0.24370538889821511, 2.6854042625898171, -2.5237311790072283, -0.52199523535077574],
    [0.27307281405404987, 1.6184898696528212, -2.9678134889305898, 1.3914155709236091],
    [1.1021077827759773, 0.54018457880892878, 0.400049374332487, -1.8736243329902047],
    [1.1934393078918768, 0.47341395959314642, 0.32553894817865342, 0.49884319995192072],
    [0.59668670327101236, 2.4961155013725516, -3.0645831443199167, 0.47077022051391104],
    [0.63112288319847576, 2.4728579738710508, -3.0313457949462519, -2.0201612193647707],
    [0.91150375944907125, 0.7506173434056046, 1.1388008131777525, -0.77149860513430468],
    [0.98410586375346043, 0.66049745122663139, 0.62343188848072639, 0.47400581409006826],
]
star_strip_1_loose_lst = [
    [-1.2886093788020956, 2.964815943857301, 0.94714796337781326, -0.86167491656400941],
    [1.4837476679871329, 0.15040610301462487, 2.5508157444993844, 1.0554740221898768],
    [-1.5935026984846863, -3.1030813951683034, 0.64751175146331297, 1.6672534194100663],
    [-1.6168611584364898, -3.1084578054758767, -0.73571105532666969, 2.4780275332794552],
    [-1.6455560842228454, -3.0936605676304039, -0.75505311109412432, 0.6892426278327326],
    [1.7743347117047907, 0.16529614343381113, -2.2879780105900425, -0.58618242384644681],
    [-1.8552558904403698, -2.9295006522436591, -2.2269136959181823, 1.9724553313503881],
    [-1.8455594597934575, -2.741712633158067, 2.6751648858910451, 2.7725765853069539],
    [1.9454899298919761, 0.21289904619267266, -2.2257658739744697, -2.5349321080174625],
    [1.9228504842556489, 0.36613806142495114, 2.6608195214036061, -1.980782578171957],
    [-2.0246972300741093, -2.8979569747018168, -2.1790662348119323, -2.4083133214718906],
    [2.0731170903375711, 0.30007358064874612, -1.206879980193821, -1.4678973902617738],
    [2.2820275458670953, 0.30895022645769316, -1.2317634191118314, 2.7982565241695814],
    [-2.3041050062542743, -2.5289468493657723, 2.751900085154634, -0.127245920437006],
    [2.4456750673680032, 0.55520404439515125, 0.13391170067068536, -2.1687272266355269],
    [2.9999859391315153, 0.84494216053378535, -0.16077962510243538, -0.30248301525127808],
]
star_strip_I_lst = [
    [-0.94021209022315944, -3.0217762191983271, 1.1904476873012182, -2.1849009768517131],
    [-1.5633062556763173, -2.880857730915654, 1.0794266691547829, 1.6705071667975502],
    [1.531593550592016, 0.50685693288740097, 2.0639025426068445, 2.1668883938221235],
    [-1.8240389496128522, -2.7305907324403309, 2.6120890276133206, 2.8093256696338318],
    [-1.9550854004868152, -2.5907745082892268, -0.7811801285233777, -0.62781434178852091],
    [1.9161275294575109, 0.50139673186948264, 2.40555731922748, -1.9990935602305626],
    [-1.9666252862198721, -2.36733007082143, -1.4901365561776592, -2.1159834288906438],
    [-1.9787383439665316, -2.3943495346256398, 2.226353123784091, 0.79736686374948107],
    [2.4731335147261273, 0.8099382695258649, -2.1139167359628273, 0.85290899148983845],
    [2.4450230241099296, 0.76178967903373951, 0.44070831888194295, -2.2047219789681867],
    [2.4904295000032617, 0.92343862154126111, -1.7957899696262389, 1.8656695898525291],
    [2.4880304662844157, 0.85555869332064116, 0.45903094420168589, -2.0102221422631006],
]
star_strip_II_lst = [
    [-0.93627625766293587, -3.0216332582064833, 1.0454044898785568, -2.0748285317199304],
    [-1.0951540341649171, -3.013941088474497, 1.5501978842799398, -2.3247447063650855],
    [1.5156384900400237, 0.51064712409938262, 2.2007296541104857, 2.0709195738125206],
    [1.5956016565130988, 0.49509884315157149, 1.8304299138634068, 2.3139476385819755],
]
star_star_lst = [
    [-1.1166220650834773, -3.0111068393674589, 1.2898543660370763, 1.576423957151694],
    [-0.72418179468738419, -2.9720370816006825, -1.0625021690419914, 2.793971652574236],
    [-0.69871823672962552, -2.9572640515061042, 0.89332342187773062, -2.4172910964970593],
    [1.3057104508490669, 0.60343920210079849, -1.9883170706662447, -0.84776923369277846],
    [1.2165558597842352, 0.6798714540025047, -2.2719843782724531, -2.6083749902076563],
    [-0.76019293502482277, -2.9883766660755398, -1.1326134996744575, 1.0290022304043998],
    [1.2039313484764487, 0.69366804357949619, 2.0687532282216416, 2.4013635460165221],
    [1.6133767295164423, 0.49274081728097313, 2.0864147089450444, -1.5924505136908014],
    [-1.6031592488626059, -2.117926033975337, -2.419211930467323, -1.6249261857957453],
    [-1.9888060480369338, -2.4302992210674619, -1.30373469355483, -0.075237188048550507],
    [2.3311235749218375, 0.6556741433400376, 0.35110586968738433, 0.7540617642124765],
    [2.4913387275983423, 0.87753358321630937, -1.9228555948184045, 0.60722472228157653],
    [2.4345904524874205, 1.050542134556306, -1.4291020765511444, 1.6975305975612205],
    [2.4364069542643874, 1.0480805569254574, 0.46321427231467815, -1.6604616803495063],
]
star_alt_stripII_lst = [
    [1.152561218051865, 0.76115920365358214, -0.94537987231516674, 1.3128298724115872],
    [1.2052877476096397, 0.69214121092973746, -0.28578037584997862, 0.81620274459505904],
    [1.113083515568694, 0.83173732068462791, -0.4548798840217243, -1.3821155966434713],
    [1.09614239994711, 0.87084471976089139, -0.68690764335104149, -1.1792473940000052],
    [-1.097210202458091, -2.0656663297508278, -1.336563405219624, -2.8664687930907049],
    [-1.2722428051652059, -2.0574764474288187, -1.4425105536116885, 1.5259593718474607],
    [1.5963195984605707, 1.4430004545932182, -2.0360046660892923, 2.8703503026046464],
    [1.765725210396794, 1.4112846723269685, -1.8740641622527097, -1.4489512167137741],
]
w_strip_1_loose_lst = [
    [1.4139451098490885, 0.2014046951678754, -1.3176747948377869, -1.1084080769059224],
    [-1.4609357479731273, -3.117155914123718, -2.8162180770136196, 1.6860916894702607],
    [1.4788417929182787, 0.25690429859811731, -1.2004395281616702, -1.0073164068110056],
    [-0.92958729311945587, 2.8341018025092768, -1.1041307296800102, 1.3228058943466108],
    [-1.6939908929922325, -3.0916685215554116, -0.41355694353579064, -0.72932751437185672],
    [1.7894781578638141, 0.15767608577289036, -2.5753138050755799, 0.61191576547422333],
    [-1.7983473952432609, -3.1017432862445427, -0.6225488949408966, -1.7527166272761114],
    [-1.8459030378404431, -2.5194161814585971, -1.1768674558943681, 1.941901426028374],
    [1.9403023787156473, 0.19193694923390386, -2.2528353680861617, 1.2774588133574598],
    [-2.0452748451908849, -2.2404523677519528, 2.8530397462496673, 2.2689136711962563],
    [-2.1516840785785711, -2.8673975910878005, 2.1381033344648097, -2.3927870756794292],
    [2.241206960757324, 0.81694517710027015, -1.8626894271680845, -2.0310407012574299],
    [-2.2355191411547271, -2.0607923854182939, -2.88418874518903, -0.78106949447450269],
    [-2.305861563494418, -2.5288753011327474, 2.6809738932433329, 0.12973156964591862],
    [-2.4114717735539752, -2.2797925566560995, -1.840945314215694, -1.9740726211486797],
    [3.0110538400259124, 0.87452894641386369, -0.47746916484804114, 0.46062802041401163],
]
w_strip_I_lst = [
    [-1.9552532171035493, -2.5904932827050042, -1.1091132080894432, 0.77471927198996937],
    [-1.9904022740211729, -2.4402049795018628, -1.3307300916274567, 2.8070359091561619],
    [-1.9229008757588568, -2.6363259412938627, 2.3427589335872074, -1.8761532743727738],
    [-1.9159761412329999, -2.2976073310041039, 2.6974958977987229, 2.765818528939719],
    [2.4610317811099995, 0.78638559054164348, -1.7325025518229067, -0.90236202410875599],
    [2.4861659511530281, 0.84737916208120911, -1.651792610333251, 2.9060894961391694],
]
w_star_lst = [
    [1.3376206156217969, 0.58290224101339183, -2.4220064667879155, 0.94386501480171603],
    [1.3376206156217969, 0.58290224101339183, -2.4220064667879155, -2.5638045280763175],
    [-0.80300858893845395, -3.0024732664088409, -0.58021483191817058, -1.1160681545968467],
    [-0.80300858893845362, -3.0024732664088409, -0.58021483191816969, 2.3916013882811882],
    [-1.4443409031337078, -2.9282301946011251, 2.2297245422125682, 1.6372458420876921],
    [-1.4443409031337084, -2.9282301946011247, 2.2297245422125682, -1.1382699222138584],
    [-1.9888788059555398, -2.4306914710946539, -1.3447165477438814, 0.076711396803204934],
    [-1.9888788059555396, -2.4306914710946534, -1.3447165477438823, 2.8522271611047558],
    [-1.8390490114836313, -2.2319515915211294, 2.7330679731772856, 2.3807455052620483],
    [-1.8390490114836311, -2.2319515915211294, 2.7330679731772851, -1.1269240376159857],
    [2.4878822698836567, 0.85484835263680081, -1.642109119442086, -0.64037311188878121],
    [2.4878822698836567, 0.85484835263680103, -1.642109119442086, 2.8672964309892528],
]
w_star_1_loose_lst = [
    [1.0801360443877399, 0.44660563723172336, -2.5882037245435012, -1.824409455644231],
    [-0.84621027034276242, -2.9746288027843657, -0.60913171213819428, -1.1940931826453234],
    [-0.85986354995464576, 2.8090436792916034, -1.0867297669421969, 1.3532596872444298],
    [-1.2019247870081058, 3.0238808621111355, 2.3253054683948227, -1.517341689446404],
    [-1.3757157818148149, -3.0861922146360712, -2.8008806630300178, 1.55439852456142],
    [1.553538584331652, 0.67136306449653527, -2.290353153005503, 2.7198573158278876],
    [-1.5780347666129424, -2.7662177083930848, 2.2719014647700648, 0.72242564778111795],
    [1.635324452372801, 0.12911032762257688, 0.98405778420209955, 2.0295192720163051],
    [1.6735213218823779, 0.39044292297937166, -0.76564278755521631, 2.5059177035857618],
    [1.7605984483140233, 0.20178509499476879, 0.18623979032519788, 2.3660456779493018],
    [-1.7811070422035831, -2.5010954382767592, -1.198708066289754, 1.9194743299635293],
    [-0.17015990428719568, 2.808489165920486, -0.12196708112366839, -0.39709330721430458],
    [-1.8615375656896531, -2.1873412381675372, 2.7960336277421458, 2.1026270986315376],
    [2.0382394892154436, 0.44768020065760855, 1.0413212518052308, -1.5883538053249389],
    [2.2263563419110377, 0.82488093695709641, -1.8620156871633524, -2.0183058140656911],
    [-2.2319732372680896, -2.058344308262793, -2.8843455754445628, -0.7799532396104194],
    [-2.4084593692442815, -2.2760814603391495, -1.843789742763466, -1.9660464307906906],
    [2.7882835985088716, 0.74460408491879237, 0.32125145803991706, -2.5172080080132826],
]
w_alt_stripI_lst = [
    [-1.0587116752200472, -3.0178747161011126, 0.55854068799585121, 2.0709050936930722],
    [-0.91379944670743141, -3.0204225049941593, 0.042378472717632114, 2.3482347357221967],
]
w_alt_stripII_lst = [
    [-1.0518628814248174, -3.0184845175337411, 0.41051666040855855, 2.1808376045623659],
    [-0.57087037409509633, -2.5212644094456786, 1.7007185392775099, 0.77089923712724939],
    [-0.59862061070378447, -2.8499389934904333, 0.35619783865847587, -1.5948697354998096],
    [-0.55482280638325432, -2.6876272786261088, -1.0753035493389369, -3.0875531247893204],
    [-0.57287873121319366, -2.5132888848160624, -0.44116694441972637, -0.76515175763182519],
    [-0.67554234292394411, -2.2991972272453127, 2.5674253613159732, 2.7011086082598914],
    [1.0899952502071635, 1.2621869861884489, 2.0105003541681046, -1.5540254161711129],
    [1.0556568076011366, 1.1284160963283691, 1.1482132186176033, 2.6743484198809866],
]
w_alt_strip_1_loose_lst = [
    [-1.0052140019571569, -3.0643411608367765, 0.46137368668853895, 2.0657684726000354],
    [-1.0653728224898777, 2.930074182975269, -2.0820214811211706, 2.2121194873586676],
    [-0.99120848418862317, 2.8754453230516797, -1.7410612447117622, 2.0922324459343198],
    [-1.1986531726003384, -2.6025859035685164, 1.4849249475631261, 3.1114531282406648],
    [1.3541718665519769, 0.79941781237125542, 2.307083003223771, 2.1590990866637902],
    [1.6927179415376739, 0.92263069812862608, 2.9961051948772206, 2.2510630256404491],
]
trap_strip_I_lst = [
    [1.7773470439311565, 0.271353380292218, 1.1500317714215433, -0.72112734960646829],
    [1.7920270271671517, 0.24593525285183671, 1.4499942670533155, -0.13080674767894518],
    [0.11711226642177466, 2.5926644988921028, -2.7641764689170509, 2.8825731279273663],
    [0.28586842743153695, 2.485438388517303, -2.8326558611256707, 2.4275020761110526],
]
trap_star_lst = [
    [1.7567670867130292, 0.31527082389530692, 0.85439118547115456, -1.0596242049367826],
    [1.7567670867130294, 0.31527082389530708, 0.85439118547115456, 1.7158915593647679],
    [-0.39996307645075369, 2.867744142335614, 1.6115508351835963, 1.9111456152715665],
    [-0.39996307645075324, 2.867744142335614, 1.6115508351835981, -1.5965239276064702],
    [1.6814070220114301, 0.70266064691856123, -1.8410023529879229, -0.49783382671196108],
    [1.6814070220114299, 0.70266064691856123, -1.841002352987922, 2.2776819375895876],
    [0.35342124951098758, 2.4399242621370218, -2.8748092009744322, -1.2377052429007396],
    [0.35342124951098819, 2.439924262137021, -2.8748092009744308, 2.269964299977298],
]
trap_star_1_loose_lst = [
  [-0.94149073385616711, 2.4122634059310704, 2.6642428731234213, 2.6836278574648027],
  [-0.64915455540105227, 2.2888504623330603, 1.7145431558541002, 2.31193474241987],
  [1.6738630842696065, 0.76579322441585695, -2.0788284552547616, -0.13636009100836866],
  [1.7253610720842736, 0.41408057699021406, 1.3782131258996859, 0.47356983016803866],
  [-0.14341215083593531, 2.7413705673019448, 0.25081107661481905, -0.49782880141505359],
  [0.35276152818137774, 2.4403764011539755, -0.77313401869837062, 0.013279171222522201],
  [2.8732907875356686, 0.85261320086247028, -0.66311903215004353, -0.33052145042297365],
  [2.9702276697007508, 0.77256350155525422, 0.54265300573128616, -0.15007275145780774],
]
trap_alt_stripI_lst = [
    [1.3449468387356174, 0.55650985656546914, -2.3648520692410417, -0.95371663766669457],
    [1.3960632444478911, 0.22467122585882657, 1.3356852205430698, -1.8833336790824431],
    [-0.91154301599112286, -3.0035889928559545, -0.087043870534809997, 2.3881974173956522],
    [1.4394532171982712, 0.42622288065614516, -2.9789166957668134, -0.042112894142952939],
    [1.6613189986171, 0.19973600598914398, 1.9190263119771593, 0.3830301663687159],
    [-0.45274430193199594, -2.7745667863831693, -1.1605982914902979, -1.1273806430464433],
    [0.16095823069222048, 2.55786350193807, -2.7832738330431255, 2.7670137063298212],
    [0.170075248028427, 3.1116888302814871, -2.9312054455128034, -0.67045796444216066],
]

E1_1_V2_1 = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_I: par_stripI_lst,
	trisAlt.star: par_star_lst,
	trisAlt.star_1_loose: par_star_1_loose_lst,
	trisAlt.alt_strip_I: par_alt_stripI_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip_1_loose_lst,
	trisAlt.strip_I: tri_strip_I_lst,
	trisAlt.strip_II: tri_strip_II_lst,
	trisAlt.star_1_loose: tri_star_1_loose_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.alt_strip_II: tri_alt_stripII_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: star_strip_1_loose_lst,
	trisAlt.strip_I: star_strip_I_lst,
	trisAlt.strip_II: star_strip_II_lst,
	trisAlt.star_1_loose: star_star_1_loose_lst,
	trisAlt.star: star_star_lst,
	trisAlt.alt_strip_II: star_alt_stripII_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip_1_loose_lst,
	trisAlt.strip_I: w_strip_I_lst,
	trisAlt.star: w_star_lst,
	trisAlt.star_1_loose: w_star_1_loose_lst,
	trisAlt.alt_strip_I: w_alt_stripI_lst,
	trisAlt.alt_strip_II: w_alt_stripII_lst,
	trisAlt.alt_strip_1_loose: w_alt_strip_1_loose_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_I: trap_strip_I_lst,
	trisAlt.star: trap_star_lst,
	trisAlt.star_1_loose: trap_star_1_loose_lst,
	trisAlt.alt_strip_I: trap_alt_stripI_lst,
    },
}

###############################################################################
E1_V2_1_1 = {
    Heptagons.foldMethod.parallel: {
	# T_STRIP_1_LOOSE checked
	trisAlt.strip_I: [
	    [-0.88723458825223489, 2.141882400564767, -1.6003210505207557, -2.1477336329497003],
	    [-0.46394192201744533, 1.621367132395708, -2.2598634519652006, 1.9795265236502502],
	    [1.369996063091216, 1.2775041217213143, 1.159285287569392, 1.6506021591176481],
	    [1.6924229251436085, 0.6486291183982027, 0.12224970772778145, 0.47344275923684709],
	    [1.1322473734478125, 0.92172928555262157, -0.84249799334320841, -0.4404078030788714],
	    [0.77202842552825701, 1.458950137980036, -0.51098977526082567, 1.7677355683811697],
	],
	trisAlt.strip_II: [
	    [-0.80628139058344039, -3.0770738846902432, 0.32574461708117614, 2.8984049195569037],
	    [-0.80628139058343917, -3.0770738846902428, 0.32574461708117791, -1.0619299882295747],
	    [-0.98191238276040615, 2.2760373479649187, -1.3988586849381255, -2.0742239094057418],
	    [-0.98191238276040671, 2.2760373479649196, -1.3988586849381237, 0.24862648998736692],
	    [0.11745889730951228, 2.7078286844471098, 1.5964891737594025, -2.3427288731661262],
	    [0.11745889730951235, 2.7078286844471098, 1.5964891737594025, 1.6176060346203496],
	    [-0.31558106130084979, -3.0286381112933989, 0.70426173268803804, 2.1744284054677125],
	    [-0.31558106130085178, -3.0286381112933984, 0.70426173268803716, -1.7859065023187597],
	    [1.2266886452420742, -0.11435973944709499, -2.671838858625927, 2.9237628783373375],
	    [1.226688645242074, -0.11435973944709499, -2.671838858625927, 0.60091247894422717],
	    [0.74575327119206369, 1.4935951820064997, -0.47983302969801755, -2.1250684033724889],
	    [0.74575327119206392, 1.4935951820064999, -0.47983302969801755, 1.8352665044139869],
	],
	trisAlt.star: [
	    [-0.23711356273166503, -1.9485321387360326, 2.6588859204636641, 0.27438318799068728],
	    [0.72053887962315089, -1.0587432257454417, -2.4208448709388839, 2.557780857852499],
	    [-0.68553105174082019, -2.1533585028252888, 1.8701178320200809, 2.1722876094332859],
	    [-0.78308063986585608, 2.1025353267841864, -1.6776023307864767, -2.4292263298835519],
	    [-1.0411509803615471, 2.0614001164372842, -1.5922594420866378, -1.501159899411018],
	    [1.2522938796548637, -0.98083804367828442, -1.935663941193229, 0.23491468889408978],
	    [0.99088112864733657, -1.5719870350953116, -3.0363367612891796, 1.934857923624846],
	    [1.2677807905403493, 1.349174166603234, 1.3901333945718353, 1.7920226371545631],
	    [1.4151923776916036, 1.0700834951041776, 1.6105159681097811, -1.5804901550554682],
	    [1.7805383361277138, 2.5930036533142866, 2.155628521555963, -0.25525589134283511],
	],
	# T_STAR_1_LOOSE checked
    },
}

###############################################################################
EV2_1_1_1 = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: [
	    [-0.11815285518002175, 1.1300265566162542, -2.6666943060109767, 0.74240619546394604],
	    [-0.11815285518002185, 1.1300265566162542, -2.6666943060109767, -0.6592023595235732],
	    [-0.78526743897550999, 2.0115660969735383, -1.7851547656536928, 0.74240619546394626],
	    [-0.78526743897551043, 2.0115660969735387, -1.7851547656536919, -0.65920235952357231],
	    [0.80721664767262302, 2.0115660969735392, 1.8413746099426032, 2.8882547785611616],
	    [0.80721664767262302, 2.0115660969735392, 1.841374609942604, -1.9933219736309038],
	    [1.4743312314681118, 1.1300265566162542, 0.95983506958531906, -1.9933219736309038],
	    [1.4743312314681121, 1.1300265566162542, 0.95983506958531961, 2.8882547785611621],
	    [0.33554736079111025, 2.0115660969735387, 0.13507754436247588, 2.9113163310874537],
	    [1.0026619445865992, 1.1300265566162542, -0.74646199599480934, 2.9113163310874532],
	    [0.33554736079111031, 2.0115660969735387, 0.13507754436247588, -1.9702604211046122],
	    [1.0026619445865992, 1.1300265566162542, -0.74646199599480934, -1.970260421104614],
	    [1.948767114768535, 2.0115660969735387, 1.0952813698697135, -0.74117297563557116],
	    [1.9487671147685353, 2.0115660969735387, 1.0952813698697139, 0.66043557935194919],
	    [2.6158816985640239, 1.1300265566162542, 0.21374182951242893, -0.74117297563557027],
	    [2.6158816985640239, 1.1300265566162542, 0.21374182951242901, 0.66043557935195096],
	],
	# T_STRIP_I checked
	# T_STRIP_II checked
	# T_STAR checked
	trisAlt.star_1_loose: [
	    [0.1272521146225038, 1.1300265566162542, -2.7013720871504643, -1.1571432969827011],
	    [-0.31657120620753615, -2.0115660969735387, 2.0874018389941096, -2.6804514106117261],
	    [0.35054337758795251, -1.1300265566162544, 2.9689413793513943, -2.6804514106117256],
	    [0.33163190296615525, 1.1300265566162542, -2.6231167374645703, -2.011568318083226],
	    [-0.33548268082933391, 2.0115660969735387, -1.7415771971072855, -2.011568318083226],
	    [-0.53986246917298597, 2.0115660969735392, -1.8198325467931795, -1.1571432969827002],
	    [0.50134721199837395, -2.0115660969735387, 2.523836905483082, -1.5123197570607836],
	    [1.1684617957938626, -1.1300265566162544, -2.8778088613392199, -1.5123197570607845],
	    [0.7224155495110216, 2.0115660969735387, 2.1460373808231648, -2.7758823633083094],
	    [0.77619880626182314, 2.0115660969735392, 1.949364837754433, 3.001031058056975],
	    [1.3895301333065104, 1.1300265566162544, 1.2644978404658813, -2.7758823633083072],
	    [1.4433133900573123, 1.1300265566162542, 1.0678252973971478, 3.0010310580569741],
	    [0.74453706928701391, 1.1300265566162542, -2.1605812266607618, 1.1748948567416937],
	    [0.077422485491525597, 2.0115660969735387, -1.2790416863034757, 1.1748948567416957],
	    [0.89539750032701915, 1.1300265566162542, -1.945112968695673, 1.7278742032840342],
	    [0.2282829165315296, 2.0115660969735387, -1.0635734283383886, 1.7278742032840322],
	],
    },
}

###############################################################################
EV2_1_V2_1 = {
    Heptagons.foldMethod.parallel: {
	# T_STRIP_1_LOOSE checked
	trisAlt.strip_I: [
	    [-0.88408594790666351, -2.6183855720519347, 1.0501269916021272, 1.1971273110129381],
	    [-0.22760538611589995, -3.0236610436586213, 2.11302679381998, -0.91640479904880934],
	    [-0.52251694896221135, 2.5997714337408078, 0.66232680538683475, -2.5646397191527139],
	    [-1.4269100891653157, 2.6067810044366331, -0.75060291603265838, -0.27559411714724558],
	    [1.6340221198353193, -0.033542043905304908, -0.70697232682802547, 2.8638966029269191],
	    [1.8089288772642329, 0.52012948245346036, 0.69374371299410953, -2.8971788945574422],
	    [0.69884395353658446, -2.8069771099869012, 1.8437108042663022, -1.1531895022337846],
	    [1.077709726202364, -3.1036307944436721, 1.8621658729852575, -0.98775836501243575],
	],
	# T_STRIP_II checked
	trisAlt.star: [
	    [-0.22731540041596912, -3.0240646448069644, 2.1129035314111286, -0.91628785621601416],
	    [-0.50480379243482942, 2.5756637730618941, 0.63149867422394834, -2.533468953526004],
	    [0.076502159387365667, 2.0515059435039364, -1.1849051379104427, -0.055808237908243186],
	    [0.95964290258137042, 0.90745051647294228, -2.1939976175417506, 0.010390132229135252],
	    [0.58015497218584866, -2.7807568557619828, 1.7632838943468929, -1.2509335691929255],
	    [1.093514924401829, -3.1214400030810618, 1.8559408694853996, -0.98305725349491091],
	    [0.58059679846632384, 2.0960448430750178, -0.3442101553928012, 1.5665478800929149],
	    [1.4589569486498692, 0.56254775250378952, -2.0199206989622489, 0.31868709760073305],
	],
	trisAlt.star_1_loose: [
	    [0.7983547701346333, 2.0115660969735392, 1.872281317887972, -2.0534510888507267],
	    [1.4654693539301229, 1.1300265566162542, 0.99074177753068682, -2.0534510888507258],
	    [0.9259363275496203, 2.0115660969735387, 1.34591149276301, 2.3199269378316019],
	    [1.5930509113451092, 1.1300265566162542, 0.46437195240572482, 2.3199269378316014],
	    [0.76587365663353224, 1.1300265566162542, -2.1307305694483532, -0.070901323940957717],
	    [0.098759072838043263, 2.0115660969735392, -1.2491910290910679, -0.070901323940958605],
	    [0.62605684322029043, 2.0115660969735387, -0.44948550866281423, 1.7242216016858887],
	    [1.2931714270157797, 1.1300265566162542, -1.3310250490200985, 1.7242216016858904],
	],
    },
}

###############################################################################
E0_1_1_1 = {
    Heptagons.foldMethod.parallel: {
	# T_STRIP_1_LOOSE checked
	trisAlt.strip_I: [
	    [0.50066103037629761, 0.10882709339528368, -3.0023604609977097, 2.0140966266804252],
	    [-0.26467626788387844, 1.3556184534457512, -2.5057044393209624, -0.37593035276325448],
	    [0.59768551357833699, 2.2976093709187233, 1.957748903716789, 2.680385915412014],
	    [1.1429524922740333, 1.5736048530614808, 1.4958239993256488, -2.3460367600275269],
	    [1.5736719388603781, 0.43047731296230907, -0.60016386225970209, -0.8643352247702083],
	    [1.1985019611460941, 0.81163808272056326, -0.87522778313280014, 2.5763539010817778],
	],
	trisAlt.strip_II: [
	    # same as STRIP_I
	    [0.50066103037629739, 0.10882709339528418, -3.0023604609977097, 2.0140966266804243],
	    [-0.26467626788387821, 1.3556184534457512, -2.5057044393209624, -0.37593035276325537],
	    [0.59768551357833688, 2.2976093709187233, 1.957748903716789, 2.6803859154120149],
	    [1.1429524922740324, 1.5736048530614817, 1.4958239993256504, -2.3460367600275274],
	    [1.5736719388603781, 0.43047731296230912, -0.60016386225970209, -0.8643352247702083],
	    [1.1985019611460945, 0.81163808272056293, -0.87522778313280014, 2.5763539010817791],
	],
	trisAlt.star: [
	    [0.77388086277561663, -0.47671588141912213, -2.0645703328144203, -1.1813891329966086],
	    [0.55687811427288847, -0.092698175989828435, -2.0645703328144203, -1.8364158733093774],
	    [-0.3380876838223647, -2.0252123250547234, 2.0645703328144194, -2.6894906158962386],
	    [-0.33808768382236476, 1.8294950976198319, -2.0645703328144194, -0.98882783477242953],
	    [-0.010302871010737156, 1.7220455646424149, -2.0645703328144194, -2.0251071946673012],
	    [-0.010302871010737111, -2.1326618580321401, 2.0645703328144203, 2.5574153313884773],
	    [0.55687811427288958, 2.3357797085152017, 2.0645703328144194, 2.7461066527464011],
	    [0.77388086277561663, 1.9517620030859095, 2.0645703328144203, -2.8820519141204168],
	],
	# T_STAR_1_LOOSE checked
    },
}

###############################################################################
E0_1_V2_1 = {
    Heptagons.foldMethod.parallel: {
	# T_STRIP_1_LOOSE checked
	trisAlt.strip_I: [
	    [0.50683836006755412, -0.55412050029899795, -3.1353952031680756, 1.4076850366971332],
	    [1.2017422000545017, -0.06517682205741071, -1.3978871467946332, -1.0285723720758568],
	    [-0.1055728440591245, 0.58803505950606749, -2.7978540220757742, -0.53028808268086536],
	    [0.26812584150105478, 2.9326668323801521, 2.6745058047736587, 3.064051778503174],
	    [0.50152329137467944, 2.5536384613729495, 2.8194302930666062, -2.5643691546525198],
	    [0.84883637368334608, 0.47511664615920363, -1.4212897928521313, -2.7363094607078535],
	],
	trisAlt.strip_II: [
	    # same as STRIP_I
	    [0.50683836006755389, -0.55412050029899795, -3.1353952031680761, 1.4076850366971323],
	    [1.2017422000545022, -0.06517682205741071, -1.3978871467946323, -1.0285723720758559],
	    [-0.10557284405912462, 0.58803505950606805, -2.7978540220757742, -0.53028808268086181],
	    [0.26812584150105395, 2.9326668323801535, 2.6745058047736578, 3.0640517785031727],
	    [0.50152329137467966, 2.553638461372949, 2.8194302930666066, -2.5643691546525194],
	    [0.8488363736833463, 0.47511664615920329, -1.4212897928521304, -2.736309460707854],
	],
	trisAlt.star: [
	    [1.2076991237109906, -0.058931378634738962, -1.3877578821507743, -1.0260027929742392],
	    [1.2076991237109909, 1.5111932981248473, 1.3877578821507743, -2.2313938805162028],
	    [0.86741423589323685, 0.49955639999623797, -1.3877578821507752, -2.7895319152019757],
	    [0.86741423589323741, 2.0696810767558245, 1.3877578821507746, 2.2882623044356474],
	],
	# T_STAR_1_LOOSE checked
    },
}

###############################################################################
AllEquilateralTris = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: [
	    [0.12225322067129163, 0.69387894107538739, -2.8805347296708912, -1.4528097830759066],
	    [0.12225322067129135, 0.69387894107538739, -2.8805347296708907, 0.97566810142912352],
	    [-1.0798457219755391, 2.4477137125144059, -1.1266999582318729, -1.4528097830759075],
	    [-1.0798457219755393, 2.4477137125144059, -1.1266999582318729, 0.97566810142912264],
	    [0.48335670145489734, 2.4477137125144059, 1.9718085849819014, -1.3005095003723568],
	    [0.48335670145489718, 2.4477137125144059, 1.9718085849819014, 2.5541979223021967],
	    [0.069502909920064734, 2.4477137125144059, 0.86221483369683438, -1.4133895408640926],
	    [0.069502909920064929, 2.4477137125144059, 0.86221483369683449, 2.4413178818104626],
	    [1.271601852566896, 0.69387894107538739, -0.89161993774218384, -1.4133895408640926],
	    [1.2716018525668957, 0.69387894107538739, -0.89161993774218473, 2.4413178818104613],
	    [1.6854556441017283, 0.69387894107538739, 0.21797381354288348, -1.3005095003723577],
	    [1.6854556441017283, 0.6938789410753875, 0.21797381354288348, 2.5541979223021971],
	    [1.4967584913927861, 2.4477137125144059, 1.2849159913648354, 1.5024366351232004],
	    [1.4967584913927861, 2.4477137125144059, 1.2849159913648354, -0.92604124938183041],
	    [2.698857434039617, 0.69387894107538739, -0.46891878007418342, -0.92604124938183041],
	    [2.6988574340396174, 0.69387894107538739, -0.46891878007418253, 1.5024366351231997],
	],
	trisAlt.strip_I: [
	    [-1.156637817378058, 2.7544847680954581, -0.60432651389549186, -2.1952192586001704],
	    [-0.80659177867111587, 2.0380849613850587, -1.7484826657781838, 0.75631842380774827],
	    [0.42167356237852688, 2.5217075314325132, 1.9601130634313986, -1.1682581061100761],
	    [0.045985361816704901, 2.6195862264538823, 1.2488853709117418, 2.2391071949708214],
	    [1.6127089750792163, 0.8960600601261185, 0.59474532287192872, 2.7202541745041593],
	    [1.632164823313732, 0.45148184556249021, -0.4345281024844514, 2.2408843223541539],
	    [0.2700664528450854, 2.0991609559786299, 0.26487872604964213, 2.8244875350830063],
	    [0.65532847315761944, 1.6099414020433973, -0.36585112032953671, -2.2559584645024433],
	    [1.046029937161403, 2.7705999979927567, 1.2607488678219125, 2.5274815882531603],
	    [2.3225481937956785, 1.5804869294071295, 0.74234494088217806, 0.28406772970135918],
	],
	# index T_STRIP_II: no solutions
	trisAlt.star: [
	    [-0.68958505376778345, -2.7696838629629861, 1.8676782736688526, -2.8833852670220774],
	    [-0.19704139133793197, -2.4699975062528203, 2.5847963085157168, -0.94597526034129231],
	    [-1.0845032151713569, -2.7900809377096936, 0.72626261351302934, -2.9760746154612101],
	    [-1.0931182092639629, 2.7314368575690051, -0.64021128226658242, -2.3596477091653614],
	    [-1.2277270226021526, -2.7907417508085364, 0.7276977195917137, -2.5022421464560081],
	    [-1.2382185407715089, 2.7319533145320043, -0.64071803589591614, -1.8835010126493845],
	    [0.63325519828989496, -1.3781269897190276, 2.9949754009094858, -2.0258812783756817],
	    [1.0822514530522973, -0.98200247015339048, -2.9335495968145002, 2.3457373536690409],
	    [1.1898603046161322, -0.3136159062298125, -1.5302505921582226, 2.9405127532309492],
	    [0.52091537040053171, -2.0394160644242385, 2.5154785652852962, -1.4681786794801743],
	    [1.6788412682906029, -0.30530724663815345, -0.89030309765033433, -1.1053291855067311],
	    [1.5927868724261478, 0.90443394452585701, 0.69420736165576036, 2.8069802147078304],
	    [1.742300860519741, 0.5429616709670313, 0.57909026065007829, -1.9874363203388654],
	    [0.90745910529245521, 1.0979361913340906, -1.9819560030787446, 1.656761037113343],
	    [0.61445205337854325, 1.5406078029015788, -1.5599598916192576, 2.1201871496572462],
	    [1.3155499020279271, -3.0834911230708753, 2.2752628509264001, -0.60007527499206059],
	],
	trisAlt.star_1_loose: [
	    [0.28592011827864433, -0.69387894107538717, 3.0914363610021587, -2.7118862151736765],
	    [0.18803380976514264, 0.69387894107538739, -2.887492084887687, -1.6205232315712745],
	    [0.45405009105009386, -0.69387894107538717, 3.1070403302585325, 3.0489972727344448],
	    [0.34459144908216149, 0.69387894107538739, -2.8717533536288018, -2.1505358163794623],
	    [-0.7480488515967384, -2.4477137125144059, 1.3532055588195133, 3.0489972727344492],
	    [-0.85750749356466915, 2.4477137125144059, -1.1179185821897839, -2.1505358163794632],
	    [-0.91617882436818654, -2.4477137125144059, 1.3376015895631408, -2.7118862151736765],
	    [-1.0140651328816883, 2.4477137125144059, -1.1336573134486683, -1.6205232315712736],
	    [0.46052924938527157, 2.4477137125144059, 2.5454679368948545, -2.1792035409732051],
	    [0.47708107305485198, 2.4477137125144059, 2.1074649520189057, 2.690505533394651],
	    [0.63369573819626746, -2.4477137125144059, 2.2084094046000917, 1.7744881136624304],
	    [1.6626281920321024, 0.6938789410753875, 0.79163316545583573, -2.179203540973206],
	    [1.6791800157016832, 0.69387894107538739, 0.35363018057988738, 2.690505533394651],
	    [0.85196300238033951, -2.4477137125144059, 2.4495268503566252, -1.0637165671611601],
	    [1.8357946808430985, -0.69387894107538717, -2.3209411311404757, 1.7744881136624304],
	    [2.0540619450271707, -0.69387894107538717, -2.0798236853839418, -1.0637165671611601],
	],
	trisAlt.alt_strip_I: [
	    [0.93235951493659841, 0.72372151864305168, 2.5678387967597498, -2.8303636866264741],
	    [0.65343249380697788, 1.1119688351391888, 2.7106581674948429, 1.4580458665383971],
	    [-0.22444785652214838, 2.6329009520668167, -1.4249456406361194, 0.91699469560519553],
	    [1.6323215439058805, 0.44872705230103893, -0.44027661545401831, 2.2378183424979614],
	    [0.4054404184668336, 2.6111188109935153, 2.0172317871425705, -0.93499108692349253],
	    [0.0093481574444067243, 2.7378791412343815, 1.3834712542872376, 2.1039240061349336],
	    [0.045291963625279368, 2.7355176831379957, -0.47679188327396993, -2.1113912990582726],
	    [0.00047569079884044732, 1.9736740017112036, -0.54248283723196877, -2.8327117424217882],
	    [0.31733061328372675, 1.5619740362055883, -1.0152782426663229, -1.7218461726803298],
	    [1.7910858498272728, 1.275648680245812, 1.2915381327916533, -2.7230426015610747],
	],
	trisAlt.alt_strip_1_loose: [
	    [-0.2458627268578423, 2.4477137125144059, -1.9572001537966859, -2.7776851018991815],
	    [-0.24586272685784233, 2.4477137125144055, -1.9572001537966859, 1.0770223207753729],
	    [0.95623621578898865, 0.69387894107538739, 2.5721503819438811, 1.0770223207753737],
	    [0.95623621578898876, 0.6938789410753875, 2.5721503819438816, -2.7776851018991811],
	    [-0.24586272685784216, 2.4477137125144055, 0.19684448775405983, 2.7776851018991819],
	    [0.95623621578898865, 0.69387894107538717, -1.5569902836849581, 2.7776851018991819],
	    [0.95623621578898854, 0.69387894107538739, -1.5569902836849581, -1.0770223207753737],
	    [-0.24586272685784225, 2.4477137125144059, 0.19684448775406072, -1.0770223207753729],
	    [0.66725358606974494, 2.4477137125144055, 2.1402385984408081, -1.077022320775372],
	    [0.66725358606974527, 2.4477137125144055, 2.1402385984408081, 2.7776851018991824],
	    [1.869352528716576, 0.6938789410753875, 0.38640382700178966, 2.7776851018991811],
	    [1.8693525287165758, 0.69387894107538739, 0.38640382700178943, -1.0770223207753729],
	    [0.66725358606974505, 2.4477137125144055, -0.013806043109939381, -2.7776851018991819],
	    [1.869352528716576, 0.6938789410753875, -1.7676408145489564, -2.7776851018991819],
	    [1.8693525287165762, 0.69387894107538739, -1.7676408145489546, 1.077022320775372],
	    [0.66725358606974494, 2.4477137125144059, -0.013806043109938493, 1.0770223207753729],
	],
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: [
	    [-0.37928429671678865, 2.4477137125144055, 1.6378373600101694, 1.7262201018590639],
	    [0.82281464593004194, 0.69387894107538739, -2.8915131757303993, 1.7262201018590648],
	    [0.11022350887753472, 0.69387894107538739, -2.8422991804193738, -0.91434765817113828],
	    [-1.0918754337692962, 2.4477137125144059, 1.6870513553211941, -0.91434765817113828],
	    [0.94391492047936831, 2.4477137125144059, -1.9222060009118058, -2.7283852939517366],
	    [2.1460138631261989, 0.69387894107538739, -0.16837122947278793, -2.728385293951737],
	    [1.5133541296334956, 2.4477137125144055, -1.8700394125440489, 0.92215961894657994],
	    [2.7154530722803263, 0.69387894107538739, -0.11620464110503104, 0.92215961894658016],
	],
	trisAlt.strip_I: [
	    [0.1732276091010776, 0.52816572632161485, -2.6642171952579274, -1.0965317568448629],
	    [0.44145650182396207, 1.1775327063113552, 3.0063789276865482, 1.2998509746393099],
	    [2.15676029301398, 0.63581007425305769, -0.10722803069920772, -2.7622927773697259],
	    [2.348224522244744, 1.5453402553363258, -0.81158843987649387, 0.21360131904630464],
	],
	trisAlt.strip_II: [
	    [-1.0173740109769405, 2.6081392183549621, 0.91764171185396504, 1.6020518782220581],
	    [0.48393194675487911, 0.69822055524780546, 3.1395184514998871, 1.6231448463884188],
	    [-0.64401596851308196, -2.7041662846345611, -0.38486088835850207, -1.3721231856384577],
	    [0.33267295635061189, 2.4608364615215881, -2.3871208355396449, 1.11526694951064],
	    [0.55852224688630026, -0.012542151319290262, -3.0086952598356365, -0.52911961859599366],
	    [0.12757817118074782, -2.7334889232293249, -2.0453984179992979, 1.4428296473368063],
	    [0.52916328188241202, 2.3549754963670981, -1.765393882565494, -0.45976903825553439],
	    [1.2449077901618673, 1.4097225870241499, -1.5172047922936196, 0.48190675011859785],
	    [1.4414596133477495, 1.5973133245049287, -1.7722782507039287, -2.9729347475372325],
	    [1.5875150325514187, 0.45313005004235585, 0.066685464603295053, 0.76550570073051194],
	    [1.039845232110181, 0.94112881502226242, 0.58965675514450577, 0.82663293702223761],
	    [1.1454562603293188, 0.85688460754755436, 1.0954143444675379, -0.46124061444038489],
	    [1.4223102570117709, 2.242563681630851, -2.3775290002535199, 1.9342770873277209],
	    [1.3268711167367437, 2.4306309475346963, -1.2560278848749951, -1.8332160432187816],
	],
	trisAlt.star: [
	    [-0.23373296122987397, -0.55594518756283939, -1.9873999503517839, -2.4041323055445654],
	    [0.38242013446232487, 1.4957117315743427, 2.5100109947299027, 1.2218140754615865],
	    [0.50230694454076719, 2.6022651424384167, -1.7385581699404362, 2.6254348211587346],
	    [0.52698279932434811, 2.5678802552018256, -1.6975020157998433, 2.7696690282215037],
	    [2.1096695450758833, 0.50651073062025809, 0.066766734495951496, 2.136486936813264],
	    [2.3960734384866127, 1.3623591825189778, -0.73589587699331993, -1.480288847100689],
	],
	trisAlt.star_1_loose: [
	    [-0.43125127814039982, 2.4477137125144055, 1.6832581745906028, 1.7017370908192433],
	    [0.77084766450643161, 0.69387894107538728, -2.8460923611499656, 1.7017370908192442],
	    [0.031020143695965056, 0.69387894107538728, -2.894840990191526, -0.87286692360127027],
	    [-1.1710787989508655, 2.4477137125144055, 1.6345095455490424, -0.87286692360127027],
	    [0.66264076915238868, 2.4477137125144055, -1.6320607761245007, 3.0509505726235773],
	    [1.8647397117992193, 0.69387894107538739, 0.12177399531451848, 3.0509505726235773],
	    [1.725095568985058, 2.4477137125144055, -1.6767258051172735, -1.0919470058995833],
	    [2.9271945116318889, 0.69387894107538739, 0.077108966321745367, -1.0919470058995842],
	],
	trisAlt.alt_strip_II: [
	    [0.40270525358650344, 1.4518129028837676, 2.9770825524514546, 0.85644694759943363],
	    [0.25478450050786922, 1.6417862816828479, -2.9572505411842669, -0.46334122839522873],
	    [0.24825380053694687, 2.6836656977283422, -2.5022322596226165, 1.0794543211516894],
	    [1.3417754325579776, 0.41340207169338417, 0.24723858109403229, -2.6780134110295553],
	    [-0.13952661937566713, 2.7105451406569299, 1.7215147939234914, -1.1293430580852784],
	    [-0.23302791636089426, 2.616033439185788, 1.3289668181762231, 0.45798878930746501],
	    [0.4398087751398308, 2.5923911919596039, -1.8817124704203039, -0.45804408192232948],
	    [1.5891461412638876, 0.43085460737427961, 0.10038478128808404, 0.77923194093304038],
	    [0.99140610744761692, 0.65203466631192164, 1.7297679376863719, -0.46989947077417149],
	    [0.91031862710327549, 0.75216686325296167, 1.1967654323384487, 0.69791550991208418],
	    [1.2570045738380773, 1.946299395408932, -2.252304226607718, 0.6620620121446591],
	    [1.479323801696008, 1.7102737409657767, -1.8881727830636823, 3.0114335335665263],
	],
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: [
	    [0.90938085507918154, 0.32295001468544721, 2.641461636565567, 1.2977803362452534],
	    [-0.44889107896484204, -3.0579387162558933, 0.59575392812648809, -2.3348591643080034],
	    [-1.3830367117522437, 3.0184937824288527, 0.86106001173747648, 1.1016723599901361],
	    [-1.4815185537345177, -2.6958472960391395, 2.6936416946264869, -3.0990394722398844],
	    [1.6962939807609121, 0.22374771941710872, 2.5922373883920509, -1.5234113058915808],
	    [-2.0703215989000321, -2.6787620660260627, 2.7002372484563746, -0.63146497908095878],
	    [2.1504483317777914, 0.5832256005374018, 0.10744578299632757, -2.8622420969733708],
	    [2.7173334033997336, 0.61790249899027749, 0.074358530622130603, 0.83037219968363818],
	],
	trisAlt.strip_I: [
	    [-1.6946922303385863, -2.815450911018373, 3.0775979788676699, -3.1187619082683642],
	    [-0.65401046167569543, -2.9222511494981531, 0.78378759397295461, 3.0609602904082567],
	    [-1.3467010249906231, -2.9601456803270083, 1.3073971927551646, 1.3521314403266977],
	    [-1.7343684733876357, -2.1708773942345028, -2.1598456128306447, -1.8111246264553813],
	    [-1.9894875135829391, -2.4341580503488478, -1.292289817677382, -0.085735151812749599],
	    [1.1384803448400429, 0.78386691378724482, 2.0591806171548681, 2.6130352072242977],
	    [1.720287836929502, 0.48588941814383768, 2.1469912954426817, -1.611693148509719],
	    [-1.9371197276809105, -2.6179000531896475, 2.3868034017036921, -0.040051447374142235],
	    [2.1581508387796484, 0.56685744429681395, 0.070843766668387487, -2.8487065257934256],
	    [2.3779849453135347, 1.1136471874790024, -1.2291708189346924, 1.5608864917306615],
	    [2.486332396897232, 0.94540034464519884, -1.7346356025019034, 0.39637445685289308],
	    [2.4830736043664094, 0.95751049935994437, 0.46119047525417139, -0.42060979143946398],
	],
	trisAlt.strip_II: [
	    [-0.78053141946535654, -2.9957044602595966, -1.6034385134490563, -1.5680768859154188],
	    [-0.83393747543675634, -3.0098215138680255, 2.8172834971135243, 1.5262764201567229],
	    [-1.0886839599106197, -3.0147217596878493, -2.8590764480997204, -0.81777292283973857],
	    [-1.1973557287519916, -2.997313079496394, -0.45191835657781798, 2.4326099535439263],
	    [-1.2681129209839859, -2.9814936264267944, 2.4264222103151609, -2.3970739519638835],
	    [1.2981938092709595, 0.60872379630467599, 2.9347078171363541, 1.4288894727727817],
	    [1.2261561918657655, 0.66996757456470279, -1.6140855525813418, 1.8686265914287086],
	    [-0.6831120099658331, -2.9465534528165946, 0.26106228848495316, -1.7038349444825647],
	    [-0.61538600339513383, -2.8771142989750773, -2.0682108330802063, 1.3618162883632694],
	    [1.2783881904692456, 0.62354964955014314, 0.65836255116914622, -1.8030488046921311],
	    [1.1532121744008685, 0.76016260588130125, -1.169735948137089, -1.3441271466926832],
	    [-1.5226451012085431, -2.8981675517266572, 1.5497322406798324, 0.98947529592358308],
	    [1.5877284024316991, 0.49626410159663759, -0.045144943666047155, 0.82170036354947695],
	    [1.6811623252946457, 0.48701132124144375, -2.4592341798948105, -2.4815656185379726],
	    [-1.1163159015562816, -2.0631829381210132, -1.9401661871207585, -1.9586257906708733],
	    [-1.4403510264114894, -2.0764037963220066, -1.3393299267944396, -1.4967250836905448],
	    [1.7398984199662659, 0.48589006044739763, 0.86470010650407725, 2.4780449650452954],
	    [2.0335255523268461, 0.52646664568419621, 1.609494857524238, -1.0339636995759252],
	],
	trisAlt.star: [
	    [-0.91589802404374965, -3.0205648425159901, 1.1710841581397453, -2.1909146891687321],
	    [1.4239939479677179, 0.54016466981517297, 2.0553349346835947, 2.1638903242770349],
	    [-1.5807455775752495, -2.8730489668852806, 1.0385108551335831, 1.7468507483615046],
	    [-1.7156285720773548, -2.8034077179474139, 2.9864902649994693, -1.6653874628874563],
	    [-1.9240180235472897, -2.6349514929460498, -0.59807417921847339, -0.87535091822462885],
	    [-1.9501962488900013, -2.339964235581236, -1.5723634544553811, -2.0863544894494321],
	    [1.9627122565696287, 0.50993408429128129, 2.5052935457025995, -2.194198316928528],
	    [-1.9551978188408037, -2.3475758693148876, 2.1966803599428459, 1.8882085989640403],
	    [2.109715528326475, 0.54931571303117632, -0.043359226574342991, 2.1911627020861655],
	    [2.4188278207608711, 0.72987396529880821, -2.3652985207474941, 1.2647840443979919],
	    [2.4787385678138159, 0.82355380484766005, -2.0745546366690437, 1.9377771661164715],
	    [2.4801187999584724, 0.82733714035074613, 0.45623239735137133, -2.0655479921033209],
	],
	trisAlt.star_1_loose: [
	    [1.0149393198743031, 0.20792227819919443, 2.5836962238028218, 1.0372615999645785],
	    [-1.0751826839844196, 2.8814957512428614, 1.1086421034768161, 1.0519563704129729],
	    [-1.3835848376724227, -2.6321617361541256, 2.7174703370577733, 3.1157268380721628],
	    [1.7331885945048515, 0.24150615740506262, 2.6015816900302511, -1.5710794914682902],
	    [-0.54489993265932091, 2.915597412444876, 1.0372186359967435, -1.4721673315795574],
	    [1.8679117432741839, 0.77002167939869515, -0.078297767071824786, -3.1307094477258608],
	    [-2.3911297255675925, -2.3707354166109549, 2.795042136361964, 0.62095797887423387],
	    [2.9284135828775808, 0.74305283843872472, -0.050029683033717909, -1.0289948820068284],
	],
	trisAlt.alt_strip_II: [
	    [-1.037049091701729, -3.0196566189887299, 2.0397254685448902, 2.8434858123186189],
	    [-1.0903064674727712, -3.0145292487300233, -2.8358007233693736, -0.86166066361481608],
	    [-0.8198802432230976, -3.0067431916460832, -1.6288111338271163, -1.6816479247650324],
	    [1.3260195982510523, 0.5900288156922201, -1.4668040415245169, 2.067419284020886],
	    [1.3426483979313535, 0.57992746594515765, -0.19454064146690531, -2.4424173437994607],
	    [1.1832000380036203, 0.71847314518718275, -1.0245840638119654, -1.579167820644737],
	    [-1.3723438996667396, -2.9523434775301562, 2.3694514968071299, -2.0512623206008813],
	    [-0.57141807044194926, -2.784233442827639, -0.68347703253737091, 0.93797472475829924],
	    [-0.5551356478428856, -2.6220746204690943, -0.77339105439584444, 0.08290071540128352],
	    [1.5372065733048164, 0.50560901223438004, 1.3514574633113607, -2.8977573261866612],
	    [1.5895085322780866, 0.49599403955605242, -0.068713981500287069, 0.86406859716884554],
	    [-0.60342260033481065, -2.4239218149609219, 2.1435042596824765, 0.015753435074164379],
	    [-0.88038498159212375, -2.1304286398827443, 2.4601388709047192, -2.5651348738353592],
	    [-1.3495960836612901, -2.0631741504163541, -1.5016259753630408, -1.6492502536602283],
	    [-1.4921745108967872, -2.0870806689269505, -1.6593709724775119, 1.2152531578184436],
	    [1.8821390773856976, 1.3784585384450738, -1.7397607167530733, 1.605868378645674],
	    [1.9043238353670378, 0.49952390395872137, 0.88952100506794785, 1.9109793433617417],
	    [1.9878597650835099, 1.3412383521025317, -1.5800729501111253, -1.0894088372429112],
	],
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: [
	    [1.1071348544592301, 0.5282092003182125, -2.4209119875614427, -1.9339385010957217],
	    [-1.1139573537726342, -2.8454877114819297, -2.2423145726564595, 0.79191801880226276],
	    [-1.4861417335734413, 3.0437874407297798, 0.042803802248485567, -1.5418482470921102],
	    [1.516021864208821, 0.6232751877723639, -2.3703142586963373, 2.8750756344210577],
	    [-1.505716419624461, -2.4709579658775276, -1.3166274984099307, 1.9845010819440037],
	    [-1.5342542549813123, 3.0541129428068938, -0.027523818080243956, -1.8655509654765794],
	    [-1.7445248374838513, -3.117792183646745, 1.7761329989476788, -1.5487636955592503],
	    [-1.4219137817889349, -2.3782898649783748, 2.5967504554976419, 2.5509612243604241],
	    [-0.48448060162531104, 2.737851074658153, -1.0955594258428585, 1.5607868274557584],
	    [1.9644742488736522, 0.92312201834975127, -1.8102301470959699, -1.8993952213905576],
	    [-2.1747017769504895, -2.1061563889775119, -1.9820908595504632, -1.6239283776744706],
	    [-2.1168094162826478, -2.6887908657580688, 2.3429912583524022, 0.66174647076184723],
	    [-1.6390667052081416, -1.807832425259976, -3.117230560741548, -0.5114725412647978],
	    [2.3112422769855931, 0.33626189210467666, 1.1766787291424696, 2.3473984750189274],
	    [2.6000231239748435, 1.1095496951676056, -0.23709566648279257, -1.1241737214449348],
	    [2.7820445889909364, 0.60161329305726285, 0.55536515367212491, -0.94443472554990393],
	],
	trisAlt.strip_I: [
	    [-1.209232239436479, -2.9948914682401906, -3.0799223022786841, 1.7295087882673474],
	    [-0.96637945414647242, -3.0222359339468374, -0.42242834915502492, -2.8366635873155737],
	    [-0.91618510052716029, -3.0205838322977736, -1.8430515880025764, 0.85860005032824382],
	    [1.2612167501808473, 0.63755121891627109, -2.2600081675162134, -2.3166233531644451],
	    [1.4365991318629088, 0.53524545498484588, -1.1653701509175622, -0.89188093603280905],
	    [1.4705268290704887, 0.52342921546216592, -2.5252627543077346, 2.9488829022780489],
	    [1.7025284678587842, 0.48620988811774823, 0.095832726302814919, -1.618539131589344],
	    [-0.70356638482104195, -2.9603179199563061, -0.82192790967289664, 2.0312051976117189],
	    [-1.6687467186791558, -2.8296795065061433, 2.1752456652069503, -1.1964974044414669],
	    [-1.9895256484762434, -2.434387601752674, -1.3392756322053057, 0.08690448622948832],
	    [-1.8592065742115063, -2.2467520200389437, -1.6514500724160088, -2.6614741309991596],
	    [-1.6013917878361821, -2.1173440957513083, 2.7571615189472176, 1.6061087920698078],
	    [-1.3490703311933974, -2.0631178424167897, 2.7704995596322313, -1.2739345380197431],
	    [-1.937131326061633, -2.6178841059021662, 2.3645720179196741, 0.039510898184166039],
	    [2.172879581530315, 0.57270717598032594, 0.89478548403792768, 1.9376119624987025],
	    [2.4877639081840792, 0.93902119821687025, -1.5325679375091434, -0.39382224968378576],
	    [2.4404647944192681, 1.0424326167799449, -1.3858941953338428, 2.0649595382325536],
	    [2.3941347982518812, 1.097695419586934, 0.051661851751112341, -1.6837784756927556],
	],
	trisAlt.star_1_loose: [
	    [1.0957407095878093, 0.26500023074799184, -2.9166150796040964, -1.5490962388328731],
	    [1.3887248722318219, 0.42561461188357952, -2.6752316136547907, -2.7968289580425569],
	    [-1.3281411187509216, 2.9750039663666579, 1.8018470311356989, -1.1190831690724394],
	    [-1.4308217659462272, 3.0417357972158467, -1.2924206914097152, 1.1545877066396815],
	    [-0.80680577194439973, 3.098272925705658, -0.17131653203190922, -1.8344520885432756],
	    [1.6333999992173736, 0.11489860952313702, -1.4789978115469449, -1.1708837220710269],
	    [-1.7825089754776458, -3.0739522397729249, -2.6961574708022127, 1.6105925381593522],
	    [-1.8861349012802282, -3.0388861491618377, 1.8701138264130333, -1.8098697948370877],
	    [1.8830587753502717, 0.24618484402224558, -0.84826638748155414, -0.9672108654206184],
	    [-0.34617340333099161, 2.6821486275943331, 0.35760859551121982, -1.0207553418563791],
	    [-2.1454224483864692, -2.6257345470177813, -1.1885078955129043, 2.374018705899942],
	    [-2.4614900853905355, -2.5104535553550011, -1.6456996979156315, -2.6064877990861226],
	    [2.4789633630937962, 0.65491193885920973, -1.7889332528453172, -2.4240266570090707],
	    [2.9668632026353183, 0.7168894749856618, -1.0341015125589896, 1.5202460342972959],
	],
	trisAlt.alt_strip_I: [
	    [-1.1964857735260939, -2.9974866566722129, -1.1994542646114308, -1.5568848632390004],
	    [-0.91757795100251671, -3.0206743312142228, -1.8185073961837723, 0.81331927366837853],
	    [-0.83384618856572024, -3.0098028520246243, 2.0601371582609409, -2.4580265586965759],
	    [1.2270527838329404, 0.6690670445296707, -2.2986986168145327, -2.1590173092777984],
	    [-0.78130278150095589, -2.995958834044143, -0.85936980394137219, 2.4243843886122249],
	    [-0.62820880302470905, -2.8942569411705628, -0.037054342865534551, -0.98778439572317556],
	    [1.1504505913795937, 0.76442106217636052, 3.088811051920151, 0.94530689545094493],
	    [-1.2697154656633491, -2.9810973492556876, -3.1224993593005155, 1.6011483525036923],
	    [1.4380838584821447, 0.53468557256964278, -1.1808485810297134, -0.8598875866349136],
	    [-1.4039612578940712, -2.9421577651378348, 1.2745632420827215, 1.6863546313672959],
	    [-1.5547287782755468, -2.8846118815805739, -2.7067341265306872, -1.3582813780717675],
	    [1.2767406923432152, 0.6248449214635855, 1.3518229869249891, 2.2169833392668608],
	    [1.6818158074314449, 0.48697994371999548, -1.6923726978044273, 1.497169540756623],
	    [1.7393662583547094, 0.48588521179432176, 0.099378381111790759, -1.5014619462252874],
	    [1.9825141256511112, 0.5141202086682769, 1.9085361778982337, -1.8704734783603829],
	    [2.0700594569169395, 0.53673836596287394, -0.44693045192619874, 1.2547516781015853],
	],
	trisAlt.alt_strip_II: [
	    [-0.56611501784458329, -2.7646069062615344, -1.5841223232908179, 2.9867922356690553],
	    [-0.751964486197087, -2.9850486861651122, 0.30868879787646919, -1.4484260730167087],
	    [-0.55516999575706805, -2.621562744834415, -0.73025535086173221, -0.078177807335152671],
	    [-1.4729294395732817, -2.9177325159827121, 0.74449579986857706, -3.08085028903702],
	    [1.1058752191033234, 0.84748617271957571, -2.1743751355893268, -2.2215635426686262],
	    [-0.60341964553356309, -2.4239287023821241, 2.1523129877368534, -0.015878765859667077],
	    [-1.0371047750375442, -2.0764275825294094, -3.0206971945332772, 2.2756589307068342],
	    [1.8006873925683431, 0.4881625402812691, 2.6681299406358612, 2.6261931954864415],
	    [1.0560123124029199, 1.039886903522111, 0.68700122971616029, 2.3985441047597025],
	    [1.0647217181362791, 1.1878586128336124, 1.5444549980473705, -0.67178528683743366],
	],
	trisAlt.alt_strip_1_loose: [
	    [-1.1150575883021376, -2.8445291345957111, -2.2409974702442623, 0.78514693256501733],
	    [1.0719245245316869, 0.56530721508571191, -2.469884499866319, -1.7738200361076961],
	    [1.021914259798985, 0.42287986758064666, 1.8793755702256683, 1.5537762975832807],
	    [-1.2071062621071067, -2.5930228173640377, -1.1635357816892338, -3.099801987992882],
	    [-1.2227806409189022, -2.5757725086049885, 2.3872065853049418, 3.0656556780687301],
	    [-1.4652246848324353, -3.0837293636442995, 1.0859654391168592, 1.8230139009753383],
	    [-1.450294439172962, -2.3557564935032693, -1.087437593498322, -2.5015997740645215],
	    [-1.4470955953387119, -2.359012462894559, 2.6357122218504005, 2.5112846678048095],
	    [-0.45153911439008604, 2.6964257339232072, -0.70130395492975239, 0.8801479038722434],
	    [2.0268501607677134, 0.22125831323649495, 2.3600385970328306, -2.3559043044069212],
	    [2.0493001376484057, 0.23317535143873086, -0.17234123113922806, 2.3403738587552936],
	    [2.0148669012770979, 1.0278583692170982, -2.3611496306711013, 1.8980599862693239],
	    [-1.4945905441304848, -2.1018498945813668, 2.5531714251899054, 1.5625791797761517],
	    [1.9923516010308595, 0.58400187934935899, -0.49727738783038777, 1.0108488707587959],
	],
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_1_loose: [
	    [-1.4845890274466147, 3.0626426449873039, -0.097780459842321754, -1.4952529282338594],
	    [-1.4845890274466147, 3.0626426449873039, 2.3306974246627101, -1.4952529282338594],
	    [-1.5340069950789443, 3.0416241021604091, 0.062287254153245541, -1.8946937131325789],
	    [-1.5340069950789441, 3.0416241021604091, 2.4907651386582765, -1.8946937131325781],
	    [-0.41888595072873896, 2.8762218841580878, 2.1655519084960666, -2.5038463969235583],
	    [-0.41888595072873863, 2.8762218841580882, -1.6891555141784895, -2.5038463969235587],
	    [1.924139913702597, 0.11912677222050019, 0.62071225503069183, 2.0052942713170037],
	    [1.9241399137025972, 0.11912677222050019, 3.0491901395357237, 2.0052942713170037],
	    [1.6991190476169364, 0.55866370571147583, -2.656534528688054, 0.23098088216484719],
	    [1.6991190476169367, 0.55866370571147572, 1.1981728939865026, 0.23098088216484666],
	    [-0.30494332537338148, 2.1580087070798282, -2.503852906419227, 1.670065435690212],
	    [-0.30494332537338215, 2.1580087070798286, 1.3508545162553318, 1.6700654356902138],
	    [-0.23122542412224847, 2.1313915228383706, 1.2509332573256926, 1.3121042603271043],
	    [-0.23122542412224681, 2.1313915228383706, -2.6037741653488649, 1.312104260327098],
	    [0.74861132948875686, 2.1343784660313974, -0.82748004091455218, 1.3938550457687566],
	    [0.74861132948875719, 2.1343784660313974, 3.0272273817600031, 1.3938550457687575],
	    [2.6183690996103559, 1.0111119666230184, -1.8576605131426467, -1.2576009337411378],
	    [2.6183690996103564, 1.0111119666230179, 0.5708173713623852, -1.2576009337411369],
	    [2.7325943248261031, 0.94615739973058832, -1.3980848791205425, -0.62841892332507232],
	    [2.7325943248261035, 0.94615739973058766, 1.0303930053844903, -0.62841892332507143],
	],
	trisAlt.strip_I: [
	    [-0.79885004672239224, 3.0179634485173019, 0.98465653767958372, -3.0572335004706765],
	    [1.7020755351265853, 0.53794940577427575, -0.27316856381484911, -1.4979162088568145],
	    [1.7833366673696338, 0.26048788850156435, 1.2497411941367886, 1.2793157131005826],
	    [0.091368094917677875, 2.6082527000933213, -2.7562233597691788, -1.7155991824890169],
	    [0.25446037722864578, 1.9651806834728971, 3.0949853889369834, 2.6184080779945837],
	    [0.33838462647700379, 1.9379857347595022, -2.7543489778932901, 2.6484027000668533],
	    [0.2858882185199767, 1.9549394751381417, -2.9549409385580958, 0.21502660611870894],
	    [0.61353295092959925, 1.8532478259896603, 2.5203104907932126, -0.34376333108011004],
	    [0.9973487531419839, 1.848175621239643, -1.5375295086327379, 2.0977096819454779],
	    [0.81032103676872091, 2.0775647744179375, -3.0926783767959627, 1.5036901846458965],
	    [2.0196258748451963, 1.2727605343260069, -2.1710329071847676, -1.8865161788125064],
	    [2.3920761643791448, 1.1224785237774848, -0.12274311530941784, -1.6315725012423954],
	],
	trisAlt.star_1_loose: [
	    [-0.78649746378031937, 3.0143035219986434, 0.40713463198700522, -2.0449340172468444],
	    [-1.503059117971141, 3.0558464405837098, 2.1712792728766832, -1.4022200757516767],
	    [-1.6059964694698923, 2.866414049889388, 1.9885321632865285, -2.5297002324221469],
	    [1.7614782023235209, 0.304169774587014, -1.794806540946527, 2.6036860682193002],
	    [1.7100410641888972, 0.48826469574678688, -2.806020940862997, 0.34762728397366383],
	    [1.8621845314786329, 0.16306937225800278, 1.4467053137497514, 1.0233338571591153],
	    [1.97305011402432, 0.095185249914189377, 0.8118697409074036, 1.8607170554564254],
	    [-0.042330154665305188, 2.6860502910686272, -2.2743057075632702, -2.9562371248119219],
	],
	trisAlt.alt_strip_I: [
	    [-0.62696375021451145, -2.9114150295340999, 0.08606365260813309, -1.0238380261272493],
	    [1.7390324717886094, 0.53802293372582799, -0.27356817216912255, -1.3776494027850816],
	    [-0.047605472532525138, 3.012833671418603, 2.1808027566006949, -0.40978769654882274],
	    [0.39852363344342367, 2.1647388286978924, 2.808094371639648, 2.1518345604702382],
	    [0.59277830030021517, 1.9391309800157357, -2.1543715722249051, 2.5470595560377429],
	    [2.0395226608749817, 0.38478181913646292, 0.84070652870124629, 0.78109026571592099],
	    [2.0143936971274261, 1.2822896911954387, -2.1778397715822209, -1.8557176549123886],
	    [1.9547040180353867, 1.5483759048647803, -1.5325258108128041, -0.98190052706106279],
	],
	trisAlt.alt_strip_1_loose: [
	    [-1.1273830838862526, 2.7864872045941964, 0.93898126309533581, -2.7269986659062937],
	    [-1.1273830838862524, 2.786487204594196, -2.9157261595792181, -2.7269986659062955],
	    [-0.26463422535080822, 2.3510694952479985, -2.8664482135073128, 0.18740225816184619],
	    [-0.26463422535080827, 2.3510694952479976, 0.98825920916724197, 0.18740225816184619],
	    [2.0502518014815978, 0.16020631612541431, 2.780614546026785, 2.1808895378171487],
	    [2.0502518014815978, 0.16020631612541447, 0.35213666152175094, 2.1808895378171487],
	    [1.9215353658718557, 0.44669537040934154, 0.86900117580147995, 0.41752335302782806],
	    [1.9215353658718559, 0.44669537040934149, -2.9857062468730726, 0.4175233530278275],
	    [0.34669987524915774, 2.219433987876362, 2.6435801098791853, 2.034670026478302],
	    [0.34669987524915769, 2.2194339878763616, -1.2111273127953694, 2.0346700264783024],
	    [0.66723327917964559, 2.4553381355981454, 2.7838044311568622, -0.013679079680867012],
	    [0.66723327917964548, 2.4553381355981454, -1.0709029915176922, -0.013679079680867012],
	],
    },
}
