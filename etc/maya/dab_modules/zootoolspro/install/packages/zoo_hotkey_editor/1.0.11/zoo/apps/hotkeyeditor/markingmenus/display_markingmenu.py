from functools import partial

from maya import cmds
from zoo.libs.maya.cmds.display import viewportmodes
import maya.mel as mel

MENU_NAME = "displayMarkingMenu"


class DisplayMMenu(object):
    def __init__(self, ctrlModifier=False, altModifier=False, shiftModifier=False):
        """Builds a marking menu with toggle functionality for the Show menu "Polygons", "NurbsCurves", "Cameras" etc:

            1. Primary functionality builds a marking menu activated. Ie. If key is held and mouse clicked
            2. Secondary functionality will toggle NurbsCurves display if the marking menu is not activated

        Bind the following code to a Maya hotkey "Press", set the modifier keys to match the hotkey being used:

            from zoo.libs.maya.cmds.hotkeys import display_markingmenu
            zooDisplayMarkingMenuInstance = display_markingmenu.pressHotkey(ctrlModifier=False, altModifier=False,
                                                                            shiftModifier=False)
            zooDisplayMarkingMenuInstance.displayMMenu()

        Bind the following code to a Maya hotkey "Release":

            from zoo.libs.maya.cmds.hotkeys import display_markingmenu
            zooDisplayMarkingMenuInstance.releaseHotkey()
            del zooDisplayMarkingMenuInstance

        :param ctrlModifier: set this flag to True if used with a hotkey using the ctrl modifier
        :type ctrlModifier: bool
        :param altModifier: set this flag to True if used with a hotkey using the alt modifier
        :type altModifier: bool
        :param shiftModifier: set this flag to True if used with a hotkey using the shift modifier
        :type shiftModifier: bool
        """
        super(DisplayMMenu, self).__init__()
        self.ctrlModifier = ctrlModifier
        self.altModifier = altModifier
        self.shiftModifier = shiftModifier

    def pressHotkey(self):
        """Starts the marking menu when pressed by a hotkey, will not show the marking menu until mouse is clicked"""
        self.mouseClicked = False
        self.currentPanel = viewportmodes.panelUnderPointerOrFocus(viewport3d=True, message=False)
        if not self.currentPanel:  # the current panel is not a valid 3d viewport
            return
        parent = mel.eval("findPanelPopupParent")  # so we can use the MM in all main windows including tearoff panels
        self.menu = cmds.popupMenu(MENU_NAME,
                                   markingMenu=True,
                                   button=True,
                                   allowOptionBoxes=True,
                                   ctrlModifier=self.ctrlModifier,
                                   altModifier=self.altModifier,
                                   shiftModifier=self.shiftModifier,
                                   parent=parent,
                                   postMenuCommandOnce=0,
                                   postMenuCommand=self._showMM)

    def releaseHotkey(self):
        """Called by a released hotkey, if no mouse click (marking menu shown) then run the alternate command """
        if cmds.popupMenu(MENU_NAME, exists=True):
            cmds.deleteUI(MENU_NAME)  # remove the marking menu if it exists
        if not self.mouseClicked and self.currentPanel:  # no menu was used so run the alternate command
            self.alternateCommand()

    def alternateCommand(self):
        """Run when the hotkey was pressed and released without activating/showing the marking menu"""
        curveStatus = not cmds.modelEditor(self.currentPanel, query=True, nurbsCurves=True)
        cmds.modelEditor(self.currentPanel, edit=True, nurbsCurves=curveStatus)

    def _showMM(self, menu, parent):
        """Display the marking menu to the user after the mouse has been clicked.d

        :param menu: the menu name (not used but needs to be caught)
        :type menu: str
        :param parent: the parent name (not used but needs to be caught)
        :type parent: str
        """
        self.mouseClicked = True
        cmds.setParent(MENU_NAME, menu=True)
        cmds.menu(MENU_NAME, edit=True, deleteAllItems=True)

        # get visibility states
        cameraVis = cmds.modelEditor(self.currentPanel, query=True, cameras=True)
        polyVis = cmds.modelEditor(self.currentPanel, query=True, polymeshes=True)
        curveVis = cmds.modelEditor(self.currentPanel, query=True, nurbsCurves=True)
        lightVis = cmds.modelEditor(self.currentPanel, query=True, lights=True)
        jointVis = cmds.modelEditor(self.currentPanel, query=True, joints=True)
        locVis = cmds.modelEditor(self.currentPanel, query=True, locators=True)
        handleVis = cmds.modelEditor(self.currentPanel, query=True, handles=True)
        nurbsVis = cmds.modelEditor(self.currentPanel, query=True, nurbsSurfaces=True)
        gridVis = cmds.modelEditor(self.currentPanel, query=True, grid=True)
        # submenu
        ikHandleVis = cmds.modelEditor(self.currentPanel, query=True, ikHandles=True)
        cvsVis = cmds.modelEditor(self.currentPanel, query=True, cv=True)
        deformersVis = cmds.modelEditor(self.currentPanel, query=True, deformers=True)
        imagePlaneVis = cmds.modelEditor(self.currentPanel, query=True, imagePlane=True)
        dynamicsVis = cmds.modelEditor(self.currentPanel, query=True, dynamics=True)
        strokesVis = cmds.modelEditor(self.currentPanel, query=True, strokes=True)
        folliclesVis = cmds.modelEditor(self.currentPanel, query=True, follicles=True)
        nClothVis = cmds.modelEditor(self.currentPanel, query=True, nCloths=True)
        motionTrailVis = cmds.modelEditor(self.currentPanel, query=True, motionTrails=True)
        pluginVis = cmds.modelEditor(self.currentPanel, query=True, pluginShapes=True)
        texturesVis = cmds.modelEditor(self.currentPanel, query=True, textures=True)
        greasePencilVis = cmds.modelEditor(self.currentPanel, query=True, greasePencils=True)
        controllerVis = cmds.modelEditor(self.currentPanel, query=True, controllers=True)

        # create radial menu items
        self._buildMenuItem("Cameras", "cameras", cameraVis, radialPosition="N", image="Camera")
        self._buildMenuItem("Polygons", "polymeshes", polyVis, radialPosition="E", image="polyMesh")
        self._buildMenuItem("Curves", "nurbsCurves", curveVis, radialPosition="S", image="nurbsCurve")
        self._buildMenuItem("Lights", "lights", lightVis, radialPosition="W", image="areaLight")
        self._buildMenuItem("Joints", "joints", jointVis, radialPosition="NE", image="kinJoint")
        self._buildMenuItem("Locators", "locators", locVis, radialPosition="SE", image="locator")
        self._buildMenuItem("Handles", "handles", handleVis, radialPosition="NW", image="pickHandlesComp")
        self._buildMenuItem("NURBS", "nurbsSurfaces", nurbsVis, radialPosition="SW", image="nurbsSurface")
        # create all and none
        cmds.menuItem(label="All Off", image="nodeGrapherClose", command=partial(self._visAllOnOff, vis=False))
        cmds.menuItem(label="All On", image="eye", command=partial(self._visAllOnOff, vis=True))
        # grid
        cmds.menuItem(divider=True)
        self._buildMenuItem("Grid", "grid", gridVis, image="out_grid")
        cmds.menuItem(divider=True)
        # submenu
        self._buildMenuItem("IK Handles", "ikHandles", ikHandleVis, image="ikHandle")
        self._buildMenuItem("NURBS CVs", "cv", cvsVis, image="selectCVs")
        self._buildMenuItem("Image Planes", "imagePlane", imagePlaneVis, image="imagePlane")
        self._buildMenuItem("Deformers", "deformers", deformersVis, image="menuIconDeformations")
        self._buildMenuItem("Dynamics", "dynamics", dynamicsVis, image="hairDynamicCurves")
        self._buildMenuItem("Strokes", "strokes", strokesVis, image="stroke")
        self._buildMenuItem("Follicles", "follicles", folliclesVis, image="follicle")
        self._buildMenuItem("NCloth", "nCloths", nClothVis, image="nCloth")
        self._buildMenuItem("Motion Trails", "motionTrails", motionTrailVis, image="motionTrail")
        self._buildMenuItem("Plugin Shapes", "pluginShapes", pluginVis, image="baked")
        self._buildMenuItem("Texture Placements", "textures", texturesVis, image="textureEditorCheckered")
        self._buildMenuItem("Grease Pencil", "greasePencils", greasePencilVis, image="greasePencilMarker")
        self._buildMenuItem("Controllers", "controllers", controllerVis, image="nurbsCurve")

    def _buildMenuItem(self, label, displayElement, boldFont, radialPosition="", image=""):
        """Builds the menu handles a workaround for the boldFont flag and no radialPosition"""
        if boldFont and radialPosition:
            cmds.menuItem(label=label, command=partial(self._visShowHide, displayElement=displayElement),
                          boldFont=boldFont, radialPosition=radialPosition, image=image)
        elif not boldFont and radialPosition:  # not bold due to bug with boldFont flag
            cmds.menuItem(label=label, command=partial(self._visShowHide, displayElement=displayElement),
                          radialPosition=radialPosition, image=image)
        elif boldFont:  # no radialPosition
            cmds.menuItem(label=label, command=partial(self._visShowHide, displayElement=displayElement),
                          boldFont=boldFont, image=image)
        else:
            cmds.menuItem(label=label, command=partial(self._visShowHide, displayElement=displayElement),
                          image=image)

    def _visShowHide(self, stateBool, displayElement=""):
        """Run when one of the menu items of the marking menu has been clicked

        :param stateBool: Is not used but needs to be caught
        :type stateBool: bool
        :param displayElement: The element to toggle the visibility of "polymeshes" or "cameras" etc
        :type displayElement: str
        """
        if displayElement == "polymeshes":
            visInvertState = not cmds.modelEditor(self.currentPanel, polymeshes=True, query=True)
            cmds.modelEditor(self.currentPanel, edit=True, polymeshes=visInvertState)
        elif displayElement == "cameras":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, cameras=True)
            cmds.modelEditor(self.currentPanel, edit=True, cameras=visInvertState)
        elif displayElement == "nurbsCurves":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, nurbsCurves=True)
            cmds.modelEditor(self.currentPanel, edit=True, nurbsCurves=visInvertState)
        elif displayElement == "lights":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, lights=True)
            cmds.modelEditor(self.currentPanel, edit=True, lights=visInvertState)
        elif displayElement == "joints":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, joints=True)
            cmds.modelEditor(self.currentPanel, edit=True, joints=visInvertState)
        elif displayElement == "locators":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, locators=True)
            cmds.modelEditor(self.currentPanel, edit=True, locators=visInvertState)
        elif displayElement == "handles":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, handles=True)
            cmds.modelEditor(self.currentPanel, edit=True, handles=visInvertState)
        elif displayElement == "nurbsSurfaces":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, nurbsSurfaces=True)
            cmds.modelEditor(self.currentPanel, edit=True, nurbsSurfaces=visInvertState)
        elif displayElement == "grid":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, grid=True)
            cmds.modelEditor(self.currentPanel, edit=True, grid=visInvertState)
        elif displayElement == "ikHandles":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, ikHandles=True)
            cmds.modelEditor(self.currentPanel, edit=True, ikHandles=visInvertState)
        elif displayElement == "cv":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, cv=True)
            cmds.modelEditor(self.currentPanel, edit=True, cv=visInvertState)
        elif displayElement == "deformers":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, deformers=True)
            cmds.modelEditor(self.currentPanel, edit=True, deformers=visInvertState)
        elif displayElement == "imagePlane":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, imagePlane=True)
            cmds.modelEditor(self.currentPanel, edit=True, imagePlane=visInvertState)
        elif displayElement == "dynamics":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, dynamics=True)
            cmds.modelEditor(self.currentPanel, edit=True, dynamics=visInvertState)
        elif displayElement == "strokes":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, strokes=True)
            cmds.modelEditor(self.currentPanel, edit=True, strokes=visInvertState)
        elif displayElement == "follicles":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, follicles=True)
            cmds.modelEditor(self.currentPanel, edit=True, follicles=visInvertState)
        elif displayElement == "nCloths":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, nCloths=True)
            cmds.modelEditor(self.currentPanel, edit=True, nCloths=visInvertState)
        elif displayElement == "motionTrails":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, motionTrails=True)
            cmds.modelEditor(self.currentPanel, edit=True, motionTrails=visInvertState)
        elif displayElement == "pluginShapes":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, pluginShapes=True)
            cmds.modelEditor(self.currentPanel, edit=True, pluginShapes=visInvertState)
        elif displayElement == "textures":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, textures=True)
            cmds.modelEditor(self.currentPanel, edit=True, textures=visInvertState)
        elif displayElement == "greasePencils":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, greasePencils=True)
            cmds.modelEditor(self.currentPanel, edit=True, greasePencils=visInvertState)
        elif displayElement == "controllers":
            visInvertState = not cmds.modelEditor(self.currentPanel, query=True, controllers=True)
            cmds.modelEditor(self.currentPanel, edit=True, controllers=visInvertState)

    def _visAllOnOff(self, stateBool, vis=True):
        """Turns all element visiblility on or off with the vis flag

        :param stateBool: Is not used but needs to be caught
        :type stateBool: bool
        :param vis: True then turn all objects visibility on, False turns off
        :type vis: bool
        """
        cmds.modelEditor(self.currentPanel, edit=True, allObjects=vis)
