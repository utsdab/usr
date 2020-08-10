import maya.cmds as cmds
from maya.api import OpenMaya as om2

from zoo.libs.maya.cmds.uvs import uvfunctions
from zoo.libs.maya.cmds.objutils import selection

"""
Unfold/Gridify/Straighten Functions
"""


def unfoldGridifyMesh(unfold, dirType, uvShellSelection, recordAutomatic, straightenLoops, faceSelection,
                      straightenAngle, edgeSelection, deleteHistory, directionWarning, mode):
    """The second half of the functions unwrapGridShellSelection() and unwrapTubeSelection() see those for documentation

    Assumes that a uvs have been gridified and proceeds with the unfold
    """
    # The edge can be tested for which way it lies, horizontal or vertical
    if dirType == "automatic":
        dirType = uvfunctions.uvEdgeVerticalOrHorizontal(edgeSelection, mode=mode)
        if not dirType:
            directionWarning = True
    if recordAutomatic:  # Then rotate 90 UV shell degrees
        if mode == "tube" and dirType == "vertical":
            cmds.select(uvShellSelection, replace=True)
            cmds.polyEditUV(relative=True, rotation=True, angle=90.0)
        if mode == "grid" and dirType == "horizontal":
            cmds.select(uvShellSelection, replace=True)
            cmds.polyEditUV(relative=True, rotation=True, angle=90.0)
            dirType = "vertical"  # switch type for later unfold
    # Unfold horizontal or vertical
    if unfold and dirType:  # type could be empty "", if empty ignore and warn user
        if dirType == "regular":
            # do regular UV unwrap both directions
            cmds.select(uvShellSelection, replace=True)
            uvfunctions.regularUnfoldSelection()
        else:
            if recordAutomatic:
                dirType = "vertical"  # then must be vertical as UV have been rotated if not
            uvfunctions.legacyUnfold(uvShellSelection, dirType=dirType)  # type is horizontal or vertical
            if straightenLoops:
                uvfunctions.straightenUv(faceSelection, angle=straightenAngle, dirType="all")  # Straighten all UVs
    # Normalize back to 1-0 space
    uvfunctions.normalize(uvShellSelection, preserveAspectRatio=True)
    # Select original selection
    selection.selectComponentSelectionMode(componentType="edges")
    cmds.select(edgeSelection, replace=True)
    # Delete history
    if deleteHistory:
        currentObject = edgeSelection[0].split(".e")[0]
        cmds.delete(currentObject, constructionHistory=True)
    if directionWarning:
        om2.MGlobal.displayWarning("The unfold direction could not be detected, "
                                   "must have more than two edges selected. Unfold the direction manually.")
        return
    om2.MGlobal.displayInfo("Success: Tube UV'd")


def unwrapGridShellSelection(dirType="automatic", straightenLoops=True, unfold=True, straightenAngle=80,
                             deleteHistory=True, message=True):
    """Gridifies a UV shell, must be a quad grid, then optionally unfolds on a single axis, or other options.

    Works from a single edge loop selection on the interior of the quad grid UV shell.

    Helpful for straightening road like UVs and other windy planes or UV shells.

    Similar to unwrapTubeSelection()

    :param dirType: "automatic", "vertical" or "horizontal" use the legacy unfold, "regular" uses Unfold3d plugin
    :type dirType: bool
    :param straightenLoops: straighten all edge loops, if off the opposite direction may not be straight
    :type straightenLoops: bool
    :param unfold: straighten all edge loops, if off the opposite direction may not be straight
    :type unfold: bool
    :param straightenAngle: The angle that Maya's straighten algorithm uses
    :type straightenAngle: float
    :param deleteHistory: After completing delete the objects history?
    :type deleteHistory: float
    :param message: Report the message to the user?
    :type message: bool
    """
    mode = "grid"
    directionWarning = False
    recordAutomatic = False
    if dirType == "automatic":
        recordAutomatic = True
    # record edge
    selList = cmds.ls(selection=True, long=True)
    edgeSelection = selection.componentSelectionFilterType(selList, "edges")
    if not edgeSelection:
        if message:
            om2.MGlobal.displayWarning("Please make an edge selection along the length of the shell grid")
            return False
    # Get shell
    selection.convertSelection("uvs")
    uvShellSelection = selection.convertSelection("uvShell")
    uvPerimeterSelection = selection.convertSelection("uvShellBorder")
    # Record the verts on the inside of the shell, so they can be sewn after Unitize
    cmds.select(uvPerimeterSelection, replace=True)  # select the uv perimeter and invert it
    cmds.select(uvShellSelection, toggle=True)
    vertInnerShellSelection = selection.convertSelection("vertices")  # record the vert selection as uvs get messed
    # Unitize, each quad goes 0-1 space
    cmds.select(uvShellSelection, replace=True)
    faceSelection = selection.convertSelection("faces")
    uvfunctions.unitize(faceSelection)
    #  Move and sew, after here has been "gridified"
    cmds.select(vertInnerShellSelection, replace=True)  # Must be Verts as UVs can be lost in the move and sew
    uvInnerShellSelection = selection.convertSelection("uvs")
    uvfunctions.moveAndSew(uvInnerShellSelection)
    # do the gridify and unwrap
    unfoldGridifyMesh(unfold, dirType, uvShellSelection, recordAutomatic, straightenLoops, faceSelection,
                      straightenAngle, edgeSelection, deleteHistory, directionWarning, mode)


def unwrapTubeSelection(dirType="automatic", straightenLoops=True, unfold=True, straightenAngle=80.0,
                        deleteHistory=True, message=True):
    """Unwraps a tube with a macro that uses the Maya unitize method of tube unwrapping, sometimes known as "gridify"

    Can optionally unfold with various options, and straighten all edges.

    type:
        "vertical" the unfold is restricted to unfold vertically
        "horizontal" the unfold is restricted to unfold vertically
        "automatic" the unfold is automatically figured out, recommended as it's accurate in most cases
        "regular" unfolds with the new Maya unfold in both directions

    Note: A lot of unavoidable selection in this function short of using other methods such as om2

    :param dirType: "automatic", "vertical" or "horizontal" use the legacy unfold, "regular" uses Unfold3d plugin
    :type dirType: bool
    :param straightenLoops: straighten all edge loops, if off the opposite direction may not be straight
    :type straightenLoops: bool
    :param unfold: straighten all edge loops, if off the opposite direction may not be straight
    :type unfold: bool
    :param straightenAngle: The angle that Maya's straighten algorithm uses
    :type straightenAngle: float
    :param deleteHistory: After completing delete the objects history?
    :type deleteHistory: float
    :param message: Report the message to the user?
    :type message: bool
    """
    mode = "tube"
    directionWarning = False
    recordAutomatic = False
    if dirType == "automatic":
        recordAutomatic = True
    # record edge
    selList = cmds.ls(selection=True, long=True)
    edgeSelection = selection.componentSelectionFilterType(selList, "edges")
    if not edgeSelection:
        if message:
            om2.MGlobal.displayWarning("Please make an edge selection along the seam of the tube")
            return False
    # select edge ring
    selection.convertSelection("edgeRing")  # face selection is best
    # select faces for later
    faceSelection = selection.convertSelection("faces")  # face selection is best for planar project
    # Planar map faces
    uvfunctions.uvProjectionSelection(type="planar", mapDirection="x", message=True)
    # Get edge perimeter to cut
    edgePerimeterSelection = selection.convertSelection("edgePerimeter")  # face selection is best
    # Add the original
    edgePerimeterSelection += edgeSelection
    # UV Cut
    uvfunctions.cutUvs(edgePerimeterSelection)
    # Get the Perimeter UVs so they can be inverted with the shell
    cmds.select(edgeSelection, replace=True)
    uvSelectionEdgeOnly = selection.convertSelection("uvs")
    uvShellSelection = selection.convertSelection("uvShell")
    uvPerimeterSelection = selection.convertSelection("uvShellBorder")
    # Record the verts on the inside of the shell, so they can be sewn after Unitize
    cmds.select(uvPerimeterSelection, replace=True)  # select the uv perimeter and invert it
    cmds.select(uvShellSelection, toggle=True)
    vertInnerShellSelection = selection.convertSelection("vertices")  # record the vert selection as uvs get messed
    # Unitize, each quad goes 0-1 space
    uvfunctions.unitize(faceSelection)
    #  Move and sew, after here has been "gridified"
    if vertInnerShellSelection:  # may not be inner vert selection.
        cmds.select(vertInnerShellSelection, replace=True)  # Must be Verts as UVs can be lost in the move and sew
        uvInnerShellSelection = selection.convertSelection("uvs")
        uvfunctions.moveAndSew(uvInnerShellSelection)
    else:  # most likely is only one edge wide, so no interior verts
        # move and sew everything but the first edge
        shellNumbers = selection.componentNumberList(uvShellSelection)
        edgeNumbers = selection.componentNumberList(uvSelectionEdgeOnly)
        notEdgeUvsNumbers = [x for x in shellNumbers if x not in edgeNumbers]  # takes edgeNumbers from shell
        obj = edgeSelection[0].split(".")[0]
        notEdgeUvs = selection.numberListToComponent(obj, notEdgeUvsNumbers, "uvs")
        cmds.select(notEdgeUvs, replace=True)
        uvfunctions.moveAndSew(notEdgeUvs)
    # Do the gridify and unwrap
    unfoldGridifyMesh(unfold, dirType, uvShellSelection, recordAutomatic, straightenLoops, faceSelection,
                      straightenAngle, edgeSelection, deleteHistory, directionWarning, mode)


"""
Straighten Functions
"""


def edgeLoopVerticalHorizontal(edgeUvSelection):
    """Calculates whether a line of uvs is more horizontal or vertical

    :param edgeUvSelection: a list of UVs in a line
    :type edgeUvSelection: list(str)
    :return directionResult: "horizontal" U is longer "vertical" v is longer, or "equal" is the same length
    :rtype directionResult: str
    """
    # uvCoords below is a list of uv coords in a giant list, take every two values as each UV
    uvCoords = cmds.polyEditUV(edgeUvSelection, query=True, uValue=True)
    uList = uvCoords[::2]  # just the u values
    vList = uvCoords[1::2]  # just the v values
    uSpread = max(uList) - min(uList)
    vSpread = max(vList) - min(vList)
    if uSpread > vSpread:
        return "horizontal"
    elif uSpread == vSpread:
        return "equal"
    else:
        return "vertical"


def walkRecordEdgeLoops(edgeSelection, walkSteps=30):
    """Walks 20 (walkSteps) left and records the edge loops, then walks the other way.

    Returns the loops left as a list of selections and the loops right.

    This function is needed since changing selection while walking will randomly changes its direction,
    avoids feedback/infinite loops
    """
    loopListLeft = list()
    loopListRight = list()
    for i in range(walkSteps):  # walk left
        loopListLeft.append(cmds.pickWalk(direction="left", type="edgeloop"))
    for i in range(walkSteps):  # walk back to start
        cmds.pickWalk(direction="right", type="edgeloop")
    for i in range(walkSteps):  # walk right
        loopListRight.append(cmds.pickWalk(direction="right", type="edgeloop"))
    return loopListLeft, loopListRight


def walkEdgeLoopsStraightenSelection(walkSteps=30, message=True):
    """Will walk (arrow keys) the edges of a gridded uv shell and straighten all edge loops within its borders

    Select an edgeloop and run on a shell that is made up of gridded quads, is fairly stable
    In some circumstances the border edges will not be straightened.

    Is generally faster than Maya's mel "texStraightenUVs" (uvFunctions.straightenUvSelection) and more reliable

    There are a number of issues regarding this function which make it messy:

        1. Pick walk is random in the direction it chooses so must pre cache the loops
        "walkSteps" is the count in each direction, so 30 means max 60 loops are potentially straightened by default.
        2. It's difficult to tell the edge loops that are on the shell border, the whole border is selected instead
        There are a number of checks to test the correct loop on a border but it can fail in some circumstances.
        3. Maya is doing a loads of selection as the converting unfortunately requires it :/

    :param walkSteps: The amount of walk steps to pre cache in each direction, due to random direction issues
    :type walkSteps: int
    :param message: return the message to the user
    :type message: bool
    """
    selList = cmds.ls(selection=True, long=True)
    edgeSelection = selection.componentSelectionFilterType(selList, "edges")
    if not edgeSelection:
        if message:
            om2.MGlobal.displayWarning("Please make an edge selection")
            return
    obj = edgeSelection[0].split(".")[0]  # the name of the maya object
    # ------------------
    # Get all the loops walking left and right, must be done first as unfortunately walk can go random directions
    # ------------------
    loopListLeft, loopListRight = walkRecordEdgeLoops(edgeSelection, walkSteps=walkSteps)
    cmds.select(edgeSelection, replace=True)
    uvEdgeOriginal = selection.convertSelection(type="uvs")
    edgeNumbers = selection.componentNumberList(uvEdgeOriginal)  # list of numbers representing each uv
    edgeLengthUvs = len(edgeNumbers)
    # ------------------
    # Get the direction of the edge, vertical horizontal
    # ------------------
    direction = edgeLoopVerticalHorizontal(uvEdgeOriginal)
    if direction == "horizontal":
        straightenType = "avgV"
    else:  # "vertical" or "equal"
        straightenType = "avgU"
    # ------------------
    # Straighten the first loop
    # ------------------
    uvfunctions.alignUvSelection(straightenType=straightenType)
    # ------------------
    # Get shell and shell border info
    # ------------------
    uvShellBorder = selection.convertSelection(type="uvShellBorder")
    shellBorderNumbers = selection.componentNumberList(uvShellBorder)  # list of numbers representing each uv
    uvShell = selection.convertSelection(type="uvShell")
    shellNumbers = selection.componentNumberList(uvShell)
    # ------------------
    # Loop over the edges and straighten
    # ------------------
    for edgeList in [loopListLeft, loopListRight]:
        previousEdgeList = edgeSelection
        for edgeLoop in edgeList:
            cmds.select(edgeLoop, replace=True)
            uvEdge = selection.convertSelection(type="uvs")
            uvEdgeNumbers = selection.componentNumberList(uvEdge)  # list is like [12, 23, 123, 34]
            # ------------------
            # Get only edges inside the shell as uvs numbers
            # ------------------
            uvEdgeNumbers = set(shellNumbers).intersection(uvEdgeNumbers)
            if not len(uvEdgeNumbers):  # no uvs are in the shell, should be super rare
                break
            if edgeLengthUvs != len(uvEdgeNumbers):  # edge has a different count so could be a shared edge
                # ------------------
                # Then the current edge loop is most likely the edge of the shell.  So try to figure the real edgeloop
                # ------------------
                uvEdgeSelection = selection.numberListToComponent(obj, uvEdgeNumbers, componentType="uvs")
                cmds.select(uvEdgeSelection, replace=True)
                # currentEdgeloop
                edgeLoopNumbers = selection.componentNumberList(edgeLoop)
                # previousEdgePerimeter
                cmds.select(previousEdgeList, replace=True)
                previousEdgePerimeter = selection.convertSelection(type="edgePerimeter")
                previousEdgePerimeterNumbers = selection.componentNumberList(previousEdgePerimeter)
                # previousEdgeRing
                cmds.select(previousEdgeList, replace=True)
                previousEdgeRing = selection.convertSelection(type="edgeRing")
                previousEdgeRingNumbers = selection.componentNumberList(previousEdgeRing)
                # Edges are in all three lists
                matchedEdgeNumbers = set(edgeLoopNumbers).intersection(previousEdgePerimeterNumbers)
                matchedEdgeNumbers = set(previousEdgeRingNumbers).intersection(matchedEdgeNumbers)
                # to uvs
                edgeLoop = selection.numberListToComponent(obj, matchedEdgeNumbers, componentType="edges")
                cmds.select(edgeLoop, replace=True)
                uvEdgeSelection = selection.convertSelection(type="uvs")
                uvEdgeNumbers = selection.componentNumberList(uvEdgeSelection)
                if edgeLengthUvs != len(uvEdgeNumbers):
                    # ------------------
                    # Most likely the shared edge on a tube, test and if is so then ignore, otherwise break
                    # ------------------
                    # get the previous edge as Uvs and grow it
                    cmds.select(previousEdgeList, replace=True)
                    selection.convertSelection(type="uvs")
                    selection.growSelection()
                    uvGrowNumbers = selection.componentNumberList(cmds.ls(selection=True))
                    # return the matches
                    uvEdgeNumbers = set(uvGrowNumbers).intersection(uvEdgeNumbers)
                    if edgeLengthUvs != len(uvEdgeNumbers):  # in most cases shouldn't break here, but can fail
                        # Could possibly find the uvs of all other shells that aren't sharing borders and remove
                        # still may fail in certain cases :/
                        break
                        # uvEdgeNumbers have passed and are correct so straighten
            # ------------------
            # Do the straighten
            # ------------------
            uvEdgeSelection = selection.numberListToComponent(obj, uvEdgeNumbers, componentType="uvs")
            cmds.select(uvEdgeSelection, replace=True)
            uvfunctions.alignUvSelection(straightenType=straightenType)  # do the straighten
            # ------------------
            # Check not a border edge, bail if so, has just been straightened
            # ------------------
            shellBorderCheck = [x for x in uvEdgeNumbers if x not in shellBorderNumbers]
            if not len(shellBorderCheck):  # is a border edge
                break
            previousEdgeList = list(edgeLoop)  # used to compare when mismatch on next loops
    # Finish select original selection
    selection.selectComponentSelectionMode(componentType="edges")
    cmds.select(edgeSelection, replace=True)
    if message:
        om2.MGlobal.displayInfo("Success: Edges Straightened")
