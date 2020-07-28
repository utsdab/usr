import re

import maya.mel as mel

import maya.cmds as cmds
from maya.api import OpenMaya as om2
from zoo.libs.maya.cmds.objutils import filtertypes

"""
MESSAGE
"""


def selWarning(warningTxt="Please make a selection", message=True, long=False):
    """Basic selection function with warning if nothing is selected"""
    selList = cmds.ls(selection=True, long=long)
    if not selList:
        if message:
            om2.MGlobal.displayWarning(warningTxt)
        return list()
    return selList


"""
FILTERS
"""


def convertGeometryFaces(nodeList, individualFaces=False):
    """From a list of node string names, return only those objects that are polys, nurbs or polyfaces

    :param nodeList: list of Maya node names
    :type nodeList: list(str)
    :param individualFaces: If True then break up the faces so that each face is an individual list item
    :type individualFaces: bool
    :return geoFaceList: list of Maya poly, nurbs and polyfaces list
    :rtype geoFaceList: list(str)
    """
    faceList = list()
    meshList = filtertypes.filterTypeReturnTransforms(nodeList, shapeType="mesh")
    nurbsList = filtertypes.filterTypeReturnTransforms(nodeList, shapeType="nurbsSurface")
    for node in nodeList:
        if ".f" in node:
            faceList.append(node)
    if individualFaces and faceList:
        # Face list will be converted into individual faces, can be lots of items in face selection
        faceList = componentFullList(faceList)
    geoFaceList = nurbsList + meshList + faceList
    return geoFaceList


"""
COMPONENT SELECTION
"""


def selectObjectNoComponent(message=True):
    """If in component mode with nothing selected, return to the object mode and return those objects instead.

    Returns the potentially updated selection, and if the user is in component mode or not

    Used in a lot of UV functions when nothing is selected you still want to operate on the current object.

    :param message: Return the messages to the user?
    :type message: bool
    :return selObjs: maya selection, could be components or objects.
    :rtype selObjs: list(str)
    :return componentMode: True if in component mode eg vertex or edge mode, False if in object mode.
    :rtype componentMode: bool
    """
    componentMode = False
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if not cmds.selectMode(query=True, component=True):  # check if in component mode
            if message:
                om2.MGlobal.displayWarning("Please select an object or its components")
            return selObjs, componentMode  # [], False
        # Is in component mode
        componentMode = True
        mel.eval('SelectTool')  # some tools lock the user from returning to object mode
        cmds.selectMode(object=True)
        selObjs = cmds.ls(selection=True)
        if not selObjs:
            if message:
                om2.MGlobal.displayWarning("Please select an object or its components")
    return selObjs, componentMode


def componentFullList(componentSelection):
    """Converts a component selection list into a full list

    Example:
        ["pSphere4.e[22:24]"]
        becomes
        ["pSphere4.e[22]", "pSphere4.e[23]", "pSphere4.e[24]"]

    :param componentSelection: A selection of Maya components eg ["pSphere4.e[1438:1439]", "pSphere4.e[23:25]"]
    :type componentSelection: list(str)
    """
    return cmds.ls(componentSelection, flatten=True)  # remove ":" entries


def componentNumberList(componentSelection):
    """Converts a component selection list into number list

    Assumes only components are from a single object

    Example:
        ["pSphere4.e[22:24]"]
        becomes
        [22, 23, 24]

    :param componentSelection: A selection of Maya components eg ["pSphere4.e[1438:1439]", "pSphere4.e[23:25]"]
    :type componentSelection: list(str)
    """
    componentFullList = list()
    flattenedList = cmds.ls(componentSelection, flatten=True)
    for component in flattenedList:
        m = re.search(r"(?<=\[).+?(?=\])", component)
        componentValue = m.group(0)  # will be something like "23:25".  Note will fail if no square brackets [23:25]
        componentFullList.append(int(componentValue))
    return componentFullList


def countComponentsInSelection(componentSelection):
    """Counts the amount of components in a selection, should be filtered to only one component type ie only edges

    :param componentSelection: A selection of Maya components eg ["pSphere4.e[1438:1439]", "pSphere4.e[23:25]"]
    :type componentSelection: list(str)
    :return componentCount: The exact numbers of components in the selection
    :rtype componentCount: int
    """
    return len(cmds.ls(componentSelection, flatten=True))


def numberListToComponent(obj, numberList, componentType="uvs"):
    """Takes a number list and makes it into a component selection

    Example:
        "pSphere", [22, 23, 24], "edges"
        becomes
        ["pSphere.e[22]", "pSphere.e[23]", "pSphere.e[24]"]

    :param obj: A maya object
    :type obj: str
    :param numberList: a list of numbers that represent component numbers
    :type numberList: list(int)
    :param componentType: the type of component "uvs", "edges", "faces", "vtx"
    :type componentType:
    :return componentSelection: The component list now created
    :rtype componentSelection: list(str)
    """
    componentSelection = list()
    if componentType == "uvs":
        type = "map"
    elif componentType == "edges":
        type = "e"
    elif componentType == "faces":
        type = "f"
    else:  # "vertices"
        type = "vtx"
    for n in numberList:
        componentSelection.append("{}.{}[{}]".format(obj, type, n))
    return componentSelection


