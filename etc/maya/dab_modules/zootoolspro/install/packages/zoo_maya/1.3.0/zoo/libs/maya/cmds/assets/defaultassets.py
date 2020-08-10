import os

from maya import cmds
import maya.api.OpenMaya as om2

from zoo.libs.utils import filesystem
from zoo.libs.maya.cmds.assets import assetsimportexport
from zoo.libs.maya.cmds.cameras import cameras
from zoo.libs.maya.cmds.renderer import exportabcshaderlights
from zoo.libs.maya.cmds.lighting import renderertransferlights
from zoo.libs.maya.cmds.display import viewportmodes
from zoo.libs.maya.cmds.lighting.renderertransferlights import LIGHTVISIBILITY, IBLTEXTURE
from zoo.libs.maya.cmds.shaders import shdmultconstants, shadermultirenderer as shdmult
from zoo.libs.maya.cmds.rig import controls
from zoo.libs.maya.cmds.renderer import multirenderersettings

# ---------------------------
# Internal Asset Folders
# ---------------------------
PREFERENCES_FOLDER_NAME = "preferences"  # preferences directory
ASSETS_FOLDER_NAME = "assets"  # main assets dir under the internal preferences folder
CONTROL_SHAPES_FOLDER_NAME = "control_shapes"  # the name of the control shapes folder under assets
MODEL_ASSETS_FOLDER_NAME = "model_assets"  # the name of the model assets folder under assets
HDR_SKYDOMES_FOLDER_NAME = "light_suite_ibl_skydomes"
LIGHT_PRESETS_FOLDER_NAME = "light_suite_light_presets"
SHADERS_FOLDER_NAME = "shaders"
# ---------------------------
# Paths To Asset Folders
# ---------------------------
currentPath = os.path.abspath(__file__)
packagePath = filesystem.upDirectory(currentPath, depth=7)  # TODO path is relative, will be a better way
CONTROL_SHAPES_PATH = os.path.join(packagePath, "preferences", ASSETS_FOLDER_NAME, CONTROL_SHAPES_FOLDER_NAME)
MODEL_ASSETS_PATH = os.path.join(packagePath, "preferences", ASSETS_FOLDER_NAME, MODEL_ASSETS_FOLDER_NAME)
HDR_SKYDOMES_PATH = os.path.join(packagePath, "preferences", ASSETS_FOLDER_NAME, HDR_SKYDOMES_FOLDER_NAME)
LIGHT_PRESETS_PATH = os.path.join(packagePath, "preferences", ASSETS_FOLDER_NAME, LIGHT_PRESETS_FOLDER_NAME)
SHADERS_PATH = os.path.join(packagePath, "preferences", ASSETS_FOLDER_NAME, SHADERS_FOLDER_NAME)
# ---------------------------
# Default Asset Names. Usually file names.
# ---------------------------
CONTROL_CIRCLE = "circle"
CONTROL_CUBE = "cube"
CONTROL_SPHERE = "sphere"

ASSET_SHADER_BOT = "shaderBot.zooScene"
ASSET_LIGHT_SCENE = "emptyA.zooScene"
ASSET_CYC_GREY_SCENE = "bgCycG.zooScene"
ASSET_CYC_DARK_SCENE = "bgCycDrk.zooScene"
ASSET_MACBETH_BALLS = "mcbthChart.zooScene"

LIGHT_PRESET_ASSET_DEFAULT = "aDflt.zooScene"
LIGHT_PRESET_THREE_POINT = "softThree.zooScene"
LIGHT_PRESET_THREE_POINT_DARK = "soft3Drk.zooScene"
LIGHT_PRESET_F_PUMPS = "fPumps.zooScene"
LIGHT_PRESET_WINTER_F = "wForest.zooScene"
LIGHT_PRESET_RED_AQUA_RIM = "redAqua.zooScene"
LIGHT_PRESET_SOFT_TOP = "sTpCircle.zooScene"
LIGHT_PRESET_SOFT_TOP_RIM = "pure_softTop_softBoxBehind.zooScene"

HDR_F_PUMPS = "factPumps.hdr"
HDR_F_PUMPS_BW = "factPumps_g.hdr"
HDR_WINTER_F = "wForest.hdr"

SHADERS_SKIN_DARK_BACKLIT = "skBnDrkB.zooScene"
SHADERS_DARK_BACKGROUND = "dkMtBg.zooScene"

# ---------------------------
# Camera Types
# ---------------------------
CAMTYPE_DEFAULT = "default"
CAMTYPE_HDR = "hdr"
CAMTYPE_CONTROL = "control"
# ---------------------------
# Default Renderer
# ---------------------------
RENDERER = "Arnold"  # Not used by UIs, just for testing
# ---------------------------
# Full Asset Paths
# ---------------------------
DEFAULT_LIGHT_PRESET_PATH = os.path.join(LIGHT_PRESETS_PATH, LIGHT_PRESET_F_PUMPS)  # bw factory pumps
WINTER_F_LIGHT_PRESET_PATH = os.path.join(LIGHT_PRESETS_PATH, LIGHT_PRESET_WINTER_F)  # Default IBL no changes
ASSET_LIGHTPRESET_PATH = os.path.join(LIGHT_PRESETS_PATH, LIGHT_PRESET_ASSET_DEFAULT)  # rim studio
THREE_POINT_LIGHT_PRESET_PATH = os.path.join(LIGHT_PRESETS_PATH, LIGHT_PRESET_THREE_POINT)  # three point soft
THREE_POINT_DRK_LIGHT_PRESET_PATH = os.path.join(LIGHT_PRESETS_PATH, LIGHT_PRESET_THREE_POINT_DARK)  # three point dark
RED_AQUA_RIM_LIGHT_PRESET_PATH = os.path.join(LIGHT_PRESETS_PATH, LIGHT_PRESET_RED_AQUA_RIM)  # three point soft
SOFT_TOP_LIGHT_PRESET_PATH = os.path.join(LIGHT_PRESETS_PATH, LIGHT_PRESET_SOFT_TOP)  # three point soft
SOFT_TOP_RIM_LIGHT_PRESET_PATH = os.path.join(LIGHT_PRESETS_PATH, LIGHT_PRESET_SOFT_TOP_RIM)  # three point soft

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------


def importZooSceneDefault(fullPath, renderer, replaceByType=False):
    """Imports a zoo scene file with default settings for the current renderer

    :param fullPath: The fullpath to the .zooScene file
    :type fullPath: str
    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param replaceByType: Will replace assets by type and delete previous shaders of the same name
    :type replaceByType: str
    """
    assetsimportexport.importZooSceneAsAsset(fullPath,
                                             renderer,
                                             replaceAssets=replaceByType,
                                             importAbc=True,
                                             importShaders=True,
                                             importLights=True,
                                             replaceShaders=replaceByType,
                                             addShaderSuffix=True,
                                             importSubDInfo=True,
                                             replaceRoots=True,
                                             turnStart=0,
                                             turnEnd=0,
                                             turnOffset=0.0,
                                             loopAbc=False,
                                             replaceByType=replaceByType,
                                             rotYOffset=0,
                                             scaleOffset=1.0)


def renderStatsAttrs(geoShape, castsShadows=None, receiveShadows=True, holdOut=None, motionBlur=None,
                     primaryVisibility=None, smoothShading=None, visibleInReflections=None, visibleInRefractions=None,
                     doubleSided=None, opposite=None):
    """Sets attribute values for the render stats on an object's shape node

    :param geoShape: A geometry shape node name
    :type geoShape: list(str)
    """
    if castsShadows is not None:
        cmds.setAttr("{}.castsShadows".format(geoShape), castsShadows)
    if receiveShadows is not None:
        cmds.setAttr("{}.receiveShadows".format(geoShape), receiveShadows)
    if holdOut is not None:
        cmds.setAttr("{}.holdOut".format(geoShape), holdOut)
    if motionBlur is not None:
        cmds.setAttr("{}.motionBlur".format(geoShape), motionBlur)
    if primaryVisibility is not None:
        cmds.setAttr("{}.primaryVisibility".format(geoShape), primaryVisibility)
    if smoothShading is not None:
        cmds.setAttr("{}.smoothShading".format(geoShape), smoothShading)
    if visibleInReflections is not None:
        cmds.setAttr("{}.visibleInReflections".format(geoShape), visibleInReflections)
    if visibleInRefractions is not None:
        cmds.setAttr("{}.visibleInRefractions".format(geoShape), visibleInRefractions)
    if doubleSided is not None:
        cmds.setAttr("{}.doubleSided".format(geoShape), doubleSided)
    if opposite is not None:
        cmds.setAttr("{}.opposite".format(geoShape), opposite)


