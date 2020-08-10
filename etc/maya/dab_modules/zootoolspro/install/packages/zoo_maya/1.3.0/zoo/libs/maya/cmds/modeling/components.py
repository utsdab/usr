"""Also see cmds.objutils.selection for various functions
"""
import re
import time

import maya.cmds as cmds
from maya.api import OpenMaya as om2

def normalListFromVtxFaces(vtxFaceList):
    normalList = list()
    for vtxFace in vtxFaceList:
        normalList.append(cmds.polyNormalPerVertex(vtxFace, query=True, xyz=True)[0])
    return normalList


def softFromEdge(edge):
    """From an edge determine if its soft or hard from the vert normals

    :param edge: A maya edge selection eg. "pSphere1.e[101]"
    :type edge: str

    :return soft: True if soft False if hard
    :rtype soft: bool
    """
    vtxFaces = cmds.polyListComponentConversion(edge, fromEdge=True, toVertexFace=True)
    vtxFaces = cmds.ls(vtxFaces, flatten=True)  # remove ":" entries
    startName = "{}]".format(vtxFaces[0].split("][")[0])
    firstList = [vtxFaces[0]]
    secondList = list()
    for vertFace in vtxFaces[1:]:
        if startName in vertFace:
            firstList.append(vertFace)
        else:
            secondList.append(vertFace)
    # check if all normals of the first list and second matches, will be soft
    if len(set(normalListFromVtxFaces(firstList))) == 1 and len(set(normalListFromVtxFaces(secondList))) == 1:
        return True
    return False


def softEdgeList(obj, time=False):
    """For each edge in a polygon object check if it's hard or soft and return as a list

    NOTE: Unused as is too slow, now using zoo.libs.buliarcacristian.lockNormals_toHS

    Annoying function to work around not being able to set vertexNormals without locking them.

    WARNING:  This takes a lot of time on dense meshes 20sec per 3k faces. Slow function

    :param obj: A maya Mesh object transform node
    :type obj: str

    :return edgeList: A list of edges of the object ["pSphere1.e[60:61]" "pSphere1.e[63:66]"]
    :rtype edgeList: list(str)
    :return softList: A list of soft edges True/False will match the edgeList [True, False]
    :rtype softList: list(bool)
    """
    if time:
        t0 = time.time()
    edgeList = cmds.ls('{}.e[*]'.format(obj), flatten=True)
    softList = list()
    for edge in edgeList:  # checks if all the vert normals match, if yes is a soft edge else is hard
        softList.append(softFromEdge(edge))
    if time:  # Because it can take ages
        t1 = time.time()
        om2.MGlobal.displayInfo("time = {}".format(t1-t0))
    return edgeList, softList
