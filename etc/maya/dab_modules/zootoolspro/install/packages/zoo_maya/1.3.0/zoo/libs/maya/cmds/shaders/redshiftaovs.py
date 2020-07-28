import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.mel as mel

from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.shaders import shaderutils

PUZZLEDEFAULT = "rsAov_PuzzleMatte"


def openRenderSettingsTabAOV():
    """Opens the render settings at the AOV tab

    """
    mel.eval('unifiedRenderGlobalsWindow')
    mel.eval('setCurrentTabInRenderGlobalsWindow(\"AOV\")')
    mel.eval('fillSelectedTabForCurrentRenderer')


def createAOV(type="Puzzle Matte", nodeName=""):
    """Creates a redshift AOV, possible types...

    "Depth",
    "Puzzle Matte",
    "Motion Vectors",
    "ObjectID",
    "Diffuse Lighting",
    "Diffuse Lighting Raw",
    "Diffuse Filter",
    "Specular Lighting",
    "Sub Surface Scatter",
    "Sub Surface Scatter Raw",
    "Reflections",
    "Reflections Raw",
    "Reflections Filter",
    "Refractions",
    "Refractions Raw",
    "Refractions Filter",
    "Emission",
    "Global Illumination",
    "Global Illumination Raw",
    "Caustics",
    "Caustics Raw",
    "Ambient Occlusion",
    "Shadows",
    "Normals",
    "Bump Normals",
    "Matte",
    "Volume Lighting",
    "Volume Fog Tint",
    "Volume Fog Emission",
    "Translucency Lighting Raw",
    "Translucency Filter",
    "Translucency GI Raw",
    "Total Diffuse Lighting Raw",
    "Total Translucency Lighting Raw",
    "Object-Space Positions",
    "Object-Space Bump Normals",
    "Background"

    :param type: the style of AOV to be created
    :type type: str
    :param nodeName: the name of the node to be created, if empty will create with default name
    :type nodeName: str
    :return nodeName: the name of the node created, note! this is not checked, may not be unique until the code is fixed
    :rtype nodeName: str
    """
    if nodeName:
        mel.eval('rsCreateAov - type"{}" - name "{}";'.format(type, nodeName))
    else:
        mel.eval('rsCreateAov - type"{}";'.format(type))
    # Refresh Render Setting AOV GUI if open
    mel.eval('if(`frameLayout -exists "rsLayout_AovAOVsFrame"`) redshiftUpdateActiveAovList;')
    return nodeName


def createAOVPuzzleMatte(imageNumber, nodeName="rsAov_PuzzleMatte", message=True):
    """Creates a puzzleMatte AOV (rgb Matte) node only and adds it to the list in the AOV tab under Render Settings
    checks for unique names as not sure how return the node name in redshift .mel

    :param nodeName: the name of the node to be created, if empty will create with default name
    :type nodeName: str
    :param message: Report the message to the user
    :type message: bool
    :return nodeName: the name of the node created
    :rtype nodeName: str
    :return matteNodeNumber: the number of the matte node starts at 0
    :rtype matteNodeNumber: int
    """
    if cmds.objExists(nodeName):
        nodeName = namehandling.nonUniqueNameNumber(nodeName)
    nodeName = createAOV(type="Puzzle Matte", nodeName=nodeName)
    if message:
        om2.MGlobal.displayInfo('AOV Created `{}`'.format(nodeName))
    # set the attributes in order depending on the name
    cmds.setAttr("{}.redId".format(nodeName), (imageNumber * 3 + 1))
    cmds.setAttr("{}.greenId".format(nodeName), (imageNumber * 3 + 2))
    cmds.setAttr("{}.blueId".format(nodeName), (imageNumber * 3 + 3))
    return nodeName


def checkPuzzleMatteColorExists(colorStr, imageNumber):
    """Checks to see if the puzzle mate number already exists
    Does this by cycling through all nodes named "*rsAov_PuzzleMatte*"
    To see if the appropriate value and number already exists

    :param colorStr: "Red", "Green", "Blue" or "Black"
    :type colorStr: str
    :param imageNumber: the image number starts at 0
    :type imageNumber: int
    :return returnState: 1 means found, 2 means color is not R G or B, 3 means it wasn't found, 4 the matte is black
    :rtype returnState: int
    """
    startNumber = imageNumber * 3
    # check "rsAov_PuzzleMatte" in the scene to see if the current imageNumber Exists
    puzzleMatteNodes = cmds.ls("*{}*".format(PUZZLEDEFAULT))
    if colorStr == "Red":
        for matteNode in puzzleMatteNodes:
            if cmds.getAttr("{}.redId".format(matteNode)) == startNumber + 1:  # found
                return 1
    elif colorStr == "Green":  # this is green
        for matteNode in puzzleMatteNodes:
            if cmds.getAttr("{}.greenId".format(matteNode)) == startNumber + 2:  # found
                return 1
    elif colorStr == "Blue":  # this is blue
        for matteNode in puzzleMatteNodes:
            if cmds.getAttr("{}.blueId".format(matteNode)) == startNumber + 3:  # found
                return 1
    elif colorStr == "Black":  # this is black
        return 4
    else:
        return 2  # this means the color is not legit red green or blue
    # the number wasn't found which most likely means the node hasn't been created yet
    return 3


def setMatteSG(shaderGroup, matteColor, imageNumber):
    """Sets a matte in Redshift, assumes all nodes are called something like
    "rsAov_PuzzleMatte" so can break, this is the default in Redshift
    assumes names like "rsAov_PuzzleMatte", "rsAov_PuzzleMatte001", "rsAov_PuzzleMatte002"

    :param shaderGroup: the name of the shading group
    :type shaderGroup: str
    :param matteColor: color in srgb (0,0,1)
    :type matteColor: tuple
    :param imageNumber: the image number starts at 0
    :type imageNumber: int
    """
    # change the shader node
    matteValue = imageNumber * 3
    if matteColor[0] > 0.99:  # red
        colorStr = "Red"
        matteValue += 1
    elif matteColor[1] > 0.99:  # green
        colorStr = "Green"
        matteValue += 2
    elif matteColor[2] > 0.99:  # blue
        colorStr = "Blue"
        matteValue += 3
    elif matteColor[0] < 0.01 and matteColor[1] < 0.01 and matteColor[2] < 0.01:  # black
        colorStr = "Black"
        matteValue = 0
    else:
        om2.MGlobal.displayError('The Color is not pure Red, Green, Blue or Black which Redshift requires')
        return
    findMatte = checkPuzzleMatteColorExists(colorStr, imageNumber)  # 1 found, 2 not pure, 3 not found, 4 matte black
    if findMatte == 2:
        om2.MGlobal.displayError('The Color is not pure Red, Green or Blue or Black which Redshift requires')
    elif findMatte == 3:  # wasn't found so should build the matte Image node (rsAov_PuzzleMatte)
        # figure what the matte should be and create it
        createAOVPuzzleMatte(imageNumber, nodeName="rsAov_PuzzleMatte", message=True)
    cmds.setAttr("{}.rsMaterialId".format(shaderGroup), matteValue)
    om2.MGlobal.displayInfo('Success: Matte Color on Shading Group `{}` set to `{}`'.format(shaderGroup, colorStr))


def setMatteSelected(matteColor, imageNumber):
    """

    :param matteColor:
    :type matteColor:
    :param imageNumber: the image number starts at 0
    :type imageNumber: int
    :return:
    :rtype:
    """
    shadingGroupList = shaderutils.getShadingGroupsFromSelectedNodes()
    if not shadingGroupList:
        om2.MGlobal.displayWarning("No objects or shaders are selected with shading groups, please select again")
        return
    for SG in shadingGroupList:  # do the matte assigne
        setMatteSG(SG, matteColor, imageNumber)
    if len(shadingGroupList) > 1:
        om2.MGlobal.displayWarning('Success with Warning:  Multiple Shading Groups were set to image number `{}`, '
                                   'check script editor for more details'.format(imageNumber))
    return


