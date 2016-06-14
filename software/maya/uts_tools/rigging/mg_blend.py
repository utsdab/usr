#  maya tool adapted from julians wblend.mel
from pymel import core as pmc
import os

class Joints(object):
    # something
    def __init__(self):
        # chain is a simple list of joint in order
        self.chain=[]
        print("class joints called")

    def gather(self,_joint):
        self.chain.append(_joint)
        _list = pmc.listRelatives(_joint, ad=True, type="joint")
        _list.reverse()
        self.chain.extend( _list )





def blender(s1, s2, t, cont, style):
    # created a blend node between two sources and a target
    # adding attributes for control
    # type - 0 for rotation or 1 for translation
    try:
        cont.attr("blend")
    except Exception,err:
        pmc.addAttr(cont, shortName='bl', longName='blend', defaultValue=0.5, minValue=0.0, maxValue=1.0)

    try:
        cont.attr("blendinverse")
    except Exception,err:
        pmc.addAttr(cont, shortName='bli', longName='blendinverse', defaultValue=0.5, minValue=0.0, maxValue=1.0)
        add=pmc.createNode("addDoubleLinear")
        mult=pmc.createNode("multiplyDivide")
        cont.bl>>mult.input1X
        mult.input2X.set(-1.0)
        mult.outputX>>add.input1
        add.output>>cont.bli
        add.input2.set(1.0)

    if style == 1:   # transformation
        try:
            bc=pmc.createNode("blendColors")
            s1.translate >> bc.color1
            s2.translate >> bc.color2
            bc.output >> t.translate
            cont.bl >> bc.blender
        except Exception,err:
            print "failed to make blend translation node %s"%err

    elif style == 0:           # rotation
        try:
            b=pmc.createNode("animBlendNodeAdditiveRotation")
            s1.rotate >> b.inputA
            s2.rotate >> b.inputB
            b.output >> t.rotate
            b.rotationInterpolation.set(1) # quarternian
            cont.bl >> b.weightA
            cont.bli >> b.weightB
        except Exception, err:
            print "failed to make blend rotation node %s"%err

    else:
        print "not translation or rotation"



class BlendUI(object):
    def __init__(self):
        # print "hello"
        # pmc.promptBox("hello","message","ok","cancel")
        print "confirmbox"
        pmc.confirmBox(title="title", message="confirm", yes="yes", no="no",)

class Test(object):
    def __init__(self):
        # make test joints then hook them up
        pmc.select(clear=True)
        a1=pmc.animation.joint(  p=(0.0,0.0,0.0))
        a2=pmc.animation.joint(  p=(1.0,0.0,0.0))
        a3=pmc.animation.joint(  p=(2.0,0.0,0.0))
        a4=pmc.animation.joint(  p=(3.0,0.0,0.0))

        pmc.select(clear=True)
        b1=pmc.animation.joint(  p=(0.0,0.0,0.0))
        b2=pmc.animation.joint(  p=(1.0,0.0,0.0))
        b3=pmc.animation.joint(  p=(2.0,0.0,0.0))
        b4=pmc.animation.joint(  p=(3.0,0.0,0.0))

        pmc.select(clear=True)
        c1=pmc.animation.joint(  p=(0.0,0.0,0.0))
        c2=pmc.animation.joint(  p=(1.0,0.0,0.0))
        c3=pmc.animation.joint(  p=(2.0,0.0,0.0))
        c4=pmc.animation.joint(  p=(3.0,0.0,0.0))

        pmc.select(clear=True)
        control = pmc.spaceLocator(name="blend_control")

        blender(a1,b1,c1,control,1)
        joints=[(a1,a2,a3,a4),(b1,b2,b3,b4),(c1,c2,c3,c4)]

        for j,joi in enumerate(joints[0]):
            for c,ch in enumerate(joints):
                # print j
                blender(joints[0][j],joints[1][j],joints[2][j],control,0)

        a=Joints()
        a.gather(a1)
        print a.chain

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
'''

