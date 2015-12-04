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


example local queue
maya -batch -command "renderManBatchRenderScript(0,1,1,1,0)"
     -file /Users/Shared/UTS_Jobs/MAYA///_rmsTestingShaders_pid52888_1209155904.ma
     -proj /Users/Shared/UTS_Jobs/MAYA
/bin/rm -rf "/Users/Shared/UTS_Jobs/MAYA/_rmsTestingShaders_pid52888_1209155904.ma"




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

        self.dirtext = 'Select your project folder, or...'
        self.filetext = 'Select your maya scene file'
        self.workspacetext = 'Select the workspace.mel file in your project'
        self.workspaceerrortext = 'Warning - no workspace.mel found!'
        self.initialProjectPath = "/Volumes/Renderfarm/"

        # Options for buttons
        self.button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}

        Label(master, text="Project Dir").grid(row=1, column=0)
        self.dirbut = Button(self.master, text=self.dirtext, fg='black', command=self.opendirectory)
        self.dirbut.pack(**self.button_opt)  ## must pack separately to get the value to dirbut
        self.dirbut.grid(row=1, column=1, sticky=W + E)

        Label(master, text="Workspace.mel").grid(row=2, column=0)
        self.workspacebut = Button(self.master, text=self.workspacetext, fg='black', command=self.openworkspace)
        self.workspacebut.pack(**self.button_opt)  ## must pack separately to get the value to dirbut
        self.workspacebut.grid(row=2, column=1, sticky=W + E)



        Label(master, text="Scene File").grid(row=3, column=0)
        self.filebut = Button(self.master, text=self.filetext, fg='black',
                              command=self.openfile)
        self.filebut.pack(**self.button_opt)
        self.filebut.grid(row=3, column=1, sticky=W + E)

        Label(master, text="Frame Start").grid(row=6, column=0)
        self.sf = StringVar()
        self.sf.set("1")
        self.bar3 = Entry(self.master, textvariable=self.sf, width=8).grid(row=6, column=1, sticky=W)

        Label(master, text="Frame End").grid(row=7, column=0)
        self.ef = StringVar()
        self.ef.set("100")
        self.bar4 = Entry(self.master, textvariable=self.ef, width=8).grid(row=7, column=1, sticky=W)

        Label(master, text="By").grid(row=8, column=0)
        self.bf = StringVar()
        self.bf.set("1")
        self.bar5 = Entry(self.master, textvariable=self.bf, width=8).grid(row=8, column=1, sticky=W)

        Label(master, text="Frame Chunks").grid(row=9, column=0)
        self.fch = StringVar()
        self.fch.set("5")
        self.bar6 = Entry(self.master, textvariable=self.fch, width=8).grid(row=9, column=1, sticky=W)

        Label(self.master, text="Maya Version").grid(row=10, column=0)
        self.mversion = StringVar()
        self.mversion.set("2015")
        combobox = ttk.Combobox(master, textvariable=self.mversion)
        combobox.config(values=("2014", "2015"))
        combobox.grid(row=10, column=1, sticky=W)

        Label(self.master, text="Renderer").grid(row=11, column=0)
        self.renderer = StringVar()
        self.renderer.set("mentalray")
        combobox = ttk.Combobox(master, textvariable=self.renderer)
        combobox.config(values=("mentalray", "maya", "rendermanStudio"))
        combobox.grid(row=11, column=1, sticky=W)

        Label(self.master, text="Output").grid(row=12, column=0)
        self.outputname = StringVar()
        self.outputname.set("<Scene>/<Scene>")
        combobox = ttk.Combobox(master, textvariable=self.outputname)
        combobox.config(values=("<Scene>/<Scene>",
                                "<Scene>/<Scene>-<Camera>",
                                "<Scene>/<Scene>-<Camera>-<Layer>"))
        combobox.grid(row=12, column=1, sticky=W + E)

        Label(self.master, text="Resolution").grid(row=13, column=0)
        self.resolution = StringVar()
        self.resolution.set("720p")
        combobox = ttk.Combobox(master, textvariable=self.resolution)
        combobox.config(values=("720p",
                                "1080p",
                                "540p"))
        combobox.grid(row=13, column=1, sticky=W + E)

        Label(master, text="Other Options").grid(row=14, column=0)
        self.options = StringVar()
        self.options.set("")
        self.bar7 = Entry(self.master, textvariable=self.options, width=40).grid(row=14, column=1, sticky=W + E)


        # Buttons
        self.cbutton = Button(self.master, text='SUBMIT', command=lambda: self.submit())
        self.cbutton.grid(row=15, column=3, sticky=W + E)

        self.vbutton = Button(self.master, text='VALIDATE', command=lambda: self.validate())
        self.vbutton.grid(row=15, column=1, sticky=W + E)

        self.vbutton = Button(self.master, text='CANCEL', command=lambda: self.cancel())
        self.vbutton.grid(row=15, column=0, sticky=W + E)

    def openfile(self):
        self.filename = tkFileDialog.askopenfilename(parent=self.master, initialdir=self.dirname,
                                                     title=self.filetext,
                                                     filetypes=[('maya ascii', '.ma'),
                                                                ('maya binary', '.mb')])  ## filename not filehandle
        self.filebut["text"] = str(self.filename) if self.filename else self.filetext

    def opendirectory(self):
        self.dirname = tkFileDialog.askdirectory(parent=self.master, initialdir=self.initialProjectPath, title=self.dirtext)
        self.dirbut["text"] = str(self.dirname) if self.dirname else self.dirtext
        _possible = "%s/workspace.mel" % (self.dirname)
        if os.path.exists(_possible):
            self.workspace = _possible
            self.workspacebut["text"] = str(self.workspace) if self.workspace else self.workspacetext
        else:
            self.workspacebut["text"] = self.workspaceerrortext


    def openworkspace(self):
        self.workspace = tkFileDialog.askopenfilename(parent=self.master, initialdir=self.initialProjectPath,
                                                      title=self.workspacetext,
                                                      filetypes=[
                                                          ('maya workspace', '.mel')])  ## filename not filehandle
        self.dirname = os.path.dirname(self.workspace)
        self.workspacebut["text"] = str(self.workspace) if self.workspace else self.workspacetext
        self.dirbut["text"] = str(self.dirname) if self.dirname else self.dirtext

    def validate(self):
        print "validate"

    def submit(self):
        try:
            print "submit"
            print "Project: %s" % self.dirname
            print "SceneFile: %s" % self.filename
            print "Start: %s" % self.sf.get()
            print "End: %s" % self.ef.get()
            print "By: %s" % self.bf.get()
            print "Chunk: %s" % self.fch.get()
            print "Maya: %s" % self.mversion.get()

            self.master.destroy()
        except:
            pass

    def cancel(self):
        print "Camcelled"
        self.master.destroy()

    def selectRenderHome(self):
        print "select render home"


