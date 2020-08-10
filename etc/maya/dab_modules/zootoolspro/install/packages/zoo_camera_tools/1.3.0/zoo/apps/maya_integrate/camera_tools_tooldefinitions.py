from zoo.apps.toolpalette import palette
from zoo.libs.maya.cmds.cameras import cameras


class CameraIconsShelf(palette.ToolDefinition):
    id = "zoo.shelf.camera"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "cameraMenu_shlf",
              "tooltip": "Camera Tools",
              "label": "Camera Tools",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):

        name = kwargs["variant"]
        if name == "create_camera":
            cameras.createCameraZxy(message=True)
        elif name == "set_display_display_camera":
            cameras.setDefaultDisplayAndCameras()
        elif name == "zoo_toggle_res_gate":
            cameras.toggleCamResGate()
        elif name == "match_gate_ratios":
            camShape = cameras.getFocusCameraShape(message=False)
            cameras.matchResolutionFilmGate(camShape)
        elif name == "toggle_overscan":
            cameras.toggleOverscan()
        elif name == "camclip_near":
            cameras.setCurrCamClipPlanes(0.09, 500.0)
        elif name == "camclip_medium":
            cameras.setCurrCamClipPlanes(0.9, 5000.0)
        elif name == "camclip_far":
            cameras.setCurrCamClipPlanes(9.0, 50000.0)
        elif name == "set_resolution_1080p":
            cameras.setGlobalsWidthHeight(1920, 1080, matchCurrentCam=True)
        elif name == "set_resolution_720p":
            cameras.setGlobalsWidthHeight(1280, 720, matchCurrentCam=True)
        elif name == "set_resolution_540p":
            cameras.setGlobalsWidthHeight(960, 540, matchCurrentCam=True)
        elif name == "set_resolution_true4k":
            cameras.setGlobalsWidthHeight(4096, 2160, matchCurrentCam=True)
        elif name == "set_resolution_ultraHD":
            cameras.setGlobalsWidthHeight(3840, 2160, matchCurrentCam=True)
        elif name == "set_resolution_true2k":
            cameras.setGlobalsWidthHeight(2048, 1080, matchCurrentCam=True)
        elif name == "set_resolution_ultraHD":
            cameras.setGlobalsWidthHeight(3840, 2160, matchCurrentCam=True)
        elif name == "set_resolution_academy":
            cameras.setGlobalsWidthHeight(1920, 1038, matchCurrentCam=True)
        elif name == "set_resolution_cinemascope":
            cameras.setGlobalsWidthHeight(1920, 817, matchCurrentCam=True)
        elif name == "set_resolution_square":
            cameras.setGlobalsWidthHeight(1080, 1080, matchCurrentCam=True)
        elif name == "set_resolution_square_540":
            cameras.setGlobalsWidthHeight(540, 540, matchCurrentCam=True)
        elif name == "tear_off_persp":
            cameras.openTearOffCam(camera='persp')
        elif name == "tear_off_camera1":
            cameras.openTearOffCam(camera='camera1')
