from zoo.apps.toolpalette import palette

class LightIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.light"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "lightMenu_shlf",
              "tooltip": "Light Tools",
              "label": "Light Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass
