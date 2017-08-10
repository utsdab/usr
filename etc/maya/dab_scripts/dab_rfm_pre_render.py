import maya.cmds as cmds
import os

'''
put this is the pythonpath then add into the prerendermel
Okay, the pre render script is definitely acting capriciously
In order to investigate, I've made a small test case.
Simple scene with only one object: nurbsSpehre1
all scripts are in external file: pre.py

CODE
import maya.cmds

def preFrame():
    maya.cmds.move( 3, 0, 0, "nurbsSphere1", r = True)
    x = maya.cmds.getAttr( "nurbsSphere1.tx" )
    file = open( "log.txt","a")
    file.write ( "x = " + x + "\r\n" )
    file.close()

pre render scripts are assigned in render globals:
Pre render MEL: python( "import pre" )
Pre render frame MEL: python( "pre.preFrame()" )


'''
#####################
def sayHello():
    print ("RUNNING PYTHON: Starting DAB Pre Render Scripts.....sayHello........")

#####################
def whichRenderer():
    current_renderer = cmds.getAttr('defaultRenderGlobals.currentRenderer')

    print "Current Renderer is: {}".format(current_renderer)

    if current_renderer == 'vray':
        cmds.setAttr('vraySettings.fileNamePrefix', '<Scene>_<Camera>_<Layer>.', type='string')
    elif current_renderer == 'mentalRay':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'mayaSoftware':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'renderManRIS':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')
    elif current_renderer == 'arnold':
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>_<Camera>_<RenderLayer>', type='string')

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
        print("Error seeting animation: {}".format(err))
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
    sayhello()
    whichrenderer()
