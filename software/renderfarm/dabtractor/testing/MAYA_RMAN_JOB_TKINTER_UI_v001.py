#!/opt/pixar/Tractor-2.0/bin/rmanpy

###############################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
###############################################################

__author__ = '120988'
__version__ = '1.01'

from Tkinter import *
import ttk
import tkMessageBox
import datetime
import tkFileDialog, Tkconstants
import tractor.api.author as author
import sys
import os

author.setEngineClientParam(hostname="tractor-engine", port=5600, user="mattg", debug=True)
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
        self.filename=""
        self.test = False

        # vcmd = (self.register(self._validate), '%s', '%P')
        # okayCommand = self.register(isOkay)

        if self.test:
            self.dabrender = "/Volumes/testrender"
            self.initialProjectPath = "/Volumes/testrender/"
        else:
            self.dabrender = "/Volumes/dabrender"
            self.initialProjectPath = "/Volumes/dabrender/"

        if os.path.ismount(self.dabrender):
            logger.info("Found %s" % self.dabrender)
        else:
            self.initialProjectPath = None
            logger.critical("Cant find central filer mounted %s" % self.dabrender)
            raise Exception, "dabrender not a valid mount point"

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

        # Label(self.master, text="Maya Version").grid(row=10, column=0)
        # self.mversion = StringVar()
        # self.mversion.set("2015")
        # combobox = ttk.Combobox(master, textvariable=self.mversion)
        # combobox.config(values=("2015"))
        # combobox.grid(row=10, column=1, sticky=W)

        # Label(self.master, text="Renderer").grid(row=11, column=0)
        # self.renderer = StringVar()
        # self.renderer.set("rman")
        #
        # okayCommand = master.register(self.isOkay)
        #
        # combobox1 = ttk.Combobox(master, textvariable=self.renderer, postcommand=lambda: self.optionspostcommand(),
        #                             # validate='all', validatecommand=lambda: self.optionscommand())
        #                             validate='all', validatecommand=(okayCommand, '%P', '%V', '%s', '%S'))
        #
        #
        # combobox1.config(values=("mr", "maya", "rman"))
        # combobox1.grid(row=11, column=1, sticky=W)

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
                                "540p",
                                ""))
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
        self.dirname = tkFileDialog.askdirectory(parent=self.master, initialdir=self.initialProjectPath,
                                                 title=self.dirtext)
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
        logger.info("Validate")

    def optionspostcommand(self):
        logger.info("Renderer change - Options post will change from %s" % self.renderer.get())
        # logger.info("oo %s" % window.bar7.current([0])

    def optionscommand(self):
        logger.info("Renderer change - Options validate will change to %s" % self.renderer.get())

    def isOkay(self, why, where, what, other):
        logger.info("isOkay: %s : %s : %s : %s :" % (why, what, where, other))

    def submit(self):
        try:
            logger.info("Submit")
            logger.info("Project: %s" % self.dirname)
            logger.info("SceneFile: %s" % self.filename)
            logger.info("Start: %s" % self.sf.get())
            logger.info("End: %s" % self.ef.get())
            logger.info("By: %s" % self.bf.get())
            logger.info("Chunk: %s" % self.fch.get())
            logger.info("Maya: %s" % self.mversion.get())

            self.master.destroy()
        except Exception, err:
            logger.warn("Problem submitting %s" % err)

    def cancel(self):
        logger.info("Camcelled")
        self.master.destroy()

    def selectRenderHome(self):
        logger.info("Select render home")


