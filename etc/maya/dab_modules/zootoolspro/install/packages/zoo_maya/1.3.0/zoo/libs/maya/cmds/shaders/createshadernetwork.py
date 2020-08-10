import maya.cmds as cmds
import maya.api.OpenMaya as om2


def createSGOnShader(shader):
    """Creates a shading group for the given shader and connects it, usually needed if one doesn't exist

    :param shader: the shader name
    :type shader: str
    :return shadingGroup: the shading group name
    :rtype shadingGroup: str
    """
    shadingGroupName = '{}SG'.format(shader)
    shadingGroup = cmds.sets(name=shadingGroupName, renderable=True, noSurfaceShader=True, empty=True)
    cmds.connectAttr('{}.outColor'.format(shader), '{}.surfaceShader'.format(shadingGroup))
    return shadingGroup


def createRampShaderFacingRatio(shaderName="rampSamplerInfo_shad", report=False):
    """Creates an ambient ramp shader useful for facing ratio tasks"

    :param shaderName:name of the shader node
    :type shaderName:str
    :param report:display report message?
    :type report:bool
    :return rampShader:name of the ramp shader
    :type rampShader:str
    """
    rampShader = cmds.shadingNode('rampShader', asShader=True, name=shaderName)
    cmds.setAttr(".".join([rampShader, 'specularity']), 0)
    cmds.setAttr(".".join([rampShader, 'ambientColor']), 1, 1, 1, type='double3')
    cmds.setAttr(".".join([rampShader, 'diffuse']), 0)
    if report:
        om2.MGlobal.displayInfo("Success: Curve created with two keys '{}'".format(rampShader))
    return rampShader


def createAnimCurveUL2Keys(curveName="animUL_crv", value1=0, float1=0, value2=1, float2=1, report=False, weighted=1):
    """Creates an (UL unit length) anim curve useful in shader creation, also can be used in rigs and for various tasks

    :param curveName:name of the curve
    :type curveName:str
    :param value1:first key value
    :type value1:float
    :param float1:first key float value (sometimes time value)
    :type float1:float
    :param value2:second key value
    :type value2:float
    :param float2:second key float value (sometimes time value)
    :type float2:float
    :param report:display report message?
    :type report:bool
    :param weighted: Is the curve weighted (0) or non weighted tangents (1)
    :type weighted: bool
    :return curveNode:name of the returned animCurve Node
    :type curveNode:str
    """
    curveNode = cmds.shadingNode("animCurveUL", asUtility=True, name=curveName)
    cmds.keyTangent(curveNode, e=1, wt=weighted)
    cmds.setKeyframe(curveNode, v=value1, f=float1, breakdown=0)
    cmds.setKeyframe(curveNode, v=value2, f=float2, breakdown=0)
    if report:
        om2.MGlobal.displayInfo("Success: Curve created with two keys '{}'".format(curveNode))
    return curveNode


def prepareColorOutput(textureNode):
    """Returns the output attribute of the texture node, different renderers have different out attr
     Should also change this to find outcolor as most Maya nodes have an outcolor not only "file"

    :param textureNode:
    :type textureNode:
    :return:
    :rtype:
    """
    nodeTypeTexture = cmds.nodeType(textureNode)
    if nodeTypeTexture == "file":
        return "outColor"
    elif nodeTypeTexture == "PxrTexture":
        return "resultRGB"
    return ""


def createMultiplyDivideColor():
    """Creates the node network rgbToHsv > multiplyDivide > hsvToRgb
    Useful for hue sat value adjustment when the renderer can't handle Maya's newer nodes.

    :return multiplyNode: the multiply node
    :rtype multiplyNode: str
    :return hsvToRgb: the hsvToRgb node
    :rtype hsvToRgb: str
    :return rgbToHsv: the rgbToHsv node
    :rtype rgbToHsv: str
    """
    multiplyNode = cmds.shadingNode('multiplyDivide', asUtility=True, n='multiHsvColor_texture')
    hsvToRgb = cmds.shadingNode('hsvToRgb', asUtility=True, n='hsvToRgb_texture')
    rgbToHsv = cmds.shadingNode('rgbToHsv', asUtility=True, n='rgbToHsv_texture')
    # connect
    cmds.connectAttr("{}.outHsv".format(rgbToHsv), "{}.input1".format(multiplyNode))
    cmds.connectAttr("{}.output".format(multiplyNode), "{}.inHsv".format(hsvToRgb))
    return multiplyNode, hsvToRgb, rgbToHsv


def connectMultiplyDivideColor(textureNode):
    """Connect the node setup (rgbToHsv > multiplyDivide > hsvToRgb) to the given texture's out
    also maintain the current conenctions input to (usually the shader) if already connected

    :param textureNode: Then texture nodes name, can be multiple node types see prepareColorOutput()
    :type textureNode: str
    :return successState: True if the operation was successful
    :rtype successState: bool
    """
    outAttr = prepareColorOutput(textureNode)
    if not outAttr:
        om2.MGlobal.displayWarning("This node is not supported by the color multiply script")
        return False
    try:  # get opposite attr
        oppositeAttrList = cmds.listConnections(".".join([textureNode, outAttr]), plugs=True)
    except:
        oppositeAttrList = None
    multiplyNode, hsvToRgb, rgbToHsv = createMultiplyDivideColor()   #build the multiply network
    cmds.connectAttr(".".join([textureNode, outAttr]), "{}.inRgb".format(rgbToHsv))  # make the connections
    if oppositeAttrList:
        for oppositeAttr in oppositeAttrList:
            # disconnect first
            cmds.disconnectAttr(".".join([textureNode, outAttr]), oppositeAttr)
            cmds.connectAttr(".".join([hsvToRgb, "outRgb"]), oppositeAttr)
    return True


def connectMultiplyDivideColorSelected():
    """Connect the node setup (rgbToHsv > multiplyDivide > hsvToRgb) to the given texture's out
    Texture node should be selected by the user
    """
    nodeList = cmds.ls(selection=True)
    if not nodeList:
        om2.MGlobal.displayWarning("Please Select a Texture Node and Run")
        return
    result = connectMultiplyDivideColor(nodeList[0])
    if result:
        om2.MGlobal.displayInfo("Success: Multiply Color Network Created")


def createLambertMaterial(shaderName="shader_VP2", specWeight=0.0, message=True, rgbColor=(.5, .5, .5)):
    """Creates a lambert Shader In Maya

    :param shaderName:The name of the RedshiftMaterial shader in Maya to be created
    :type shaderName:str
    :param specOff: If True the specular weight is set to 0 (off)
    :type specOff: bool
    :param message:If on will return the create message to Maya
    :type message:bool
    :return:The name of the redshift material shader in Maya that was created
    :type message:str (possibly unicode)
    """
    lambertShaderName = cmds.shadingNode('lambert', asShader=True, name=shaderName)
    if message:
        om2.MGlobal.displayInfo('Created Shader: `{}`'.format(lambertShaderName))
    # colorSrgbInt = colors.convertColorSrgbToLinear(colorSrgbInt)  # linearize colors
    # diffuse
    cmds.setAttr("{}.color".format(lambertShaderName), rgbColor[0], rgbColor[1], rgbColor[2], type="double3")
    return lambertShaderName
