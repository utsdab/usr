#  maya tool adapted from julians wblend.mel


from pymel.core import *
import os

class joints(object):
	def __init__(self):
		# chain is a simple list of joint in order
		self.chain=[]
		print "class joints called"
		pass
		
	def size():
		return self.chain.

def blender(joint_s1, joint_s2, joint_t, controller, type):
	# created a blend node between two sources and a target 
	# adding attributes for control
	# type - 0 for rotation or 1 for translation





'''
sphere1, hist = polySphere(name='mySphere')
grp = group(sphere1)
grp2 = instance(grp)[0]
sphere2 = grp2.getChildren()[0]


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

foo = """I can't believe I can do "this" with python!"""
bar = '''works with "single quotes" and "double quotes" too.'''
print foo
print bar


promptDialog(message='what exposure do you want to add?', text='1')
value = promptDialog(query=True, text=True)
value = float(value)
[ x.exposure.set( x.exposure.get() + value ) for x in ls(type='phxAreaLight') ]

loc2.listAttr()
'''

