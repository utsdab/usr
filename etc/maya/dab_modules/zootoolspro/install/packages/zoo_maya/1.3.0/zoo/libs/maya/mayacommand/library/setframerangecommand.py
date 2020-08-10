from zoo.libs.maya.api import anim
from zoo.libs.command import command
from maya.api import OpenMayaAnim as om2Anim


class SetSceneFrameRangeCommand(command.ZooCommand):
    """This command Create a standard camera and adds the node as a MetaCamera
    """
    id = "zoo.scene.setFrameRange"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "camera",
              "tooltip": "Create camera",
              "label": "Create Camera",
              "color": "",
              "backgroundColor": ""
              }
    _settings = {}

    def doIt(self, start=0, end=1, newCurrentFrame=0):
        self._settings = {"start": om2Anim.MAnimControl.minTime().value,
                          "end": om2Anim.MAnimControl.maxTime().value,
                          "newCurrentFrame": om2Anim.MAnimControl.currentTime().value}
        anim.setCurrentRange(start, end, newCurrentFrame)
        return True

    def undoIt(self):
        if self._settings:
            anim.setCurrentRange(**self._settings)
            return True
        return False
