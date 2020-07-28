import maya.cmds as cmds

TEXTURENODES = ["file"]

TYPE = "gType"
FILEPATH = "gType"
LINEAR = "gLinear"

# filenode does have a linear node type, need to look it up
FILENODE = {TYPE: "file",
            FILEPATH: "fileTextureName",
            LINEAR: None}

TEXTURENODEDICT = {"file": FILENODE}


def createFileTexture(name="file", colorSpace="sRGB", imagePath="", ignoreColorSpace=False):
    """creates a file (texture) node with the place2dTextureNode and all connections

    :param name: The name of the file node, the place2dTextureNode is suffixed with "_place3dTex"
    :type name: str
    :param colorSpace: the default color space of the file node "sRGB", "Raw" etc
    :type colorSpace: str
    :param imagePath: the optional image path for the texture, not yet connected
    :type imagePath: str
    :param ignoreColorSpace: Ignores colour space warning, useful for Raw which always complains if using tif ect.
    :type ignoreColorSpace: bool
    :return fileNode: the name of the created file node
    :rtype fileNode: str
    :return place2dTextureNode: the name of the created place2dTextureNode
    :rtype place2dTextureNode: str
    """
    fileNode = cmds.shadingNode("file", name=name, asTexture=True, isColorManaged=True)
    place2dTextureNode = cmds.shadingNode("place2dTexture", name="{}_place3dTex".format(name), asUtility=True)
    # set image path
    if imagePath:
        cmds.setAttr("{}.fileTextureName".format(fileNode), imagePath, type="string")
    # set color space
    cmds.setAttr("{}.colorSpace".format(fileNode), colorSpace, type='string')
    cmds.setAttr("{}.ignoreColorSpaceFileRules".format(fileNode), ignoreColorSpace)
    # make the connections
    cmds.connectAttr('{}.coverage'.format(place2dTextureNode), '{}.coverage'.format(fileNode), force=True)
    cmds.connectAttr('{}.translateFrame'.format(place2dTextureNode), '{}.translateFrame'.format(fileNode), force=True)
    cmds.connectAttr('{}.rotateFrame'.format(place2dTextureNode), '{}.rotateFrame'.format(fileNode), force=True)
    cmds.connectAttr('{}.mirrorU'.format(place2dTextureNode), '{}.mirrorU'.format(fileNode), force=True)
    cmds.connectAttr('{}.mirrorV'.format(place2dTextureNode), '{}.mirrorV'.format(fileNode), force=True)
    cmds.connectAttr('{}.stagger'.format(place2dTextureNode), '{}.stagger'.format(fileNode), force=True)
    cmds.connectAttr('{}.wrapU'.format(place2dTextureNode), '{}.wrapU'.format(fileNode), force=True)
    cmds.connectAttr('{}.wrapV'.format(place2dTextureNode), '{}.wrapV'.format(fileNode), force=True)
    cmds.connectAttr('{}.repeatUV'.format(place2dTextureNode), '{}.repeatUV'.format(fileNode), force=True)
    cmds.connectAttr('{}.offset'.format(place2dTextureNode), '{}.offset'.format(fileNode), force=True)
    cmds.connectAttr('{}.rotateUV'.format(place2dTextureNode), '{}.rotateUV'.format(fileNode), force=True)
    cmds.connectAttr('{}.noiseUV'.format(place2dTextureNode), '{}.noiseUV'.format(fileNode), force=True)
    cmds.connectAttr('{}.vertexUvOne'.format(place2dTextureNode), '{}.vertexUvOne'.format(fileNode), force=True)
    cmds.connectAttr('{}.vertexUvTwo'.format(place2dTextureNode), '{}.vertexUvTwo'.format(fileNode), force=True)
    cmds.connectAttr('{}.vertexUvThree'.format(place2dTextureNode), '{}.vertexUvThree'.format(fileNode), force=True)
    cmds.connectAttr('{}.vertexCameraOne'.format(place2dTextureNode), '{}.vertexCameraOne'.format(fileNode), force=True)
    cmds.connectAttr('{}.outUV'.format(place2dTextureNode), '{}.uv'.format(fileNode), force=True)
    cmds.connectAttr('{}.outUvFilterSize'.format(place2dTextureNode), '{}.uvFilterSize'.format(fileNode), force=True)

    return fileNode, place2dTextureNode


