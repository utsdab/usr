from maya import cmds
from maya.api import OpenMaya as om2
import maya.mel as mel

from zoo.libs.maya.cmds.objutils import selection

# For combo box presets
DISP_NO_IMAGE = "Display No Image"
DISP_WIRE_ONLY = "Display Wireframe"
DISP_CHECKER_100 = "Display Checker 100%"
DISP_CHECKER_75 = "Display Checker 75%"
DISP_CHECKER_50 = "Display Checker 50%"
DISP_CHECKER_25 = "Display Checker 25%"
DISP_CHECKER_05 = "Display Checker 5%"
DISP_SHADED = "Display Shaded"
DISP_DISTORTION = "Display Distortion"
DISP_COLORED_SHELLS = "Display Colored Shells"
DISP_TEXTURE_05 = "Display Texture 5%"
DISP_TEXTURE_25 = "Display Texture 25%"
DISP_TEXTURE_50 = "Display Texture 50%"
DISP_TEXTURE_75 = "Display Texture 75%"
DISP_TEXTURE_100 = "Display Texture 100%"
DISPLAY_MODES = [DISP_NO_IMAGE, DISP_WIRE_ONLY, DISP_CHECKER_100, DISP_CHECKER_75, DISP_CHECKER_50, DISP_CHECKER_25,
                 DISP_CHECKER_05, DISP_SHADED, DISP_COLORED_SHELLS, DISP_DISTORTION, DISP_TEXTURE_05, DISP_TEXTURE_25,
                 DISP_TEXTURE_50,
                 DISP_TEXTURE_75, DISP_TEXTURE_100]

UNFOLD_PLUGIN_NAME = "Unfold3D"


def uvLists(componentSelection):
    """From any maya selection return the UVs as two lists, u space and v space:

        uList = [12, 23.0, 34.5]
        vList = [12.34, 23.23, 3.5]

    :param componentSelection: Maya selection
    :type componentSelection: str(lists)
    :return:
    :rtype:
    """
    rememberSelection = cmds.ls(selection=True)
    rememberComponentMode = selection.componentSelectionType(rememberSelection)
    cmds.select(componentSelection, replace=True)
    uvSelection = selection.convertSelection("uvs")
    # get the uv coords
    uvCoords = cmds.polyEditUV(uvSelection, query=True, uValue=True)
    uList = uvCoords[::2]  # just the u values
    vList = uvCoords[1::2]  # just the v values
    # return original selection
    if rememberSelection:
        selection.selectComponentSelectionMode(rememberComponentMode)  # sets the correct component mode
        cmds.select(rememberSelection, replace=True)
    else:
        cmds.select(deselect=True)
    return uList, vList


"""
DISPLAY
"""


def uvEdgeVerticalOrHorizontal(componentSelection, mode="tube"):
    """Returns whether the uv edge selection is in horizontal or vertical space, assumes perfectly horizontal/vertical
    Usually used with gridify and unfold on a single axis.

    Automatically figures if unwrap should be vertical or horizontal.

    If mode is "tube" then assumes the edge selection is on a UV border (has been gridified), otherwise "grid" is a \
    single edge-loop. "tube" mode needs more than one edge selected or it will fail.

    The selection will have 2 rows or columns in a perfectly straight UV line, return whether:
        Columns = should unwrap "horizontal"
        Rows = should unwrap "vertical"
        Unknown not detected = ""

    mode is the method to figure:

        "tube": is two uv edge loops (only in uvs) sharing a shell border
        "grid": one edge loop

    :param componentSelection: A Maya selection, a border seam edge that has been gridified
    :type componentSelection: list(str)
    :return: "horizontal" if rows, "vertical" if columns,  return "" if unknown
    :rtype: str
    """
    # a single edge is not enough to calculate if in "tube" mode, return unknown
    if mode == "tube":
        if selection.countComponentsInSelection(componentSelection) == 1:
            return ""
    uList, vList = uvLists(componentSelection)
    if mode == "tube":
        if len(set(uList)) == 2:
            return "horizontal"
        if len(set(vList)) == 2:
            return "vertical"
    else:  # mode will be "grid" (shell grid)
        if len(set(uList)) > 1:  # single straight line so won't have more than one entry if horizontal
            return "horizontal"
        else:
            return "vertical"
    return ""


def uvBoundingBoxSize(componentSelection):
    """returns the bounding box size of the component selection in uvs

    Example:
        componentSelection = ["object.f[0:123]", "object.f[333]"]
        return uWidth: 0.751,
        return vHeight: 0.221

    :param componentSelection: Maya object or component selection
    :type componentSelection: list(str)
    :return uWidth: the width of the uv bounding box
    :rtype uWidth: float
    :return vHeight: the height of the uv bounding box
    :rtype vHeight: float
    """
    # get the uv data
    uList, vList = uvLists(componentSelection)
    uList.sort()
    vList.sort()
    # range of lists
    uWidth = uList[-1] - uList[0]
    vHeight = vList[-1] - vList[0]
    return uWidth, vHeight


def boundingBoxHorizontalOrVertical(selComponents):
    """Tests to see if the UV bounding box of any maya selection is more vertical or horizontal.

    returns "" if the uv bounding box is identical in width and height

    :param selComponents: Maya object or component selection
    :type selComponents: list(str)
    :return horizontalOrVertical: Can be "horizontal", "vertical" or "" if identical
    :rtype horizontalOrVertical: str
    """
    uWidth, vHeight = uvBoundingBoxSize(selComponents)
    if uWidth == vHeight:  # is the same
        return ""
    elif uWidth > vHeight:
        return "horizontal"
    return "vertical"


"""
UV EDITOR
"""


def openUVEditor(displayStyle=""):
    """Opens Mayas UV editor and optionally sets the newly opened UV editor's display settings

    :param displayStyle: The preset name as defined in the globals
    :type displayStyle: str
    """
    mel.eval('texturePanelShow;')
    if displayStyle:
        uvDisplayModePresets(displayStyle=displayStyle)


"""
DISPLAY
"""


def uvDisplayModePresets(displayStyle=DISP_CHECKER_100):
    """Presets for various UV editor display modes

    :param displayStyle: The preset name as defined in the globals
    :type displayStyle: str
    """
    if displayStyle == DISP_WIRE_ONLY:
        uvDisplayMode(checker=False, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=1.0)
    elif displayStyle == DISP_NO_IMAGE:  # silly case because image is often not removed, due to buggy Maya code
        texWinName = cmds.getPanel(sty='polyTexturePlacementPanel')
        for window in texWinName:  # usually only one window
            cmds.textureWindow(window, edit=True, imageDisplay=0)
    elif displayStyle == DISP_SHADED:
        uvDisplayMode(checker=False, textureImage=False, shaded=True, distortion=False, coloredShells=False,
                      textureTransparency=1.0)
    elif displayStyle == DISP_DISTORTION:
        uvDisplayMode(checker=False, textureImage=False, shaded=True, distortion=True, coloredShells=False,
                      textureTransparency=1.0)
    elif displayStyle == DISP_COLORED_SHELLS:
        uvDisplayMode(checker=False, textureImage=False, shaded=True, distortion=False, coloredShells=True,
                      textureTransparency=1.0)
    elif displayStyle == DISP_CHECKER_100:
        uvDisplayMode(checker=True, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=1.0)
    elif displayStyle == DISP_CHECKER_75:
        uvDisplayMode(checker=True, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=0.75)
    elif displayStyle == DISP_CHECKER_50:
        uvDisplayMode(checker=True, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=0.5)
    elif displayStyle == DISP_CHECKER_25:
        uvDisplayMode(checker=True, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=0.25)
    elif displayStyle == DISP_CHECKER_05:
        uvDisplayMode(checker=True, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=0.05)
    elif displayStyle == DISP_TEXTURE_05:
        uvDisplayMode(checker=False, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=0.05)
    elif displayStyle == DISP_TEXTURE_25:
        uvDisplayMode(checker=False, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=0.25)
    elif displayStyle == DISP_TEXTURE_50:
        uvDisplayMode(checker=False, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=0.50)
    elif displayStyle == DISP_TEXTURE_75:
        uvDisplayMode(checker=False, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=0.75)
    elif displayStyle == DISP_TEXTURE_100:
        uvDisplayMode(checker=False, textureImage=True, shaded=False, distortion=False, coloredShells=False,
                      textureTransparency=1.0)


def uvDisplayMode(checker=True, textureImage=False, shaded=False, distortion=False, coloredShells=False,
                  textureTransparency=1.0):
    """Sets the UV display settings of the UV editor

    Note this code can be a little flakey, seems to be due to Maya code doing weird things, works in most cases.

    :param checker: Sets the checker texture visibility, must also have textureImage on. checker False is maya texture
    :type checker: bool
    :param textureImage:  Sets the texture image on or off.  Can be the texture or the objects texture see "checker"
    :type textureImage: bool
    :param shaded: Sets the shaded mode on needed for distortion and coloredShells, otherwise is blue shells
    :type shaded: bool
    :param distortion: Sets the distortion to be on, must have "shaded" on, coloredShells off
    :type distortion: bool
    :param coloredShells: Sets each UV shell to be a different color, must have "shaded" on, distortion off
    :type coloredShells: bool
    :param textureTransparency:  Sets the texture dimming level 1.0 is full texture, 0.0 is black
    :type textureTransparency: bool
    """
    texWinName = cmds.getPanel(sty='polyTexturePlacementPanel')
    for window in texWinName:  # usually only one window "polyTexturePlacementPanel1"
        cmds.textureWindow(window,
                           edit=True,
                           displayCheckered=checker,
                           imageDisplay=textureImage,
                           displayDistortion=distortion,
                           solidMapPerShell=coloredShells,
                           imageDim=True,
                           imageBaseColor=(textureTransparency, textureTransparency, textureTransparency))
        mel.eval('textureWindowDisplayCheckered(1, {});'.format(int(checker)))
        mel.eval('textureWindowSolidMap(1, {})'.format(int(shaded)))  # shaded must be an Int not True or False
        mel.eval('textureWindowDistortion(1, {})'.format(int(distortion)))
        # mel.eval('txtWndUpdateEditor( "{}", "textureWindow", "null", 101 );'.format(window))  # refresh?


def uvBorderSize(borderSize=2):
    """Sets the UV border display width

    :param borderSize: Border width in pixels
    :type borderSize: int
    """
    texWinName = cmds.getPanel(sty='polyTexturePlacementPanel')
    for window in texWinName:  # usually only one window
        cmds.textureWindow(window, edit=True, textureBorderWidth=borderSize)
    mel.eval('uvTbImageDimmingCallback;')  # does a refresh find actual command?
    # mel.eval('txtWndUpdateEditor( "{}", "textureWindow", "null", 101 );'.format(window))  # refresh?


def checkerTextureSize(checkerDensity=128):
    """Sets the check size if visible, above 256 is a lot of squares and can alias badly

    :param checkerDensity: The amount of squares horizontally or vertically
    :type checkerDensity: int
    """
    texWinName = cmds.getPanel(sty='polyTexturePlacementPanel')
    cmds.textureWindow(texWinName[0], edit=True, checkerDensity=checkerDensity)
    # needs to refresh active window
    # mel.eval('txtWndUpdateEditor( "{}", "textureWindow", "null", 101 );'.format(window))  # refresh?


"""
PROJECTION
"""


def uvProjection(selList, type="planar", mapDirection="c"):
    """Standard Maya UV projection,  "planar", "cylindrical", "spherical"

    Must use selection in this function due to converting to faces with selection.convertSelection(type="faces")

    :param selList: The selection to UV map
    :type selList: list(str)
    :param type: type of mapping to be performed "planar", "cylindrical", "spherical"
    :type type: str
    :param mapDirection: "c" is camera "x" is X, "z" is Z, "y" is Y "bestPlane" finds the best plane
    :type mapDirection: str
    """
    rememberSelection = cmds.ls(selection=True)
    cmds.select(selList, replace=True)
    selection.convertSelection(type="faces")
    projectNode = cmds.polyProjection(type=type, mapDirection=mapDirection)
    cmds.select(rememberSelection, replace=True)
    return projectNode


def uvProjectionSelection(type="planar", mapDirection="c", message=True):
    """Standard Maya UV projection,  "planar", "cylindrical", "spherical" uses selection

    :param selList: The selection to UV map
    :type selList: list(str)
    :param type: type of mapping to be performed "planar", "cylindrical", "spherical"
    :type type: str
    :param mapDirection: "c" is camera "x" is X, "z" is Z, "y" is Y "bestPlane" finds the best plane
    :type mapDirection: str
    :param message: Report the message to the user?
    :type message: bool
    :return success: Operation was successful True or not False
    :rtype success: bool
    """
    # Todo: maybe better to use the mel command, as doesn't bring up the manipluator etc
    selObjs, componentMode = selection.selectObjectNoComponent()
    if not selObjs:  # message already given
        return
    projectNode = uvProjection(selObjs, type=type, mapDirection=mapDirection)
    if componentMode:
        cmds.selectMode(component=True)
    cmds.select(projectNode, deselect=True)
    cmds.select(projectNode, addFirst=True)
    # show manipulatorq
    mel.eval('setToolTo ShowManips')
    return True


"""
MIRROR/SYMMETRY
"""


def symmetryBrush(auto=True, UVAxisOffset=0.5, UVAxis=0, UVAxisIncrement=0.1, useMayaOptions=False):
    """Activates the symmetry brush with automatic setting of the UVAxisOffset and UVAxis

        1. Select a center edge (if auto=True)
        2. Run the script
        3. Select the same center edge
        4. Pivot and axis are set automatically

    :param auto: When True will take the selection if a edge, uv or vert selection
    :type auto: bool
    :param UVAxisOffset: The pivot of the symmetry, is overriden by auto=True
    :type UVAxisOffset: float
    :param UVAxis: 0 is horizontal, 1 is vertical
    :type UVAxis: int
    :param UVAxisIncrement: For the ctrl MMB set axis manually, amount to increment that line
    :type UVAxisIncrement: float
    :param useMayaOptions: If True will use Maya's default options, instead of our kwargs, "auto" must be False
    :type useMayaOptions: bool
    """
    selComponents = cmds.ls(selection=True)
    if selComponents:
        componentType = selection.componentSelectionType(selComponents)
    if selComponents and auto and componentType != "object":
        # Do the auto calculation
        if componentType == "faces":
            om2.MGlobal.displayWarning("Please select center edge, or line of uvs or vertices")
            return
        symAxis = boundingBoxHorizontalOrVertical(selComponents)
        # set the axis for the mel
        UVAxis = 1 if symAxis == "horizontal" else 0
        # Set pivot for the symmetry
        cmds.select(selComponents, replace=True)
        uvSelection = selection.convertSelection("uvs")
        uvCoords = cmds.polyEditUV(uvSelection, query=True, uValue=True)
        if symAxis == "horizontal":
            alignUvSelection(straightenType="avgV")  # align is bad and doesn't take the average only max min
            UVAxisOffset = uvCoords[1]  # first uv u coord is the pivot in u space, second is v vertical
        else:  # will be "vertical" or ""
            alignUvSelection(straightenType="avgU")  # align is bad and doesn't take the average only max min
            UVAxisOffset = uvCoords[0]  # first uv u coord is the pivot in u space, second is v vertical
    # Do the symmetrize
    if not useMayaOptions or auto:
        mel.eval('optionVar -iv polySymmetrizeUVAxis {};'.format(str(UVAxis)))
        mel.eval('optionVar -fv polySymmetrizeUVAxisOffset {};'.format(str(UVAxisOffset)))
        mel.eval('optionVar -fv polySymmetrizeUVAxisIncrement {};'.format(str(UVAxisIncrement)))
    mel.eval('setToolTo texSymmetrizeUVContext;')


