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
edge_0_1_1_0	=  9
only_hepts	= 10
only_o3_tris	= 11
border_o3_tris	= 12
square_o3_tris	= 13
edge_V2_1_1_0	= 14

Stringify = {
    dyn_pos:		'Enable Sliders',
    no_o3_tris:		'48 Triangles',
    all_eq_tris:	'All 80 Triangles Equilateral',
    edge_1_1_V2_1:	'32 Triangles and 24 Folded Squares: I',
    edge_1_V2_1_1:	'32 Triangles and 24 Folded Squares: II',
    edge_V2_1_1_1:	'56 Triangles and 12 Folded Squares',
    edge_V2_1_V2_1:	'8 Triangles and 36 Folded Squares',
    squares_24:		'24 Folded Squares',
    edge_0_1_1_1:	'56 Triangles',
    edge_0_1_V2_1:	'8 Triangles and 24 Folded Squares',
    edge_0_1_1_0:	'24 Triangles',
    only_hepts:		'No Extra Faces, Only Heptagons',
    only_o3_tris:	'8 Triangles (O3)',
    border_o3_tris:	'32 Triangles (24 + 8)',
    square_o3_tris:	'8 Triangles and 12 Folded Squares',
    edge_V2_1_1_0:	'24 Triangles and 12 Folded Squares',
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
        R0   = GeomTypes.Hz
        R1   = Rot(axis = Vec([ 1,  1,  1]), angle =     GeomTypes.tTurn)
        R1_2 = Rot(axis = Vec([ 1,  1,  1]), angle = 2 * GeomTypes.tTurn)
        R2   = Rot(axis = Vec([-1, -1,  1]), angle =     GeomTypes.tTurn)
        R2_2 = Rot(axis = Vec([-1, -1,  1]), angle = 2 * GeomTypes.tTurn)
        R3   = GeomTypes.Hy;
        Geom3D.IsometricShape.__init__(this,
            Vs = [], Fs = [],
            directIsometries = [
                    GeomTypes.E, R0,
                    R1,          R1_2,
                    R1*R0,       R1_2 * R0,
                    R2,          R2_2,
                    R2*R0,       R2_2 * R0,
                    R3,          R3 * R0
                ],
#            oppositeIsometry = GeomTypes.I,
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
        size = (745, 700)
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
		    trisAlt.strip_II:      OnlyHeptagons[Heptagons.foldMethod.parallel],
		    trisAlt.star:          OnlyHeptagons[Heptagons.foldMethod.parallel],
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.parallel],
                },
                Heptagons.foldMethod.w: {
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.w],
		    trisAlt.strip_I:       OnlyHeptagons[Heptagons.foldMethod.w],
		    trisAlt.strip_II:      OnlyHeptagons[Heptagons.foldMethod.w],
		    trisAlt.star:          OnlyHeptagons[Heptagons.foldMethod.w],
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.w],
                },
	    },
	    only_o3_tris: {
		# Note: all triangle variants are the same:
		# no solutions for Heptagons.foldMethod.parallel
		#     reason: it is impossible to get distance c == 0
		#     since max to fit Rho in: 2*Rho*sin(pi/7) < Rho.
		Heptagons.foldMethod.triangle: {
		    trisAlt.strip_1_loose: OnlyO3Triangles[Heptagons.foldMethod.triangle],
		    trisAlt.strip_I:       OnlyO3Triangles[Heptagons.foldMethod.triangle],
		    trisAlt.strip_II:      OnlyO3Triangles[Heptagons.foldMethod.triangle],
		    trisAlt.star:          OnlyO3Triangles[Heptagons.foldMethod.triangle],
		    trisAlt.strip_1_loose: OnlyO3Triangles[Heptagons.foldMethod.triangle],
                },
                Heptagons.foldMethod.star: {
		    trisAlt.strip_1_loose: OnlyO3Triangles[Heptagons.foldMethod.star],
		    trisAlt.strip_I:       OnlyO3Triangles[Heptagons.foldMethod.star],
		    trisAlt.strip_II:      OnlyO3Triangles[Heptagons.foldMethod.star],
		    trisAlt.star:          OnlyO3Triangles[Heptagons.foldMethod.star],
		    trisAlt.strip_1_loose: OnlyO3Triangles[Heptagons.foldMethod.star],
                },
                Heptagons.foldMethod.w: {
		    trisAlt.strip_1_loose: OnlyO3Triangles[Heptagons.foldMethod.w],
		    trisAlt.strip_I:       OnlyO3Triangles[Heptagons.foldMethod.w],
		    trisAlt.strip_II:      OnlyO3Triangles[Heptagons.foldMethod.w],
		    trisAlt.star:          OnlyO3Triangles[Heptagons.foldMethod.w],
		    trisAlt.strip_1_loose: OnlyO3Triangles[Heptagons.foldMethod.w],
                },
                Heptagons.foldMethod.trapezium: {
		    trisAlt.strip_1_loose: OnlyO3Triangles[Heptagons.foldMethod.trapezium],
		    trisAlt.strip_I:       OnlyO3Triangles[Heptagons.foldMethod.trapezium],
		    trisAlt.strip_II:      OnlyO3Triangles[Heptagons.foldMethod.trapezium],
		    trisAlt.star:          OnlyO3Triangles[Heptagons.foldMethod.trapezium],
		    trisAlt.strip_1_loose: OnlyO3Triangles[Heptagons.foldMethod.trapezium],
		},
	    },
	    border_o3_tris: BorderAndO3Triangles,
	    square_o3_tris: FoldedSquareAndO3Triangle,
	    edge_V2_1_1_0: FoldedSquareAnd1TriangleType,
	    edge_0_1_1_0: { # TODO change name: only one kind of triangle
		# index T_STRIP_1_LOOSE nothing special TODO double check
		# index T_STAR_1_LOOSE nothing special TODO double check
                Heptagons.foldMethod.parallel: {
		    trisAlt.strip_I:  Only1TriangleType[Heptagons.foldMethod.parallel],
		    trisAlt.strip_II: Only1TriangleType[Heptagons.foldMethod.parallel],
		    trisAlt.star:     Only1TriangleType[Heptagons.foldMethod.parallel],
                },
		Heptagons.foldMethod.triangle: {
		    trisAlt.strip_I:  Only1TriangleType[Heptagons.foldMethod.triangle],
		    trisAlt.strip_II: Only1TriangleType[Heptagons.foldMethod.triangle],
		    trisAlt.star:     Only1TriangleType[Heptagons.foldMethod.triangle],
                },
	    },
	    all_eq_tris: AllEquilateralTris,
	    no_o3_tris: {
		Heptagons.foldMethod.parallel: NoO3Triangles[Heptagons.foldMethod.parallel],
	    },
	    squares_24: {
		Heptagons.foldMethod.parallel: FoldedSquares_0[Heptagons.foldMethod.parallel],
	    },
	    edge_1_1_V2_1: {
		Heptagons.foldMethod.parallel: E1_1_V2_1[Heptagons.foldMethod.parallel],
	    },
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
		Stringify[square_o3_tris],
		Stringify[edge_0_1_1_0],
		Stringify[squares_24],
		Stringify[border_o3_tris],
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
                label = 'Only Regular Faces:',
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
        if this.prePosGui.GetSelection() != 0:
            this.onPrePos()
        else:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()

    def onFoldMethod(this, event):
        this.foldMethod = this.foldMethodListItems[
		this.foldMethodGui.GetSelection()
	    ]
	this.shape.setFoldMethod(this.foldMethod)
        if this.prePosGui.GetSelection() != 0:
            this.onPrePos()
        else:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()

    def onFirst(this, event = None):
        this.specPosIndex = 0
        this.onPrePos()

    def onLast(this, event = None):
        this.specPosIndex = 0xefffffff
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
            this.onPrePos()

    def onNext(this, event = None):
        prePosIndex = this.getPrePos()
        if prePosIndex != dyn_pos:
	    try:
		if (this.specPosIndex < len(this.specPos[prePosIndex][
		    this.foldMethod][this.trisAlt]) - 1
		):
		    this.specPosIndex += 1
		#else:
		#    this.specPosIndex = 0
	    except KeyError:
		pass
	    this.onPrePos()

    tNone = 1.0
    aNone = 0.0
    fld1None = 0.0
    fld2None = 0.0
    def onPrePos(this, event = None):
        sel = this.getPrePos()
	# if only_hepts:
	# 1. don't show triangles
	# 2. disable triangle strip.
	if (sel == only_hepts):
	    this.shape.addTriangles = False
	    this.addTrisGui.Disable()
	    this.trisAltGui.Disable()
	    this.restoreTris = True
	    # handle here instead of below...
	    if (this.restoreO3Tris):
		this.restoreO3Tris = False
		this.shape.onlyO3Triangles = False
	elif (this.restoreTris):
	    this.restoreTris = False
	    this.trisAltGui.Enable()
	    this.addTrisGui.Enable()
	    this.shape.addTriangles  = this.addTrisGui.IsChecked()
	    # needed for sel == dyn_pos
	    this.shape.updateShape = True
	if (sel == only_o3_tris):
	    this.shape.onlyO3Triangles = True
	    this.trisAltGui.Disable()
	    this.restoreO3Tris = True
	elif (this.restoreO3Tris):
	    this.restoreO3Tris = False
	    this.trisAltGui.Enable()
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
		if (this.specPosIndex >=
		    len(this.specPos[sel][this.foldMethod][this.trisAlt])
		):
		    this.specPosIndex = len(
			    this.specPos[sel][this.foldMethod][this.trisAlt]
			) - 1
		elif (this.specPosIndex <  0):
		    this.specPosIndex = 0
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
		    nrPos = len(this.specPos[sel][this.foldMethod][this.trisAlt])
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
	    elif ( this.foldMethod == Heptagons.foldMethod.parallel and (
		    (
			sel == squares_24
			and
			not (
			    this.trisAlt == trisAlt.strip_I
			    or
			    this.trisAlt == trisAlt.star
			)
		    )
		    or
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
			    sel == edge_0_1_1_0
			) and (
			    this.trisAlt == trisAlt.strip_1_loose
			    or
			    this.trisAlt == trisAlt.star_1_loose
			)
		    )
		)
	    ):

		this.statusBar.SetStatusText('Doesnot mean anything special for this triangle alternative')
	    else:
		this.nrTxt.SetLabel('%d/%d' % (this.specPosIndex + 1, nrPos))
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
    Heptagons.foldMethod.w: [
	[-1.8868486799927435, -2.6758432135380379, -3.1283205574215183, 1.9544544516064626],
	[-1.322333216810468, -2.9671800030020141, -1.1832507472772251, 1.6683015362824891],
	[1.7889621671929601, 0.48746365476050291, -1.6930224693313676, -1.5136933696889994],
	[2.380384930679721, 0.693073733186942, -0.568746300899379, -0.882436236397252],
    ],
    # none found for the others,... :(
}

