import maya.cmds as cmds
import random
import maya.api.OpenMaya as om2

def getObjEdgeCount():
    """Gets the edge count of selected objs and returns two lists

    :return objList: list of object names
    :rtype objList: list
    :return edgeList: list of edge numbers that correspond to the objList names
    :rtype edgeList: list
    """
    objList = cmds.ls(sl=True)
    edgeList = []
    for obj in objList:
        edgeList.append(cmds.polyEvaluate(edge=True))
    return objList, edgeList


def randomizeFlipTriEdge(objList, edgeList, selectObjs=True, randomizeEvery=5):
    """Flips random triangle edges give an object and corresponding edge list
    On medium to high poly counts can be slow

    :return objList: list of object names
    :rtype objList: list
    :return edgeList: list of edge numbers that correspond to the objList names
    :rtype edgeList: list
    :param selectObjs: would you like to select all object after completion
    :type selectObjs: bool
    :param randomizeEvery: best not to randomize every triangle, so will randomize 1 in x
    :type randomizeEvery: int
    """
    for i, obj in enumerate(objList):
        for edge in range(0, edgeList[i]):
            flip = random.randint(0, randomizeEvery)
            if not flip:
                try:  # could be a border edge and will fail, no error given just a warning
                    cmds.select('{}.e[{}]'.format(obj, edge), replace=True)
                    cmds.polyFlipEdge(edit=True)
                except:  # has failed, probably a border edge
                    pass
        cmds.select(objList, replace=True)


def randomizeFlipTriEdgeSel(triangulate=True):
    """Flips random triangle edges on selected objects, optionally triangulates the meshes too
    On medium to high poly counts will be slow

    :param triangulate: Would you like to triangulate all meshes
    :type triangulate: bool
    """
    objList, edgeList = getObjEdgeCount()
    if triangulate:
        for obj in objList:
            cmds.polyTriangulate(obj)
    randomizeFlipTriEdge(objList, edgeList, selectObjs=True, randomizeEvery=5)
    om2.MGlobal.displayInfo("Edges Successfully Randomized On Selected Objects")


# randomizeFlipTriEdgeSel(triangulate=True)