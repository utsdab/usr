"""Arnold AOV related
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoovendor.six.moves import range
from zoo.libs.maya.cmds.shaders import shaderutils


def getAllAovNodes():
    return cmds.ls(type="aiAOV")


def checkAovNameExists(name):
    """checks for the existence of all aov nodes .name, if a match is found then True, if not False

    :param name: name of the AOV
    :type name: str
    :return exists: does the name exist on any of the aiAOV nodes?
    :rtype exists: bool
    """
    aovNodeList = getAllAovNodes()
    for aovNode in aovNodeList:
        if cmds.getAttr("{}.name".format(aovNode)) == name:
            return True
    return False


def createAOV(aovName):
    """Creates a custom AOV with the name given keeps it unique by doing checks, the aovName is not the node name

    :param aovName:
    :type aovName:
    :return:
    :rtype:
    """
    if checkAovNameExists(aovName):  # If True it exists
        om2.MGlobal.displayWarning('AOV name `{}` already exists skipping node creation'.format(aovName))
        return False
    import mtoa.aovs as aovs  # importing here as Arnold may not be loaded and can error, difficult to check
    nodeData = aovs.AOVInterface().addAOV(aovName)
    return nodeData


def getAllAOVsAndNames():
    import mtoa.aovs as aovs  # importing here as Arnold may not be loaded and can error, difficult to check
    return aovs.AOVInterface().getAOVNodes(names=True)


def createAiWriteColor(nodeName="aiWriteColor", imageNumber=0, matteColor=(0, 0, 0), message=True):
    """Creates a aiWriteColor Node in Maya, to be used in a RGBA Mattes (AOVs)

    :param imageNumber: The name of the aiWriteColor node in Maya to be created
    :type imageNumber: str
    :param message: If on will return the create message to Maya
    :type message: bool
    :return aiWriteColor: The name of the aiWriteColor Node in Maya that was created
    :type aiWriteColor: str
    """
    aiWriteColor = cmds.shadingNode('aiWriteColor', asTexture=True, name=nodeName)
    cmds.setAttr("{}.input".format(aiWriteColor), matteColor[0], matteColor[1], matteColor[2], type="double3")
    cmds.setAttr("{}.aovName".format(aiWriteColor), "matte{}".format(imageNumber), type="string")
    if message:
        om2.MGlobal.displayInfo('Created Texture Node: `{}`'.format(aiWriteColor))
    return aiWriteColor


def createRGBMatteAOV(nodeList, matteColor, imageNumber):
    """Creates RGB mattes to shading groups associated with an nodeList, usually meshes, shaders or shading groups
    1. Creates the AOV image node if it doesn't already exist
    2. Creates a aiWriteColor node and assigns the attributes correctly to match the AOV name
    3. Connects between the shader and the shading group

    :param nodeList: node list, can be objects, shaders or shading group names
    :type nodeList: list
    :param matteColor: the color of the matte to create
    :type matteColor: tuple
    :param imageNumber: the matte AOV image number
    :type imageNumber: int
    """
    # get the shader info
    warnings = False
    shadingGroupList = shaderutils.getShadingGroupsFromNodes(nodeList)
    aovName = "matte{}".format(imageNumber)
    # --------------------
    # create AOV nodes (the image output)
    # --------------------
    if not checkAovNameExists(aovName):
        # create AOV
        createAOV(aovName)
    # --------------------
    # create aiWriteColor nodes (the image output) and connect
    # --------------------
    for SG in shadingGroupList:
        # create ai write color node
        aiWriteColor = createAiWriteColor(nodeName="aiWriteColor_matte", imageNumber=imageNumber,
                                          matteColor=matteColor, message=False)
        # get shader from shading group
        shaderList = shaderutils.getShadersFromSGList({SG})  # set with only SG in it
        if len(shaderList) == 1:
            cmds.connectAttr("{}.outColor".format(shaderList[0]), "{}.beauty".format(aiWriteColor))  # from shader
        else:
            if not shaderList:
                om2.MGlobal.displayWarning('Created Texture Node: `{}`'.format(aiWriteColor))
            else:
                om2.MGlobal.displayWarning('Connection between a shader and `{}` node skipped, '
                                           'multiple shaders are assigned to this shading group'.format(aiWriteColor))
            warnings = True
        cmds.connectAttr("{}.outColor".format(aiWriteColor), "{}.aiSurfaceShader".format(SG))  # out to shading group
    # --------------------
    # message
    # --------------------
    if warnings:
        om2.MGlobal.displayWarning('Success but with warnings. Matte AOVs created on shading groups {}. '
                                   'See script editor for details.'.format(shadingGroupList))
        return
    om2.MGlobal.displayInfo('Success: Matte AOVs created on shading groups {}.'.format(shadingGroupList))


def createRGBMatteAOVSelected(matteColor, imageNumber):
    """Creates RGB mattes to shading groups associated with a selection, usually meshes, shaders or shading groups
    1. Creates the AOV image node if it doesn't already exist
    2. Creates a aiWriteColor node and assigns the attributes correctly to match the AOV name
    3. Connects between the shader and the shading group

    :param matteColor: the color of the matte to create
    :type matteColor: tuple
    :param imageNumber: the matte AOV image number
    :type imageNumber: int
    """
    selObj = cmds.ls(selection=True)
    if not selObj:
        om2.MGlobal.displayWarning('Nothing selected, please select a mesh, shader or shading group')
    createRGBMatteAOV(selObj, matteColor, imageNumber)


def aiMaskSet():
    """function from
    http://therenderblog.com/creating-id-mask-passes-using-python-based-on-selection-sets/
    Not tested good example of AOV code
    """
    allSets = cmds.ls(set=1)
    aiMasksSets = []

    for set in allSets:
        if set[0:6] == 'aiMask':
            aiMasksSets.append(set)

    if aiMasksSets == []:
        return cmds.warning('No aiMask sets!')

    if cmds.objExists('defaultArnoldDriver') is False:
        import mtoa.core as core
        core.createOptions()

    aiColors = [cmds.shadingNode('aiUserDataColor', asShader=1),
                cmds.shadingNode('aiUserDataColor', asShader=1),
                cmds.shadingNode('aiUserDataColor', asShader=1)]

    cmds.setAttr(aiColors[0] + '.defaultValue', 1, 0, 0, typ='double3')
    cmds.setAttr(aiColors[1] + '.defaultValue', 0, 1, 0, typ='double3')
    cmds.setAttr(aiColors[2] + '.defaultValue', 0, 0, 1, typ='double3')

    for aiSet in range(0, len(aiMasksSets), 3):

        tSwitch = cmds.shadingNode('tripleShadingSwitch', au=1)
        cmds.setAttr(tSwitch + '.default', 0, 0, 0, typ='double3')

        aiUshader = cmds.shadingNode('aiUtility', asShader=1)
        cmds.setAttr(aiUshader + '.shadeMode', 2)
        cmds.connectAttr(tSwitch + '.output', aiUshader + '.color', f=1)

        for n, i in enumerate(aiMasksSets[aiSet:aiSet + 3]):
            aiColor = aiColors[n % len(aiColors)]

            for obj in cmds.listRelatives(cmds.sets(i, q=1), pa=1):
                inpt = cmds.getAttr(tSwitch + '.input', s=1)

                cmds.connectAttr(obj + '.instObjGroups[0]', tSwitch + '.input[' + str(inpt) + '].inShape', f=1)
                cmds.connectAttr(aiColor + '.outColor', tSwitch + '.input[' + str(inpt) + '].inTriple', f=1)
        # AOV'S
        aovListSize = cmds.getAttr('defaultArnoldRenderOptions.aovList', s=1)
        customAOV = cmds.createNode('aiAOV', n='aiAOV_rgbMask_' + str(aiSet // 3 + 1), skipSelect=True)
        cmds.setAttr(customAOV + '.name', 'rgbMask_' + str(aiSet // 3 + 1), type='string')
        cmds.connectAttr(customAOV + '.message', 'defaultArnoldRenderOptions.aovList[' + str(aovListSize) + ']', f=1)
        cmds.connectAttr('defaultArnoldDriver.message', customAOV + '.outputs[0].driver', f=1)
        cmds.connectAttr('defaultArnoldFilter.message', customAOV + '.outputs[0].filter', f=1)
        # connect to default shader
        cmds.connectAttr(aiUshader + '.outColor', customAOV + '.defaultValue', f=1)