###############################################################################
OnlyO3Triangles = {
    Heptagons.foldMethod.trapezium: [
	[1.6713285948103263, 0.78612999312594156, 0.94665778267419576, 2.2644932672720368],
        [1.603988045241469, 1.1791617966606149, -1.2247214682758774, 0.9875936306319586],
    ],
    Heptagons.foldMethod.star: [
       [-1.2787114409728058, -2.5182959872317254, 2.6830500115396658, -0],
       [-1.278711440972806, -2.5182959872317263, -1.4154825122609482, 0.0],
       [1.7787114409728062, 0.94749966043682887, -1.7261101413288449, 5.9249751911283334e-17],
    ],
    # note, same as Heptagons.foldMethod.star:
    Heptagons.foldMethod.w: [
        [-1.278711440972806, -2.5182959872317259, 2.6830500115396663, 0.0],
        [-1.2787114409728058, -2.5182959872317259, -1.4154825122609482, 0.0],
        [1.7787114409728058, 0.94749966043682898, -1.726110141328844, -2.6645352591003757e-15],
    ],
    Heptagons.foldMethod.triangle: [
	[1.6800854296744396, 0.47457010697125623, 0.74503485547995096, 2.2177947528033286],
    ],
}

###############################################################################
Only1TriangleType = {
    # valid for all non-loose methods:
    Heptagons.foldMethod.parallel: [
	[1.0667369771505062, 0.17460360869707484, -2.0645703328144194, 1.8471533350794935],
	[0.73520075865433276, 0.53851116038768643, -2.0645703328144194, 2.9951020996341051],
	[0.7352007586543331, 2.9669890448927174, 2.0645703328144198, 1.2944393185102951],
	[1.066736977150506, 2.6030814932021062, 2.0645703328144198, 0.14649055395568578],
    ],
    Heptagons.foldMethod.triangle: [
	[1.1964935651638633, -0.27352488932327734, 1.8842755148636305, -2.6593078492130866],
	[1.3090169943749472, -0.12747672487732764, 1.6744710166353975, 0.75403191432758199],
	[1.0742687982864947, 2.5927093577804059, -2.1000230413726158, 0.081756270399801309],
    ],
}

