from zoo.libs.command import command
from zoo.libs.maya.api import scene
from zoo.libs.maya.api import plugs

from maya.api import OpenMaya as om2


class ConnectSRTSelectedCommand(command.ZooCommand):
    id = "zoo.maya.connect.selection.localsrt"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "connection",
              "tooltip": "Connects the translate, rotate, scale from the first selected node to all others",
              "label": "Connect SRT",
              "color": "",
              "backgroundColor": ""
              }
    _modifier = None

    def resolveArguments(self, arguments):
        selected = scene.getSelectedNodes()
        if len(selected) < 2:
            self.cancel("Please Select 2 or more nodes")
        targets = [om2.MObjectHandle(i) for i in selected[1:] if i.hasFn(om2.MFn.kDagNode)]
        driver = om2.MObjectHandle(selected[0]) if selected[0].hasFn(om2.MFn.kDagNode) else None
        if not targets or not driver:
            self.cancel("Incorrect node types selected only kDagNode acceptable!")
        arguments.update({"targets": targets, "driver": driver})
        return arguments

    def doIt(self, driver=None, targets=None, translate=True, rotate=True, scale=True):
        """Create the meta node based on the type parameter, if the type isn't specified then the baseMeta class will
        be used instead

        """
        sourceFn = om2.MFnDependencyNode(driver.object())
        sourceScalePlug = sourceFn.findPlug("scale", False)
        sourceRotatePlug = sourceFn.findPlug("rotate", False)
        sourceTranslatePlug = sourceFn.findPlug("translate", False)
        self._modifier = om2.MDGModifier()
        for t in targets:
            drivenFn = om2.MFnDependencyNode(t.object())
            if scale:
                plugs.connectVectorPlugs(sourceScalePlug, drivenFn.findPlug("scale", False), (True, True, True),
                                         force=True, modifier=self._modifier)
            if rotate:
                plugs.connectVectorPlugs(sourceRotatePlug, drivenFn.findPlug("rotate", False), (True, True, True),
                                         force=True, modifier=self._modifier)
            if translate:
                plugs.connectVectorPlugs(sourceTranslatePlug, drivenFn.findPlug("translate", False), (True, True, True),
                                         force=True, modifier=self._modifier)
        self._modifier.doIt()
        return True

    def undoIt(self):
        if self._modifier is not None:
            self._modifier.undoIt()
