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


################################################################################
frange = nuke.FrameRange(framerange)
################################################################################
width=1280
height=720
heightbottom=20
heighttop=700
################################################################################
readNode = nuke.nodes.Read(
            file = inputfile,
            first=frange.first(),
            last=frange.last(),
            on_error="black",
            colorspace="linear",
            raw=True)
################################################################################
cropNode = nuke.nodes.Crop(crop=True)
cropNode["box"].setValue([0,heightbottom,width,heighttop])
cropNode.setInput(0,readNode)
################################################################################
reformatNode2 = nuke.nodes.Reformat(
            format="{w} {h} 0 0 {w} {h} 1 HD_720".format(
                w=width,
                h=height),
            resize="width",
            center=True,
            black_outside=True)
################################################################################
reformatNode2.setInput(0, cropNode)
################################################################################
textNode1 = nuke.nodes.Text2()
textNode1["font"].setValue("Courier 10 Pitch","Regular")
textNode1["message"].setValue("[format %04d [frame]]")
textNode1["box"].setValue([0,0,width,height])
textNode1["xjustify"].setValue("right")
textNode1["yjustify"].setValue("bottom")
textNode1["global_font_scale"].setValue(0.2)
################################################################################
textNode1.setInput(0,cropNode)
################################################################################
textNode2 = nuke.nodes.Text2()
textNode2["font"].setValue("Courier 10 Pitch","Regular")
textNode2["message"].setValue("[basename [value [topnode].file]]")
textNode2["box"].setValue([0,0,width,height])
textNode2["xjustify"].setValue("left")
textNode2["yjustify"].setValue("bottom")
textNode2["global_font_scale"].setValue(0.2)
################################################################################
textNode2.setInput(0,textNode1)
################################################################################
textNode3 = nuke.nodes.Text2()
textNode3["font"].setValue("Courier 10 Pitch","Regular")
textNode3["message"].setValue("[date %Y]-[date %m]-[date %d]")
textNode3["box"].setValue([0,0,width,height])
textNode3["xjustify"].setValue("right")
textNode3["yjustify"].setValue("top")
textNode3["global_font_scale"].setValue(0.2)
################################################################################
textNode3.setInput(0,textNode2)
################################################################################
textNode4 = nuke.nodes.Text2()
textNode4["font"].setValue("Courier 10 Pitch","Regular")
textNode4["message"].setValue("[join [lrange [file split [value [topnode].file]] 4 4] /]")
textNode4["box"].setValue([0,0,width,height])
textNode4["xjustify"].setValue("left")
textNode4["yjustify"].setValue("top")
textNode4["global_font_scale"].setValue(0.2)
################################################################################
textNode4.setInput(0, textNode3)
################################################################################
writeNode = nuke.nodes.Write()
writeNode["file"].setValue(outputfile)
writeNode["file_type"].setValue("mov")
writeNode["meta_codec"].setValue("apco")
#w["meta32_codec"].setValue("apco")
#w["meta64_codec"].setValue("apco")
writeNode["mov64_bitrate"].setValue(20000)
writeNode["mov64_bitrate_tolerance"].setValue(40000000)
writeNode["mov64_quality_min"].setValue(2)
writeNode["mov64_quality_max"].setValue(31)
writeNode["mov64_gop_size"].setValue(12)
writeNode["mov64_b_frames"].setValue(0)
################################################################################
writeNode.setInput(0, textNode4)
################################################################################
nuke.execute("Write1",frange.first(),frange.last(),frange.increment())