class MayaBatchJob(object):
    """
    This is a maya batch job
    """

    def __init__(self,  mayaversion="2015",
                        projectpath="/Volumes/dabrender/",
                        scenefile="scene.0001.ma",
                        start=1, end=100, by=1,
                        renderer="rman",
                        renderdirectory="renderout",
                        options=""):

        self.mayaversion = mayaversion
        self.mayaprojectpath = projectpath
        self.mayascene = scenefile
        self.startframe = start
        self.endframe = end
        self.byframe = by
        self.framechunks = 10
        self.renderer = renderer
        self.renderdirectory = renderdirectory
        self.imagetemplate = "<Scene>/<Scene>-<Camera>_<Layer>"
        self.options = options
        self.localhost = "localhost"
        self.localworkarea = "/scratch2/dabRenderJobs/"
        self.centralworkarea = "138.25.195.200"

    def getValues(entries):
        for entry in entries:
            field = entry[0]
            text = entry[1].get()
            logger.info('%s: "%s"' % ( field, text))

    def expandArgumentString(self, inputargs=""):
        """
        This takes a string like "-r 2 -l 4" and returns
        {-r} {2} {-l} {4} which is what tractor wants for arguments
        """
        arglist=inputargs.split(" ")
        outputstring = "} {".join(arglist)
        return outputstring

    def usedirmap(self,inputstring):
        """
        wraps a string in the bits needed for dirmap functionality in tractor eg %D(mayabatch)
        :param inputstring: mayabatch
        :return: %D(mayabatch)
        """
        return '%D({thing})'.format(thing=inputstring)

    def build(self):
        """
        main build of job
        :return:
        """
        self.__mayascenefullpath = "%s/%s" % (self.mayaprojectpath, self.mayascene)
        self.__mayascenebase = os.path.splitext(self.mayascene)[0]

        self.job = author.Job(title="Render Job - (maya)",
                              priority=100,
                              envkey=["maya%s" % self.mayaversion],
                              service="PixarRender")

        # ############## general commands ############
        env = author.Command(argv = ["printenv"])
        pwd = author.Command(argv = ["pwd"])

        # ############## task 1 ##############
        task1 = author.Task(title="Make output directory", service="PixarRender")
        makediectory = author.Command(
            argv=["mkdir", os.path.join(self.mayaprojectpath, "images")])
        task1.addCommand(makediectory)
        self.job.addChild(task1)

        # ############## task 2 ###########
        task2 = author.Task(title="Copy Project Locally", service="PixarRender")
        copyin = author.Command(argv=["scp", "%s:%s" % (self.centralworkarea, self.mayaprojectpath),
                                      "%s:%s" % (self.localhost, self.localworkarea)])
        task2.addCommand(copyin)
        self.job.addChild(task2)

        # ############## task 3 ##############
        if self.renderer == "mr":
            pass
        elif self.renderer == "rman":
            pass
        elif self.renderer == "maya":
            pass

        task3 = author.Task(title="Rendering", service="PixarRender")

        if (self.endframe - self.startframe) < self.framechunks:
            self.framechunks = 1
            chunkend = self.endframe
        else:
            chunkend = self.startframe + self.framechunks

        chunkstart = self.startframe

        while self.endframe >= chunkstart:

            if chunkend >= self.endframe:
                chunkend = self.endframe

            commonargs = [
                "Render",
                "-r", self.renderer,
                "-proj", self.mayaprojectpath,
                "-start", "%s" % chunkstart,
                "-end", "%s" % chunkend,
                "-by", self.byframe,
                "-rd", self.renderdirectory,
                "-im", self.imagetemplate
                ]

            rendererspecificargs = [
                self.expandArgumentString(self.options),
                self.__mayascenefullpath
                ]

            finalargs = commonargs + rendererspecificargs

            render = author.Command(argv=finalargs)

            task3.addCommand(render)
            chunkstart = chunkend + 1
            chunkend += self.framechunks

        self.job.addChild(task3)

        # ############## task 4 ###############
        task4 = author.Task(title="Copy Project Back", service="PixarRender")
        copyout = author.Command(argv=["scp", "%s:%s" % (self.localhost, self.localworkarea),
                                       "%s:%s" % (self.centralworkarea, self.mayaprojectpath)])
        task4.addCommand(copyout)
        self.job.addChild(task4)

        print "\n{}".format(self.job.asTcl())

    def spool(self):
        try:
            logger("Spooled correctly")
            # all jobs owner by pixar user on the farm
            self.job.spool(owner="pixar")
        except Exception, spoolerror:
            logger.warn("A spool error %s" % spoolerror)


if __name__ == '__main__':
    root = Tk()
    root.title("Tractor Maya-RenderMan Batch Submit {u} {f}".format(u=user, f="DAB"))
    window = Window(root)
    root.mainloop()

    job = MayaBatchJob()

    try:
        job.mayascene = window.filename
        job.mayaprojectpath = window.dirname
        job.framechunks = int(window.fch.get())
        job.startframe = int(window.sf.get())
        job.endframe = int(window.ef.get())
        job.byframe = int(window.bf.get())
        # job.renderer = window.renderer.get()
        job.renderdirectory = "%s/images" % window.dirname
        job.imagetemplate = window.outputname.get()
        job.options = window.options.get()

        job.build()
        # j.spool()
    except Exception, err:
        logger.warn("Something wrong %s" % err)
    try:
        root.destroy()
    except Exception, err:
        logger.warn("Cant destroy the window %s" % err)