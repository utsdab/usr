from maya import cmds
import maya.api.OpenMaya as om2


def panelUnderCursor(viewport3d=True):
    """Returns the panel under the pointer, with a check to filter for a viewport panel.  Returns "" if not found

    :param viewport3d: if True will test to see if the panel under the cursor is a 3d viewport with a camera
    :type viewport3d: bool
    :return mayaPanel: The name of the Maya panel, will be "" if no panel found
    :rtype mayaPanel: str
    """
    try:
        mayaPanel = cmds.getPanel(underPointer=True)
        if viewport3d:
            cmds.modelPanel(mayaPanel, query=True, camera=True)  # test if a 3d viewport, will error here if not
        return mayaPanel
    except RuntimeError:  # should always be an active viewport
        return ""


def panelWithFocus(viewport3d=True):
    """Returns the panel with focus, with a check to filter for a viewport panel.  Returns "" if not found

    :param viewport3d: if True will test to see if the panel under the cursor is a 3d viewport with a camera
    :type viewport3d: bool
    :return mayaPanel: The name of the Maya panel, will be "" if no panel found
    :rtype mayaPanel: str
    """
    focusPanel = cmds.getPanel(withFocus=True)
    try:
        if viewport3d:
            cmds.modelPanel(focusPanel, query=True, camera=True)  # test if a 3d viewport, will error here if not
    except RuntimeError:  # should always be an active viewport
        return ""
    return focusPanel


def firstViewportPanel():
    """Returns the first visible viewport panel it finds in the current Maya session

    :return viewportPanel: The name of the Maya panel that is a viewport, will be "" if not found (might be impossible)
    :rtype viewportPanel: str
    """
    panel = ""
    allPanels = cmds.getPanel(visiblePanels=True)
    for panel in allPanels:
        try:
            cmds.modelPanel(panel, query=True, camera=True)  # test if a 3d viewport, will error here if not
            break
        except RuntimeError:  # if not a 3d viewport, so set panel to ""
            panel = ""
    return panel


def panelUnderPointerOrFocus(viewport3d=False, prioritizeUnderCursor=True, message=True):
    """returns the mayaPanel that is either:

        1. Under the cursor
        2. The active panel (with focus)
        3. First visible viewport panel (only if viewport3d=True)

    If prioritizeUnderCursor=True then the active panel (with focus) will prioritize before under the cursor.

    In general use prioritizeUnderCursor=True for hotkeys and prioritizeUnderCursor=False for UIs.

    The "viewport3d" flag set to True will return only panels with 3d cameras, ie 3d viewports, otherwise None

    :param viewport3d: if True will test to see if the panel under the cursor is a 3d viewport with a camera
    :type viewport3d: bool
    :param prioritizeUnderCursor: if True return under cursor first, and if not then with focus
    :type prioritizeUnderCursor: bool
    :param message: report a potential fail message to the user?
    :type message: bool

    :return mayaPanel: The name of the Maya panel, will be "" if no panel found
    :rtype mayaPanel: str
    """
    if prioritizeUnderCursor:
        panel = panelUnderCursor(viewport3d=viewport3d)
        if panel:
            return panel
        panel = panelWithFocus(viewport3d=viewport3d)  # will be "" if no viewport found
        if panel:
            return panel
    else:
        panel = panelWithFocus(viewport3d=viewport3d)
        if panel:
            return panel
        panel = panelUnderCursor(viewport3d=viewport3d)  # will be "" if no viewport found
        if panel:
            return panel
    # No viewport panels in focus or under pointer so try to find the first open viewport panel in the scene.
    if viewport3d:
        panel = firstViewportPanel()
        if panel:
            return panel
    if message:
        om2.MGlobal.displayWarning("No viewport found, the active window must be under the cursor or the "
                                   "active window must be a 3d viewport.")
    return panel  # returns ""


def displayToggleTextureMode():
    """Toggles the texture viewport mode, will invert. Eg. if "on" turns "off", usually on a hotkey"""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:
        return
    invertStatus = not cmds.modelEditor(mayaPanel, query=True, displayTextures=True)
    cmds.modelEditor(mayaPanel, edit=True, displayTextures=invertStatus)  # set as inverse of current texture mode


def displayToggleWireShadedMode():
    """Toggles the shaded viewport mode. Will invert. Eg. if "wireframe" turns "shaded",  usually on a hotkey"""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return
    displayAppearance = cmds.modelEditor(mayaPanel, query=True, displayAppearance=True)
    if displayAppearance == "wireframe":  # is currently wireframe so make shaded
        cmds.modelEditor(mayaPanel, edit=True, displayAppearance="smoothShaded")
    else:  # is currently shaded so make wireframe
        cmds.modelEditor(mayaPanel, edit=True, displayAppearance="wireframe")


def displayToggleLightingMode():
    """Toggles the light viewport mode. Will invert. Eg. if "lights on" turns "lights off",  usually on a hotkey"""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return
    displayAppearance = cmds.modelEditor(mayaPanel, query=True, displayLights=True)
    if displayAppearance == "all":  # is currently lights on so turn off
        cmds.modelEditor(mayaPanel, edit=True, displayLights="default")
    else:  # is currently lights off so turn on
        cmds.modelEditor(mayaPanel, edit=True, displayLights="all")


def displayLightingMode(displayOn=True):
    """Turns on/off the light viewport mode."""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return
    cmds.modelEditor(mayaPanel, edit=True, displayLights="all")


def displayToggleWireOnShadedMode():
    """Toggles the 'wireframe on shaded' viewport mode. Will invert. Eg. if "shaded" turns "wireframeOnShaded" """
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return
    invertStatus = not cmds.modelEditor(mayaPanel, query=True, wireframeOnShaded=True)
    cmds.modelEditor(mayaPanel, edit=True, wireframeOnShaded=invertStatus)  # set as inverse of current texture mode


def displayToggleXrayMode():
    """Toggles the xray viewport mode. Will invert. Eg. if "xray on" turns "xray off",  usually on a hotkey"""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return
    invertStatus = not cmds.modelEditor(mayaPanel, query=True, xray=True)
    cmds.modelEditor(mayaPanel, edit=True, xray=invertStatus)  # set as inverse of current texture mode


def setDisplayOcclusion(enable=True):
    """Sets the value of the viewport sceen space ambient occlusion

    :param enable: True enables Ambient Occlusion in the viewport
    :type enable: bool
    """
    cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", enable)


def setDisplayMotionBlur(enable=True):
    """Sets the value of the viewport motion blur

    :param enable: True enables Motion Blur in the viewport
    :type enable: bool
    """
    cmds.setAttr("hardwareRenderingGlobals.motionBlurEnable", enable)


def setAntiAliasVPSamples(samples=16):
    """Set VP2 anti-alias sample settings

    :param samples: Sample level of the viewport settings, 8 or 16 etc
    :type samples: int
    """
    cmds.setAttr("hardwareRenderingGlobals.aasc", samples)


def enableAntiAliasMutliSample(enable=True):
    """

    :param enable:
    :type enable:
    """
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", enable)


