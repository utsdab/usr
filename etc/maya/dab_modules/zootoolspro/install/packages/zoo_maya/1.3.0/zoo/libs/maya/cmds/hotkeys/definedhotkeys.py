"""
Zoo Python Hotkeys
"""
import zoo.libs.maya.cmds.shaders.shaderutils

"""
Create Functions
"""


def createCamRooXzy():
    """Creates a camera and changes it's rotate order to zxy"""
    from zoo.libs.maya.cmds.cameras import cameras
    cameras.createCameraZxy()


def createCubeMatch():
    """Creates a cube and will match it to the selected object if an object is selected"""
    from zoo.libs.maya.cmds.modeling import create
    create.createPrimitiveAndMatch(cube=True, sphere=False, cylinder=False, plane=False)


def createCylinderMatch():
    """Creates a cylinder and will match it to the selected object if an object is selected"""
    from zoo.libs.maya.cmds.modeling import create
    create.createPrimitiveAndMatch(cube=False, sphere=False, cylinder=True, plane=False)


def createPlaneMatch():
    """Creates a plane and will match it to the selected object if an object is selected"""
    from zoo.libs.maya.cmds.modeling import create
    create.createPrimitiveAndMatch(cube=False, sphere=False, cylinder=False, plane=True)


def createSphereMatch():
    """Creates a plane and will match it to the selected object if an object is selected"""
    from zoo.libs.maya.cmds.modeling import create
    create.createPrimitiveAndMatch(cube=False, sphere=True, cylinder=False, plane=False)


"""
Settings
"""


def hotkeySetToggle():
    """Toggles through all the zoo hotkey sets and user sets"""
    from zoo.apps.hotkeyeditor.core import keysets
    keysets.KeySetManager().nextKeySet()


def reloadZooTools():
    """Reloads Zoo Tools for developers"""
    from zoo.apps.toolpalette import run
    run.show().executePluginById("zoo.reload")


"""
Objects
"""


def alignSelection():
    """Match Align based on selection (rotation and translation)

    Matches to the first selected object, all other objects are matched to the first in the selection
    """
    from zoo.libs.maya.cmds.objutils import alignutils
    alignutils.matchObjTransRotSelection()


"""
Zoo Windows / Menu Items
"""


def windowHiveArtistUI():
    """Opens the Hive Artist UI Window """
    from zoo.apps.toolpalette import run
    run.show().executePluginById("zoo.hive.artistui")


def windowHiveArtistUI():
    """Opens the Hive Artist UI Window """
    from zoo.apps.toolpalette import run
    run.show().executePluginById("zoo.hive.artistui")


def winHotkeyManager():
    """Opens the Hotkey Manager Window """
    from zoo.apps.toolpalette import run
    run.show().executePluginById("zoo.hotkeyeditorui")


def winShaderManager():
    """Opens the Shader Manager Window """
    # TODO
    pass


def mirrorInstanceGroupWorldX():
    """mirror instances an object across world X"""
    from zoo.libs.maya.cmds.modeling import mirror
    mirror.instanceMirror()


def mirrorPolygonPlus():
    """Mirrors polygon with special zero edge or vert selection, plus smooth all edges and delete history"""
    from zoo.libs.maya.cmds.modeling import mirror
    mirror.mirrorPolyEdgeToZero(smoothEdges=True, deleteHistory=True, smoothAngle=180, mergeThreshold=0.001)


"""
Animation
"""


def animMakeHold():
    """Creates a held pose with two identical keys and flat tangents intelligently from the current keyframes

    See zoo.libs.maya.cmds.animation.grapheditorfcurve.animHold() for documentation
    """
    from zoo.libs.maya.cmds.animation import grapheditorfcurve
    grapheditorfcurve.animHold()


def animMoveTimeBack5Frames():
    """Moves the time slider backwards by 5 frames."""
    from zoo.libs.maya.cmds.animation import playbacktime
    playbacktime.animMoveTimeForwardsBack(-5)


def animMoveTimeForwards5Frames():
    """Moves the time slider forwards by 5 frames."""
    from zoo.libs.maya.cmds.animation import playbacktime
    playbacktime.animMoveTimeForwardsBack(5)


def playbackRangeStartToCurrentFrame(animationStartTime=True):
    """Sets the range slider start to be the current frame in time

    :param animationEndTime: if True sets the range to be the entire range, False is playback range only
    :type animationStartTime: bool
    """
    from zoo.libs.maya.cmds.animation import playbacktime
    playbacktime.playbackRangeStartToCurrentFrame(animationStartTime=animationStartTime)


def playbackRangeEndToCurrentFrame(animationEndTime=True):
    """Sets the range slider end to be the current frame in time

    :param animationEndTime: if True sets the range to be the entire range, False is playback range only
    :type animationEndTime: bool
    """
    from zoo.libs.maya.cmds.animation import playbacktime
    playbacktime.playbackRangeEndToCurrentFrame(animationEndTime=animationEndTime)


def jumpKeySelectedTime():
    """Changes the current time in the graph editor (Maya timeline) to match to the closest selected keyframe"""
    from zoo.libs.maya.cmds.animation import grapheditorfcurve
    grapheditorfcurve.jumpToSelectedKey()


def keySnapToTime():
    """Moves the selected keys to the current time. The first keyframe matching, maintains the spacing of selection"""
    from zoo.libs.maya.cmds.animation import grapheditorfcurve
    grapheditorfcurve.moveKeysSelectedTime()


def toogleKeyVisibility():
    """Reverses the visibility of an object in Maya and keys it's visibility attribute"""
    from zoo.libs.maya.cmds.animation import keyframes
    keyframes.toggleAndKeyVisibility()


def resetAttrs():
    """Resets attributes in the channel box to defaults"""
    from zoo.libs.maya.cmds.animation import resetattrs
    resetattrs.resetSelection()


def selectObjFromFCurve():
    """Selects an object from an fCurve"""
    from zoo.libs.maya.cmds.animation import grapheditorfcurve
    grapheditorfcurve.selectObjFromFCurve()


def selectAllAnimated():
    # todo is missing in the hotkey editor
    pass


def selectAnimatedInHierarchy():
    # todo is missing in the hotkey editor
    pass


"""
Display
"""


def displayToggleTextureMode():
    """Toggles the texture viewport mode, will invert. Eg. if "on" turns "off" """
    from zoo.libs.maya.cmds.display import viewportmodes
    viewportmodes.displayToggleTextureMode()


def displayToggleWireShadedMode():
    """Toggles the texture viewport mode, will invert. Eg. if "on" turns "off" """
    from zoo.libs.maya.cmds.display import viewportmodes
    viewportmodes.displayToggleWireShadedMode()


def displayToggleLightingMode():
    """Toggles the light viewport mode, will invert. Eg. if "on" turns "off" """
    from zoo.libs.maya.cmds.display import viewportmodes
    viewportmodes.displayToggleLightingMode()


def displayToggleWireOnShadedMode():
    """Toggles the 'wireframe on shaded' viewport mode. Will invert. Eg. if "shaded" turns "wireframeOnShaded" """
    from zoo.libs.maya.cmds.display import viewportmodes
    viewportmodes.displayToggleWireOnShadedMode()


def displayToggleXrayMode():
    """Toggles the xray viewport mode. Will invert. Eg. if "xray on" turns "xray off" """
    from zoo.libs.maya.cmds.display import viewportmodes
    viewportmodes.displayToggleXrayMode()


def selectCamInView():
    """Selects the camera under the pointer or if an error, get the camera in active panel, if error return message"""
    from zoo.libs.maya.cmds.cameras import cameras
    cameras.selectCamInView()


"""
Select
"""


def selectHierarchy():
    """Select all children in the hierarchy"""
    from zoo.libs.maya.cmds.objutils import selection
    selection.selectHierarchy()


def selectNodeOrShaderAttrEditor():
    """Selects the shader or the selected nodes:

        1. Selects the node if selected in the channel box and opens the attribute editor
        2. Or if a transform node is selected, select the shaders of the current selection and open attr editor

    """
    zoo.libs.maya.cmds.shaders.shaderutils.selectNodeOrShaderAttrEditor()
