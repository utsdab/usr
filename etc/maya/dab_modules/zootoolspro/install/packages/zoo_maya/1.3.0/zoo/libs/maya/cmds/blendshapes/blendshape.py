import maya.cmds
import maya.api.OpenMaya as om2


def renameBlendshape(blendshapeNode, blendAttrOld, blendAttrNew, message=True):
    """Function for renaming blendshape target attributes.
    Annoying because cmds does not support it and blendshapes are index's with aliased names.

    Loops over the blendshape and queries the index to find the alias's name then replaces the alias if a match.

    Credit, original version from Evan Cox http://blog.evancox.net/2016/07/27/renaming-blendshape-targets/

    :param blendshapeNode: The blendshape node name
    :type blendshapeNode:
    :param blendAttrOld: The old blendshape name  "pCube1"
    :type blendAttrOld: str
    :param blendAttrNew: The new blendshape name "aNiceName"
    :type blendAttrNew: str
    :param message: Report any messages to the user?
    :type message: bool
    """
    failList = []
    numberOfTargets = maya.cmds.getAttr('{}.weight'.format(blendshapeNode), size=True)
    # Iterate through the weight list
    for index in range(0, numberOfTargets):
        # Query the name of the current blendshape weight
        oldName = maya.cmds.aliasAttr('{}.weight[{}]'.format(blendshapeNode, index), query=True)
        # If the old name doesn't match
        if oldName == blendAttrOld:  # Rename
            absoluteName = '{0}.weight[{1}]'.format(blendshapeNode, index)
            maya.cmds.aliasAttr(blendAttrNew, absoluteName)  # Re-aliasing / Renaming occurs here.
            if message:
                om2.MGlobal.displayInfo("Success: Changed `{}` to `{}`".format(oldName, blendAttrNew))
        else:  # Add the failure to the fail list
            failList.append(oldName)
    if failList:
        om2.MGlobal.displayWarning("{} names were not changed. {}".format(len(failList), failList))