"""
CUT/SEW
"""


def cutUvs(edgeSelection, constructionHistory=False):
    """Cuts UV edge based on selList list with edge selection

    :param edgeSelection: Maya selection list
    :type edgeSelection: list(str)
    """
    cmds.polyMapCut(edgeSelection, constructionHistory=constructionHistory)
    return True


def cutUvsSelection(message=True, constructionHistory=True):
    """Cuts UV edge based on selection with edge check and warning message

    :param message: Report the message to the user?
    :type message: bool
    :return success: Operation was successful True or not False
    :rtype success: bool
    """
    selList = cmds.ls(selection=True, long=True)
    edgeSelection = selection.componentSelectionFilterType(selList, "edges")
    if not edgeSelection:
        if message:
            om2.MGlobal.displayWarning("Please make an edge selection")
            return False
    cutUvs(edgeSelection, constructionHistory=constructionHistory)
    return True


def cutPerimeterUVs(componentSelection, constructionHistory=True):
    """Cuts a perimeter edge of UVs while maintaining the current selection and component mode

    :param componentSelection: A maya selection
    :type componentSelection: list(str)
    :param constructionHistory: keep construction history?
    :type constructionHistory: bool
    """
    cmds.select(componentSelection, replace=True)
    componentType = selection.componentSelectionType(componentSelection)  # gets the component mode
    if componentType == "object":
        om2.MGlobal.displayWarning("Selection must be component selection, not objects")
        return
    edgeSelection = selection.convertSelection("edgePerimeter")
    cutUvs(edgeSelection, constructionHistory=constructionHistory)
    selection.selectComponentSelectionMode(componentType)  # sets the correct component mode
    cmds.select(componentSelection, replace=True)


def cutPerimeterUVsSelection(constructionHistory=True):
    """Cuts a perimeter edge of UVs based on selection, while maintaining the current selection and component mode

    :param constructionHistory: keep construction history?
    :type constructionHistory: bool
    """
    selObs = cmds.ls(selection=True)
    if not selObs:
        om2.MGlobal.displayWarning("Please make an component selection")
        return
    if "." not in selObs[0]:
        om2.MGlobal.displayWarning("Please make an component selection")
        return
    cutPerimeterUVs(selObs, constructionHistory=constructionHistory)


def sewUvs(edgeSelection, constructionHistory=False):
    """Cuts UV edges based on selList list with edge selection

    :param edgeSelection: Maya selection list
    :type edgeSelection: list(str)
    """
    cmds.polyMapSew(edgeSelection, constructionHistory=constructionHistory)
    return True


def sewUvsSelection(constructionHistory=False, message=True):
    """Sews UV edges based on selection with edge check and warning message

    :param message: Report the message to the user?
    :type message: bool
    :return success: Operation was successful True or not False
    :rtype success: bool
    """
    selList = cmds.ls(selection=True, long=True)
    edgeSelection = selection.componentSelectionFilterType(selList, "edges")
    if not edgeSelection:
        if message:
            om2.MGlobal.displayWarning("Please make an edge selection")
            return False
    sewUvs(edgeSelection, constructionHistory=constructionHistory)
    return True


def moveAndSew(selList):
    """Move and sew uvs with default settings

    :param selList: Maya selection
    :type selList: list(str)
    """
    cmds.polyMapSewMove(selList)


