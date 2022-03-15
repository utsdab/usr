##################################################################################
#                                                                                #
#                             NUKE CONVERT GUI 1.0                               #
#                               David Emeny 2014                                 #
#                                                                                #
#                                                                                #
##################################################################################

#GUI to run nukeConvert.py from within Nuke
#To avoid user using the terminal themselves.

import nuke
import os
import subprocess
import time

#find where this file is and assume nukeConvert.py is in the same place
dirname, filename = os.path.split(os.path.abspath(__file__))
scriptPath = dirname + "/nukeConvert.py"


start_time = time.time()

def showWindow():

    if os.path.exists(scriptPath) and os.path.basename(scriptPath) == "nukeConvert.py":

        #show panel
        panel = panelName()
        panel.showModal()

        if panel.result == 0:
            return None

    else:
        nuke.message("Cannot find nukeConvert.py. Make sure it's in the same place as nukeConvertGUI.py")
        return None


if nuke.env['gui']:
    import nukescripts

    #define custom panel class
    class panelName(nukescripts.PythonPanel):
        def __init__(self):
            nukescripts.PythonPanel.__init__(self, 'Nuke Convert', 'nukeConvert')

            self.result = None

            self.myTextKnob1 = nuke.Text_Knob('info1','', 'Uses Nuke in the background to convert lots of image files from one format to another.\n')
            self.addKnob(self.myTextKnob1)

            #horizontal rule
            divider3 = nuke.Text_Knob("divider3","","")
            self.addKnob(divider3)

            self.sourceBox = nuke.String_Knob('sourceBox','Source folder', '')
            self.addKnob(self.sourceBox)

            self.findDir1 = nuke.PyScript_Knob("Find Source","Find Source")
            self.addKnob(self.findDir1)
     
            self.destBox = nuke.String_Knob('destBox','Destination folder', '')
            self.addKnob(self.destBox)

            self.findDir2 = nuke.PyScript_Knob("Find Destination","Find Destination")
            self.addKnob(self.findDir2)

            self.formatChoice = nuke.Enumeration_Knob('formatChoice', 'Destination format', ["jpg","exr","dpx","tif","sga","tga","png"])
            self.addKnob(self.formatChoice)

            #horizontal rule
            divider1 = nuke.Text_Knob("divider1","","")
            self.addKnob(divider1)

            self.subfolders = nuke.Boolean_Knob( 'subfolders', 'Include subfolders' )
            self.subfolders.setValue(False)
            self.addKnob( self.subfolders )

            self.overwrite = nuke.Boolean_Knob( 'overwrite', 'Overwrite existing files in destination' )
            self.overwrite.setValue(False)
            self.addKnob( self.overwrite )

            #horizontal rule
            divider2 = nuke.Text_Knob("divider2","","")
            self.addKnob(divider2)

            self.myTextKnob = nuke.Text_Knob('info','', 'When you press OK, a terminal will appear to show you the progress.\n\n')
            self.addKnob(self.myTextKnob)

            #buttons
            self.cancel = nuke.PyScript_Knob("Cancel","Cancel")
            self.addKnob(self.cancel)
            self.ok = nuke.PyScript_Knob("OK","OK")
            self.addKnob(self.ok)

            
            
            #force a minimum size
            self.setMinimumSize(800, 200)

        def knobChanged(self,knob):

            if (knob == self.ok):
                #check all input boxes are valid
                allValid = False
                try:
                    #get values from the panel
                    source = self.sourceBox.value()
                    dest = self.destBox.value()
                    
                    if source != "" and dest != "" and os.path.isdir(source) and os.path.isdir(dest):
                        allValid = True

                except:
                    pass

                #cancel if values weren't valid
                if allValid == True:
    
                    #OK BUTTON PRESSED
                    self.result = 1
                    self.finishModalDialog(True)

                    if self.subfolders.value() == True:
                        sub = "-sub"
                    else:
                        sub = ""

                    if self.overwrite.value() == True:
                        overwrite = "-overwrite"
                    else:
                        overwrite = ""


                    #create terminal string
                    #eg:
                    #"gnome-terminal -x nuke -t /mnt/home/myUserName/.nuke/python/nukeConvert.py /mnt/home/myUserName/Desktop/origImages /mnt/home/myUserName/Desktop/convertedImages jpg -sub -overwrite -keepOpen"                    

                    theString = "gnome-terminal -x nuke -t %s %s %s %s %s %s -keepOpen" %(scriptPath,source,dest,self.formatChoice.value(),sub,overwrite)

                    #run it in a subprocess
                    #brings up a terminal and shows the output to the user
                    subprocess.Popen(theString, shell=True)
                    


                else:
                    nuke.message("Please check you have a valid source and destination.")

                
            elif (knob == self.cancel):
                #CANCEL BUTTON PRESSED
                self.result = 0
                self.finishModalDialog(True)



            elif (knob == self.findDir1):
                #findDir1 BUTTON PRESSED
                
                path = nuke.getFilename('Choose source folder', '*.*')
                path = os.path.dirname(path)
                self.sourceBox.setText(path)
              

            elif (knob == self.findDir2):
                pass
                #findDir2 BUTTON PRESSED
                
                path = nuke.getFilename('Choose destination folder', '*.*')
                path = os.path.dirname(path)
                self.destBox.setText(path)



