from zoo.apps.toolpalette import palette


class ShaderIconsShelf(palette.ToolDefinition):
    id = "zoo.shelf.shader"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "shaderMenu_shlf",
              "tooltip": "Shader Tools",
              "label": "Shader Tools",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass