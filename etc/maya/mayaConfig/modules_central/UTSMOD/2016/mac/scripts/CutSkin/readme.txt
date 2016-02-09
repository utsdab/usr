SCRIPT:		cutSkin v1.0
AUTHOR:		Christian Stejnar - Technical Artist
CONTACT:	christian.stejnar@rockstarvienna.com
WEB:		www.8ung.at/stejnar

DATE:		05/01/2006

DESCRIPTION:
The basic idea of cutSkin was to convert a smooth skinnned geometry into a separated group of single meshes - each single separated mesh ist parented to its most influencing bone. The result is a "rigid" version of your smooth skinned mesh - good for playback - easy to animate! 

WORKFLOW:
Simply select a smooth skinned mesh and press the "START" button. This will convert the given mesh to a collection of separated rigid meshes parented to their corresponding bones - these resulting meshes are stored in two different layers. Layer "CutSkin" holds the parented and separated results of the smooth skinned mesh - layer "SourceMesh" holds the original mesh. If checked in UI the resulting cutSkin meshes are reduced by the given percentage.

The workflow consists ob three automatic steps:

1. Polygon reduction (if checked in UI)
2. Gathering skinning information in order to sort the vertex information per joint (max. weight per joint)
3. Detaching the vertices on the given max. weights per joint into new meshes and parenting them to the joint hierarchy.

INSTALL:
Place the MEL file in one of your Maya script folders, start Maya and type cutSkin in your commandline

MAYA:
Currently tested in Maya6.5 and Maya 7.0

KNOWN ISSUES:
Performance: 
Some of the procedures should be done using the Maya API. 
On high detail geometry (polycount 100.000 plus) the calculation tends to be very timeconsuming :-(

Polygon reduction:
The standard Maya polygon reduction produces sometimes strange results. This means that in certain cases the cutSkin results parented to joints are messed up a little bit - eg. dislocated vertices.

IDEA: 
The first idea for a tool like this was from Leander Schock (senior animator at rockstarvienna) - then after a lot of different approaches the outcome was the cutSkin.mel ;-)

UPCOMING:
Improve performance using Maya API instead of MEL.
Fix polygon reduction issues.