def moveAndSewSelection(message=True):
    """Unitize UV faces (old normalize), each quad is zero to one space

    :param message: Report the message to the user?
    :type message: bool
    :return success: Operation was successful True or not False
    :rtype success: bool
    """
    selList = selection.selWarning(message=message)
    if not selList:
        return False
    moveAndSew(selList)
    return True


def cutAndSewTool3d():
    """Enters Maya's 3d Cut and Sew tool"""
    # Todo: options for no break apart while in the UV Editor
    mel.eval('texCutContext - edit - mode Cut texCutUVContext; setToolTo superCutUVContext')


def autoSeamsSelection(splitShells=0.0, cutPipes=1):
    """Maya's auto seam tool

    :param splitShells: The slider for more or less edges in the automatic seam selection (0.0 -1.0)
    :type splitShells: float
    :param cutPipes:
    :type cutPipes:
    """
    mel.eval('u3dAutoSeam '
             '-splitShells {} '
             '-cutPipes {};'.format(str(splitShells),
                                    str(cutPipes)))


"""
ALIGN/STRAIGHTEN
"""


def orientEdge():
    """Orients the whole shell by straightening to the selected edge"""
    mel.eval('texOrientEdge;')


def orientShell():
    """Orients the whole shell automatically, select an object or shell, no component selected will work on object"""
    selObjs, componentMode = selection.selectObjectNoComponent()
    if not selObjs:  # message already given
        return
    mel.eval('texOrientShells;')


def alignUvSelection(straightenType="avgV"):
    """Align Straighten UVs to the center, max or min on either horizontal (U) or vertical (V)

    straightenType is a str, the average minimum or maximum value, and on either vertical or horizontal:
        "minV", "maxV", "avgV", "minU", "maxU", "avgU"

    :param selection: Maya selection of components, ie verts, edges, uvs etc
    :type selection: list(str)
    :param straightenType: how to straighten? "minV", "maxV", "avgV", "minU", "maxU", "avgU",
    :type straightenType: str
    """
    mel.eval('alignUV {};'.format(straightenType))


def straightenUv(components, angle=30, dirType="all"):
    """Mel straighten UV command with options, this function passes in a component selection

    type:
        "all" is all edges are straightened mel "UV"
        "horizontal" restricts to only horizontal edges or "U"
        "vertical" restricts to only vertical edges or "V"

    angle:
        The angle threshold where the straighten occurs

    :param components: A Maya selection, usually faces or UVs, can be objects, edges or vertices too
    :type components: list(str)
    :param angle: The angle threshold where the straighten occurs
    :type angle: float
    :param type: Straighten only on the "vertical" or "horizontal" axis or "all"
    :type type: str
    """
    rememberSelection = cmds.ls(selection=True)
    cmds.select(components, replace=True)
    if dirType == "all":
        dirType = "UV"
    elif dirType == "horizontal":
        dirType = "U"
    elif dirType == "vertical":
        dirType = "V"
    mel.eval('texStraightenUVs "{}" {};'.format(dirType, angle))
    cmds.select(rememberSelection, replace=True)


def straightenUvSelection(angle=30, dirType="all"):
    """Mel straighten UV command with options, works off current selection

    type:
        "all" is all edges are straightened mel "UV"
        "horizontal" restricts to only horizontal edges or "U"
        "vertical" restricts to only vertical edges or "V"

    angle:
        The angle threshold where the straighten occurs

    :param angle: The angle threshold where the straighten occurs
    :type angle: float
    :param type: Straighten only on the "vertical" or "horizontal" axis or "all"
    :type type: str
    """
    if not cmds.ls(selection=True):
        om2.MGlobal.displayWarning("Please make a selection")
        return
    if dirType == "all":
        dirType = "UV"
    elif dirType == "horizontal":
        dirType = "U"
    elif dirType == "vertical":
        dirType = "V"
    mel.eval('texStraightenUVs "{}" {};'.format(dirType, angle))


"""
UNFOLD
"""


