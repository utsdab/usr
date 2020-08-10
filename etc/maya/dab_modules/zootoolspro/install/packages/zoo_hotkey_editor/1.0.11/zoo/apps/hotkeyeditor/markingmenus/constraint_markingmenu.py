import maya.mel as mel
import maya.cmds as cmds

from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.objutils import constraints


class ConstraintMarkingMenuCommand(menu.MarkingMenuCommand):
    """Command class for the Constraint Marking Menu

    Commands are related to the file (JSON) in the same directory:

        constraint.mmlayout

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
        zooMenu.MarkingMenu.buildFromLayout("markingMenu.constraint",
                                            "markingMenuConstraint",
                                            parent="viewPanes",
                                            options={"altModifier": False,
                                                     "shiftModifier": True})

    Map to hotkey release:

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.removeExistingMenu("markingMenuConstraint")

    """
    id = "constraintMarkingMenu"  # a unique identifier for a class, should never be changed
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

    def execute(self, arguments):
        """The main execute methods for the constraint marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "matchPosRot":
            cmds.matchTransform(cmds.ls(selection=True), pos=True, rot=True, scl=False, piv=False)
        elif operation == "matchPos":
            cmds.matchTransform(cmds.ls(selection=True), pos=True, rot=False, scl=False, piv=False)
        elif operation == "orientConstrainMOffset":
            cmds.orientConstraint(cmds.ls(selection=True), maintainOffset=True)
        elif operation == "parentConstrainNoMOffset":
            cmds.parentConstraint(cmds.ls(selection=True), maintainOffset=False)
        elif operation == "parentConstrainMOffset":
            cmds.parentConstraint(cmds.ls(selection=True), maintainOffset=True)
        elif operation == "pointConstrainNoMOffset":
            cmds.pointConstraint(cmds.ls(selection=True), maintainOffset=False)
        elif operation == "pointConstrainMOffset":
            cmds.pointConstraint(cmds.ls(selection=True), maintainOffset=True)
        elif operation == "matchRot":
            cmds.matchTransform(cmds.ls(selection=True), pos=False, rot=True, scl=False, piv=False)
        elif operation == "aimConstraint":
            mel.eval("performAimConstraint 0;")
        elif operation == "deleteConstraintsSelected":
            constraints.deleteConstraintsFromSelObj(message=True)
        elif operation == "orientConstraintNoMOffset":
            cmds.orientConstraint(cmds.ls(selection=True), maintainOffset=False)
        elif operation == "poleVectorConstraint":
            cmds.poleVectorConstraint(cmds.ls(selection=True))
        elif operation == "pointOnPolyConstraint":
            cmds.pointOnPolyConstraint(cmds.ls(selection=True))
        elif operation == "geoNormalConstraint":
            cmds.geometryConstraint(cmds.ls(selection=True))
            cmds.normalConstraint(cmds.ls(selection=True))
        elif operation == "curveConstraint":
            cmds.geometryConstraint(cmds.ls(selection=True))
            cmds.tangentConstraint(cmds.ls(selection=True))
        elif operation == "geoConstraint":
            cmds.geometryConstraint(cmds.ls(selection=True))
        elif operation == "normalConstraint":
            cmds.normalConstraint(cmds.ls(selection=True))
        elif operation == "tangentConstraint":
            cmds.tangentConstraint(cmds.ls(selection=True))
        elif operation == "scaleConstraint":
            cmds.scaleConstraint(cmds.ls(selection=True))
        elif operation == "motionPath":
            mel.eval("AttachToPath")
        elif operation == "matchScale":
            cmds.matchTransform(cmds.ls(selection=True), pos=False, rot=False, scl=True, piv=False)
        elif operation == "matchAll":
            cmds.matchTransform(cmds.ls(selection=True), pos=True, rot=True, scl=True, piv=False)
        elif operation == "matchPivot":
            cmds.matchTransform(cmds.ls(selection=True), pos=False, rot=False, scl=False, piv=True)

    def executeUI(self, arguments):
        """The option box execute methods for the constraint marking menu. see execute() for main commands

        For this method to be called "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "orientConstrainMOffset" or operation == "orientConstrainNoMOffset":
            mel.eval("performOrientConstraint 1;")
        elif operation == "parentConstrainMOffset" or operation == "parentConstrainNoMOffset":
            mel.eval("performParentConstraint 1;")
        elif operation == "pointConstrainMOffset" or operation == "pointConstrainNoMOffset":
            mel.eval("performPointConstraint 1;")
        elif operation == "aimConstraint":
            mel.eval("performAimConstraint 1;")
        elif operation == "orientConstraintNoMOffset":
            mel.eval("performOrientConstraint 1")
        elif operation == "normalConstraint":
            mel.eval("performNormalConstraint 1")
        elif operation == "tangentConstraint":
            mel.eval("performTangentConstraint 1")
        elif operation == "scaleConstraint":
            mel.eval("performScaleConstraint 1")
        elif operation == "pointOnPolyConstraint":
            mel.eval("performPointOnPolyConstraint 1")
        elif operation == "motionPath":
            mel.eval("AttachToPathOptions")


