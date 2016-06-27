'''maya tool adapted from julians wblend.mel
    after discussion te desire is for
    1 setect target joint start
    the traget joint end
    the 2 source start joints

    check there is a chain between star and end
    check that other sources match
    create locator at end as controller
    locator is costrained to end pos
    blend together

'''

# from pymel import core as pmc
import PySide.QtCore as qc
import PySide.QtGui as qg
import os
import sys
from functools import partial

# -------------------------------------------------------------------------------------------------------------------- #
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(filename)s as %(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)

try:
    import maya.cmds  as mc
    import pymel.core as pmc
    import shiboken
    import maya.OpenMayaUI as mui
    import maya.OpenMaya as om

except Exception, err:
    logger.warn("No maya import {} presuming from a shell".format(err))


class Joints(object):
    # short joint chain
    def __init__(self):
        # chain is a simple list of joint in order
        self.chain = []
        self.length = 0
        print("class joints called")

    def setstart(self,_start):
        self.chain = []
        self.length = 0
        # _start = pmc.ls(selection=True, type="joint")
        print "start joint is %s" % _start
        self.startjoint = _start

    def setend(self,_end):
        # _end = pmc.ls(selection=True, type="joint")
        print "end joint is %s" % _end
        self.endjoint = _end

    def setlength(self,_length):
        self.length=_length

    def gather(self):
        self.chain = []
        self.chain.extend(pmc.ls(self.startjoint))
        _list = pmc.listRelatives(self.startjoint, ad=True, type="joint")
        _list.reverse()
        for i, j in enumerate(_list):
            try:
                if ( j in self.endjoint ):
                    self.chain.extend(pmc.ls(j))
                    print "x"
                    break
            except Exception, err:
                if ( i == self.length + 1 ):
                    self.chain.extend(pmc.ls(j))
                    print "y"
                    break
            finally:
                self.chain.extend(pmc.ls(j))

        print "all joint are %s" % self.chain
        self.length = len(self.chain)

    def getlength(self):
        return self.length


def blender(s1, s2, t, cont, style):
    # created a blend node between two sources and a target
    # adding attributes for control
    # type - 0 for rotation or 1 for translation
    try:
        cont.attr("blend")
    except Exception, err:
        pmc.addAttr(cont, shortName='bl', longName='blend', defaultValue=0.5, minValue=0.0, maxValue=1.0)

    try:
        cont.attr("blendinverse")
    except Exception, err:
        pmc.addAttr(cont, shortName='bli', longName='blendinverse', defaultValue=0.5, minValue=0.0, maxValue=1.0)
        add = pmc.createNode("addDoubleLinear")
        mult = pmc.createNode("multiplyDivide")
        cont.bl >> mult.input1X
        mult.input2X.set(-1.0)
        mult.outputX >> add.input1
        add.output >> cont.bli
        add.input2.set(1.0)

    if style == 1:  # transformation
        try:
            bc = pmc.createNode("blendColors")
            s1.translate >> bc.color1
            s2.translate >> bc.color2
            bc.output >> t.translate
            cont.bl >> bc.blender
        except Exception, err:
            print "failed to make blend translation node %s" % err

    elif style == 0:  # rotation
        try:
            b = pmc.createNode("animBlendNodeAdditiveRotation")
            s1.rotate >> b.inputA
            s2.rotate >> b.inputB
            b.output >> t.rotate
            b.rotationInterpolation.set(1)  # quarternian
            cont.bl >> b.weightA
            cont.bli >> b.weightB
        except Exception, err:
            print "failed to make blend rotation node %s" % err

    else:
        print "not translation or rotation"