###############################################################################
# These lists are valid for stripI and stripII:
tri_strip_lst = [
    [0.39884399626845796, 1.4568403064826343, 2.5715853033334066, -0.88428111441002599],
    [-0.25245320098095386, 2.5254918903733907, 1.2927536380277551, -1.9009046158502372],
    [0.56477962526448244, 2.5170214708479355, -1.6342822146880849, 1.884160303072703],
    [1.1958969269857136, 0.47194194051049571, 1.874835153247457, 2.2245693304207181],
]
star_strip_lst = [
    [1.3589033857968413, 0.57075868490494164, -1.854104152973628, -1.5872846507074385],
    [1.1510711142603265, 0.76345718622723957, -2.5719659710126268, 1.3787127661296772],
    [-0.83500624291190872, -3.0100387448217596, -1.2472158731015446, 1.9370891705806654],
    [-0.61728150693957284, -2.8798182278826023, -0.67139289769202648, -1.3539686423323598],
    [-1.5443915209996073, -2.1001904551266772, -2.5300662835391172, 0.86765835633091604],
    [-1.0961611397416087, -2.0658152219428132, 2.7790349062846875, 0.9745184453712924],
    [1.240760438271816, 1.4093511342004652, 0.64591225448264056, -1.2296559797224518],
]
w_strip_lst = [
    [-1.1862476804268163, -2.9994899812656386, 2.8263876295048935, -1.8915912003967748],
    [-1.5497210407978861, -2.8867778263039949, 2.1809990026242287, 1.3489777010932347],
    [-1.5841901109149064, -2.1118412402325202, -2.0696948161710793, -0.77601462834736079],
    [1.6882306382363743, 0.48669510129948473, 0.48415173585818649, 1.9868324248931146],
    [2.0749106784006828, 0.53819543761494271, 0.93672429915381661, -1.2680892577785441],
]
star_1loose_lst = [
   [-1.3267612461683367, -2.5778529653405711, 2.7362124611005836, -0.28126669081465216],
   [-0.28922422512916357, 2.6718456414892255, -0.21375757704173282, 1.9914479371053699],
   [1.8724618970261588, 0.76451178362743311, -0.0724688081506768, 1.8409398419822915],
   [-1.1124714157602793, -2.0230027283437906, 2.8368103677052008, 1.0316703289486415],
   [0.46925383056107556, 1.8313682859304494, 1.0348362820959265, -2.4222351368105524],
   [2.0846486004668447, 1.2250086511365692, -0.78617831355469914, -0.51598138539488669],
   [0.60829171411896221, 2.0264126913595617, 0.5479286501894568, -2.2482115235445761],
]
w_1loose_lst = [
   [-1.1877980818382776, 3.0908140965136033, 2.5643831539870465, -1.7178783670933822],
   [-1.1877980818382778, -2.6151617110632355, -2.5643831539870456, -3.1056362492441583],
   [-1.3421828273353866, -2.5969300935689588, 2.5643831539870452, 0.30631407367199226],
   [1.6394224984499302, 0.12273044694942978, 1.0770223207753735, 1.9593075245191285],
   [1.6394224984499308, 0.90677165981343011, -1.0770223207753737, -2.2593074498460375],
   [2.0993392707370284, 0.42611693996126931, 1.0770223207753733, -1.5924703792971675],
   [2.0993392707370289, 1.2101581528252696, -1.0770223207753729, 0.4720999535172512],
]
tri_1loose_lst = [
   [-0.2458627268578423, 2.4477137125144059, 1.4573873326240594, -1.7538347714390188],
   [0.95623621578898843, 0.69387894107538728, -3.0719632031165078, -1.7538347714390188],
   [0.9562362157889881, 0.69387894107538739, 2.0568031048575843, 1.753834771439017],
   [-0.24586272685784227, 2.4477137125144055, 0.3029683334185661, 1.7538347714390179],
   [0.66725358606974539, 2.4477137125144055, -1.6404257772681818, 1.7538347714390179],
   [1.8693525287165764, 0.69387894107538739, 0.11340899417083616, 1.753834771439017],
   [1.8693525287165764, 0.69387894107538728, 1.2678279933763301, -1.753834771439017],
   [0.66725358606974572, 2.4477137125144055, -0.48600677806268777, -1.753834771439017],
]
BorderAndO3Triangles = {
    # TODO: fill in more...
    # no solutions found for trapezium and parallel fold (for any triangles).
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_I: tri_strip_lst,
	trisAlt.strip_II: tri_strip_lst,
	trisAlt.strip_1_loose: tri_1loose_lst,
	trisAlt.star_1_loose: tri_1loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_I: star_strip_lst,
	trisAlt.strip_II: star_strip_lst,
	trisAlt.strip_1_loose: star_1loose_lst,
	trisAlt.star_1_loose: star_1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_I: w_strip_lst,
	trisAlt.strip_II: w_strip_lst,
	trisAlt.strip_1_loose: w_1loose_lst,
	trisAlt.star_1_loose: w_1loose_lst,
    },
}

