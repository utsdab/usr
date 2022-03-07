'''
This script is called by nuke on the farm like this:
/Applications/Nuke9.0v6/Nuke9.0v6.app/Contents/MacOS/Nuke9.0v6 -V 2 -t /Volumes/dabrender/usr/custom/nuke/proxy_script_templates/nuke_proxy_v002.py /Volumes/dabrender/work/olivertabbott/3D_Project_2.5/renderman/set.0058_animaticv5_clean/images/set.0058_animaticv5_clean_###.exr /var/tmp/out.mov "1-720x1"

ie
Nuke -t this_script img_seq output range


Burning text in nuke with the text2 node is rubbish
'''
import sys
import os

def splitInputPath(inputpath):
	basename = os.path.basename(inputpath)
	


print "\n"
print "-----------UTS PROXY SCRIPT------------"
print "ARGS: {}".format(sys.argv)
inputfile=sys.argv[1]
print "Inputfile = {}".format(inputfile)
outputfile=sys.argv[2]
print "Outputfile = {}".format(outputfile)
framerange = sys.argv[3]
print "FRAMERANGE",framerange

frange = nuke.FrameRange(framerange)

r = nuke.nodes.Read(file = inputfile,
	first=frange.first(),
	last=frange.last()
)

rf = nuke.nodes.Reformat(
	format="1280 720 0 0 1280 720 1 HD_720"
)
rf.setInput(0, r)

t = nuke.nodes.Text2()

#t["font"].setValue("Courier 10 Pitch","Regular")
#t["message"].setValue("12345")
#t["box"].setValue([0,0,1280,720])
#t["xjustify"].setValue("right")
#t["yjustify"].setValue("bottom")


t.setInput(0,rf)

w = nuke.nodes.Write()
w["file"].setValue(outputfile)
w["file_type"].setValue("mov")
w["meta_codec"].setValue("apco")
#w["meta32_codec"].setValue("apco")
#w["meta64_codec"].setValue("apco")
w["mov64_bitrate"].setValue(20000)
w["mov64_bitrate_tolerance"].setValue(40000000)
w["mov64_quality_min"].setValue(2)
w["mov64_quality_max"].setValue(31)
w["mov64_gop_size"].setValue(12)
w["mov64_b_frames"].setValue(0)
w.setInput(0, t)

nuke.execute("Write1",frange.first(),frange.last(),frange.increment())
nuke.scriptSave("junk.nk")
