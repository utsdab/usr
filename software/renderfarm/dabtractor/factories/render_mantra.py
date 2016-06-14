'''
DABMLB0606627MG:testProject01 120988$ hrender /Users/Shared/UTS_Jobs/TESTING_HOUDINI/HoudiniProjects/testProject01/scripts/torus1.hipnc -d mantra1 -v -f 1 240 -i 1

Usage:

Single frame:   hrender    [options] driver|cop file.hip [imagefile]
Frame range:    hrender -e [options] driver|cop file.hip

driver|cop:     -c /img/imgnet
                -c /img/imgnet/cop_name
                -d output_driver

options:        -w pixels       Output width
                -h pixels       Output height
                -F frame        Single frame
                -b fraction     Image processing fraction (0.01 to 1.0)
		-t take		Render a specified take
                -o output       Output name specification
                -v              Run in verbose mode
                -I              Interleaved, hscript render -I

with "-e":	-f start end    Frame range start and end
                -i increment    Frame increment

Notes:  1)  For output name use $F to specify frame number (e.g. -o $F.pic).
        2)  If only one of width (-w) or height (-h) is specified, aspect ratio
            will be maintained based upon aspect ratio of output driver.

Error: Cannot specify frame range without -e.
'''
