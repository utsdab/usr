
import sys
try:
    import pymel.core as pm
except Exception, err:
    print "Cant find pymel sorry {}".format(err)
    sys.exit()


'''
A linear slider that drives two opposing blend shapes
the outputs are on the frame node and there are two gain attributes that can amplify the values passed to blend shapes.
'''

def doit():
    pm.select(clear=True)
    _top=pm.group()
    _top.rename("CONTROLER_DUAL_INPUT_BLENDER")

    _frame = pm.curve(d=1,p=[(-.1,1,0), (.1,1,0), (.1,-1,0), (-.1,-1,0), (-.1,1,0)])
    _frame.rename("frame")
    _frameshape=_frame.getShape()
    pm.setAttr(_frameshape + ".overrideEnabled", 1)
    pm.setAttr(_frameshape + ".overrideDisplayType", 2)

    pm.parent(_frame,_top)

    _target = pm.curve( d=1, p=[(-.15,.15,0), (.15,.15,0), (.15,-.15,0), (-.15,-.15,0), (-.15,.15,0)])
    _target.rename("target")
    _target.setLimited('translateMinX',True)
    _target.setLimit('translateMinX',0)
    _target.setLimited('translateMaxX',True)
    _target.setLimit('translateMaxX',0)
    _target.setLimited('translateMinY',True)
    _target.setLimit('translateMaxY',-1)
    _target.setLimited('translateMaxY',True)
    _target.setLimit('translateMaxY',1)
    _target.setLimited('translateMinZ',True)
    _target.setLimit('translateMinZ',0)
    _target.setLimited('translateMaxZ',True)
    _target.setLimit('translateMaxZ',0)

    pm.parent(_target, _frame, shape=False, relative=True, addObject=False)
    pm.addAttr(_frame, niceName = "vl", longName = "value1" , usedAsColor = False, attributeType = 'double' )
    pm.addAttr(_frame, niceName = "v2", longName = "value2" , usedAsColor = False, attributeType = 'double' )
    pm.addAttr(_frame, niceName = "g1", longName = "gain1" , usedAsColor = False, attributeType = 'double' )
    pm.addAttr(_frame, niceName = "g2", longName = "gain2" , usedAsColor = False, attributeType = 'double' )

    pm.setAttr(_target + ".translateY",0)
    pm.setAttr(_frame + ".gain1",1.0)
    pm.setAttr(_frame + ".gain2",1.0)

    _multiplyA=pm.createNode("multiplyDivide")
    _multiplyB=pm.createNode("multiplyDivide")
    _clampA=pm.createNode("clamp")

    _multiplyA.rename("multiplyA")
    _multiplyB.rename("multiplyB")
    _clampA.rename("clampA")

    _target.ty >> _clampA.input.inputR
    _target.ty >> _clampA.input.inputG

    _clampA.output.outputR >> _multiplyA.input1.input1X
    _clampA.output.outputG >> _multiplyA.input1.input1Y

    _multiplyA.output.outputX >> _multiplyB.input1.input1X
    _multiplyA.output.outputY >> _multiplyB.input1.input1Y

    _multiplyB.output.outputX >> _frame.value1
    _multiplyB.output.outputY >> _frame.value2

    _frame.gain1 >> _multiplyB.input2.input2X
    _frame.gain2 >> _multiplyB.input2.input2Y

    try:
        pm.setAttr(_multiplyA + ".input2Y", -1.0)
        pm.setAttr(_clampA + ".maxR", 1.0)
        pm.setAttr(_clampA + ".minR", 0.0)
        pm.setAttr(_clampA + ".maxG", 0.0)
        pm.setAttr(_clampA + ".minG", -1.0)
    except Exception, err:
        print "crap {}".format(err)


    print "Created Control group, the  value is are located on the frame inside the group"


def main():
    try:
        doit()
    except:
        print "Oops"
    else:
        print "Created Control group, the quadrant values are located on the frame inside the group"

