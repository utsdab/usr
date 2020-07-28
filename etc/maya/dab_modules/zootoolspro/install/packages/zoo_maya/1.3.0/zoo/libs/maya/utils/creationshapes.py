from maya import cmds
from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import constraints


def createAnnotation(rootObj, endObj, text=None, name=None):
    newparent = nodes.createDagNode("_".join([name, "ann_hrc"]), "transform")
    name = name or "annotation"
    locator = nodes.createDagNode("_".join([name, "loc"]), "locator", newparent)

    annotationNode = nodes.asMObject(cmds.annotate(nodes.nameFromMObject(locator), tx=text))
    annParent = nodes.getParent(annotationNode)
    nodes.rename(annParent, name)
    nodes.setParent(annParent, newparent, False)
    extras = [newparent]
    constraint = constraints.MatrixConstraint(name="_".join([name, "startMtx"]))

    extras.extend(constraint.create(endObj, locator, (True, True, True), (True, True, True), (True, True, True)))
    extras.extend(constraint.create(rootObj, annParent, (True, True, True), (True, True, True), (True, True, True)))

    return annParent, locator, extras