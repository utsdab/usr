from maya import cmds
from zoo.apps.toolpalette import palette
from zoo.libs.command import executor


class ImageBrowserUi(palette.ToolDefinition):
    id = "zoo.browserui"
    creator = "Keen Foong"
    tags = ["image", "browser", "ui"]
    uiData = {"icon": "menu_cube",
              "tooltip": "Image Browser",
              "label": "Image Browser",
              "color": "",
              "backgroundColor": "",
              "multipleTools": False,
              "frameless": {"frameless": True, "force": False},
              "dock": {"dockable": True, "tabToControl": ("AttributeEditor", -1), "floating": False}
              }

    def execute(self, *args, **kwargs):
        if len(args) > 0:
            browserType = args[0]
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
        self.tool.remove(tool)

    def teardown(self):
        for t in self.tool:
            if t:
                try:
                    t['tool'].close()
                except RuntimeError:
                    pass

        self.tool = []