###############################################################################
star_strip_lst = [
   [1.1337834018831718, 0.3983033753431518, -2.1797039818918522, -1.5328428576100608],
   [0.90307327376725277, 0.63885212596863361, -2.8904845931275038, 2.0878012966188395],
   [-0.5420331566827894, 2.9979749183990561, -0.78779708747906696, 1.9216762369325204],
   [-0.30364010591499141, -3.129387164358028, -0.38799713202612018, -1.8798977866386348],
   [0.85606927913462993, 1.6261911991325377, 0.83086420958161999, -1.8031208657168927],
   [0.98417091688110503, 1.7002804053036806, 0.57313683688259065, -1.6982959819999621],
]
w_strip_lst = [
    [-1.1873278995710541, 3.0795212915489931, 2.5484729998858415, -1.7099925934432898],
    [-1.6002075589879676, -3.0554878503734844, 1.9505868416444843, 1.950374772184948],
    [1.6791195265785936, 0.28190668923148438, 0.7894679357209311, 1.9408382769201495],
    [2.0981469671043058, 0.35412999252799127, 1.17394892523243, -1.8111512922408615],
]
triangle_strip_lst = [
    [0.76992497486360933, 0.94624022871632729, 3.0803702160830282, -1.3554280853678113],
    [-0.027892439365956069, 2.0135355382599829, 1.1365693454289998, 1.1300966239587744],
    [-0.17038567171338109, 2.692349840061993, 0.68719186423390977, -2.2850437463779456],
    [0.27367697466186752, 2.6735422903020791, -1.4278661736369687, 2.2346826212529747],
    [1.7889887751470579, 0.56584486671766454, 1.5850459818848297, -2.0045929968418328],
    [1.1391199990835519, 2.0596070208421637, -0.46567402798771518, -1.1822021274704628],
]
FoldedSquareAndO3Triangle = {
    # nothing found for parallel and trapezium fold (strip triangle alt)
    Heptagons.foldMethod.star: {
	trisAlt.strip_I: star_strip_lst,
	trisAlt.strip_II: star_strip_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_I: w_strip_lst,
	trisAlt.strip_II: w_strip_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_I: triangle_strip_lst,
	trisAlt.strip_II: triangle_strip_lst,
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
NoO3Triangles = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: [
	    [0.61336294993015139, 0.69387894107538739, -2.0238552489037858, -2.9635369142286225],
	    [-0.5887359927166792, 2.4477137125144059, -0.27002047746476787, -2.9635369142286265],
	    [-0.58873599271667931, 2.4477137125144055, -0.27002047746476787, -0.53505902972359287],
	    [0.61336294993015172, 0.6938789410753875, -2.0238552489037858, -0.5350590297235911],
	    [1.1885747858746869, 2.4477137125144059, 2.0238552489037858, -0.17805573936116925],
	    [1.1885747858746867, 2.4477137125144059, 2.0238552489037858, -2.6065336238662007],
	    [2.3906737285215178, 0.69387894107538739, 0.27002047746476765, -2.6065336238662007],
	    [2.3906737285215178, 0.69387894107538739, 0.27002047746476748, -0.17805573936117014],
	],
	trisAlt.strip_I: [
	    [-0.44916112192145952, 2.1122756168847681, -0.79012198328513161, -2.3865538712183882],
	    [-0.17280305940844223, 1.708197033320781, -1.3032695012730287, -1.0165778617602852],
	    [1.9747407952132807, 1.4333956202690126, 1.3032695012730287, -2.125014791829507],
	    [2.2510988577262974, 1.0293170367050262, 0.79012198328513306, -0.75503878237140576],
	],
	# T_STRIP_II checked?
	trisAlt.star: [
	    # same as T_STRIP_I, since d==0
	    [-0.44916112192145868, 2.1122756168847676, -0.7901219832851325, -2.38655387121839],
	    [-0.17280305940844282, 1.7081970333207814, -1.3032695012730278, -1.0165778617602879],
	    [1.9747407952132801, 1.433395620269013, 1.3032695012730293, -2.1250147918295088],
	    [2.2510988577262974, 1.0293170367050257, 0.7901219832851325, -0.75503878237140576],
	],
	trisAlt.star_1_loose: [
	    # same as T_STRIP_1_LOOSE, since d == 0
	    [0.61336294993015139, 0.69387894107538739, -2.0238552489037858, -2.9635369142286225],
	    [-0.5887359927166792, 2.4477137125144059, -0.27002047746476787, -2.9635369142286265],
	    [-0.58873599271667931, 2.4477137125144055, -0.27002047746476787, -0.53505902972359287],
	    [0.61336294993015172, 0.6938789410753875, -2.0238552489037858, -0.5350590297235911],
	    [1.1885747858746869, 2.4477137125144059, 2.0238552489037858, -0.17805573936116925],
	    [1.1885747858746867, 2.4477137125144059, 2.0238552489037858, -2.6065336238662007],
	    [2.3906737285215178, 0.69387894107538739, 0.27002047746476765, -2.6065336238662007],
	    [2.3906737285215178, 0.69387894107538739, 0.27002047746476748, -0.17805573936117014],
	],
    },
}