def autoSeamsUnfoldSelection(splitShells=0.0, cutPipes=1, select=1, mapSize=1024):
    """Maya's autoseam tool with unfold

    :param splitShells:
    :type splitShells:
    :param cutPipes:
    :type cutPipes:
    :param select:
    :type select:
    :param mapSize:
    :type mapSize:
    :return:
    :rtype:
    """
    pack = 1
    selObjs, componentMode = selection.selectObjectNoComponent()
    if not selObjs:  # message already given
        return
    uvProjectionSelection(type="planar", mapDirection="x", message=True)
    autoSeamsSelection(splitShells=splitShells, cutPipes=cutPipes)
    cmds.select(selObjs, replace=True)
    if componentMode:
        pack = 0
    regularUnfoldSelection(iterations=1, pack=pack, borderintersection=1, triangleflip=1, mapsize=mapSize, roomspace=1)


def regularUnfoldSelection(iterations=1, pack=0, borderintersection=1, triangleflip=1, mapsize=1024, roomspace=0):
    """The default newer plugin Unfold3D algorithm, not legacy unfold.  Works on selection.

    :param iterations: Number of times the calculations are performed
    :type iterations: int
    :param pack: Pack the UVs after unfolding? Note must be 1 or 0 as it's mel
    :type pack: int
    :param borderintersection: prevents self-intersections on the border of the unfolded UV shells, must be 0 or 1
    :type borderintersection: int
    :param triangleflip: prevents degenerate UV maps. Degeneracy can occur when a UV is moved so a face overlaps itself
    :type triangleflip: int
    :param mapsize: The texture map size in pixels to account for shell spacing
    :type mapsize: int
    :param roomspace: Space between UVs on own shells see Maya documentation, recommended don't go past 2
    :type roomspace: int
    """
    selObjs, componentMode = selection.selectObjectNoComponent()
    if not selObjs:  # no selection found
        if componentMode:
            cmds.selectMode(component=True)
        return
    mel.eval('u3dUnfold '
             '- iterations {} '
             '- pack 0 '
             '- borderintersection {} '
             '- triangleflip {} '
             '- mapsize {} '
             '- roomspace {} ;'.format(iterations,
                                       borderintersection,
                                       triangleflip,
                                       mapsize,
                                       roomspace))
    if pack:
        layoutUvs(selObjs, resolution=mapsize)
    if componentMode:
        cmds.selectMode(component=True)


def regularUnfoldSelectionPackOption(iterations=1, borderintersection=1, triangleflip=1, mapsize=1024, roomspace=0):
    """Same as regularUnfoldSelection but will auto pack if an object selection and not pack if component

    Depreciated as the Unfold layout isn't great, could use regular unfold after?

    See regularUnfoldSelection() for documentation
    """
    selObjs, componentMode = selection.selectObjectNoComponent()
    if not selObjs:  # no selection found
        if componentMode:
            cmds.selectMode(component=True)
        return
    if "." in selObjs[0]:  # then is in component so don't pack
        pack = 0
    else:  # is object mode so pack
        pack = 1
    regularUnfoldSelection(iterations=iterations, pack=pack, borderintersection=borderintersection,
                           triangleflip=triangleflip, mapsize=mapsize, roomspace=roomspace)
    if componentMode:
        cmds.selectMode(component=True)


def legacyUnfold(selList, dirType=""):
    """Legacy unfold UVs with options, usually for directional unfolding as is not in the new plugin

    Mostly used for unfolding on one axis
    If using both axis then better to use regularUnfoldSelection()

    :param selList: Maya selection
    :type selList: list(str)
    :param type: "vertical" is vertical, "horizontal" is horizontal, "" is both directions (legacy unfold)
    :type type: str
    """
    if dirType == "vertical":
        optimizeAxis = 1
    elif dirType == "horizontal":
        optimizeAxis = 2
    else:
        optimizeAxis = 0
    cmds.unfold(selList,
                optimizeAxis=optimizeAxis,
                areaWeight=.1,
                stoppingThreshold=0.001,
                iterations=5000,
                globalBlend=False,
                globalMethodBlend=0.5,
                pinUvBorder=False,
                useScale=False)


