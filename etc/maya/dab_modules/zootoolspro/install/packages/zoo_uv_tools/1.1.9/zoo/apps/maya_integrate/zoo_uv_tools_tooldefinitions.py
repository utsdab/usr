from zoo.apps.toolpalette import palette


class UVIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.uv"
    creator = "Keen Foong"
    tags = ["shelf", "icon"]
    uiData = {"icon": "uvMenu_shlf",
              "tooltip": "Uv Tools",
              "label": "Uv Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass