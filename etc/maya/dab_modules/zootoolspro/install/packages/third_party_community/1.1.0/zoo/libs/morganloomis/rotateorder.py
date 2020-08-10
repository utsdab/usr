"""
Note: The code here has been modified from the original scripts by Morgan Loomis (http://morganloomis.com)
Code falls under http://creativecommons.org/licenses/by-sa/3.0/ and may be redistributed with Attribution/ShareAlike
"""


import maya.cmds as cmds
import maya.api.OpenMaya as om2

ROTATE_ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]


def convertRotateOrder(objList, roo="zxy", message=True):
    """Converts the rotation order of an object list, potentially animated Maya objects for the entire timeline.

    If an object has been animated it will be re-keyed for all rotate values x, y and z on all keys.

    Note: This function has been modified from the original script by Morgan Loomis (http://morganloomis.com)
    These files can be redistributed under http://creativecommons.org/licenses/by-sa/3.0/ with Attribution/ShareAlike

    :param objList: The list of objects to change their rotation order
    :type objList: list(str)
    :param roo: The rotate order, as a string with three letters "xyz", "yzx", "zxy", "xzy", "yxz", or "zyx"
    :type roo: str
    :param message: report the message back to the user?
    :type message: bool
    """
    if roo not in ROTATE_ORDERS:
        om2.MGlobal.displayWarning("Not a valid rotation order: {}".format(roo))
        return
    time = cmds.currentTime(query=True)
    # Check that all rot channels have keys, or no keys
    keytimes = dict()
    prevRoo = dict()
    allKeytimes = list()
    keyedObjs = list()
    unkeyedObjs = list()
    for obj in objList:
        rotKeys = cmds.keyframe(obj, attribute='rotate', query=True, timeChange=True)
        if rotKeys:
            keytimes[obj] = list(set(rotKeys))
            prevRoo[obj] = ROTATE_ORDERS[cmds.getAttr(obj + '.rotateOrder')]
            allKeytimes.extend(rotKeys)
            keyedObjs.append(obj)
        else:
            unkeyedObjs.append(obj)
    if keyedObjs:  # Change rotation order for keyed objects
        allKeytimes = list(set(allKeytimes))
        allKeytimes.sort()
        with IsolateViews():  # Disables all viewports while roo is changed
            for frame in allKeytimes:  # Set keyframes first, so frames are keyed on all rotate attributes x, y and z
                cmds.currentTime(frame, edit=True)
                for obj in keyedObjs:
                    if frame in keytimes[obj]:
                        cmds.setKeyframe(obj, attribute='rotate')  # Make sure every channel has a key
            for frame in allKeytimes:
                cmds.currentTime(frame, edit=True)
                for obj in keyedObjs:
                    if frame in keytimes[obj]:
                        cmds.xform(obj, preserve=True, rotateOrder=roo)  # Change the rotation order to the new value
                        cmds.setKeyframe(obj, attribute='rotate')  # Set a keyframe with the new rotation order
                        # Change rotation order back without preserving, so that the next value is correct
                        cmds.xform(obj, preserve=False, rotateOrder=prevRoo[obj])
            cmds.currentTime(time, edit=True)  # Reset current time while still isolated, for speed.
            for keyObj in keyedObjs:  # Set the final rotate order for keyed objects
                cmds.xform(keyObj, preserve=False, rotateOrder=roo)
                cmds.filterCurve(keyObj)
        if unkeyedObjs:  # For unkeyed objects, rotation order just needs to be changed with xform
            for obj in unkeyedObjs:
                cmds.xform(obj, preserve=True, rotateOrder=roo)
    if message:
        om2.MGlobal.displayInfo('Rotation order changed to {} for objects: {}'.format(roo, objList))


def convertRotateOrderSelected(roo="zxy", message=True):
    """Converts the rotation order of selected objects, potentially animated Maya objects for the entire timeline.

    If an object has been animated it will be re-keyed for all rotate values x, y and z on all keys.

    Note: This function has been modified from the original script by Morgan Loomis (http://morganloomis.com)
    This module is under http://creativecommons.org/licenses/by-sa/3.0/ may be redistributed Attribution/ShareAlike

    :param roo: The rotate order, as a string with three letters "xyz", "yzx", "zxy", "xzy", "yxz", or "zyx"
    :type roo: str
    :param message: report the message back to the user?
    :type message: bool
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        om2.MGlobal.displayWarning('No objects selected. Please make a selection.')
        return
    convertRotateOrder(selObjs, roo=roo, message=message)
    cmds.select(selObjs)  # Reset the selection as has been changed


class IsolateViews():
    """Isolates selection with nothing selected for all viewports speeds up processes that cause the viewport to refresh

    For example, baking or changing time.

    Original script by Morgan Loomis (http://morganloomis.com)
    This class IsolateViews() is under http://creativecommons.org/licenses/by-sa/3.0/ and may be redistributed
    with Attribution/ShareAlike
    """
    def __enter__(self):

        self.sel = cmds.ls(sl=True)
        self.modelPanels = cmds.getPanel(type='modelPanel')
        self.isolate(True)

        cmds.select(clear=True)

        # save and turn off settings that might print to the script editor
        self.resetCycleCheck = cmds.cycleCheck(query=True, evaluation=True)
        cmds.cycleCheck(evaluation=False)

        self.resetAutoKey = cmds.autoKeyframe(query=True, state=True)
        cmds.autoKeyframe(state=False)

    def __exit__(self, *args):
        # reset settings
        cmds.cycleCheck(evaluation=self.resetCycleCheck)
        cmds.autoKeyframe(state=self.resetAutoKey)

        if self.sel:
            cmds.select(self.sel)

        self.isolate(False)

    def isolate(self, state):

        cmds.select(clear=True)
        for each in self.modelPanels:
            cmds.isolateSelect(each, state=state)