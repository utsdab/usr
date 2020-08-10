import maya.api.OpenMaya as om2
import maya.mel as mel
from maya import cmds

from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.objutils import joints
from zoo.apps.toolsetsui import run
from zoo.libs.maya.cmds.rig import controls


class JointsMarkingMenuCommand(menu.MarkingMenuCommand):
    """Command class for the joints marking menu.

    Commands are related to the file (JSON) in the same directory:

        joints.mmlayout

    Zoo paths must point to this directory, usually on zoo startup inside the repo root package.json file.

    Example add to package.json:

        "ZOO_MM_COMMAND_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",
        "ZOO_MM_MENU_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",
        "ZOO_MM_LAYOUT_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",

    Or if not on startup, run in the script editor, with your path:

        os.environ["ZOO_MM_COMMAND_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"
        os.environ["ZOO_MM_MENU_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"
        os.environ["ZOO_MM_LAYOUT_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"

    Map the following code to a hotkey press. Note: Change the key modifiers if using shift alt ctrl etc:

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.buildFromLayout("markingMenu.joints",
                                            "markingMenuJoints",
                                            parent="viewPanes",
                                            options={"altModifier": False,
                                                     "shiftModifier": True})

    Map to hotkey release:

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.removeExistingMenu("markingMenuJoints")

    """
    id = "jointsMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        """This method is mostly over ridden by the associated json file"""
        return {"icon": "",
                "label": "",
                "bold": False,
                "italic": False,
                "optionBox": False,
                "optionBoxIcon": ""
                }

    def copyContols(self):
        self.text = "adsfdsfdfa"

    def pasteControls(self):
        print(self.text)

    def reconnectCtrls(self):
        masterCtrlList = controls.reconnectAllBreakCtrls()
        cmds.select(deselect=True)
        if not masterCtrlList:
            om2.MGlobal.displayWarning("No break off controls found in the scene connected to network "
                                       "nodes named".format(controls.ZOO_TEMPBREAK_NETWORK))
            return
        self.selObjs = masterCtrlList
        om2.MGlobal.displayInfo("Success: Controls reconnected `{}`".format(masterCtrlList))

    def execute(self, arguments):
        """The main execute methods for the joints marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "jointCreate":
            mel.eval("setToolTo jointContext")
        elif operation == "jointInsert":
            mel.eval("setToolTo insertJointContext")
        elif operation == "breakOffControls":
            controls.breakOffControlSelected()
        elif operation == "reconnectControls":
            controls.reconnectAllBreakCtrls()
        elif operation == "copyControls":
            controls.CNTRL_CLIPBOARD_INSTANCE.copyControl()
        elif operation == "pasteControls":
            controls.CNTRL_CLIPBOARD_INSTANCE.pasteControl()
        elif operation == "zooOrientJoint":
            run.openTool("jointTool")
        elif operation == "localRotAxisTgl":
            joints.toggleLocalRotationAxisSelection(children=True, message=True)
        elif operation == "changeRotOrder":
            run.openTool("generalAnimationTools")
        elif operation == "mirrorJoint":
            joints.mirrorJointSelected("X")
        elif operation == "jointRemove":
            mel.eval("doRemoveJoint")
        elif operation == "zooCreateControls":
            run.openTool("controlCreator")
        elif operation == "orientJoint":
            mel.eval("performJointOrient 0")
        elif operation == "ikHandleCreate":
            mel.eval("setToolTo ikHandleContext")
        elif operation == "splineIkCreate":
            mel.eval("setToolTo ikSplineHandleContext")
        elif operation == "ikSolverToggle":  # TODO this needs to be a toggle menu item (disabled in layout)
            mel.eval("ikSystem - e - sol(!`ikSystem - q - sol`)")
        elif operation == "zooRenamer":
            run.openTool("zooRenamer")
        elif operation == "colorOverrides":
            run.openTool("colorOverrides")

    def executeUI(self, arguments):
        """The option box execute methods for the joints marking menu. see execute() for main commands

        For this method to be called, in the JSON set "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "jointCreate":
            mel.eval("setToolTo jointContext; toolPropertyWindow")
        elif operation == "mirrorJoint":
            mel.eval("performMirrorJoint 1")
        elif operation == "orientJoint":
            mel.eval("performJointOrient 1")
        elif operation == "ikHandleCreate":
            mel.eval("setToolTo ikHandleContext; toolPropertyWindow")
        elif operation == "splineIkCreate":
            mel.eval("setToolTo ikSplineHandleContext; toolPropertyWindow")
