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
#-------------------------------------------------------------------
#
# $Log$
#
#

import os
import wx
import wx.lib.colourselect as wxLibCS
import math
import rgb
import Geom3D
import Geom4D
import GeomGui
import Scenes3D
import isometry
from OpenGL.GL import *

Title = 'Create Polyhedron by Orbiting'

class Shape(Geom3D.SimpleShape):
    def __init__(this):
        Geom3D.SimpleShape.__init__(this, [], [])
        #this.dbgTrace = True

    def glInit(this):
        Geom3D.SimpleShape.glInit(this)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glEnable(GL_BLEND)
        pass

class CtrlWin(wx.Frame):
    def __init__(this, shape, canvas, *args, **kwargs):
        this.shape = shape
        this.name = shape.name
        this.canvas = canvas
        kwargs['title'] = Title
        wx.Frame.__init__(this, *args, **kwargs)
        # initialise some default colours:
        c = lambda rgbCol: [c*255 for c in rgbCol]
        this.cols = [
                c(rgb.gold),       c(rgb.forestGreen),
                c(rgb.red4),       c(rgb.deepSkyBlue),
                c(rgb.khaki4),     c(rgb.midnightBlue),
                c(rgb.chocolate1), c(rgb.burlywood1),
                c(rgb.chocolate4), c(rgb.yellow),
                c(rgb.aquamarine), c(rgb.indianRed1)
            ]
        this.statusBar = this.CreateStatusBar()
        this.panel = wx.Panel(this, -1)
        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
        this.mainSizer.Add(
                this.createControlsSizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.setDefaultSize((582, 847))
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()

    def createControlsSizer(this):
        ctrlSizer = wx.BoxSizer(wx.VERTICAL)

        this.showGui = []

        facesSizer = wx.StaticBoxSizer(
            wx.StaticBox(this.panel, label = 'Face(s) Definition'),
            wx.VERTICAL
        )
        ctrlSizer.Add(facesSizer, 0, wx.EXPAND)

        dataSizer = wx.BoxSizer(wx.HORIZONTAL)

        #VERTICES
        this.showGui.append(wx.StaticBox(this.panel, label = 'Vertices'))
        bSizer = wx.StaticBoxSizer(this.showGui[-1])
        this.showGui.append(GeomGui.Vector3DSetDynamicPanel(this.panel))
        this.__VsGuiIndex = len(this.showGui) - 1
        bSizer.Add(this.showGui[-1], 1, wx.EXPAND)
        dataSizer.Add(bSizer, 1, wx.EXPAND)

        # FACES
        this.showGui.append(wx.StaticBox(this.panel, label = 'Faces'))
        bSizer = wx.StaticBoxSizer(this.showGui[-1])
        this.showGui.append(
            GeomGui.FaceSetDynamicPanel(this.panel, 0, faceLen = 3)
        )
        this.__FsGuiIndex = len(this.showGui) - 1
        bSizer.Add(this.showGui[-1], 1, wx.EXPAND)
        dataSizer.Add(bSizer, 1, wx.EXPAND)
        facesSizer.Add(dataSizer, 0, wx.EXPAND)

        # Import
        this.showGui.append(wx.Button(this.panel, wx.ID_ANY, "Import"))
        this.panel.Bind(wx.EVT_BUTTON, this.onImport,
                id = this.showGui[-1].GetId())
        facesSizer.Add(this.showGui[-1], 0)

        # SYMMETRY
        this.showGui.append(
            GeomGui.SymmetrySelect(this.panel,
                'Final Symmetry',
                onSymSelect = lambda a: this.onSymmetrySeleect(a)
            )
        )
        this.__FinalSymGuiIndex = len(this.showGui) - 1
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        # Stabiliser
        this.showGui.append(
            GeomGui.SymmetrySelect(this.panel,
                'Stabiliser Symmetry',
                this.showGui[
                    this.__FinalSymGuiIndex
                ].getSymmetryClass(applyOrder = True).subgroups,
            )
        )
        this.__StabSymGuiIndex = len(this.showGui) - 1
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        this.showGui.append(wx.Button(this.panel, wx.ID_ANY, "Apply Symmetry"))
        this.panel.Bind(
            wx.EVT_BUTTON, this.onApplySymmetry, id = this.showGui[-1].GetId())
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        this.ctrlSizer = ctrlSizer
        return ctrlSizer

    def addColourGui(this):
        try:
            this.colSizer.Clear(True)
        except AttributeError:
            this.colGuiBox = wx.StaticBox(this.panel, label = 'Colour Setup')
            this.colSizer = wx.StaticBoxSizer(this.colGuiBox, wx.VERTICAL)
            this.ctrlSizer.Add(this.colSizer, 0, wx.EXPAND)
        finalSymClass = this.showGui[this.__FinalSymGuiIndex].getSymmetryClass(
                applyOrder = True
            )
        stabSymClass = this.showGui[this.__StabSymGuiIndex].getSymmetryClass(
                applyOrder = True
            )
        finalSym = this.showGui[this.__FinalSymGuiIndex].GetSelected()
        stabSym = this.showGui[this.__StabSymGuiIndex].GetSelected()
        this.colIsomsList     = []
        this.colIsomsFiltered = []
        this.posColStabSym    = []
        this.nrOfCols         = []
        nrOfColsChoiceList    = []
        #print 'addColourGui check sub-groups'
        for subSymGrp in finalSymClass.subgroups:
            #print 'subSymGrp', subSymGrp
            #print '...contains stabSymClass', stabSymClass, '...??..',
            if stabSymClass in subSymGrp.subgroups:
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

                colIsoms = finalSym.realiseSubgroups(subSymGrp)
                #print 'check list of len:', len(colIsoms)
                for i in range(len(colIsoms)-1, -1, -1):
                    #print 'isSubgroup', stabSym, colIsoms[i]
                    if stabSym.isSubgroup(colIsoms[i]):
                        #print 'yes, break at index', i
                        break
                    else:
                        # remove this from the list, this is part of the work of
                        # filtering the list. This is not done completely here
                        # since it costs time, and the user might not choose
                        # this colouring anyway (hence the break above). But to
                        # save time later, remove it already.
                        #print 'no'
                        del colIsoms[i]
                if colIsoms != []:
                    #print 'add True'
                    this.posColStabSym.append(subSymGrp)
                    this.colIsomsList.append(colIsoms)
                    this.colIsomsFiltered.append(False)
                    #print 'addColourGui, finalSymClass', finalSymClass
                    fo = isometry.order(finalSymClass)
                    assert fo != 0
                    po = isometry.order(subSymGrp)
                    assert po != 0
                    q = fo / po
                    this.nrOfCols.append(q)
                    nrOfColsChoiceList.append(
                        '%d (based on %s)' % (q, subSymGrp.__name__)
                    )
                #else:
                #    print 'add False'
            #else:
            #    print 'no'
        this.colGuis = []
        this.colGuis.append(
            wx.Choice(this.panel, wx.ID_ANY, choices = nrOfColsChoiceList)
        )
        this.colSizer.Add(this.colGuis[-1], 0, wx.EXPAND)
        this.panel.Bind(wx.EVT_CHOICE,
            this.onNrColsSel, id = this.colGuis[-1].GetId())
        this.colGuis[-1].SetSelection(0)
        this.__nrOfColsGuiId = this.colGuis[-1]
        this.onNrColsSel(this.colGuis[-1])

    def onSymmetrySeleect(this, sym):
        this.showGui[this.__StabSymGuiIndex].setList(
                this.showGui[this.__FinalSymGuiIndex].getSymmetryClass().subgroups,
            )

    def onApplySymmetry(this, e):
        print this.GetSize()
        Vs = this.showGui[this.__VsGuiIndex].get()
        Fs = this.showGui[this.__FsGuiIndex].get()
        if Fs == []:
            this.statusBar.SetStatusText(
                "ERROR: No faces defined!"
            )
            return
        finalSym = this.showGui[this.__FinalSymGuiIndex].GetSelected()
        stabSym = this.showGui[this.__StabSymGuiIndex].GetSelected()
        this.shape = Geom3D.SymmetricShape(Vs, Fs,
                finalSym = finalSym, stabSym = stabSym, name = this.name
            )
        this.FsOrbit = this.shape.getIsoOp()['direct']
        this.shape.recreateEdges()
        this.canvas.panel.setShape(this.shape)
        this.addColourGui()
        this.panel.Layout()
        this.statusBar.SetStatusText("Symmetry applied: choose colours")
        try:
            tst = this.cols
        except AttributeError:
            this.cols = [(255, 100, 0)]
        e.Skip()

    def onNrColsSel(this, e):
        try:
            this.selColSizer.Clear(True)
        except AttributeError:
            this.selColSizer = wx.BoxSizer(wx.VERTICAL)
            this.colSizer.Add(this.selColSizer, 0, wx.EXPAND)
            nextPrevColSizer = wx.BoxSizer(wx.HORIZONTAL)
            this.colGuis.append(
                wx.Button(this.panel, wx.ID_ANY, "Previous Alternative"))
            this.panel.Bind(
                wx.EVT_BUTTON, this.onPrevColAlt, id = this.colGuis[-1].GetId())
            nextPrevColSizer.Add(this.colGuis[-1], 0, wx.EXPAND)
            this.colGuis.append(
                wx.Button(this.panel, wx.ID_ANY, "Next Alternative"))
            this.panel.Bind(
                wx.EVT_BUTTON, this.onNextColAlt, id = this.colGuis[-1].GetId())
            nextPrevColSizer.Add(this.colGuis[-1], 0, wx.EXPAND)
            this.colSizer.Add(nextPrevColSizer, 0, wx.EXPAND)

        colDivNr = e.GetSelection()
        colSym = this.posColStabSym[colDivNr]
        this.colIsoms = this.colIsomsList[colDivNr]
        finalSym = this.showGui[this.__FinalSymGuiIndex].GetSelected()
        assert len(this.colIsoms) != 0
        nrOfCols = this.nrOfCols[colDivNr]
        this.selColGuis = []
        initColour = (255, 255, 255)
        maxColPerRow = 12
        # Add buttons for choosing individual colours:
        for i in range(nrOfCols):
            try:
                col = this.cols[i]
            except IndexError:
                col = initColour
                this.cols.append(col)
            if i % maxColPerRow == 0:
                selColSizerRow = wx.BoxSizer(wx.HORIZONTAL)
                this.selColSizer.Add(selColSizerRow, 0, wx.EXPAND)
            this.selColGuis.append(
                wxLibCS.ColourSelect(this.panel, wx.ID_ANY, colour = col)
            )
            this.panel.Bind(wxLibCS.EVT_COLOURSELECT, this.onColSel)
            selColSizerRow.Add(this.selColGuis[-1], 0, wx.EXPAND)
        this.colAlternative = 0
        if not (this.colIsomsFiltered[colDivNr]):
            # Now filter out the stabilisers that are not a subgroup for this
            # orientation.
            # (part of this is done in addColourGui)
            # E.g.
            # final symmetry S4xI
            # stabiliser: D2C2 with principle axis: one 2-fold from S4xI
            #                                       (ie not a 4-fold axis)
            # Now D4xI is a subgroup of S4xI
            # and D2C2 is a subgroup of D4xI,
            # but not necessarily this orientation. In fact only one of the
            # three possible D4xI will have this D2C2 as subgroup.
            stabSym = this.showGui[this.__StabSymGuiIndex].GetSelected()
            for i in range(len(this.colIsoms)-1, -1, -1):
                if not stabSym.isSubgroup(this.colIsoms[i]):
                    del this.colIsoms[i]
            assert len(this.colIsoms) != 0, (
                "This case should have be taken care of in addColourGui")

        this.updatShapeColours()
        this.panel.Layout()

    def onColSel(this, e):
        col = e.GetValue().Get()
        guiId = e.GetId()
        for i, gui in zip(range(len(this.selColGuis)), this.selColGuis):
            if gui.GetId() == guiId:
                #print 'update %d with colour %s.' % (i, col)
                this.cols[i] = col
                this.updatShapeColours()
                break

    def updatShapeColours(this):
        """apply symmetry on colours
        """
        finalSym = this.showGui[this.__FinalSymGuiIndex].GetSelected()
        #print 'finalSym', finalSym
        #print 'close finalSym', finalSym.close()
        #print 'this.colAlternative', this.colAlternative
        colQuotientSet = finalSym  / this.colIsoms[this.colAlternative]
        #print '-----colQuotientSet-----------'
        #for isom in colQuotientSet: print isom
        #print '------------------------------'
        #print '--------FsOrbit---------------'
        #for isom in this.FsOrbit: print isom
        #print '------------------------------'
        colPerIsom = []
        for isom in this.FsOrbit:
            for subSet, i in zip(colQuotientSet, range(len(colQuotientSet))):
                if isom in subSet:
                    colPerIsom.append(this.cols[i])
                    break;
        #print 'colPerIsom', colPerIsom
        cols = [
                ([[float(colCh)/255 for colCh in col]], [])
                for col in colPerIsom
            ]
        this.shape.setSymmetricFaceColors(cols)
        this.statusBar.SetStatusText(
            "Colour alternative %d of %d applied" % (
                this.colAlternative + 1, len(this.colIsoms)
            )
        )
        this.canvas.paint()
        #print 'TODO: gen colour quotientset and compare with face quotient set'

    # move to general class
    def setDefaultSize(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

    def onNextColAlt(this, e):
        this.colAlternative += 1
        if this.colAlternative >= len(this.colIsoms):
            this.colAlternative -= len(this.colIsoms)
        this.updatShapeColours()

    def onPrevColAlt(this, e):
        this.colAlternative -= 1
        if this.colAlternative < 0:
            this.colAlternative += len(this.colIsoms)
        this.updatShapeColours()

    def onImport(this, e):
        dlg = wx.FileDialog(this, 'New: Choose a file', '.', '',
                'Python files (*.py)|*.py|OFF files (*.off)|*.*off', wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            importDirName  = dlg.GetDirectory()
            print "opening file:", filename
            fd = open(os.path.join(importDirName, filename), 'r')
            if filename[-3:] == '.py':
                shape = Geom3D.readPyFile(fd)
            else:
                shape = Geom3D.readOffFile(fd, recreateEdges = False)
            fd.close()
            if isinstance(shape, Geom3D.IsometricShape):
                Vs = shape.baseShape.Vs
                Fs = shape.baseShape.Fs
            else:
                print 'no isometry'
                Vs = shape.Vs
                Fs = shape.Fs
            print 'read ', len(Vs), ' Vs and ', len(Fs), ' Fs.'
            this.showGui[this.__VsGuiIndex].set(Vs)
            this.showGui[this.__FsGuiIndex].set(Fs)
            this.name = filename
        dlg.Destroy()

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
