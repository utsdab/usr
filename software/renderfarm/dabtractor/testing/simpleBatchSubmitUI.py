#!/opt/pixar/Tractor-2.0/bin/rmanpy
"""
This is a tkinter front end to the dabtractor 2.0 job authoring api to submit basic maya batch renders
12th Oct 2014
Matt Gidney
consider this v1.0
20141013:9pm


Standard Widgets

    Basic Widgets: Toplevel, Frame, Button, Checkbutton, Entry, Label, Listbox, OptionMenu, Photoimage,
                    Radiobutton, Scale.
    Fancy Widgets: Canvas, Text. These have taggable contents that act like objects.
    Hard to Use: Menu, Menubutton, Scrollbar.

Tk Variables: StringVar, IntVar, DoubleVar, BooleanVar. These are data containers needed by certain widgets,
are handy with many others for easy access to contents, and can trigger callbacks when their data is changed.

Extra Modules (not loaded by "import Tkinter")
    tkFont defines the Font class for font metrics and getting names of fonts. If you set a widget's font to a
    Font object, then changing the Font live-updates the widget. To get a font object from the name of a
    font (which is all that wdg["font"] gives you): tkFont.Font(font=name_of_font).
    FileDialog defines FileDialog, LoadFileDialog, SaveFileDialog. Here is an example:
    fdlg = FileDialog.LoadFileDialog(root, title="Choose A File")
        fname = fdlg.go() # opt args: dir_or_file=os.curdir, pattern="*", default="", key=None)
        if file == None: # user cancelled
    tkColorChooser defines askcolor(initialcolor), which returns a user-chosen color.
    tkSimpleDialog defines askinteger(title, prompt, initialvalue, minvalue, maxvalue), askfloat and askstring.

Examine the source code in .../Lib/lib-tk to find others and see examples of use.

Geometry Management  ######

The Packer
    pack(side="top/right/bottom/left", expand=0/1, anchor="n/nw/w...", fill="x/y/both")
    By default, widgets are centered within a parcel; use anchor to change this.
    By default, widgets do not grow to fill the parcel; use expand and fill to change this.
The Gridder
    grid(row, column, rowspan=?, columnspan=?, sticky="news", ipadx=?, ipady=?, padx=?, pady=?)
    columnconfigure(row, weight=?, minsize=?, pad=?)
    columnconfigure(column, weight=?, minsize=?, pad=?)

Each row and column shrinks to fit the smallest element in that row and column.
By default, widgets are centered within a cell and do not grow to fill it; use sticky to change this.
By default rows and columns to not grow when the user resizes a window; set nonzero weights using
rowconfigure and columnconfigure to change this.
Rowconfigure and columnconfigure are also helpful to solve a common problem: spanning can cause rows or
columns to increase in size. Suppose you have two columns that are 20 and 30 pixels wide, respectively.
Suppose you also want to grid a "wide widget" 100 pixels wide without making the existing columns wider.
Simply gridding the object to span the two columns will force them to grow so the total
spans 100 pixels (they each gain 25 pixels, for a total of 45 and 55 pixels, respectively).
Gridding the wide object to span more columns reduces the problem (by distributing the extra pixels
among more columns) but does not solve it. The solution is to have the wide widget span at least one
extra column and use columnconfigure to configure the extra column to have weight 1.

Getting Information from Widgets

    There are several ways of retrieving configuration information from a widget:

    Treat it like a dictionary: aWidget["text"]. (Note: this works both for setting and getting information.)
    Use the cget method: aWidget.cget("text").
    You can retrieve a dictionary of all settings by calling configure with no arguments: aWidget.configure().


"""
__author__ = '120988'
__version__ = '1.00'

from Tkinter import *
import ttk
import tkMessageBox
import datetime
import tkFileDialog, Tkconstants
import dabtractor.api.author as author
import sys
import os

author.setEngineClientParam(hostname="dabtractor-engine", port=5600, user="mattg", debug=True)
user = os.getenv("USER")



class Window(object):
    def __init__(self, master):
        """Construct the main window interface
        """
        self.master = master

        # Options for buttons
        self.button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}

        Label(master, text="Command").grid(row=14, column=0)
        self.command = StringVar()
        self.command.set("ls -lrt")
        self.bar1 = Entry(self.master, textvariable=self.command, width=60).grid(row=14, column=1, sticky=W + E)

        # Buttons
        self.cbutton = Button(self.master, text='SUBMIT', command=lambda: self.submit())
        self.cbutton.grid(row=15, column=3, sticky=W + E)

        self.vbutton = Button(self.master, text='VALIDATE', command=lambda: self.validate())
        self.vbutton.grid(row=15, column=1, sticky=W + E)

        self.vbutton = Button(self.master, text='CANCEL', command=lambda: self.cancel())
        self.vbutton.grid(row=15, column=0, sticky=W + E)



    # def openfile(self):
    #     self.filename = tkFileDialog.askopenfilename(parent=self.master, initialdir=self.dirname,
    #                                                  title=self.filetext,
    #                                                  filetypes=[('maya ascii', '.ma'),
    #                                                             ('maya binary', '.mb')])  ## filename not filehandle
    #     self.filebut["text"] = str(self.filename) if self.filename else self.filetext




    def validate(self):
        print "Validate Button"
        print "Command to Run: %s"%self.command.get()

    def submit(self):
        try:
            print "Submit Button"
            self.master.destroy()
        except:
            print "Submit Button Wierdness"

    def cancel(self):
        print "Camcel Button"
        self.master.destroy()
        sys.exit("Cancelled")

    def selectRenderHome(self):
        print "Select Render Home"

class SimpleJob(object):
    '''
    This is a simple job with a single command
    '''

    def __init__(self,window):
        '''
        initialize the job
        :return:
        '''

        self.command = window.command.get()


    def build(self):
        '''
        build the job
        :return:
        '''

        self.job = author.Job(title="Simple Command Job",
                              priority=100,
                              envkey=["maya2015"],
                              service="PixarRender")

        #############################
        task = author.Task(title="Single Command", service="PixarRender")
        command1 = author.Command(
            argv=[os.path.join (self.command)])
        task.addCommand(command1)
        self.job.addChild(task)

        print "\n{}".format(self.job.asTcl())

    def spool(self):
        '''
        spool the job
        :return:
        '''
        try:
            print "Job Spool Success"
            #self.job.spool(owner="mattg")
            self.job.spool()
        except SpoolError:
            print "Job Spool Error"




if __name__ == '__main__':
    root = Tk()
    root.title("Tractor Simple Batch Submit {u} {f}".format(u=user,f="DAB"))
    window = Window(root)
    root.mainloop()

    j = SimpleJob(window)
    j.build()
    j.spool()

    try:
        root.destroy()
    except:
        print "Cleanup found no dangling windows"


