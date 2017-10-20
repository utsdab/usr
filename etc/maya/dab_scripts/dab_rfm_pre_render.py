import os
try:
    import maya.cmds as cmds
    import pymel.core as pm
except ImportWarning, err:
    print (err)


#####################
def sayHello():
    print ("RUNNING PYTHON: Starting DAB Pre Render Scripts.....sayHello........")

#####################
def whichRenderer():
    current_renderer = cmds.getAttr('defaultRenderGlobals.currentRenderer')

    print "Current Renderer is: {}".format(current_renderer)

    if current_renderer == 'vray':
        cmds.setAttr('vraySettings.fileNamePrefix', '<Scene>_<Camera>_<RenderLayer>.', type='string')
    elif current_renderer == 'mayaSoftware':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'renderManRIS':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'arnold':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')

def setIntegrator(integrator="PxrVisualizer"):
    '''
    do this in mel
    rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrVisualizer");
    rmanSetAttr("PxrVisualizer","style","matcap");

    rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrDebugShadingContext");
    rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrDefault");
    rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrDirectLighting");
    rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrOcclusion");
    rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrPathTracer");
    rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrVCM");
    rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrValidateBxdf");
    rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrVisualizer");
    '''
    rfm_integrator = cmds.getAttr("renderManRISGlobals.rman__riopt__Integrator_name")
    print "Current Integrator is: {}".format(rfm_integrator)
    print "Setting Integrator to {i}".format(integrator)


#################################
def setMe(node="renderManRISGlobals", attr="rman__torattr___motionBlur", value=1):
    # helper to set an attribute
    try:
        _selected = pm.select(node)
    except Exception, err:
        print "Node not found {}".format(node)
        raise()
    else:
        pass
        #print "Node found {}".format(node)

    try:
        _fullAttr = "{}.{}".format(node, attr)
        print _fullAttr
        pm.setAttr(_fullAttr, value)
    except Exception, err:
        print "Cant set {}".format(_fullAttr)
    else:
        print "Set {} to {}".format(_fullAttr, value)


#####################
def setResolution(w,h):
    try:
        print("Setting resolution: {}x{}".format(w,h))
        cmds.setAttr("defaultResolution.width", w)
        cmds.setAttr("defaultResolution.height", h)
    except Exception,err:
        print("Error setting resolution: {}x{}".format(w,h))
    else:
        pass
    finally:
        print("Set resolution: {}".format(""))

#####################
def setAnimation():
    try:
        print("Setting for animation: {}".format(""))
        cmds.setAttr("defaultRenderGlobals.extensionPadding", 4)
        cmds.setAttr("defaultRenderGlobals.byFrameStep", 1)
        # cmds.getAttr("rmanFinalOutputGlobals0.rman__riopt__Display_type")
        cmds.setAttr("defaultRenderGlobals.outFormatControl", 0)
        cmds.setAttr("defaultRenderGlobals.animation", 1)
        cmds.setAttr("defaultRenderGlobals.putFrameBeforeExt", 1)
    except Exception,err:
        print("Error setting animation: {}".format(err))
    else:
        cmds.setAttr("defaultRenderGlobals.imageFormat", 19)


def setMotionBlur():
    try:
        print("Setting for motionblur: {}".format(""))
        cmds.setAttr("defaultRenderGlobals.motionBlurByFrame", 1.0)
        cmds.setAttr("defaultRenderGlobals.motionBlurUseShutter", 1)
        # cmds.getAttr("rmanFinalOutputGlobals0.rman__riopt__Display_type")
        cmds.setAttr("defaultRenderGlobals.motionBlurShutterOpen", -0.5)
        cmds.setAttr("defaultRenderGlobals.motionBlurShutterClose", 0.5)
    except Exception,err:
        print("Error setting motionblur: {}".format(err))
    else:
        cmds.setAttr("defaultRenderGlobals.imageFormat", 19)

#####################
def setPasses():
    '''
    rmanGetChannelClasses;
    rmanAddOutput rmanFinalGlobals specular;

    rmanGetOutputs rmanFinalGlobals;
    rmanAddOutput "rmanFinalPass" "N";
    rmanCreatePass Shadow;
    rmanUpdateAE;
    '''

    try:
        # passes=cmds.mel("rmanGetOutputs rmanFinalGlobals;")
        pass
    except Exception, err:
        print("Error setting basic Passes: {}".format(err))
    else:
        print("Setting basic Passes: {}".format(""))


def showEnvironment():

    try:
        print os.environ[ 'MAYA_LOCATION' ]
        print("--------MAYA_APP_DIR--------")
        print os.environ[ 'MAYA_APP_DIR' ]
        print("--------MAYA_SCRIPT_PATH---------")
        print os.environ[ 'MAYA_SCRIPT_PATH' ]
        print("--------MAYA_PLUG_IN_PATH---------")
        print os.environ[ 'MAYA_PLUG_IN_PATH' ]
        print("--------PYTHONPATH---------")
        print os.environ[ 'PYTHONPATH' ]
        print("--------RDIR---------")
        print os.environ[ 'RDIR' ]
        print("--------RMS_SCRIPT_PATHS---------")
        print os.environ[ 'RMS_SCRIPT_PATHS' ]
    except Exception, err:
        print "WARNING: {}".format(err)
    else:
        pass
    finally:
        print("-----------------")


def setUp():
    setMe("renderManRISGlobals","rman__torattr___motionBlur",1)
    setMe("renderManRISGlobals","rman__torattr___cameraBlur",1)
    setMe("renderManRISGlobals","rman__torattr___motionSamples",4)
    setMe("renderManRISGlobals","rman__toropt___shutterAngle",180)
    setMe("renderManRISGlobals","rman__toropt___motionBlurType","frame")
    setMe("renderManRISGlobals","rman__torattr___denoise",0)
    setMe("renderManRISGlobals","rman__riopt__rib_format","binary")
    setMe("renderManRISGlobals","rman__riopt__rib_compression","gzip")
    setMe("renderManRISGlobals","rman__torattr___linearizeColors",1)


'''
//Get the name of the first image in the sequence and process any file name prefix tokens.
string $firstImageName[] = `renderSettings -firstImageName -leaveUnmatchedTokens`;


// Get the name of the first and last image for the current layer
string $fl[] = `renderSettings -firstImageName -lastImageName`;
print ("First image is "+$fl[0]+"\n");
// This is the empty string if the scene is not set for animation
if ($fl[1] == "") {
	print "Not rendering animation\n";
} else {
	print ("Last image is "+$fl[1]+"\n");
}


rman getvar STAGE;
// Result: untitled //
rman getvar RIBPATH;
// Result: renderman/untitled/rib //

rmanGetAttrName "ShadingRate";
// Result: rman__riattr___ShadingRate //

//https://renderman.pixar.com/resources/RenderMan_20/howToSetRenderGlobalValues.html
rmanCreateGlobals;


getAttr "rmanFinalOutputGlobals0.rman__riopt__Display_type";


rmanGetChannelClasses;
rmanAddOutput rmanFinalGlobals specular;

rmanGetOutputs rmanFinalGlobals;
rmanAddOutput "rmanFinalPass" "N";
rmanCreatePass Shadow;
rmanUpdateAE;

rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrVisualizer");
rmanSetAttr("PxrVisualizer","style","matcap");

rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrDebugShadingContext");
rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrDefault");
rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrDirectLighting");
rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrOcclusion");
rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrPathTracer");
rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrVCM");
rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrValidateBxdf");
rmanSetAttr("renderManRISGlobals","rman__riopt__Integrator_name","PxrVisualizer");
'''

if __name__ == "__main__":
    pass
    # sayhello()
    # setRfnIntegrator()
    # whichrenderer()