'''
class BlendUI(object):
    def __init__(self):
        # print "hello"
        # pmc.promptBox("hello","message","ok","cancel")
        pass


class Test(object):
    def __init__(self):
        # make test joints then hook them up
        pmc.select(clear=True)
        a1 = pmc.animation.joint(p=(0.0, 0.0, 0.0))
        a2 = pmc.animation.joint(p=(1.0, 0.0, 0.0))
        a3 = pmc.animation.joint(p=(2.0, 0.0, 0.0))
        a4 = pmc.animation.joint(p=(3.0, 0.0, 0.0))

        pmc.select(clear=True)
        b1 = pmc.animation.joint(p=(0.0, 0.0, 0.0))
        b2 = pmc.animation.joint(p=(1.0, 0.0, 0.0))
        b3 = pmc.animation.joint(p=(2.0, 0.0, 0.0))
        b4 = pmc.animation.joint(p=(3.0, 0.0, 0.0))

        pmc.select(clear=True)
        c1 = pmc.animation.joint(p=(0.0, 0.0, 0.0))
        c2 = pmc.animation.joint(p=(1.0, 0.0, 0.0))
        c3 = pmc.animation.joint(p=(2.0, 0.0, 0.0))
        c4 = pmc.animation.joint(p=(3.0, 0.0, 0.0))

        pmc.select(clear=True)
        control = pmc.spaceLocator(name="blend_control")

        # blender(a1,b1,c1,control,1)
        # joints=[(a1,a2,a3,a4),(b1,b2,b3,b4),(c1,c2,c3,c4)]
        #
        # for j,joi in enumerate(joints[0]):
        #     for c,ch in enumerate(joints):
        #         # print j
        #         blender(joints[0][j],joints[1][j],joints[2][j],control,0)


# -------------------------------------------
import maya.OpenMaya as OpenMaya

class Selected(object):
    def __init__(self):
        self.selected=None

    def selectjoint(self,*args, **kwargs):

        self.selected = pmc.ls(selection=True, type="joint")
        print "You selected joint %s" % self.selected

    def selector(self):
        try:
            self.idx = om.MEventMessage.addEventCallback("SelectionChanged", self.selectjoint)
        except Exception, err:
            print "error %s" % err

    def kill(self):
            # when ever you finish doing your stuff!!!
            print "kill"
            try:
                om.MMessage.removeCallback(self.idx)
            except Exception, err:
                print "error %s" % err
'''
def blendchains(t,s1,s2):
    print "Length is %s" % t.length
    s1.setlength(t.length)
    s1.gather()
    s2.setlength(t.length)
    s2.gather()
    pmc.select(clear=True)
    control = pmc.spaceLocator(name="blend_control")
    pmc.parentConstraint(t.endjoint,control)
    blender(s1.chain[0],s2.chain[0],t.chain[0],control,1)

    for i, j in enumerate(t.chain):
        blender(s1.chain[i],s2.chain[i],j,control,0)
    '''
    constrain parent locator to end of target chain
    make blend attr keyable
    make cancel work
    '''


def buttonPressed(button, jointobject, position):
    _selected = pmc.ls(selection=True, flatten=True)
    if pmc.nodeType(_selected[0])=="joint":
        print "%s is %s" % (button,_selected[0])
        if position == 0:
            jointobject.setstart(_selected[0])
        elif position == 1:
            jointobject.setend(_selected[0])
            jointobject.gather()
    else:
        print "You need to select a joint you selected a %s" % pmc.nodeType(_selected[0])


# -------------------------------------------

def main():
    pmc.select(clear=True)
    logging.info("Select Target Chain Start Joint")


    win = pmc.window(title="mg_joint_blender")
    layout = pmc.formLayout()

    t=Joints()
    s1=Joints()
    s2=Joints()

    pmc.button( label='Target Start Joint', backgroundColor = [0.6,0.5,0.5],
                command = pmc.Callback( buttonPressed, 'Target Start Joint', t, 0 ) )
    pmc.button( label='Target End Joint', backgroundColor = [0.6,0.5,0.5],
                command = pmc.Callback( buttonPressed, 'Target End Joint', t, 1 ) )
    pmc.button( label='Source 1 Start Joint', backgroundColor = [0.5,0.6,0.5],
                command = pmc.Callback( buttonPressed, 'Source 1 Start Joint', s1, 0 ) )
    pmc.button( label='Source 2 Start Joint', backgroundColor = [0.5,0.5,0.6],
                command = pmc.Callback( buttonPressed, 'Source 2 Start Joint', s2, 0 ) )

    pmc.button( label="BLEND" , command = lambda *args: blendchains(t,s1,s2))
    pmc.button( label="CANCEL")
    layout.redistribute()
    pmc.showWindow()






if __name__ == '__main__':
    main()

'''
sphere1, hist = polySphere(name='mySphere')
grp = group(sphere1)
grp2 = instance(grp)[0]
sphere2 = grp2.getChildren()[0]
print sphere2
print "mg_blend.py"

loc2 = spaceLocator(name="mattLocator")
loc2.relative(False)
loc2.absolute(True)
loc2.setPosition([1.0,0.0,0.0])


select(clear=True)
gp=group(name="mattGroup")
parent(loc2,gp)


myshape = loc2.listRelatives()
print 'the shape is: ',
print myshape[0]

myhistory = myshape[0].listHistory()
print 'the history is: ',
print myhistory

selection = ls(selection=True)
shapes = [ x.listRelatives()[0] for x in selection ]
print shapes


ls('*.radius')

print myshape[0].nodeType()


print foo
print bar




promptDialog(message='what exposure do you want to add?', text='1')
value = promptDialog(query=True, text=True)
value = float(value)
[ x.exposure.set( x.exposure.get() + value ) for x in ls(type='phxAreaLight') ]

loc2.listAttr()

#-------------------------------------------
import maya.OpenMaya as OpenMaya
def test(*args, **kwargs):
    print pmc.ls(selection=True)

idx = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", test)

#when ever you finish doing your stuff!!!
OpenMaya.MMessage.removeCallback(idx)
#-------------------------------------------


'''
