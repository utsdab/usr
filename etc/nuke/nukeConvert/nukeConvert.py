###########################################################################################
#                                                                                         #
#                                     NUKE CONVERT                                        #
#                                   David Emeny 2014                                      #
#                                                                                         #
# Converts a folder of image files into another format.                                   #
# Give it the source and destination paths and the desired file extension.                #
#                                                                                         #
# Option to convert all images in subfolders and recreate the whole tree.                 #
#                                                                                         #
# Sets jpgs to highest quality, exrs to most efficient compression.                       #
#                                                                                         #
# Sets channels to match source file (rgb, rgba or a)                                     #
#                                                                                         #
###########################################################################################



#Open terminal
#Navigate to the folder containing this py file, or add the path in front
#Use this line to call it:
#nuke -t nukeConvert.py <source_folder> <destination_folder> <desired_file_extension> -sub -overwrite

#<source_folder> = the full path to the folder containing the image files
#<destination_folder> = the full path to the folder you would like them to be rendered to
#<desired_file_extension> = the file type to be converted to eg: jpg
#-sub = optional argument to convert all subfolders too
#-overwrite = optional argument to force overwriting of files, otherwise ignores existing ones

#example:
#converting files to jpg, including all the subfolders and images within them:

#nuke -t nukeConvert.py /mnt/home/davide/Desktop/myImages /mnt/home/davide/Desktop/convertedImages jpg -sub -overwrite

#Or use my nukeConvertGUI.py in Nuke to call this script using a friendly dialogue

import sys
import nuke
import os
import time

#sys.argv[0] = this script name, ignore

#get arguments
inputPath = sys.argv[1]
outputPath = sys.argv[2]
format = sys.argv[3]

#gather all bool args at end in whatever order
boolArgs = []
for i in [4,5,6]:
    try:
        if sys.argv[i]:
            boolArgs.append(sys.argv[i])
    except:
        pass

recursive = False
overwrite = False
keepOpen = False

for arg in boolArgs:

    if arg == "-sub":
        recursive = True

    if arg == "-overwrite":
        overwrite = True

    #-keepOpen = optional argument used when called from GUI to keep terminal open
    if arg == "-keepOpen":
        keepOpen = True


print "---------------------------------"
print "Source: %s" %(inputPath)
print "Destination: %s" %(outputPath)
print "File format: %s" %(format)
print "Include subfolders: %s" %(recursive)
print "Overwrite files: %s" %(overwrite)
print "---------------------------------"

pairs = []


#define recursive function to get list of all paths
#filling the array 'pairs' with input and output paths

def getFilePairs(inputFolderPath, outputFolderPath):

    #put a '/' on the end of paths if needed
    if not inputFolderPath.endswith(os.sep):
        inputFolderPath += os.sep

    if not outputFolderPath.endswith(os.sep):
        outputFolderPath += os.sep


    if not (os.path.exists(inputFolderPath)):
        print "Source folder doesn't exist. Cancelled."
        return None

    if not len(os.listdir(inputFolderPath)) > 0:
        print "Source folder is empty. Cancelled."
        return None


    for file in os.listdir(inputFolderPath):

        #get full path to the file
        inputFilePath = inputFolderPath + file

        #double check this file exists
        if os.path.exists(inputFilePath):

            #if it's a folder, call this function recursively on that folder
            if os.path.isdir(inputFilePath):
                if recursive == True:
                    getFilePairs(inputFilePath, outputFolderPath + file)
                else:
                    #ignore this file (folder)
                    continue

            #double check this isn't a folder when coming back from recursion
            if not os.path.isdir(inputFilePath):

                #generate destination file path for this file
                fileName = os.path.splitext(os.path.basename(file))[0] # get name without extension
                outputFilePath = outputFolderPath + fileName + "." + format

                #add this source file path, paired with it's destination file path 
                #to the global array 'pairs'

                #check if the output file is already there first
                outputExists = os.path.exists(outputFilePath)
                if (not outputExists) or (outputExists and overwrite):
                    #if not, or overwrite is set, add it
                    pairs.append([inputFilePath,outputFilePath])
                    


#define function to create the nuke nodes and do the actual converting
def createNodesAndWrite():
    print "Preparing nuke to start converting... please wait"
    count = 1
    total = (len(pairs))

    #create read and write for each pair of file paths
    #this can result in a massive script with hundreds of nodes,
    #but as there's no GUI, nuke doesn't care

    for pair in pairs:
        r = nuke.nodes.Read(file = pair[0])
        w = nuke.nodes.Write()

        w['file'].fromUserText(pair[1])#ensures other knobs are activated
        w.setInput(0, r)   

        #set up ideal settings for certain formats
        if format == "jpg" or format == "jpeg":
            w['_jpeg_quality'].setValue(1)
        elif format == "exr":
            w['compression'].setValue('Zip (1 scanline)')
            w['datatype'].setValue('16 bit half')

        #set amount of channels to match input
        if len(r.channels()) > 3:
            w['channels'].setValue('rgba')
        else:
            w['channels'].setValue('rgb')

    #execute all write nodes
    start_time = time.time()

    for w in nuke.allNodes('Write'):

        #clear the terminal of previous output
        os.system('cls' if os.name=='nt' else 'clear')

        #print info about this file and time estimation
        print "---------------------------------"
        print "Image %s of %s" %(count,total)
        print w.input(0)['file'].value().split(inputPath).pop()
        print w['file'].value().split(outputPath).pop()
   
        elapsedTime = time.time() - start_time        
        timeRemaining = ((elapsedTime / count) * (total - count))

        if timeRemaining >=0:
            m, s = divmod(timeRemaining, 60)
            h, m = divmod(m, 60)
            
            print "Est. time remaining: %d:%02d:%02d" % (h, m, s)
            print "---------------------------------"

        #create the output folder/subfolder if not there
        thisPath = os.path.dirname(w['file'].value())
        if not (os.path.exists(thisPath)):
            try:
                os.makedirs(thisPath)
            except:
                print "Problem creating output folder: %s" %(thisPath)
                break

        #execute node
        nuke.execute(w.name(),1,1)

        #delete the read and write to clear some memory
        try:
            r = w.input(0)
            nuke.delete(r)
            nuke.delete(w)
        except:
            print "Couldn't delete nodes"

        count+=1

    #all files converted, clear terminal and present results
    os.system('cls' if os.name=='nt' else 'clear')
    m, s = divmod(elapsedTime, 60)
    h, m = divmod(m, 60)
    print "-----------FINISHED!----------"
    print "%s image(s) converted" %(total)
    print "Total time taken: %d:%02d:%02d" % (h, m, s)
    print "------------------------------"
        



#call it the first time
print "Calculating amount of files, please wait..."
getFilePairs(inputPath, outputPath)


#tell user how many files found
print "%s image files to convert" %(len(pairs))

#if over 1000 files ask user if they want to continue 
if len(pairs)>1000:
    answer = None
    while answer not in ['y', 'n']:
        answer = raw_input("This could take some time, continue converting these files? y/n ").lower()

    if answer == 'n':
        sys.exit()

    elif answer == 'y':
        pass

#start converting
if len(pairs)>0:
    createNodesAndWrite()
else:
    print "Either the source folder had no images or the converted images all exist in the destination already."
    if recursive == False or overwrite == False:
        print "Maybe try again with 'Include subfolders' and/or 'Overwrite' ticked."

if keepOpen:
    #force terminal to stay open if called from GUI
    print "It is safe to close this terminal, ignore the warning if you get one."
    os.system("$SHELL")


