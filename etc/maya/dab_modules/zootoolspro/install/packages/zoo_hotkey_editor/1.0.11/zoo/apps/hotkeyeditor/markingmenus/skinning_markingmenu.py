import maya.mel as mel

from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.skin import bindskin

class SkinMarkingMenuCommand(menu.MarkingMenuCommand):
    """Command class for the skinning marking menu.

    Commands are related to the file (JSON) in the same directory:

        skinning.mmlayout

    Zoo paths must point to this directory, usually on zoo startup inside the repo root package.json file.

    Example add to package.json:

        "ZOO_MM_COMMAND_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",
        "ZOO_MM_MENU_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",
        "ZOO_MM_LAYOUT_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",

    Or if not on startup:

        os.environ["ZOO_MM_COMMAND_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"
        os.environ["ZOO_MM_MENU_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"
        os.environ["ZOO_MM_LAYOUT_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"

    Map the following code to a hotkey press. Note: Change the key modifiers if using shift alt ctrl etc:

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.buildFromLayout("markingMenu.skinning",
                                            "markingMenuSkinning",
                                            parent="viewPanes",
                                            options={"altModifier": False,
                                                     "shiftModifier": True})

    Map to hotkey release:

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.removeExistingMenu("markingMenuSkinning")

    """
    id = "skiningMarkingMenu"  # a unique identifier for a class, should never be changed
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
        """The main execute methods for the skinning marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "skinSelected":
            bindskin.bindSkinSelected(toSelectedBones=True, maximumInfluences=5, maxEditLimit=5, bindMethod=0,
                                      displayMessage=True)
        elif operation == "unbindSkin":
            bindskin.unbindSkinSelected()
        elif operation == "mirrorXToNegX":
            bindskin.mirrorSkinSelection(mirrorMode='YZ', mirrorInverse=False)
        elif operation == "smoothVertSelBraverabbit":
            pass
        elif operation == "zooVertSkinning":
            pass
        elif operation == "paintSmoothBraverabbit":
            pass
        elif operation == "NGSkinTools":
            pass
        elif operation == "paintWeightsWindow":
            mel.eval("artAttrSkinToolScript 3")
        elif operation == "transferSkinWeights":
            bindskin.transferSkinWeightsSelected()
        elif operation == "duplicateOriginal":
            bindskin.duplicateSelectedBeforeBind()
        elif operation == "bindSelHeatMap":
            bindskin.bindSkinSelected(bindMethod=2)
        elif operation == "bindHierarchyDefaults":
            bindskin.bindSkinSelected(toSelectedBones=False, maximumInfluences=5, maxEditLimit=5, bindMethod=0,
                                      displayMessage=True)
        elif operation == "bindSelectedRigid":
            bindskin.bindSkinSelected(toSelectedBones=True, maximumInfluences=0, maxEditLimit=5, bindMethod=0,
                                      displayMessage=True)
        elif operation == "bindSkinGeodesic":
            bindskin.bindSkinSelected(bindMethod=3)
        elif operation == "addJointsToSkin":
            bindskin.addJointsToSkinnedSelected()
        elif operation == "removeInfluences":
            bindskin.removeInfluenceSelected()
        elif operation == "componentEditor":
            mel.eval('tearOffRestorePanel "Component Editor" "componentEditorPanel" true;')
        elif operation == "zooSkinWeightsWindow":
            pass
        elif operation == "importWeightsBraverabbit":
            pass
        elif operation == "exportWeightsBraverabbit":
            pass
        elif operation == "hammerWeights":
            mel.eval("weightHammerVerts;")
        elif operation == "pruneSmallWeights":
            mel.eval("performPruneWeights false;")
        elif operation == "skinToWeightBlended":
            bindskin.skinClusterMethodSwitch(skinningMethod=2, displayMessage=True)
        elif operation == "combineSkinnedMeshes":
            pass

    def executeUI(self, arguments):
        """The option box execute methods for the skinning marking menu. see execute() for main commands

        For this method to be called "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "skinSelected" \
                or operation == "bindSelHeatMap" \
                or operation == "bindHierarchyDefaults" \
                or operation == "bindSelectedRigid" \
                or operation == "bindSkinGeodesic":
            mel.eval("performSkinCluster true;")
        elif operation == "unbindSkin":
            mel.eval("DetachSkinOptions;")
        elif operation == "addJointsToSkin":
            mel.eval("performAddInfluence true;")
        elif operation == "mirrorXToNegX":
            mel.eval("performMirrorSkinWeights true;")
        elif operation == "pruneSmallWeights":
            mel.eval("performPruneWeights true;")
