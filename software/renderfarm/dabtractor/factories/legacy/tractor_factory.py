#!/usr/bin/python
'''
This is a collection of user interfaces for tools
Initially for the tractor submission tools
'''
# ##############################################################
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
# sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################
import os
import sys
from Tkinter import *
import ttk
import tkFileDialog
import Tkconstants
from software.renderfarm.dabtractor.factories import farm_user as fu

class Student(object):
    def __init__(self, test=False):

        if test is True:
            self.user = "120988"
            self.number = "120988"
            self.name = "matthewgidney"
            self.dabrender = "/Volumes/dabrender"
            self.dabrenderwork = "/Volumes/dabrender/work"
        else:
            self.user = os.getenv("USER")
            self.test = False

            # get the names of the central render location for the user
            student = fu.FarmUser(self.user)
            student.query()

            self.name = student.getusername()
            self.number = student.getusernumber()
            self.dabrender = student.getrendermountpath()
            self.dabrenderwork = student.getrenderhome()

class WindowBase(object):
    """
    Base class for all batch jobs
    """

    def __init__(self):
        self.user = os.getenv("USER")
        self.spooljob = False

        try:
            # get the names of the central render location for the user
            ru = Student(test=True)
            self.renderusernumber = ru.number
            self.renderusername = ru.name
            self.renderuserhomefullpath = os.path.join(ru.dabrenderwork,self.renderusername)

            self.dabrender = ru.dabrender
            self.dabrenderworkpath = ru.dabrenderwork
            self.initialProjectPath = self.renderuserhomefullpath

        except Exception, erroruser:
            logger.warn("Cant get the users name and number back %s" % erroruser)
            sys.exit("Cant get the users name")


        if os.path.ismount(self.dabrender):
            logger.info("Found %s" % self.dabrender)
        else:
            self.initialProjectPath = None
            logger.critical("Cant find central filer mounted %s" % self.dabrender)
            raise Exception, "dabrender not a valid mount point"


