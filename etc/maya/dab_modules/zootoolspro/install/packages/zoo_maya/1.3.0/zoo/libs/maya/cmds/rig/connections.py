import maya.cmds as cmds


def getConnections(node, attributeName):
    return cmds.listConnections('.'.join(node, attributeName))


def createMessageConnection(sourceObj, destinationObj, attrName):
    """creates and connects the sourceObj.message to the destinationObj.attributeName

    :param sourceObj: the source obj name, this will have the .attrName
    :type sourceObj: str
    :param destinationObj: the destination object, this will be the .message connection
    :type destinationObj: str
    :param attrName: the attribute name 'objName.attrName'
    :type attrName: str
    :return attributeName: the name of the attribute obj.attr
    :type attributeName: str
    """
    if not cmds.attributeQuery(attrName, node=sourceObj, exists=True):
        cmds.addAttr(sourceObj, longName=attrName, attributeType='message')
    if not cmds.attributeQuery(attrName, node=destinationObj, exists=True):
        cmds.addAttr(destinationObj, longName=attrName, attributeType='message')
    cmds.connectAttr('.'.join([sourceObj, attrName]), '.'.join([destinationObj, attrName]))
    attributeName = '.'.join([sourceObj, attrName])
    return attributeName


def createMessageConnectionList(sourceNode, attrName, destinationList):
    """creates and connects the sourceObj.attrName to the list of objects with destinationObj.message

    :param sourceObj: the source obj name, this will have the .attrName
    :type sourceObj: str
    :param attrName: the attribute name 'objName.attrName'
    :type attrName: str
    :param destinationList: the list of destination objects, will be connected via .message
    :type destinationList: list
    :return attributeNameList: the list of names of the attributes created eg  [obj.attr, obj2.attr]
    :type attributeNameList: list
    """
    attributeNameList = list()
    for destinationNode in destinationList:
        attributeNameList.append(createMessageConnection(sourceNode, destinationNode, attrName))
    return attributeNameList