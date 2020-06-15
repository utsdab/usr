# importing libraries:
import maya.cmds as cmds
import dpBaseControlClass as BaseControl
reload(BaseControl)

# global variables to this module:    
CLASS_NAME = "BallonFlat"
TITLE = "m117_ballonFlat"
DESCRIPTION = "m099_cvControlDesc"
ICON = "/Icons/dp_ballonFlat.png"

dpBallonFlatVersion = 1.1

class BallonFlat(BaseControl.ControlStartClass):
    def __init__(self, *args, **kwargs):
        #Add the needed parameter to the kwargs dict to be able to maintain the parameter order
        kwargs["CLASS_NAME"] = CLASS_NAME
        kwargs["TITLE"] = TITLE
        kwargs["DESCRIPTION"] = DESCRIPTION
        kwargs["ICON"] = ICON
        BaseControl.ControlStartClass.__init__(self, *args, **kwargs)
    
    
    def cvMain(self, useUI, cvID=None, cvName=CLASS_NAME+'_Ctrl', cvSize=1.0, cvDegree=1, cvDirection='+Y', cvRot=(0, 0, 0), cvAction=1, dpGuide=False, *args):
        """ The principal method to call all other methods in order to build the cvControl curve.
            Return the result: new control curve or the destination list depending of action.
        """
        result = self.cvCreate(useUI, cvID, cvName, cvSize, cvDegree, cvDirection, cvRot, cvAction, dpGuide)
        return result
    
    
    def getLinearPoints(self, *args):
        """ Get a list of linear points for this kind of control curve.
            Set class object variables cvPointList, cvKnotList and cvPeriodic.
        """
        r = self.cvSize
        self.cvPointList = [(0, 0, 0), (-0.115*r, 0.02*r, 0), (-0.3*r, 0.07*r, 0), (-0.6*r, 0.6*r, 0), (-0.4*r, r, 0),
                            (0, 1.05*r, 0), (0.4*r, r, 0), (0.6*r, 0.6*r, 0), (0.3*r, 0.07*r, 0), (0.115*r, 0.02*r, 0),
                            (0, 0, 0)]
        self.cvKnotList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        self.cvPeriodic = True #closed
    
    
    def getCubicPoints(self, *args):
        """ Get a list of cubic points for this kind of control curve.
            Set class object variables cvPointList, cvKnotList and cvPeriodic.
        """
        r = self.cvSize
        self.cvPointList = [(0, 0, 0), (-0.115*r, 0.02*r, 0), (-0.3*r, 0.07*r, 0), (-0.6*r, 0.6*r, 0), (-0.4*r, r, 0),
                            (0, 1.05*r, 0), (0.4*r, r, 0), (0.6*r, 0.6*r, 0), (0.3*r, 0.07*r, 0), (0.115*r, 0.02*r, 0),
                            (0, 0, 0), (-0.115*r, 0.02*r, 0), (-0.3*r, 0.07*r, 0)]
        self.cvKnotList = [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        self.cvPeriodic = True #closed