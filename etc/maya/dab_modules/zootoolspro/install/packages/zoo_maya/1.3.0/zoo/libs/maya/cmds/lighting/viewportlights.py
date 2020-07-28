from maya import cmds
from zoo.libs.maya.cmds.display import viewportmodes
from maya.api import OpenMaya as om2

def createViewportLight_surfaceStandard(cameraActive="persp", selectLight=True, viewportShadows=True,
                                        shadowColor=(0.4, 0.4, 0.4), message=True):
    """Replicates the viewport light but adjusts for standardSurface and aiStandardSurface 2020 shaders

    :param cameraActive: The camera transform to affect, the light will be constrained.
    :type cameraActive: str
    :param selectLight: select the light after building it
    :type selectLight: bool
    :param message: Report the message to the user
    :type message: bool
    :return lightShape: The name of the created light shape node
    :rtype lightShape: str
    :return lightTransform: The name of the created light transform node
    :rtype lightTransform: str
    :return lightGrp: The name of the created light group node
    :rtype lightGrp: str
    :return parentConstraint:  The name of the created parent constraint node
    :rtype parentConstraint: str
    """
    # delete old setup if there is one
    recreate = False
    if cmds.objExists("vp2_light_grp"):
        cmds.delete("vp2_light_grp")
        recreate = True
    # Create directional light and grp
    lightShape = cmds.directionalLight(rotation=(-13.706, -2.883, -11.653), name="vp2_light")
    lightTransform = cmds.listRelatives(lightShape, parent=True)[0]
    lightGrp = cmds.group(lightTransform, name="vp2_light_grp")
    # Lock and set attrs
    cmds.setAttr('{}.rotateX'.format(lightTransform), lock=True)
    cmds.setAttr('{}.rotateY'.format(lightTransform), lock=True)
    cmds.setAttr('{}.rotateZ'.format(lightTransform), lock=True)
    cmds.setAttr('{}.translateX'.format(lightTransform), 3)
    cmds.setAttr('{}.translateY'.format(lightTransform), 2)
    cmds.setAttr('{}.translateZ'.format(lightTransform), -10)
    # Set the new light intensity
    cmds.setAttr('{}.intensity'.format(lightShape), 1.7)
    # Constrain to the given camera
    parentConstraint = cmds.parentConstraint(cameraActive, lightGrp, maintainOffset=False)
    # Turn on viewport light mode on for current view if possible
    viewportmodes.displayLightingMode(True)
    if viewportShadows:
        cmds.setAttr('{}.useDepthMapShadows'.format(lightShape), 1)
        cmds.setAttr('{}.dmapResolution'.format(lightShape), 4096)
        cmds.setAttr('{}.dmapFilterSize'.format(lightShape), 5)
        cmds.setAttr('{}.shadowColor'.format(lightShape), 0.4, 0.4, 0.4, type="double3")
        try:  # Turn Arnold vis off
            cmds.setAttr('{}.aiDiffuse'.format(lightShape), 0)
            cmds.setAttr('{}.aiSpecular'.format(lightShape), 0)
            cmds.setAttr('{}.aiSss'.format(lightShape), 0)
            cmds.setAttr('{}.aiIndirect'.format(lightShape), 0)
            cmds.setAttr('{}.aiVolume'.format(lightShape), 0)
        except RuntimeError:  # Arnold is probably not loaded
            pass
    if selectLight:
        cmds.select(lightTransform, replace=True)
    if message:
        if recreate:
            om2.MGlobal.displayInfo("Success: Light setup recreated and attached to camera `{}`".format(cameraActive))
        else:
            om2.MGlobal.displayInfo("Success: Light setup created and attached to camera `{}`".format(cameraActive))
    return lightShape, lightTransform, lightGrp, parentConstraint