def getTextureFileAttributeName(nodeType):
    """returns the attribute name for setting the file texture path of the given nodeType
    Searches through all supported shaders in a dict and returns the corresponding attribute

    :param nodeType: the type of a supported texture node
    :type nodeType: str
    :return attributeName: the attribute name for the disk file path texture
    :rtype: str
    """
    for node in TEXTURENODES:
        if node == nodeType:
            return TEXTURENODEDICT[node][FILEPATH]


def getTexureNodeType(node):
    """Returns the texture node type, will be None if it's not a recognised texture node

    :param node: a maya node name
    :type node: str
    :return: the type of texture node, or None if it's not a legimate texture node
    :rtype:
    """
    objType = cmds.objectType(node)
    for node in TEXTURENODES:
        if objType == node:  # check if it's a recognised texture node
            return objType


def getTexturePathCheckNode(textureNode):
    """Gets the texture path from a given texture node.  Checks if the node type is a correct texture node
    Supports texture nodes from TEXTURENODEDICT
    If the node is not legitimate return None, note a legitimate return is an empty string

    :param textureNode: maya node name, should be a texture node recognised by the dict TEXTURENODEDICT
    :type textureNode: str
    :return filePath: the full filepath from the texture
    :rtype filePath: str
    """
    textureType = getTexureNodeType(textureNode)
    if textureType:
        attributeName = getTextureFileAttributeName(textureType)
        filePath = cmds.getAttr(".".join([textureNode, attributeName]))
        return filePath


def getFileTextureNameFromAttr(nodeName, attributeName):
    """Finds the texturePath of a texture node from a given attribute ie "file1.color"
    Is compatible with texture nodes in TEXTURENODEDICT
    Checks the node type to be a legitimate texture

    :param nodeName: maya node name, should be a texture node recognised by the dict TEXTURENODEDICT
    :type nodeName: str
    :param attributeName: the attribute name that the node is connected to a texture node
    :type attributeName: str
    :return filePath:
    :rtype filePath:
    """
    connectedNode = cmds.listConnections('.'.join([nodeName, attributeName]), destination=False, source=True)
    if not connectedNode:
        return
    return getTexturePathCheckNode(connectedNode[0])


def setTexturePath(textureNode, nodeType, texturePath):
    """If the textureNode and nodeType is known set the texturePath
    Works on any supported texture

    :param textureNode: the texture node's name
    :type textureNode: str
    :param nodeType: the texture nodes type
    :type nodeType: str
    :param texturePath: the full file path of the texture on disk
    :type texturePath: str
    :return attributeName: the attribute name set
    :rtype attributeName: str
    """
    attributeName = getTextureFileAttributeName(nodeType)
    cmds.setAttr(".".join([textureNode, attributeName]), texturePath, type="string")
    return attributeName


def setTexturePathCheckNode(textureNode, texturePath):
    """Smart function that checks the node and assigns a texture file path to the node.
    Returns None if no legit nodes found

    :param textureNode: the texture node's name
    :type textureNode: str
    :param texturePath: the full file path of the texture on disk
    :type texturePath: str
    :return fileTextureName: the attribute name set, None if not found
    :rtype fileTextureName: str
    """
    nodeType = getTexureNodeType(textureNode)
    attributeName = getTextureFileAttributeName(nodeType)
    if not attributeName:
        return None
    cmds.setAttr(".".join([textureNode, attributeName]), texturePath, type="string")
    return textureNode


def setFileTextureFromAttr(nodeName, attributeName, texturePath):
    """From a given current node and current node attribute ie plasticShader.color, find a connected texture node
    and set a new texture file path on disk.

    :param nodeName: the name of the node to search from, eg "plasticShader"
    :type nodeName: str
    :param attributeName: the attribute name to search from eg "color"
    :type attributeName: str
    :return fileTextureName:  If found the connected texture node name, None if no node was found
    :rtype fileTextureName: str
    """
    connectedNode = cmds.listConnections('.'.join([nodeName, attributeName]), destination=False, source=True)
    if not connectedNode:
        return
    return setTexturePathCheckNode(connectedNode[0], texturePath)