def renderStatsAttrsList(geoShapeList, castsShadows=None, receiveShadows=True, holdOut=None, motionBlur=None,
                         primaryVisibility=None, smoothShading=None, visibleInReflections=None,
                         visibleInRefractions=None,
                         doubleSided=None, opposite=None):
    """Sets attribute values for the render stats on an object's shape node

    :param geoShapeList: A list of geometry shape nodes
    :type geoShapeList: list(str)
    """
    for geoShape in geoShapeList:
        renderStatsAttrs(geoShape, castsShadows=castsShadows, receiveShadows=receiveShadows, holdOut=holdOut,
                         motionBlur=motionBlur, primaryVisibility=primaryVisibility, smoothShading=smoothShading,
                         visibleInReflections=visibleInReflections, visibleInRefractions=visibleInRefractions,
                         doubleSided=doubleSided, opposite=opposite)


def createDefaultCamera(type=CAMTYPE_DEFAULT):
    """Creates a default camera for scenes based on the type

    type:

        CAMTYPE_DEFAULT = "default"
        CAMTYPE_HDR = "hdr"
        CAMTYPE_CONTROL = "control"

    :param type: The type of asset the camera is for, "default", "hdr", "control"
    :type type: str
    :return cameraTransform: The camera transform node name
    :rtype cameraTransform: str
    :return cameraShape: The camera shape node name
    :rtype cameraShape: str
    """
    # check camera to see if it exists
    cameraTransform, cameraShape = cameras.createCameraZxy(message=True)
    if type == CAMTYPE_DEFAULT:
        cmds.move(0, 75, 700, cameraTransform, absolute=True)
        cmds.setAttr("{}.focalLength".format(cameraShape), 80)
        cmds.setAttr("{}.centerOfInterest".format(cameraShape), 720)
    elif type == CAMTYPE_HDR:
        cmds.setAttr("{}.focalLength".format(cameraShape), 12)
    elif type == CAMTYPE_CONTROL:
        cmds.setAttr("{}.orthographic".format(cameraShape), 1)
        cmds.setAttr("{}.orthographicWidth".format(cameraShape), 2.5)
        cmds.setAttr("{}.rotateX".format(cameraTransform), -45.0)
        cmds.setAttr("{}.rotateY".format(cameraTransform), 45.0)
        cmds.move(0, 0, 4, cameraTransform, objectSpace=True)
    return cameraTransform, cameraShape


def setCameraResolution(cameraShape="cameraShape1", width=520, height=520, clipPlanes=(0.9, 5000.0), antiAlias=True,
                        grid=False, setRes=True):
    """Sets the camera film gate and scene resolution (render globals render image width height)

    Also sets up the display of the camera clip planes and anti aliasing

    :param cameraShape: The name of the camera shape node
    :type cameraShape: str
    :param width: The width in pixels of the render globals render image size
    :type width: int
    :param height: The height in pixels of the render globals render image size
    :type height: int
    :param clipPlanes: The viewport display clipping planes
    :type clipPlanes: tuple(int)
    :param antiAlias: Anti alias the viewport?
    :type antiAlias: bool
    :param grid: Show the grid in the viewport?
    :type grid: bool
    """
    # Set Render Globals -----------------------------
    if setRes:
        cameras.setGlobalsWidthHeight(width, height)
    if cameraShape:
        # Set Camera -----------------------------
        cameras.setZooResolutionGate(cameraShape, resolutionGate=True)
        cameras.setCamFitResGate(cameraShape, fitResolutionGate=cameras.CAM_FIT_RES_OVERSCAN)
        # Look Through ----------------------------
        camTransform = cmds.listRelatives(cameraShape, parent=True)[0]
        cmds.lookThru(camTransform)
        if not grid:  # Then hide the grid
            panel = viewportmodes.panelUnderPointerOrFocus(viewport3d=True, message=False)
            cmds.modelEditor(panel, edit=1, grid=False)
    # Set Clip Planes Anti Aliasing -----------------------------------------
    cameras.setCurrCamClipPlanes(clipPlanes[0], clipPlanes[1])
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", antiAlias)  # Anti-aliasing on


def importLightPreset(renderer=RENDERER, lightPresetPath=DEFAULT_LIGHT_PRESET_PATH, hdrImage=HDR_F_PUMPS_BW,
                      showIbl=False):
    """Import a light preset from a folder path and image with basic kwargs.

    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param lightPresetPath: The full path to the folder of the light presets
    :type lightPresetPath: str
    :param hdrImage: The HDR Image name with extension
    :type hdrImage: str
    :param showIbl: Render the Skydome in the background?
    :type showIbl: bool
    """
    exportabcshaderlights.importLightPreset(lightPresetPath, renderer, True)
    allIblLightShapes = renderertransferlights.getIBLLightsInScene(renderer)
    if allIblLightShapes:  # check if IBL exists to apply the bgVisibility setting from the GUI
        lightDictAttributes = renderertransferlights.getSkydomeLightDictAttributes()  # dict with keys/empty values
        lightDictAttributes[LIGHTVISIBILITY] = showIbl
        if hdrImage:  # override with internal HDR lores image
            lightDictAttributes[IBLTEXTURE] = os.path.join(HDR_SKYDOMES_PATH, hdrImage)  # Low internal path
        renderertransferlights.setIblAttrAuto(lightDictAttributes, renderer, message=False)


