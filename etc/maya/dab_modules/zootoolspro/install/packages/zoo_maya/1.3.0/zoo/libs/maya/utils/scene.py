import os
import contextlib
from maya import cmds
from zoo.libs.maya.api import scene


def findAdditionalSceneDependencies(references=True, textures=True):
    """
    Find additional dependencies from the scene by looking at the file references and texture paths
    """
    refPaths = set()
    if references:
        refPaths.union(findSceneReferences())
    if textures:
        refPaths.union(findSceneTextures())
    return refPaths


def findSceneTextures():
    paths = set()
    # now look at file texture nodes
    for file_node in cmds.ls(l=True, type="file"):
        # ensure this is actually part of this scene and not referenced
        if cmds.referenceQuery(file_node, isNodeReferenced=True):
            continue
        # get path and make it platform dependent
        texture_path = cmds.getAttr(os.path.normpath(".".join([file_node, "fileTextureName"])))
        if texture_path:
            paths.add(texture_path)
    return paths


def findTextureNodePairs():
    paths = set()
    # now look at file texture nodes
    for file_node in cmds.ls(l=True, type="file"):
        # ensure this is actually part of this scene and not referenced
        if cmds.referenceQuery(file_node, isNodeReferenced=True):
            continue
        # get path and make it platform dependent
        texture_path = cmds.getAttr(os.path.normpath(".".join([file_node, "fileTextureName"])))
        if texture_path:
            paths.add((file_node, texture_path))
    return paths


def iterTextureNodePairs(includeReferences=False):
    # now look at file texture nodes
    for file_node in cmds.ls(l=True, type="file"):
        # ensure this is actually part of this scene and not referenced
        if includeReferences and cmds.referenceQuery(file_node, isNodeReferenced=True):
            continue
        # get path and make it platform dependent
        texture_path = cmds.getAttr(os.path.normpath(".".join([file_node, "fileTextureName"])))
        if texture_path:
            yield ([file_node, texture_path])


def findSceneReferences():
    paths = set()

    # first let's look at maya references
    for ref_node in scene.iterReferences():
        # get the path:
        ref_path = ref_node.fileName(True, False, False).replace("/", os.path.sep)
        if ref_path:
            paths.add(ref_path)
    return paths


@contextlib.contextmanager
def isolatedNodes(nodes, panel):
    """Context manager for isolating `nodes` in maya model `panel`"""

    cmds.isolateSelect(panel, state=True)
    for obj in nodes:
        cmds.isolateSelect(panel, addDagObject=obj)
    yield
    cmds.isolateSelect(panel, state=False)