###############################################################################
l = [
   [-0.08705843892515136, 1.5969418702542431, -1.421867197734886, 2.9924491746224842],
   [0.49431990960006078, 0.84938187722147296, -1.9643841934177342, 0.66547727260192069],
   [1.3076178262047773, 2.2922107763683206, 1.9643841934177342, 2.4761153809878742],
   [1.8889961747299897, 1.5446507833355498, 1.4218671977348862, 0.14914347896730806],
]
FoldedSquares_0 = {
    Heptagons.foldMethod.parallel: {
	# T_STRIP_1_LOOSE checked?
	trisAlt.strip_I: l,
	trisAlt.strip_II: [
	   [-0.11267755272150123, -3.0831450050562297, 1.3877578821507743, 1.8449713169461077],
	   [-0.11267755272150136, -3.0831450050562297, 1.3877578821507746, -2.1153635908403672],
	   [-0.11267755272150137, 1.6299156253637703, -1.3877578821507743, -0.9099725032984054],
	   [-0.11267755272150125, 1.6299156253637701, -1.3877578821507743, 3.0503624044880708],
	   [1.9146152885263397, -0.058447648533563878, -1.3877578821507743, 1.2966213366436845],
	   [1.9146152885263397, -0.058447648533563878, -1.3877578821507743, -1.0262290627494259],
	   [1.9146152885263397, 1.511677028226023, 1.3877578821507743, -2.2316201502913877],
	   [1.9146152885263394, 1.5116770282260232, 1.3877578821507748, 0.091230249101723615],
	],
	trisAlt.star: l,
	# T_STAR_1_LOOSE checked?
    },
}