# ---------------------------
# BUILD SCENE - MAIN FUNCTIONS
# ---------------------------


def buildDefaultLightSceneCyc(renderer=RENDERER, lightPresetPath=DEFAULT_LIGHT_PRESET_PATH, message=True):
    """Builds a default Light Presets scene for thumbnail rendering

    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param lightPresetPath: The full path to the .zooScene file
    :type lightPresetPath:
    :param message: Report messages to the user?
    :type message: bool
    """
    # Import Assets Settings -----------------------------
    importZooSceneDefault(os.path.join(MODEL_ASSETS_PATH, ASSET_SHADER_BOT), renderer)  # Shader Bot
    importZooSceneDefault(os.path.join(MODEL_ASSETS_PATH, ASSET_LIGHT_SCENE), renderer)  # Light Scene
    # Render Stat Settings -----------------------------
    renderStatsAttrs("lineDontRenderShape", castsShadows=False, receiveShadows=False, holdOut=False, motionBlur=False,
                     primaryVisibility=False, smoothShading=False, visibleInReflections=False,
                     visibleInRefractions=False, doubleSided=False, opposite=False)
    sphereList = ["ball_reflect_geoShape", "ball_greyMatte_geoShape", "ball_greyPlastic_geoShape",
                  "ball_greyPlastic_geo1Shape"]
    renderStatsAttrsList(sphereList, castsShadows=False, receiveShadows=False)
    renderStatsAttrs("lowerFloor_geoShape", primaryVisibility=False)
    renderStatsAttrs("cyc_geoShape", castsShadows=False)
    # Optional Light Preset -----------------------------
    if lightPresetPath:  # create a light preset and change the skydome to off
        importLightPreset(renderer=renderer, lightPresetPath=DEFAULT_LIGHT_PRESET_PATH, hdrImage=HDR_F_PUMPS_BW)
    # Set Camera, Resolution and Globals -----------------------------
    setCameraResolution()
    # Set renderer defaults -----------------------
    multirenderersettings.setDefaultRenderSettings(renderer=renderer)
    # Message -----------------------------
    if message:
        om2.MGlobal.displayInfo("Success: Light Presets render thumbnail scene created")


def buildDefaultHDRIScene(renderer=RENDERER, message=True):
    """Builds a default HDRI Skydome scene for thumbnail rendering

    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param message: Report messages to the user?
    :type message: bool
    """
    # Import light Preset with HDR
    skydomeName = "skydomeLight_{}".format(shdmultconstants.SHADER_SUFFIX_DICT[renderer])
    renderertransferlights.createSkydomeLightRenderer(skydomeName, renderer, warningState=False, cleanup=False,
                                                      setZXY=True)
    # Set Camera, Resolution and Globals -----------------------------
    cameraTransform, cameraShape = createDefaultCamera(type=CAMTYPE_HDR)
    cmds.setAttr("{}.rotateX".format(cameraTransform), 25)
    setCameraResolution(cameraShape=cameraShape)
    cameras.openTearOffCam(camera='persp')
    # Select Skydome ------------------
    cmds.select(skydomeName, replace=True)
    # Set renderer defaults -----------------------
    multirenderersettings.setDefaultRenderSettings(renderer=renderer)
    # Message -----------------------------
    if message:
        om2.MGlobal.displayInfo("Success: HDR Skydome render thumbnail scene created")


