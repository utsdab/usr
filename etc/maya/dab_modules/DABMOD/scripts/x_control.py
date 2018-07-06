import sys
try:
    import pymel.core as pm
except Exception, err:
    print "Cant find pymel sorry {}".format(err)
    sys.exit()


# Simple interface nugget tobuild a facce linear controller interface
# build a cocntrol group and a target withib a frame
# the quadrant values appear as extra attributes on the frame and an be used to drive
# shapes or whatever.
# script is crappy - draft version 1

def doit():
    pm.select(clear=True)
    _top=pm.group()
    _top.rename("CONTROLER")

    _frame = pm.curve(d=1,p=[(-.1,1,0), (.1,1,0), (.1,-1,0), (-.1,-1,0), (-.1,1,0)])
    _frame.rename("frame")

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

    _target.ty >> _frame.value1

    print "Created Control group, the  value is are located on the frame inside the group"


def main():
    try:
        doit()
    except:
        print "Oops"
    else:
        print "Created Control group, the quadrant values are located on the frame inside the group"