###############################################################################
E1_1_V2_1 = {
    Heptagons.foldMethod.parallel: {
	# T_STRIP_1_LOOSE checked
	trisAlt.strip_I: [
	   [-0.7567470429582589, -2.5576199555507575, 1.1795454244237868, 2.3059857893662681],
	   [-1.1678661078471526, -2.8121029764287098, 0.68295574950813442, -2.7139655274915295],
	   [-0.41297524742965674, -3.1174972074287144, 1.7516400761892816, 2.79576640194874],
	   [0.077508458941164482, -3.1132425768136569, 2.5081433873465593, -1.0130287751739537],
	   [1.3083497604815739, -0.1140786213581082, -1.285439266528412, 2.7129193530365638],
	   [0.25783404055203479, -2.5546307363274132, 1.7636722787631758, -2.2647077563220268],
	   [1.7906535720932244, 0.18641414197294012, -0.10475933583315822, -1.4181438292384954],
	   [1.7043186392248841, 2.5563292347776989, 1.7243790607070171, -0.22076373594903842],
	],
	# T_STRIP_II checked
	trisAlt.star: [
	   [0.16424126714814655, 2.9498362993661056, 2.3874240497328016, -1.1058248893059073],
	   [-0.19882278292562994, 2.9032159671887756, 1.5610799938533146, 2.4783868428030944],
	   [0.25790649607642102, -2.5549946510779682, 1.7632951187038364, -2.2653071966369556],
	   [0.93204577472517836, 1.5477756634948827, -0.99061381559026351, 2.1311786323813067],
	   [1.4034311724568889, 0.99681726039765606, -1.4331975048281924, 1.4674950784683738],
	   [1.8605312748771268, 2.3066435603055355, 1.4909152805218127, -0.17100514406483569],
	],
	trisAlt.star_1_loose: [
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
	],
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
	]
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
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: [
	    [1.6962939807609119, 0.223747719417109, 2.5922373883920513, -1.5234113058915808],
	],
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: [
	    [-1.4219137817889349, -2.3782898649783748, 2.5967504554976419, 2.5509612243604232],
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
    },
}