def buildDefaultAssetsSceneCyc(renderer=RENDERER,
                               assetDirPath=MODEL_ASSETS_PATH,
                               assetZooScene=ASSET_CYC_DARK_SCENE,
                               lightPresetPath=ASSET_LIGHTPRESET_PATH,
                               hdrImage=HDR_F_PUMPS_BW,
                               buildCamera=True,
                               buildBot=False,
                               setRes=True,
                               replaceByType=False,
                               setDefaultRenderSet=True,
                               darkShader=True,
                               message=True):
    """Builds a default Model Assets scene for thumbnail rendering

    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param message: Report messages to the user?
    :type message: bool
    """
    if assetZooScene:
        # Import Cyc
        importZooSceneDefault(os.path.join(assetDirPath, assetZooScene), renderer, replaceByType=replaceByType)
        if darkShader:
            # Add dark shader -----------------------------
            zooScenePath = os.path.join(SHADERS_PATH, SHADERS_DARK_BACKGROUND)
            shaderName = "cycStudio_{}".format(shdmultconstants.SHADER_SUFFIX_DICT[renderer])
            shaderType = shdmult.RENDERERSHADERS[renderer][0]
            exportabcshaderlights.setShaderAttrsZooScene(zooScenePath,
                                                         shaderName,
                                                         shaderType,
                                                         renameToZooName=False,
                                                         message=message)
    if buildBot:  # Shader Bot
        importZooSceneDefault(os.path.join(MODEL_ASSETS_PATH, ASSET_SHADER_BOT), renderer, replaceByType=replaceByType)
    if lightPresetPath:  # Light Preset
        importLightPreset(renderer=renderer, lightPresetPath=lightPresetPath, hdrImage=hdrImage)
    # Set Camera, Resolution and Globals -----------------------------
    if buildCamera:
        cameraTransform, cameraShape = createDefaultCamera(type=CAMTYPE_DEFAULT)
        setCameraResolution(cameraShape=cameraShape, setRes=setRes)
    if setDefaultRenderSet:
        # Set renderer defaults -----------------------
        multirenderersettings.setDefaultRenderSettings(renderer=renderer)
    # Message -----------------------------
    if message:
        om2.MGlobal.displayInfo("Success: Asset render thumbnail scene created")


def buildDefaultShaderSceneCyc(renderer=RENDERER, message=True):
    """Builds a default Shader Preset scene for thumbnail rendering

    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param message: Report messages to the user?
    :type message: bool
    """
    # Import Cyc and Shader Bot -----------------------------
    importZooSceneDefault(os.path.join(MODEL_ASSETS_PATH, ASSET_CYC_GREY_SCENE), renderer)  # Cyc Grey
    importZooSceneDefault(os.path.join(MODEL_ASSETS_PATH, ASSET_SHADER_BOT), renderer)  # Shader Bot
    # Light Preset -----------------------------
    importLightPreset(renderer=renderer, lightPresetPath=DEFAULT_LIGHT_PRESET_PATH, hdrImage=HDR_F_PUMPS_BW)
    # Set Camera, Resolution and Globals -----------------------------
    cameraTransform, cameraShape = createDefaultCamera(type=CAMTYPE_DEFAULT)
    setCameraResolution(cameraShape=cameraShape)
    # Add a shader on shader bot -----------------------------
    zooScenePath = os.path.join(SHADERS_PATH, SHADERS_SKIN_DARK_BACKLIT)
    shaderName = "greyClearCoatSubtle_{}".format(shdmultconstants.SHADER_SUFFIX_DICT[renderer])
    shaderType = shdmult.RENDERERSHADERS[renderer][0]
    exportabcshaderlights.setShaderAttrsZooScene(zooScenePath,
                                                 shaderName,
                                                 shaderType,
                                                 renameToZooName=False,
                                                 message=message)
    # Move shader bot framing -----------------------------
    cmds.move(-4.0, 0.0, 0.0, "shaderBot_package_grp", absolute=True)
    # Set renderer defaults -----------------------
    multirenderersettings.setDefaultRenderSettings(renderer=renderer)
    # Message -----------------------------
    if message:
        om2.MGlobal.displayInfo("Success: Shader Preset render thumbnail scene created")


def buildDefaultControlsScene(message=True):
    """Builds a default Control Shape scene for thumbnail rendering

    :param message: Report messages to the user?
    :type message: bool
    """
    # Build a Control Circle
    controls.buildControlsGUI(buildType=controls.CONTROL_BUILD_TYPE_LIST[1],
                              folderpath=CONTROL_SHAPES_PATH,
                              designName=CONTROL_CIRCLE,
                              rotateOffset=(0, -90, 0),
                              scale=(1.0, 1.0, 1.0),
                              children=False,
                              rgbColor=(0.16, 0.3, 0.875),
                              postSelectControls=True,
                              trackScale=True,
                              lineWidth=6,
                              grp=True,
                              freezeJnts=False)
    # Set Camera, Resolution and Globals -----------------------------
    cameraTransform, cameraShape = createDefaultCamera(type=CAMTYPE_CONTROL)
    setCameraResolution(cameraShape=cameraShape)
    # Message -----------------------------
    if message:
        om2.MGlobal.displayInfo("Success: Control Shape thumbnail Scene Created")