class WindowRman(WindowBase):
    """
    Ui Class for render submit
    This should be a self contained window object holding its own cruft
    """

    def __init__(self, master):
        """Construct the main window interface
        """
        super(WindowRman, self).__init__()
        self.master = master
        self.dirtext = 'Select your project folder, or...'
        self.filetext = 'Select your maya scene file'
        self.workspacetext = 'Select the workspace.mel file in your project'
        self.workspaceerrortext = 'Warning - no workspace.mel found!'
        self.filename = ""
        self.dirname = ""
        self.workspace = ""

        # ################ Options for buttons ####################
        self.button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}

        __row = 1

        # print help(Label)
        Label(self.master, bg=windowbg2, text="------ MAYA RENDERMAN STUDIO SUBMISSION ------").grid(row=__row, column=1)
        __row += 1

        Label(self.master, bg=windowbg1, text="------ Project Details ------").grid(row=__row, column=1)
        __row += 1

        Label(master, bg=windowbg1, text="Project Dir").grid(row=__row, column=0)
        self.dirbut = Button(self.master, text=self.dirtext, bg = windowbg2, fg='black', command=self.opendirectory)
        self.dirbut.pack(**self.button_opt)  # must pack separately to get the value to dirbut
        self.dirbut.grid(row=__row, column=1, sticky=W + E)
        __row += 1

        Label(master, bg=windowbg1, text="Workspace.mel").grid(row=__row, column=0)
        self.workspacebut = Button(self.master, bg=windowbg2, text=self.workspacetext, fg='black', command=self.openworkspace)
        self.workspacebut.pack(**self.button_opt)  # must pack separately to get the value to dirbut
        self.workspacebut.grid(row=__row, column=1, sticky=W + E)
        __row += 1

        Label(master, bg=windowbg1, text="Scene File").grid(row=__row, column=0)
        self.filebut = Button(self.master, text=self.filetext, fg='black',
                              command=self.openfile)
        self.filebut.pack(**self.button_opt)
        self.filebut.grid(row=__row, column=1, sticky=W + E)
        __row += 1

        Label(self.master, bg= windowbg1,
              text="------- Maya Generic Details -------").grid(row=__row, column=1, rowspan=1)
        __row += 1

        Label(master, bg= windowbg1, text="Frame Start").grid(row=__row, column=0)
        self.sf = StringVar()
        self.sf.set("1")
        self.bar3 = Entry(self.master, bg=windowbg2,
                          textvariable=self.sf, width=8).grid(row=__row, column=1, sticky=W)
        __row += 1

        Label(master, bg= windowbg1, text="Frame End").grid(row=7, column=0)
        self.ef = StringVar()
        self.ef.set("4")
        self.bar4 = Entry(self.master, bg=windowbg2,
                          textvariable=self.ef, width=8).grid(row=__row, column=1, sticky=W)
        __row += 1

        Label(master,bg= windowbg1, text="By").grid(row=__row, column=0)
        self.bf = StringVar()
        self.bf.set("1")
        self.bar5 = Entry(self.master, bg=windowbg2,
                          textvariable=self.bf, width=8).grid(row=__row, column=1, sticky=W)
        __row += 1

        Label(master, bg=windowbg1, text="Frame Chunks").grid(row=__row, column=0)
        self.fch = StringVar()
        self.fch.set("4")
        self.bar6 = Entry(self.master, bg=windowbg2,
                          textvariable=self.fch, width=8).grid(row=__row, column=1, sticky=W)
        __row += 1

        Label(self.master, bg=windowbg1, text="Maya Version").grid(row=__row, column=0)
        self.mversion = StringVar()
        self.mversion.set("2015")
        combobox = ttk.Combobox(master, textvariable=self.mversion)
        combobox.config(values="2015")
        combobox.grid(row=__row, column=1, sticky=W)
        __row += 1

        Label(self.master, bg=windowbg1, text="Resolution").grid(row=__row, column=0)
        self.resolution = StringVar()
        self.resolution.set("720p")
        combobox = ttk.Combobox(master, textvariable=self.resolution)
        combobox.config(values=("720p",
                                "1080p",
                                "540p",
                                "SCENE"))
        combobox.grid(row=__row, column=1, sticky=W + E)
        __row += 1

        Label(self.master, bg=windowbg1, text="Output Format").grid(row=__row, column=0)
        self.outformat = StringVar()
        self.outformat.set("exr")
        combobox = ttk.Combobox(master, textvariable=self.outformat)
        combobox.config(values=("exr", "tif_8bit", "tif_16bit", "iff"))
        combobox.grid(row=__row, column=1, sticky=W)
        __row += 1

        Label(self.master, bg=windowbg1, text="------ Renderer Specific Details ------").grid(row=__row, column=1)
        __row += 1

        Label(self.master, bg=windowbg1, text="Renderer").grid(row=__row, column=0)
        self.renderer = StringVar()
        self.renderer.set("rms-ris")
        combobox = ttk.Combobox(master, textvariable=self.renderer)
        combobox.config(values=("rms-ris", "rms-reyes"))
        combobox.grid(row=__row, column=1, sticky=W)
        __row += 1

        Label(self.master, bg=windowbg1, text="RIS Integrator").grid(row=__row, column=0)
        self.integrator = StringVar()
        self.integrator.set("pxr")
        combobox = ttk.Combobox(master, textvariable=self.integrator)
        combobox.config(values=("pxr", "vcm"))
        combobox.grid(row=__row, column=1, sticky=W)
        __row += 1

        Label(master, bg=windowbg1, text="Other Options").grid(row=__row, column=0)
        self.options = StringVar()
        self.options.set("")
        self.bar7 = Entry(self.master, bg=windowbg2,
                          textvariable=self.options, width=40).grid(row=__row, column=1, sticky=W + E)
        __row += 1

        Label(self.master, bg=windowbg1, text="------- Submit Job To Tractor  -------").grid(row=__row, column=1)
        __row += 1

        # Buttons
        self.cbutton = Button(self.master, bg=windowbg1, text='SUBMIT', command=lambda: self.submit())
        self.cbutton.grid(row=__row, column=3, sticky=W + E)

        self.vbutton = Button(self.master, bg=windowbg1, text='VALIDATE', command=lambda: self.validate())
        self.vbutton.grid(row=__row, column=1, sticky=W + E)

        self.vbutton = Button(self.master, bg=windowbg1, text='CANCEL', command=lambda: self.cancel())
        self.vbutton.grid(row=__row, column=0, sticky=W + E)

    def openfile(self):
        self.filename = tkFileDialog.askopenfilename(parent=self.master, initialdir=self.dirname,
                                                     title=self.filetext,
                                                     filetypes=[('maya ascii', '.ma'),
                                                                ('maya binary', '.mb')])  # filename not filehandle
        self.filebut["text"] = str(self.filename) if self.filename else self.filetext

    def opendirectory(self):
        self.dirname = tkFileDialog.askdirectory(parent=self.master, initialdir=self.initialProjectPath,
                                                 title=self.dirtext)
        self.dirbut["text"] = str(self.dirname) if self.dirname else self.dirtext
        _possible = "%s/workspace.mel" % self.dirname
        if os.path.exists(_possible):
            self.workspace = _possible
            self.workspacebut["text"] = str(self.workspace) if self.workspace else self.workspacetext
        else:
            self.workspacebut["text"] = self.workspaceerrortext

    def openworkspace(self):
        self.workspace = tkFileDialog.askopenfilename(parent=self.master, initialdir=self.initialProjectPath,
                                                      title=self.workspacetext,
                                                      filetypes=[
                                                          ('maya workspace', '.mel')])  # filename not filehandle
        self.dirname = os.path.dirname(self.workspace)
        self.workspacebut["text"] = str(self.workspace) if self.workspace else self.workspacetext
        self.dirbut["text"] = str(self.dirname) if self.dirname else self.dirtext

    def validate(self):
        logger.info("Validate")

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
            self.spooljob = True
            self.master.destroy()
        except Exception, submiterror:
            logger.warn("Problem submitting %s" % submiterror)

    def cancel(self):
        logger.info("Camcelled")
        self.master.destroy()


if __name__ == '__main__':

    # if running as main - you are essentially testing the factory classes

    sh.setLevel(logging.DEBUG)
    student = Student(test=True)
    windowbg1 = "light cyan"
    windowbg2 = "lemon chiffon"

    root = Tk()
    root.title("Test UI {u} {f}".format(u=os.getenv("USER"), f="RMAN"))
    root.configure(background="light cyan")
    window = WindowRman(root)
    root.mainloop()

    for key in  window.__dict__.keys():

        logger.debug("{} {}".format(key, window.__dict__.get(key)))
        try:
            logger.debug("\t {} {}".format(key, window.__dict__.get(key).get()))
        except:
            pass

    try:
        root.destroy()
    except Exception, destroyerror:
        logger.warn("Cant destroy the window %s" % destroyerror)