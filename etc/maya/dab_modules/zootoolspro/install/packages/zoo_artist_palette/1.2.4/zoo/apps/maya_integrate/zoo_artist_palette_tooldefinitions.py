from maya import cmds
from zoo.apps.toolpalette import palette
from zoo.libs.command import executor


class TriggerStateToggle(palette.ToolDefinition):
    id = "zoo.triggers.state"
    creator = "David Sparrow"
    tags = ["triggers"]
    uiData = {"icon": "menu_reload",
              "tooltip": "Toggles the state of triggers, if off then marking menus will no longer operate",
              "label": "Trigger Toggle",
              "color": "",
              "backgroundColor": "",
              "isCheckable": True,
              "isChecked": True,
              "multipleTools": False,
              "loadOnStartup": True
              }

    def execute(self, state):
        from zoo.libs.maya.markingmenu import markingmenuoverride
        if state:
            # turn on the triggers
            markingmenuoverride.setup()
            return
        # remove the triggers
        markingmenuoverride.reset()

    def teardown(self):
        from zoo.libs.maya.markingmenu import markingmenuoverride
        # remove the triggers
        markingmenuoverride.reset()


class FramelessWindowToggle(palette.ToolDefinition):
    id = "zoo.frameless.state"
    creator = "Keen Foong"
    tags = ["frameless"]
    uiData = {"icon": "menu_reload",
              "tooltip": "Toggles windows to use ZooTools frameless, or Operating system default windows.",
              "label": "Zoo Custom Window",
              "color": "",
              "backgroundColor": "",
              "isCheckable": True,
              "isChecked": True,
              "multipleTools": False,
              "loadOnStartup": True
              }
    state = uiData['isChecked']

    def execute(self, state):
        self.state = state

    def teardown(self):
        pass


class Reload(palette.ToolDefinition):
    id = "zoo.reload"
    creator = "David Sparrow"
    tags = ["reload"]
    uiData = {"icon": "menu_zoo_reload",
              "tooltip": "Reloads zootools by reloading the zootools.py plugin",
              "label": "Reload",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        cmds.evalDeferred('from maya import cmds;cmds.unloadPlugin("zootools.py")\ncmds.loadPlugin("zootools.py")')


class Shutdown(palette.ToolDefinition):
    id = "zoo.shutdown"
    creator = "David Sparrow"
    tags = ["menu_shutdown"]
    uiData = {"icon": "zoo_shutdown",
              "tooltip": "shutdown zootools by unloading the zootools.py plugin",
              "label": "Shutdown",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self):
        cmds.evalDeferred('from maya import cmds;cmds.unloadPlugin("zootools.py")')


class HotkeyEditorUi(palette.ToolDefinition):
    id = "zoo.hotkeyeditorui"
    creator = "Keen Foong"
    tags = ["hotkey", "hotkeys", "editor"]
    uiData = {"icon": "menu_keyboard",
              "tooltip": "Create custom hotkeys",
              "label": "Hotkey Editor",
              "color": "",
              "backgroundColor": "",
              "multipleTools": False,
              "frameless": {"frameless": True, "force": False},
              "dock": {"dockable": True, "tabToControl": ("AttributeEditor", -1), "floating": False}
              }

    def execute(self, *args, **kwargs):
        return self.executeFrameless(*args, **kwargs)

    def runTool(self, framelessActive=True, toolArgs=None):
        from zoo.apps.hotkeyeditor import run
        return run.launch(framelessChecked=framelessActive)

    def setFrameless(self, tool, frameless):
        if tool is not None:
            tool.setFrameless(frameless)

    def setStyleSheet(self, style):
        for t in self.tool:
            t['tool'].setWindowStyleSheet(style)

    def toolClosed(self, tool):
        """ Clean up after tool has closed

        :param tool:
        :return:
        """
        if tool in self.tool:
            self.tool.remove(tool)

    def teardown(self):
        for t in self.tool:
            if t:
                t['tool'].close()

        self.tool = []


class ImageBrowserUi(palette.ToolDefinition):
    id = "zoo.imagebrowserui"
    creator = "Keen Foong"
    tags = ["hotkey", "hotkeys", "editor"]
    uiData = {"icon": "menu_keyboard",
              "tooltip": "Image browser ui",
              "label": "Hotkey Editor",
              "color": "",
              "backgroundColor": "",
              "multipleTools": False,
              "frameless": {"frameless": True, "force": False},
              "dock": {"dockable": True, "tabToControl": ("AttributeEditor", -1), "floating": False}
              }

    def execute(self, *args, **kwargs):
        return self.executeFrameless(*args, **kwargs)

    def runTool(self, framelessActive=True, toolArgs=None):
        from zoo.apps.imagebrowserui import run
        return run.launch(framelessChecked=framelessActive)

    def setFrameless(self, tool, frameless):
        if tool is not None:
            tool.setFrameless(frameless)

    def setStyleSheet(self, style):
        for t in self.tool:
            t['tool'].setWindowStyleSheet(style)

    def toolClosed(self, tool):
        """ Clean up after tool has closed

        :param tool:
        :return:
        """
        if tool in self.tool:
            self.tool.remove(tool)

    def teardown(self):
        for t in self.tool:
            if t:
                t['tool'].close()

        self.tool = []


class TriggersUi(palette.ToolDefinition):
    id = "zoo.triggersui"
    creator = "Dave Sparrow"
    tags = ["trigger", "triggers"]
    uiData = {"icon": "menu_rayGun",
              "tooltip": "Loads Triggers UI",
              "label": "Triggers",
              "color": "",
              "backgroundColor": "",
              "multipleTools": False,
              "frameless": {"frameless": True, "force": False},
              "dock": {"dockable": True, "tabToControl": ("AttributeEditor", -1), "floating": False}
              }

    def execute(self, *args, **kwargs):
        return self.executeFrameless(*args, **kwargs)

    def runTool(self, framelessActive=True, toolArgs=None):
        from zoo.apps.triggersui import run
        return run.launch(framelessChecked=framelessActive)

    def setFrameless(self, tool, frameless):
        if tool is not None:
            tool.setFrameless(frameless)

    def setStyleSheet(self, style):
        for t in self.tool:
            t['tool'].setWindowStyleSheet(style)

    def toolClosed(self, tool):
        """ Clean up after tool has closed

        :param tool:
        :return:
        """
        self.tool.remove(tool)

    def teardown(self):
        for t in self.tool:
            if t:
                try:
                    t['tool'].close()
                except RuntimeError:
                    pass

        self.tool = []


class PreferencesUi(palette.ToolDefinition):
    id = "zoo.preferencesui"
    creator = "Dave Sparrow"
    tags = ["preference"]
    uiData = {"icon": "menu_zoo_preferences",
              "tooltip": "Loads the zootools preferences GUI",
              "label": "Preferences",
              "color": "",
              "backgroundColor": "",
              "multipleTools": False,
              "frameless": {"frameless": True, "force": False},
              "dock": {"dockable": True, "tabToControl": ("AttributeEditor", -1), "floating": False}
              }

    def execute(self, *args, **kwargs):
        return self.executeFrameless(*args, **kwargs)

    def runTool(self, framelessActive=True, toolArgs=None):
        from zoo.apps.preferencesui import run
        return run.launch(framelessChecked=framelessActive)

    def setFrameless(self, tool, frameless):
        if tool is not None:
            tool.setFrameless(frameless)

    def setStyleSheet(self, style):
        for t in self.tool:
            t['tool'].setWindowStyleSheet(style)

    def toolClosed(self, tool):
        """ Clean up after tool has closed

        :param tool:
        :return:
        """
        self.tool.remove(tool)

    def teardown(self):
        for t in self.tool:
            if t:
                try:
                    t['tool'].close()
                except RuntimeError:
                    pass

        self.tool = []


class ToolsetsUi(palette.ToolDefinition):
    id = "zoo.toolsets"
    creator = "Keen Foong"
    tags = ["tools", "toolsets"]
    uiData = {"icon": "menu_toolsets",
              "tooltip": "Toolsets Window for tool browsing",
              "label": "Toolsets",
              "color": "",
              "backgroundColor": "",
              "multipleTools": True,
              "frameless": {"frameless": True, "force": False},
              "dock": {"dockable": True, "tabToControl": ("AttributeEditor", -1), "floating": False}
              }

    def execute(self, *args, **kwargs):
        return self.executeFrameless(*args, **kwargs)

    def runTool(self, framelessActive=True, toolArgs=None):
        toolArgs = {} or toolArgs

        from zoo.apps.toolsetsui import run
        return run.launch(framelessChecked=framelessActive, toolArgs=toolArgs)

    def setFrameless(self, tool, frameless):
        if tool is not None:
            tool.setFrameless(frameless)

    def setStyleSheet(self, style):
        for t in self.tool:
            t['tool'].setWindowStyleSheet(style)

    def toolClosed(self, tool):
        """ Clean up after tool has closed

        :param tool:
        :return:
        """
        if tool in self.tool:
            self.tool.remove(tool)

    def teardown(self):
        from zoo.apps.toolsetsui import toolsetui
        toolsetuis = list(toolsetui.toolsetUis())
        for t in toolsetuis:
            t.close()

        self.tool = []


class UnitestUI(palette.ToolDefinition):
    id = "zoo.dev.unitest.ui"
    creator = "David Sparrow"
    tags = ["dev", "unitest"]
    uiData = {"icon": "menu_test",
              "tooltip": "Zootools unitesting GUI",
              "label": "Unittest",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        from unittestui import unittestui
        try:
            for tool in self.tool:
                tool.close()
        except (AttributeError, TypeError, RuntimeError):
            pass
        self.tool.append(unittestui.show())

    def teardown(self):
        if self.tool:
            for tool in self.tool:
                tool.close()


"""
SHELF ICONS
"""


class ModelingIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.modeling"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "modelingMenu_shlf",
              "tooltip": "Modeling And Object Tools",
              "label": "Modeling And Object Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass


class AnimationIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.animation"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "animationMenu_shlf",
              "tooltip": "Animation Tools",
              "label": "Animation Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass


class RiggingIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.rigging"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "riggingMenu_shlf",
              "tooltip": "Rigging Tools",
              "label": "Rigging Tools",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        name = kwargs["variant"]
        exe = executor.Executor()
        if name == "match_curves":
            exe.execute("zoo.maya.curves.match")


class ShaderIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.shader"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "shaderMenu_shlf",
              "tooltip": "Shader Tools",
              "label": "Shader Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass


class UvIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.uv"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "uvMenu_shlf",
              "tooltip": "UV Tools",
              "label": "UV Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass


class CameraIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.camera"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "cameraMenu_shlf",
              "tooltip": "Camera Tools",
              "label": "Camera Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass


class UtilitiesIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.utility"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "utilsMenu_shlf",
              "tooltip": "Utilities",
              "label": "Utilities Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass


class DevIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.dev"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "devMenu_shlf",
              "tooltip": "Developer Tools",
              "label": "Developer Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        name = kwargs["variant"]
        if name == "zoo_unittest":
            self.manager.executePluginById("zoo.dev.unitest.ui")
        elif name == "reload":
            self.manager.executePluginById("zoo.reload")
        elif name == "shutdown":
            self.manager.executePluginById("zoo.shutdown")
        elif name == "logging":
            pass


class HelpIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.help"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "helpMenu_shlf",
              "tooltip": "Help Menu",
              "label": "Help Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        name = kwargs["variant"]
        if name == "create3dcharacters":
            import webbrowser
            webbrowser.open('http://create3dcharacters.com')
        elif name == "zooToolsHelpContents":
            import webbrowser
            webbrowser.open('https://create3dcharacters.com/maya-zoo-tools-tutorials-main')
        elif name == "zooToolsInstallUpdate":
            import webbrowser
            webbrowser.open('https://create3dcharacters.com/maya-zoo-tools-pro-installer')
        elif name == "zooChangelog":
            import webbrowser
            webbrowser.open('https://create3dcharacters.com/maya-zoo-tools-pro-changelog')
        elif name == "zooIssuesFixes":
            import webbrowser
            webbrowser.open('https://create3dcharacters.com/maya-zoo-tools-pro-known-issues')
        elif name == "coursesByOrder":
            import webbrowser
            webbrowser.open('https://create3dcharacters.com/package-courses')
        elif name == "coursesByPopularity":
            import webbrowser
            webbrowser.open('https://create3dcharacters.com/package-by-popularity')
        elif name == "coursesByDateAdded":
            import webbrowser
            webbrowser.open('https://create3dcharacters.com/package-by-date-added')
        elif name == "intermediateCourse":
            import webbrowser
            webbrowser.open('https://create3dcharacters.com/package-maya-generalist-intermediate')
        elif name == "advancedCourse":
            import webbrowser
            webbrowser.open('https://create3dcharacters.com/package-maya-generalist-advanced')
        elif name == "mayaHotkeyList":
            import webbrowser
            webbrowser.open('https://create3dcharacters.com/maya-hotkeys-2017')