def buildConnectTextureNodeAttribute(nodeName, nodeAttribute, textureNodeName="fileText", nodeType="file",
                                     texturePath=None, colorSpace="sRGB", asAlpha=False):
    """Builds a texture node and connects from the given nodeName and nodeAttribute eg
    plasticShader.color > new created texture node
    Can assign a texture path
    Node types can be any supported nodes from TEXTURENODES list
    Texture can be multiple channels (color) asAlpha=False or single channel asAlpha=True (scalar)

    :param nodeName: current maya node's name, this node will connect to the new texture node
    :type nodeName: str
    :param nodeAttribute: attribute of the current maya node to connect to the new texture
    :type nodeAttribute: str
    :param textureNodeName: the name of the texture node to be created
    :type textureNodeName: str
    :param nodeType: the type of node to be created, eg "file"
    :type nodeType: str
    :param texturePath: the disk texture path of the texture to be assigned, None if none.
    :type texturePath: str
    :param colorSpace: the color space of the texture "sRGB" linear etc.
    :type colorSpace: str
    :param asAlpha: if True then connect as a single channel not as color (multiple channels)
    :type asAlpha: bool
    :return createNodes: the created node list
    :rtype: list
    """
    if nodeType == "file":
        fileNode, place2dTextureNode = createFileTexture(name=textureNodeName, colorSpace=colorSpace,
                                                         imagePath=texturePath)
        if not asAlpha:  # connectTexture to color
            cmds.connectAttr('{}.outColor'.format(fileNode), '.'.join([nodeName, nodeAttribute]), force=True)
        if asAlpha:  # connectTexture out alpha
            cmds.connectAttr('{}.outAlpha'.format(fileNode), '.'.join([nodeName, nodeAttribute]), force=True)
        createdNodes = [fileNode, place2dTextureNode]
        return createdNodes


def setOrCreateFileTexturePath(nodeName, attributeName, texturePath, textureNodeName="fileText", nodeType="file",
                               colorSpace="sRGB", asAlpha=False):
    """Sets the texture file path from a given node.attribute, usually a shader
    eg. shader plasticShader.color
    This function finds the connected texture node, if it's supported sets the texture
    If no texture node is found. The function creates a texture node of the given type and sets the texture path
    returns a warning (if True could not set the connected node) and created nodes if nodes were created
    Node types can be any supported nodes from TEXTURENODES list
    Texture can be multiple channels (color) asAlpha=False or single channel asAlpha=True (scalar)

    :param nodeName: current maya node's name, this node will connect to the new texture node
    :type nodeName: str
    :param attributeName: attribute of the current maya node to connect to the new texture
    :type attributeName: str
    :param texturePath: the disk texture path of the texture to be assigned, None if none.
    :type texturePath: str
    :param textureNodeName: the name of the texture node to be created
    :type textureNodeName: str
    :param nodeType: If a texture needs to be created this is the type of texture node to create
    :type nodeType: str
    :param colorSpace: the color space of the texture "sRGB" "Raw" etc.
    :type colorSpace: str
    :param asAlpha: if True then connect as a single channel not as color (multiple channels)
    :type asAlpha: bool
    :return warning: a warning, if True something is connected but it's not a fileTexture
    :rtype warning: bool
    :return createdNodes: the created nodes as a list if any were created
    :rtype createdNodes: list
    """
    warning = False
    # check if already connected
    connected = cmds.listConnections('.'.join([nodeName, attributeName]), destination=False, source=True)
    if connected:
        fileTextureName = setFileTextureFromAttr(nodeName, attributeName, texturePath)
        if fileTextureName is None:
            warning = True  # warn the user that the found node is incompatible/not supported
        else:
            cmds.select(fileTextureName, replace=True)
        createdNodes = None
        return warning, createdNodes

    createdNodes = buildConnectTextureNodeAttribute(nodeName, attributeName, texturePath=texturePath,
                                                    textureNodeName=textureNodeName, nodeType=nodeType,
                                                    colorSpace=colorSpace, asAlpha=asAlpha)
    cmds.select(createdNodes[0], replace=True)
    return warning, createdNodes




