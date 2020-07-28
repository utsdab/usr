from zoo.apps.toolpalette import palette


class DynamicsIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.dynamics"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "fxDynamicsMenu_shlf",
              "tooltip": "Dynamics Tools",
              "label": "Dynamics Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass