import sys
try:
    import pymel.core as pm
except Exception, err:
    print "Cant find pymel sorry {}".format(err)
    sys.exit()

# Simple interface nugget tobuild a facce xx-y controller interface
# build a cocntrol group and a target withib a frame
# the quadrant values appear as extra attributes on the frame and an be used to drive
# shapes or whatever.
# script is crappy - draft version 1
# run by calling

def doit():
    pm.select(clear=True)
    _top=pm.group()
    _top.rename("CONTROLER_FOUR_INPUT_SYMMETRY_BLEND")

    _frame = pm.curve(d=1,p=[(-1,1,0), (1,1,0), (1,-1,0), (-1,-1,0), (-1,1,0)])
    _frame.rename("frame")
    _frameshape=_frame.getShape()
    pm.setAttr(_frameshape + ".overrideEnabled", 1)
    pm.setAttr(_frameshape + ".overrideDisplayType", 2)

    _guide = pm.curve(d=1,p=[(-1,0,0), (0,1,0), (1,0,0), (0,-1,0), (-1,0,0)])
    _guide.rename("guide")
    _guideShape=_guide.getShape()
    pm.setAttr(_guideShape + ".overrideEnabled", 1)
    pm.setAttr(_guideShape + ".overrideDisplayType", 2)

    pm.parent(_frame,_top)
    pm.parent(_guideShape, _frame, shape=True, relative=True, addObject=False)
    pm.delete(_guide)

    _target = pm.curve( d=1, p=[(-.1,.1,0), (.1,.1,0), (.1,-.1,0), (-.1,-.1,0), (-.1,.1,0)])
    _target.rename("target")
    _target.setLimited('translateMinX',True)
    _target.setLimit('translateMinX',-1)
    _target.setLimited('translateMaxX',True)
    _target.setLimit('translateMaxX',1)
    _target.setLimited('translateMinY',True)
    _target.setLimit('translateMaxY',-1)
    _target.setLimited('translateMaxY',True)
    _target.setLimit('translateMaxY',1)
    _target.setLimited('translateMinZ',True)
    _target.setLimit('translateMinZ',0)
    _target.setLimited('translateMaxZ',True)
    _target.setLimit('translateMaxZ',0)

    pm.parent(_target, _frame, shape=False, relative=True, addObject=False)

    _minus=pm.createNode("plusMinusAverage")
    _add=pm.createNode("plusMinusAverage")
    _minus.rename("minus")
    _add.rename("add")

    _target.translateX >> _minus.input2D[0].input2Dx
    _target.translateY >> _minus.input2D[1].input2Dx
    _target.translateX >> _add.input2D[0].input2Dx
    _target.translateY >> _add.input2D[1].input2Dx

    _half_neg=pm.createNode("multiplyDivide")
    _half=pm.createNode("multiplyDivide")
    _half_neg.rename("half_neg")
    _half.rename("half")

    _add.setAttr("operation",1)
    _minus.setAttr("operation",2)

    _add.output2D.output2Dx >> _half_neg.input1.input1X
    _add.output2D.output2Dx >> _half.input1.input1X
    _minus.output2D.output2Dx >> _half_neg.input1.input1Y
    _minus.output2D.output2Dx >> _half.input1.input1Y

    _half_neg.setAttr("operation",2)
    _half_neg.setAttr("input2.input2X",-2)
    _half_neg.setAttr("input2.input2Y",-2)
    _half.setAttr("operation",2)
    _half.setAttr("input2.input2X",2)
    _half.setAttr("input2.input2Y",2)

    _clampA=pm.createNode("clamp")
    _clampB=pm.createNode("clamp")

    _half_neg.output.outputX >> _clampA.input.inputR
    _half_neg.output.outputY >> _clampA.input.inputG
    _half.output.outputX >> _clampB.input.inputR
    _half.output.outputY >> _clampB.input.inputG
    _clampA.setAttr("maxR",1)
    _clampB.setAttr("maxR",1)
    _clampA.setAttr("maxG",1)
    _clampB.setAttr("maxG",1)

    pm.addAttr(_frame, niceName = "ql", longName = "quadrant1" , usedAsColor = False, attributeType = 'double' )
    pm.addAttr(_frame, niceName = "q2", longName = "quadrant2" , usedAsColor = False, attributeType = 'double' )
    pm.addAttr(_frame, niceName = "q3", longName = "quadrant3" , usedAsColor = False, attributeType = 'double' )
    pm.addAttr(_frame, niceName = "q4", longName = "quadrant4" , usedAsColor = False, attributeType = 'double' )

    _clampA.output.outputR >> _frame.quadrant3
    _clampA.output.outputG >> _frame.quadrant4
    _clampB.output.outputR >> _frame.quadrant1
    _clampB.output.outputG >> _frame.quadrant2

    pm.setAttr(_target + ".translateY",0)

def main():
    try:
        doit()
    except:
        print "Oops"
    else:
        print "Created Control group, the quadrant values are located on the frame inside the group"