def legacyUnfoldSelection(dirType="", message=True):
    """Unitize UV faces (old normalize), each quad is zero to one space

    :param message: Report the message to the user?
    :type message: bool
    :return success: Operation was successful True or not False
    :rtype success: bool
    """
    uvSelection = selection.selWarning(message=message)
    if not uvSelection:
        return False
    legacyUnfold(uvSelection, dirType=dirType)
    cmds.select(uvSelection, replace=True)
    return True


"""
LAYOUT
"""


def layoutUvs(selObjs="", resolution=1024, preScaleMode=1, preRotateMode=0, shellSpacing=2, tileMargin=2,
              packBox="0 1 0 1"):
    """

    Works on the selection if selection is ""

    :param selObjs:
    :type selObjs:
    :param resolution:
    :type resolution:
    :param preScaleMode:
    :type preScaleMode:
    :param preRotateMode:
    :type preRotateMode:
    :param shellSpacing:
    :type shellSpacing:
    :param tileMargin:
    :type tileMargin:
    :param packBox:
    :type packBox:
    :return:
    :rtype:
    """
    selObjs, componentMode = selection.selectObjectNoComponent()
    if not selObjs:  # no selection found
        if componentMode:
            cmds.selectMode(component=True)
        return
    if shellSpacing:
        shellSpacing = float(shellSpacing) / float(resolution)  # shellSpacing is in 0-1 and is dependant on resolution
    if tileMargin:
        tileMargin = float(tileMargin) / float(resolution)  # tileMargin is in 0-1 space and is dependant on resolution
    mel.eval('u3dLayout '
             '-resolution {} '
             '-preScaleMode {} '
             '-preRotateMode {} '
             '-shellSpacing {} '
             '-tileMargin {} '
             '-packBox {} '
             '{};'.format(str(resolution),
                          str(preScaleMode),
                          str(preRotateMode),
                          str(shellSpacing),
                          str(tileMargin),
                          packBox,
                          ""))
    if componentMode:  # return to component mode if was changed
        cmds.selectMode(component=True)


"""
NORMALIZE
"""


def normalize(selList, preserveAspectRatio=True):
    """Normalizes UVs into 0-1 space. Preserve aspect ratio does not stretch UVs

    :param selList: Maya selection
    :type selList: list(str)
    :param preserveAspectRatio: True does not stretch UVs, False will fill the uv space
    :type preserveAspectRatio: bool
    """
    cmds.polyNormalizeUV(selList, preserveAspectRatio=preserveAspectRatio)


def normalizeSelection(selList, preserveAspectRatio=True, message=True):
    """Normalizes UVs into 0-1 space based on selection. Preserve aspect ratio does not stretch UVs

    :param selList: Maya selection
    :type selList: list(str)
    :param preserveAspectRatio: True does not stretch UVs, False will fill the uv space
    :type preserveAspectRatio: bool
    :param message: Report the message to the user?
    :type message: bool
    :return success: Operation was successful True or not False
    :rtype success: bool
    """
    selList = selection.selWarning(message=message)
    if not selList:
        return False
    cmds.polyNormalizeUV(selList, preserveAspectRatio=preserveAspectRatio)
    return True


"""
UNITIZE
"""


def unitize(selList):
    """Unitize UV faces, each quad is set to zero to one space

    :param selList: Maya selection
    :type selList: list(str)
    """
    cmds.polyForceUV(selList, unitize=True)


def unitizeSelection(message=True):
    """Unitize UV faces (old normalize), each quad is set to zero to one space

    :param message: Report the message to the user?
    :type message: bool
    :return success: Operation was successful True or not False
    :rtype success: bool
    """
    selList = selection.selWarning(message=message)
    if not selList:
        return False
    unitize(selList)
    return True
