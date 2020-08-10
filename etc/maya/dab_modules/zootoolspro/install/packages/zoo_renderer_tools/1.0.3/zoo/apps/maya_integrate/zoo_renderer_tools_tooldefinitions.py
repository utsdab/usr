from zoo.apps.toolpalette import palette


class RendererIconsShelf(palette.ToolDefinition):
    id = "zoo.shelf.rendering"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "renderingMenu_shlf",
              "tooltip": "Renderer Tools",
              "label": "Renderer Tools",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        name = kwargs["variant"]
        from zoo.libs.maya.cmds.renderer import multirenderersettings
        if name == "zoo_set_default_render_settings":
            multirenderersettings.setDefaultRenderSettingsAuto()
        elif name == "zoo_open_render_view":
            multirenderersettings.openRenderviewAuto()
        elif name == "zoo_open_render_view_ipr":
            multirenderersettings.openRenderviewAuto(ipr=True)
        elif name == "zoo_open_render_view_final":
            multirenderersettings.openRenderviewAuto(final=True)
        elif name == "zoo_set_arnold_renderer":
            multirenderersettings.changeRenderer("Arnold")
        elif name == "zoo_set_redshift_renderer":
            multirenderersettings.changeRenderer("Redshift")
        elif name == "zoo_set_renderman_renderer":
            multirenderersettings.changeRenderer("Renderman")
