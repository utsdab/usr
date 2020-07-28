"""Renderman AOV related


TODO:  Add the following code
https://renderman.pixar.com/answers/questions/14093/create-in-code-rman-attrs-and-aovs-in-v23-rfm2.html?childToView=14837#answer-14837

import rfm2
pdict = {'name': 'MatteID1', 'label': 'MatteID1',
         'type': 'color', 'default': (1, 0, 0),
         'connectable': False}
rfm2.ui.user_attrs.user_attrs_add('rman_userAttrs', ['nurbsSphere1'], pdict)
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.mel as mel

from zoo.libs.maya.cmds.shaders import shaderutils


def createPxrMatteID(textureName="PxrMatteID", matteNumber=0, message=True):
    """Creates a PxrMatteID Texture in Maya, these are used for RGBA Mattes (AOVs)

    :param textureName: The name of the pxrMatteID node in Maya to be created
    :type shaderName: str
    :param message: If on will return the create message to Maya
    :type message: bool
    :return pxrMatteID: The name of the pxrMatteID Node in Maya that was created
    :type pxrMatteID: str (possibly unicode)
    """
    pxrMatteID = cmds.shadingNode('PxrMatteID', asTexture=True, name=textureName)
    cmds.setAttr(("{}.inputAOV").format(pxrMatteID), matteNumber)
    if message:
        om.MGlobal.displayInfo('Created Texture: `{}`'.format(pxrMatteID))
    return pxrMatteID


def rmanCreateRenderSettingsMatteAOV(matteNumber):
    """Creates a Renderman Matte AOV in nodes, Render Settings will need to be reopened for settings to apply

    If node setup already exists should bail

    Annoying function possibly and easier way with rfm2 api

    :param matteNumber: The number of the image to create starts at 0
    :type matteNumber: int
    """
    displayName = "_MatteID{}".format(str(matteNumber))
    displayChannelName = "MatteID{}".format(str(matteNumber))
    d_pngName = "d_png{}".format(str(matteNumber))
    # Delete for rebuild
    if cmds.objExists(displayName):  # bail should already exist
        return
    # Create
    displayName = cmds.createNode("rmanDisplay", name=displayName, skipSelect=True)
    displayChannelName = cmds.createNode("rmanDisplayChannel", name=displayChannelName, skipSelect=True)
    d_pngName = cmds.createNode("d_png", name=d_pngName, skipSelect=True)
    # Connect
    cmds.connectAttr("{}.message".format(displayChannelName), "{}.displayChannels[0]".format(displayName))
    cmds.connectAttr("{}.message".format(displayName), "rmanGlobals.displays[{}]".format(str(matteNumber + 1)))
    cmds.connectAttr("{}.message".format(d_pngName), "{}.displayType".format(displayName))
    # set attribute
    cmds.setAttr("{}.channelSource".format(displayChannelName), "MatteID{}".format(str(matteNumber)), type="string")


def rmanAddAttrMatte(rendermanShader, matteNumber=0, matteColor=(1, 0, 0)):
    """Creates an attribute for pxrMattes this defines the matte color on a shader

    :param pxrSurfaceShader:The Shader name that the attr is added to
    :param matteNumber:The image number of the matte, starts at 0
    :param matteColor:the color of the matte as a rgb tuple (1, 0, 0) is red
    :return:
    """
    try:  # try in version 22 and above, API has changed
        import rfm2  # if passes then is version 22 or 23
        om.MGlobal.displayInfo("Note: Ignoring 'rmanAddAttr' error, building for Renderman 22 and above")
        # find all geo with
        # mel.eval('if (`currentRenderer` != "renderman") setCurrentRenderer("renderman");')  # set Renderman as default
        return 23
    except:  # only in Renderman 21 and below. Renderman's old mel api
        mel.eval(
            'rmanAddAttr {} `rmanGetAttrName "rman__riattr__user_MatteID{}"` "{} {} {}";'.format(rendermanShader,
                                                                                                 matteNumber,
                                                                                                 matteColor[0],
                                                                                                 matteColor[1],
                                                                                                 matteColor[2]))
        return 20


def getColorStringFromTuple(matteColor):
    """changes a tuple (0, 1, 1) into a string "green"

    :param matteColor: color as a tuple (0, 0, 1) is blue
    :type matteColor: tuple
    :return colorString: color as a string
    :rtype colorString: str
    """
    if matteColor == (1, 0, 0):
        return "Red"
    elif matteColor == (0, 1, 0):
        return "Green"
    elif matteColor == (0, 0, 1):
        return "Blue"
    else:
        return str(matteColor)


def connectPxrMatteID(rendermanShader, pxrMatteID=None, matteNumber=0, matteColor=(1, 0, 0)):
    """When a Shader is selected will create and connect the PxrMatteID for RGB Mattes (AOVs)
    Can pass in specific node names

    need to check if object matte is already connected
    """
    if not pxrMatteID:  # then create the node
        pxrMatteID = createPxrMatteID(textureName="{}_PxrMatteID".format(rendermanShader), matteNumber=matteNumber)
    # connect the pxrMatteID to the shader
    cmds.connectAttr("{}.resultAOV".format(pxrMatteID), "{}.utilityPattern[0]".format(rendermanShader))
    # add custom rman__riattr__user_MatteID attribute to shader
    supportVersion = rmanAddAttrMatte(rendermanShader, matteNumber=matteNumber, matteColor=matteColor)
    # add the Render settings AOV
    if supportVersion == 23:  # then can build the nodes for the Render Settings
        rmanCreateRenderSettingsMatteAOV(matteNumber=matteNumber)


def connectPxrMatteIDSelected(matteNumber, matteColor, pxrMatteID=None):
    """from selected shader/s or object transforms assign the matte color to be the given color by nodes
    Filters v21 Renderman Shaders only
    *Still needs to be able to reassign colors and image number if node already exists

    :param matteNumber: This is the number of the image starting at 0, mattes can be across more than one image
    :type matteNumber: int
    :param matteColor: The color of the matte as rgb tuple (1, 0, 0) is red
    :type matteColor: tuple
    :param pxrMatteID: this is the name of the incoming node assigned to the shader, it will be created if None
    :type pxrMatteID: str
    """
    selection = set(cmds.ls(sl=True, l=True))
    dagShaders = set(shaderutils.getShadersObjList(list(selection)))
    selection = list(selection.union(dagShaders))  # combine the sets so so items are unique, don't want two shaders
    rendermanShaderList = cmds.ls(selection, type=("PxrSurface", "PxrLayerSurface"))  # filter type of shader/selection
    if not rendermanShaderList:
        oldShaders = cmds.ls(selection, type=("PxrDisney", "PxrLMDiffuse", "PxrLMGlass", "PxrLMMetal", "PxrLMPlastic",
                                              "PxrLMSubsurface", "PxrLightEmission"))
        if oldShaders:
            om.MGlobal.displayWarning('Old Renderman shaders pre v21 are not supported. Please upgrade to PxrSurface '
                                      'or PxrLayerSurface')
            return
        om.MGlobal.displayWarning('No Renderman Shader/s or Object/s Selected. Please select a shader or related'
                                  ' object.')
        return
    for rendermanShader in rendermanShaderList:
        connectPxrMatteID(rendermanShader, pxrMatteID=pxrMatteID, matteNumber=matteNumber, matteColor=matteColor)
    if selection:  # re select the original selection
        cmds.select(selection, replace=1)
    colorString = getColorStringFromTuple(matteColor)
    om.MGlobal.displayInfo('Success:  Shader/s Have Been Matte Colored "{}".  '
                           'Extra Setup is required in Renderman, please see the help "?" icon link.'.format(colorString))