class MayaBatchJob(object):
    '''
    This is a maya batch job
    '''

    def __init__(self):

        self.mayaversion = 2014
        self.mayaprojectpath = '/Volumes/Renderfarm/Render4/mattg/maya'
        self.mayascene = 'scene.0001.ma'
        self.startframe = 100
        self.endframe = 200
        self.byframe = 1
        self.framechunks = 10
        self.renderer = "mr"
        self.renderdirectory = "renderOutput"
        self.imagetemplate = "<Scene>/<Scene>-<Camera>_<Layer>"
        self.options = ""
        self.localhost = "localhost"
        self.localworkarea = "/scratch2/dabRenderJobs/"
        self.centralworkarea = "138.25.195.200"

    def getValues(entries):
        for entry in entries:
            field = entry[0]
            text = entry[1].get()
            print('%s: "%s"' % ( field, text))

    def build(self):
        self.__mayascenefullpath = "%s/%s" % (self.mayaprojectpath, self.mayascene)
        self.__mayascenebase = os.path.splitext(self.mayascene)[0]

        self.job = author.Job(title="MayaBatch Render Job",
                              priority=100,
                              envkey=["maya%s" % self.mayaversion],
                              service="PixarRender")

        ############### task 1 ##############
        task = author.Task(title="Make output directory", service="PixarRender")
        makediectory = author.Command(
            argv=["mkdir", os.path.join (self.mayaprojectpath, "images")])
        task.addCommand(makediectory)
        self.job.addChild(task)

        ############### task 2 ###########
        task = author.Task(title="Copy Project Locally", service="PixarRender")
        copyin = author.Command(argv=["scp", "%s:%s" % (self.centralworkarea,self.mayaprojectpath),
                                      "%s:%s" % (self.localhost, self.localworkarea)])
        task.addCommand(copyin)
        self.job.addChild(task)


        ############### task 3 ##############
        task = author.Task(title="Rendering", service="PixarRender")

        if ((self.endframe - self.startframe) < self.framechunks):
            self.framechunks = 1
            chunkend = self.endframe
        else:
            chunkend = self.startframe + self.framechunks

        chunkstart = self.startframe

        while (self.endframe >= chunkstart):

            if chunkend >= self.endframe:
                chunkend = self.endframe

            render = author.Command(argv=["mayabatch", self.options,
                                          "-proj", self.mayaprojectpath,
                                          "-start", "%s" % (chunkstart),
                                          "-end", "%s" % (chunkend),
                                          "-by", self.byframe,
                                          "-rd", self.renderdirectory,
                                          "-im", self.imagetemplate,
                                          "-r", self.renderer,
                                          self.options,
                                          self.__mayascenefullpath])

            task.addCommand(render)
            chunkstart = chunkend + 1
            chunkend = chunkend + self.framechunks

        self.job.addChild(task)

        ############### task 4 ###############
        task = author.Task(title="Copy Project Back", service="PixarRender")
        copyout = author.Command(argv=["scp", "%s:%s" % (self.localhost, self.localworkarea),
                                       "%s:%s" % (self.centralworkarea,self.mayaprojectpath)])
        task.addCommand(copyout)
        self.job.addChild(task)

        print "\n{}".format(self.job.asTcl())

    def spool(self):
        print "spool"
        # print dir(self.job.spool)
        # print help(self.job.spool)
        try:
            print "spool success"
            self.job.spool(owner="mattg")
        except SpoolError:
            print "a spool error"


if __name__ == '__main__':
    root = Tk()
    root.title("Tractor Maya Batch Submit {u} {f}".format(u=user,f="DAB"))
    window = Window(root)
    root.mainloop()

    j = MayaBatchJob()

    try:
        j.mayascene = window.filename
        j.mayaprojectpath = window.dirname
        j.framechunks = int(window.fch.get())
        j.startframe = int(window.sf.get())
        j.endframe = int(window.ef.get())
        j.byframe = int(window.bf.get())
        j.renderer = "mr"
        j.renderdirectory = "renders"
        j.imagetemplate = "<Scene/<Scene>_<Layer>_<Camera>"
        j.options = ""

        j.build()
        # j.spool()
    except:
        print "something wrong"
    try:
        root.destroy()
    except:
        pass