def componentsToObjectList(componentSelection):
    """From a list of components return only the objects in the selection. Handles long or short names and namespaces

    Example:
        ["pSphere.e[22]", "pSphere.e[23]", "pCube.e[24]"]
        becomes
        ["pSphere", "pCube"]

    :param componentSelection: A list of components or objects or both
    :type componentSelection: list(str)
    :return objectList: A list of objects now filtered
    :rtype objectList: list(str)
    """
    objList = list()
    for sel in componentSelection:
        objList.append(sel.split(".")[0])
    return list(set(objList))  # Remove duplicates


def componentSelectionFilterType(selectedComponents, selectType):
    """Pass in a selection and will return the single selection list specified by selectType:

        selectType can be "faces", "vertices", or "edges"

    :param selectedComponents: Regular Maya selection list
    :type selectedComponents: list(str)
    :param selectType: The selection to return can be "faces", "vertices", or "edges"
    :type selectType: str
    :return fileteredSelection: The selection now filtered by type
    :rtype fileteredSelection: list(str)
    """
    filteredSelection = list()
    if selectType == "edges":
        for sel in selectedComponents:
            if ".e[" in sel:
                filteredSelection.append(sel)
    elif selectType == "faces":
        for sel in selectedComponents:
            if ".f[" in sel:
                filteredSelection.append(sel)
    elif selectType == "vertices":
        for sel in selectedComponents:
            if ".vtx[" in sel:
                filteredSelection.append(sel)
    return filteredSelection


def componentSelectionType(componentSelection):
    """Returns "object", "vertices", "edges", "faces" or "uvs" depending on the first selection type.

    Will return None if unknown

    :param componentSelection: a Maya selection
    :type componentSelection: list(str)
    :return componentType: the type of component as the first selection, eg. "vertices"
    :rtype componentType: str
    """
    if not componentSelection:  # nothing selected
        return None
    if "." not in componentSelection[0]:
        return "object"
    elif ".vtx[" in componentSelection[0]:
        return "vertices"
    elif ".e[" in componentSelection[0]:
        return "edges"
    elif ".f[" in componentSelection[0]:
        return "faces"
    elif ".map[" in componentSelection[0]:
        return "uvs"
    return None


def selectComponentSelectionMode(componentType="vertices"):
    """Selects a component mode "vertices", "edges", "faces" or "uvs"

    :param componentType: The component mode to enter "vertices", "edges", "faces" or "uvs"
    :type componentType: str
    """
    # todo add object mode
    if not componentType:
        return
    elif componentType == "vertices":
        cmds.selectType(smp=1, pv=1)  # vert selection
    elif componentType == "edges":
        cmds.selectType(sme=1, pe=1)  # edge selection
    elif componentType == "faces":
        cmds.selectType(smf=1, pf=1)  # face selection
    elif componentType == "uvs":
        cmds.selectType(smu=1, puv=1)  # face selection


def convertSelection(type="faces"):
    """Converts a selection to either edges, faces, vertices, or uvs

    selectType can be:
        "faces"
        "vertices"
        "edges"
        "edgeLoop"
        "edgeRing"
        "edgePerimeter"
        "uvs"
        "uvShell"
        "uvShellBorder"


    :param type: The selection to convert to "faces", "vertices", "edges", "edgeRing" etc see function documentation
    :type type: str
    """
    if type == "faces":
        mel.eval('ConvertSelectionToFaces;')
    elif type == "vertices":
        mel.eval('ConvertSelectionToVertices;')
    elif type == "edges":
        mel.eval('ConvertSelectionToEdges;')
    elif type == "uvs":
        mel.eval('ConvertSelectionToUVs;')
    elif type == "edgeLoop":
        mel.eval("SelectEdgeLoopSp;")
    elif type == "edgeRing":
        mel.eval("SelectEdgeRingSp;")
    elif type == "edgePerimeter":
        mel.eval("ConvertSelectionToEdgePerimeter;")
    elif type == "uvShell":
        mel.eval("ConvertSelectionToUVShell;")
    elif type == "uvShellBorder":
        mel.eval("ConvertSelectionToUVShellBorder;")

    return cmds.ls(selection=True)


"""
HIERARCHY
"""


def selectHierarchy(nodeType='transform'):
    """Filters the select hierarchy command by a node type, usually transform type so it doesn't select the shape nodes

    :param nodeType: type of node to be filtered in the selection, usually transform
    :type nodeType: str
    :return: objsFiltered: the objs selected
    :type filterList: list
    """
    cmds.select(hierarchy=True, replace=True)
    objsAllHierachy = cmds.ls(selection=True, long=True)
    objsFiltered = cmds.ls(objsAllHierachy, type=nodeType)
    cmds.select(objsFiltered, replace=True)
    return objsFiltered


"""
GROW/SHRINK
"""


def growSelection():
    """Standard maya grow component selection ">" hotkey """
    mel.eval('PolySelectTraverse 1;')


def shrinkSelection():
    """Standard maya grow component selection "<" hotkey """
    mel.eval('PolySelectTraverse 2;')

