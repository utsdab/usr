#!/usr/bin/env rmanpy
"""
To do:
    cleanup routine for rib
    create a ribgen then prman version
    check and test options
    run farmuser to check is user is valid

"""
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

import Tkinter as tk
import ttk
import tkFileDialog
import Tkconstants
import os
import sys
from dabtractor.factories import user_factory as ufac
from dabtractor.factories import configuration_factory as config
import dabtractor
from functools import partial


class WindowBase(object):
    """
    Base class for all batch jobs
    """

    def __init__(self):
        self.user = os.getenv("USER")
        self.spooljob = False
        self.validatejob = False
        self.master = tk.Tk()

        try:
            # get the names of the central render location for the user
            ru = ufac.Student()
            self.renderusernumber = ru.number
            self.renderusername = ru.name
            self.dabrender = ru.dabrender
            self.dabrenderworkpath = ru.dabrenderwork
            self.initialProjectPath = ru.dabrenderwork  # self.renderuserhomefullpath

        except Exception, erroruser:
            logger.warn("Cant get the users name and number back %s" % erroruser)
            sys.exit("Cant get the users name")

        if os.path.ismount(self.dabrender):
            logger.info("Found %s" % self.dabrender)
        else:
            self.initialProjectPath = None
            logger.critical("Cant find central filer mounted %s" % self.dabrender)
            raise Exception, "dabrender not a valid mount point"


class WindowPrman(WindowBase):
    """
    Ui Class for render submit
    """

    def __init__(self):
        """Construct the main window interface
        """
        super(WindowPrman, self).__init__()
        self.dirtext = 'Select your project folder, or...'
        self.filetext = 'Select your maya scene file'
        self.workspacetext = 'Select the workspace.mel file in your project'
        self.workspaceerrortext = 'Warning - no workspace.mel found!'
        self.filename = ""
        self.dirname = ""
        self.workspace = ""
        self.bgcolor0 = "light cyan"
        self.bgcolor1 = "white"
        self.bgcolor2 = "light grey"
        self.bgcolor3 = "pale green"
        self.master.configure(background=self.bgcolor1)
        self.user = os.getenv("USER")
        self.master.title("Maya/Renderman Tractor Submit: {u}".format(u=self.user))

        # ################ Options for buttons and canvas ####################
        self.button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}
        self.canvas = tk.Canvas(self.master, height=200, width=300)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        imagepath = os.path.join(os.path.dirname(dabtractor.__file__),"icons","Pixar_logo.gif")
        imagetk = tk.PhotoImage(file=imagepath)
        # keep a link to the image to stop the image being garbage collected
        self.canvas.img = imagetk
        self.labelimage = tk.Label(self.canvas, image=imagetk)
        self.labelimage.grid(row=0, column=0, columnspan=4,sticky=tk.NW + tk.NE)
        __row = 1

        # ###################################################################
        self.envstructuretext="$DABRENDERPATH/$TYPE/$SHOW/$PROJECT/scenes/$SCENE"
        self.labelenv = tk.Label(self.canvas, bg=self.bgcolor3, text="Environment Setup")
        self.labelenv.grid(row=__row,column=0,columnspan=5, sticky=tk.W + tk.E)
        __row += 1
        self.labelenv2 = tk.Label(self.canvas, bg=self.bgcolor3, text=self.envstructuretext)
        self.labelenv2.grid(row=__row, column=0,columnspan=5,sticky=tk.W + tk.E)
        __row += 1

        # ###################################################################
        self.labeldab1 = tk.Label(self.canvas, bg=self.bgcolor1,text="DABRENDERPATH")
        self.labeldab1.grid(row=__row, column=0,  sticky=tk.E)
        self.dabrenderpath = tk.StringVar()
        self.dabrenderpath.set(config.CurrentConfiguration().dabrenderpath)
        self.cbdabrender = ttk.Combobox(self.canvas, textvariable=self.dabrenderpath)
        self.cbdabrender.config(values=config.CurrentConfiguration().dabrenderpath)
        self.cbdabrender.grid(row=__row, column=1, sticky=tk.W)
        self.labeldab2 = tk.Label(self.canvas, bg=self.bgcolor1,text="")
        self.labeldab2.grid( row=__row,column=2,columnspan=2,sticky=tk.W)
        __row += 1

        # ###################################################################
        # self.envtypeextratext="group project OR solo work"
        # self.labeltype1 = tk.Label(self.canvas, bg=self.bgcolor1,text="TYPE")
        # self.labeltype1.grid(row=__row, column=0, sticky=tk.E)
        # self.envtype = tk.StringVar()
        # # self.envtype.set(config.CurrentConfiguration().envtype)
        #
        # self.cbxenvtype = ttk.Combobox(self.canvas, textvariable=self.envtype, postcommand=self.settype,
        #                                state="readonly")
        # self.envtype.set("Select something")
        # self.cbxenvtype.config(values=config.CurrentConfiguration().envtypes)
        # self.cbxenvtype.grid(row=__row, column=1, sticky=tk.W)
        # self.labeltype2 = tk.Label(self.canvas, bg=self.bgcolor1,text=self.envtypeextratext)
        # self.labeltype2.grid( row=__row, column=2, columnspan=2, sticky=tk.W)
        # __row += 1

        # ###################################################################
        self.envtypeextratext="group project OR solo work"
        self.envtypetext = "Select your type"
        self.labeltype1 = tk.Label(self.canvas, bg=self.bgcolor1,text="TYPE")
        self.labeltype1.grid(row=__row, column=0, sticky=tk.E)
        self.envtype = tk.StringVar()
        self.envtypebut = tk.Button(self.canvas, text=self.envtypetext, bg=self.bgcolor2, fg='black',
                                    command=self.opentype)

        # button = Tk.Button(master=frame, text='press', command= lambda: action(someNumber))


        self.envtypebut.pack(**self.button_opt)  # must pack separately to get the value to dirbut
        self.envtypebut.grid(row=__row, column=1, sticky=tk.W + tk.E)
        self.labeltype2 = tk.Label(self.canvas, bg=self.bgcolor1, text="")
        self.labeltype2.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.envshowtext = "Select your show"
        self.labelshow1 = tk.Label(self.canvas, bg=self.bgcolor1,text="SHOW")
        self.labelshow1.grid(row=__row, column=0, sticky=tk.E)
        self.envshow = tk.StringVar()
        self.envshowbut = tk.Button(self.canvas, text=self.envshowtext, bg=self.bgcolor2, fg='black',
                                    command=self.openshow)
        self.envshowbut.pack(**self.button_opt)  # must pack separately to get the value to dirbut
        self.envshowbut.grid(row=__row, column=1, sticky=tk.W + tk.E)
        self.labelshow2 = tk.Label(self.canvas, bg=self.bgcolor1,text="")
        self.labelshow2.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.envprojecttext="Select your maya project"
        self.labelproj1 = tk.Label(self.canvas, bg=self.bgcolor1,text="PROJECT")
        self.labelproj1.grid(row=__row, column=0, sticky=tk.E)
        self.envproject = tk.StringVar()
        self.envprojectbut = tk.Button(self.canvas, text=self.envprojecttext, bg=self.bgcolor2, fg='black',
                                       command=self.openproj)
        self.envprojectbut.pack(**self.button_opt)  # must pack separately to get the value to dirbut
        self.envprojectbut.grid(row=__row, column=1, sticky=tk.W + tk.E)
        self.labelproj2 = tk.Label(self.canvas, bg=self.bgcolor1, text="")
        self.labelproj2.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.envscenetext="Select your maya scene file"
        self.envscene = tk.StringVar()
        self.envscenefullpath = ""
        self.labelscene1 = tk.Label(self.canvas, bg=self.bgcolor1,text="SCENE")
        self.labelscene1.grid(row=__row, column=0, sticky=tk.E)
        self.envscenebut = tk.Button(self.canvas, text=self.envscenetext, bg=self.bgcolor2, fg='black',
                                     command=self.openscene)
        self.envscenebut.pack(**self.button_opt)  # must pack separately to get the value to dirbut
        self.envscenebut.grid(row=__row, column=1, sticky=tk.W + tk.E)
        self.labelscene2 = tk.Label(self.canvas, bg=self.bgcolor1,text="")
        self.labelscene2.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.labelmaya = tk.Label(self.canvas, bg=self.bgcolor3,text="Maya RIB generation then Prman")
        self.labelmaya.grid(row=__row, column=0,columnspan=5, sticky=tk.W + tk.E)
        __row += 1

        # ###################################################################
        self.labelmayagen = tk.Label(self.canvas, bg=self.bgcolor3,text="Maya Generic Details")
        self.labelmayagen.grid(row=__row,column=0, columnspan=4,rowspan=1,sticky=tk.W + tk.E)
        __row += 1

        # ###################################################################
        self.labelmayav = tk.Label(self.canvas, bg=self.bgcolor1, text="Maya Version")
        self.labelmayav.grid(row=__row, column=0, sticky=tk.E)
        self.mayaversion = tk.StringVar()
        self.mayaversion.set(config.CurrentConfiguration().mayaversion)
        self.cbxmayav = combobox = ttk.Combobox(self.canvas, textvariable=self.mayaversion, state="readonly")
        self.cbxmayav.config(values=config.CurrentConfiguration().mayaversions)
        self.cbxmayav.grid(row=__row, column=1, sticky=tk.W)
        __row += 1

        # ###################################################################
        tk.Label(self.canvas, bg=self.bgcolor1,text="Project Group").grid(row=__row, column=0, sticky=tk.E)
        self.projectgroup = tk.StringVar()
        self.projectgroup.set(config.CurrentConfiguration().projectgroup)
        self.cbxprojgrp = combobox = ttk.Combobox(self.canvas, textvariable=self.projectgroup, state="readonly")
        self.cbxprojgrp.config(values=config.CurrentConfiguration().projectgroups)
        self.cbxprojgrp.grid(row=__row, column=1, sticky=tk.W)
        self.labelprojgrp = tk.Label(self.canvas, bg=self.bgcolor1,text="** type of project")
        self.labelprojgrp.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.labelstart = tk.Label(self.canvas, bg=self.bgcolor1,text="Frame Start")
        self.labelstart.grid(row=__row, column=0, sticky=tk.E)
        self.sf = tk.StringVar()
        self.sf.set("1")
        self.bar3 = tk.Entry(self.canvas, bg=self.bgcolor2,textvariable=self.sf,width=8)
        self.bar3.grid(row=__row,column=1,sticky=tk.W)
        # __row += 1

        # ###################################################################
        self.labelend = tk.Label(self.canvas, bg=self.bgcolor1,text="Frame End")
        self.labelend.grid(row=__row, column=2, sticky=tk.W)
        self.ef = tk.StringVar()
        self.ef.set("4")
        self.bar4 = tk.Entry(self.canvas, bg=self.bgcolor2,textvariable=self.ef, width=8)
        self.bar4.grid(row=__row,column=1,sticky=tk.E)
        __row += 1

        # ###################################################################
        self.labelby = tk.Label(self.canvas, bg=self.bgcolor1,text="By")
        self.labelby.grid(row=__row, column=0, sticky=tk.E)
        self.bf = tk.StringVar()
        self.bf.set("1")
        self.bar5 = tk.Entry(self.canvas, bg=self.bgcolor2,textvariable=self.bf, width=8)
        self.bar5.grid(row=__row, column=1, sticky=tk.W)

        # ###################################################################
        self.labelres1 = tk.Label(self.canvas, bg=self.bgcolor1,text="Resolution")
        self.labelres1.grid(row=__row, column=0, sticky=tk.E)
        self.resolution = tk.StringVar()
        self.resolution.set("720p")
        self.cbxres = ttk.Combobox(self.canvas, textvariable=self.resolution, state="readonly")
        self.cbxres.config(values=("720p","1080p", "540p","108p","SCENE"))
        self.cbxres.grid(row=__row, column=1, sticky=tk.W)
        self.labelres2 = tk.Label(self.canvas, bg=self.bgcolor1,text="** 720p recommended")
        self.labelres2.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.labelrenddet = tk.Label(self.canvas, bg=self.bgcolor3, text="Renderer Specific Details")
        self.labelrenddet.grid(row=__row,column=0,columnspan=4,sticky=tk.W + tk.E)
        __row += 1

        # ###################################################################
        self.labelrmanv = tk.Label(self.canvas, bg=self.bgcolor1,text="Renderman Version")
        self.labelrmanv.grid(row=__row, column=0, sticky=tk.E)
        self.rendermanversion = tk.StringVar()
        self.rendermanversion.set(config.CurrentConfiguration().rendermanversion)
        self.cbxrmanv = ttk.Combobox(self.canvas, textvariable=self.rendermanversion, state="readonly")
        self.cbxrmanv.config(values=config.CurrentConfiguration().rendermanversions)
        self.cbxrmanv.grid(row=__row, column=1, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.labeloutf1 = tk.Label(self.canvas, bg=self.bgcolor1,text="Output Format")
        self.labeloutf1.grid(row=__row, column=0)
        self.outformat = tk.StringVar()
        self.outformat.set("exr")
        self.cbxoutf = ttk.Combobox(self.canvas, textvariable=self.outformat, state="readonly")
        self.cbxoutf.config(values=("exr", "jpg", "tif", "png"))
        self.cbxoutf.grid(row=__row, column=1, sticky=tk.W)
        self.labeloutf2 = tk.Label(self.canvas, bg=self.bgcolor1,text="** exr recommended")
        self.labeloutf2.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.labelrthread1 =tk.Label(self.canvas, bg=self.bgcolor1,text="Render Threads")
        self.labelrthread1.grid(row=__row, column=0, sticky=tk.E)
        self.renderthread = tk.StringVar()
        self.renderthread.set(config.CurrentConfiguration().renderthread)
        self.cbxrthrd = ttk.Combobox(self.canvas, textvariable=self.renderthread, state="readonly")
        self.cbxrthrd.config(values=config.CurrentConfiguration().renderthreads)
        self.cbxrthrd.grid(row=__row, column=1, sticky=tk.W)
        self.labelrthread2 =tk.Label(self.canvas, bg=self.bgcolor1,text="** 8 recommended")
        self.labelrthread2.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.labelrmem1 = tk.Label(self.canvas, bg=self.bgcolor1,text="Render Memory mb")
        self.labelrmem1.grid(row=__row, column=0, sticky=tk.E)
        self.rendermemory = tk.StringVar()
        self.rendermemory.set(config.CurrentConfiguration().rendermemory)
        self.cbxrmem = ttk.Combobox(self.canvas, textvariable=self.rendermemory, state="readonly")
        self.cbxrmem.config(values=config.CurrentConfiguration().rendermemorys)
        self.cbxrmem.grid(row=__row, column=1, sticky=tk.W)
        self.labelrmem2 = tk.Label(self.canvas, bg=self.bgcolor1, text="** 4000 recommended")
        self.labelrmem2.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.labelmax1 = tk.Label(self.canvas, bg=self.bgcolor1,text="Max Samples")
        self.labelmax1.grid(row=__row, column=0, sticky=tk.E)
        self.rendermaxsamples = tk.StringVar()
        self.rendermaxsamples.set(config.CurrentConfiguration().rendermaxsample)
        self.cbxmaxsamp = ttk.Combobox(self.canvas, textvariable=self.rendermaxsamples, state="readonly")
        self.cbxmaxsamp.config(values=config.CurrentConfiguration().rendermaxsamples)
        self.cbxmaxsamp.grid(row=__row, column=1, sticky=tk.W)
        self.labelmax2 = tk.Label(self.canvas, bg=self.bgcolor1, text="** 256 recommended")
        self.labelmax2.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.skipframes = tk.IntVar()
        self.skipframes.set(0)
        self.checkbutskip = tk.Checkbutton(self.canvas, bg=self.bgcolor1, text="Skip Existing Frames", variable=self.skipframes)
        self.checkbutskip.grid(row=__row, column=1, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.labelopt = tk.Label(self.canvas, bg=self.bgcolor1,text="Other Options")
        self.labelopt.grid(row=__row, column=0)
        self.options = tk.StringVar()
        self.options.set("")
        self.bar7 = tk.Entry(self.canvas, bg=self.bgcolor2, textvariable=self.options,width=40)
        self.bar7.grid(row=__row,column=1,columnspan=4, sticky=tk.W + tk.E)
        __row += 1

        # ###################################################################
        self.labelmakeproxy = tk.Label(self.canvas, bg=self.bgcolor3,text="Make Proxy")
        self.labelmakeproxy.grid(row=__row,column=0,columnspan=4,sticky=tk.W + tk.E)
        __row += 1

        # ###################################################################
        self.makeproxy = tk.IntVar()
        self.makeproxy.set(1)
        self.checkbutproxy = tk.Checkbutton(self.canvas, bg=self.bgcolor1, text="Make Proxy Movie",variable=self.makeproxy)
        self.checkbutproxy.grid(row=__row, column=1, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.labelnot = tk.Label(self.canvas, bg=self.bgcolor3, text="Tractor Notifications ... not yet fully implemented")
        self.labelnot.grid(row=__row, column=0, columnspan=4, sticky=tk.W + tk.E)
        __row += 1

        # ###################################################################
        self.emailjob = tk.IntVar()
        self.emailjob.set(1)
        self.checkbutjob = tk.Checkbutton(self.canvas, variable=self.emailjob, bg=self.bgcolor1, text="Job")
        self.checkbutjob.grid(row=__row, column=1, sticky=tk.W)

        self.emailstart = tk.IntVar()
        self.emailstart.set(0)
        self.checkbutstart = tk.Checkbutton(self.canvas, variable=self.emailstart, bg=self.bgcolor1, text="Start")
        self.checkbutstart.grid(row=__row, column=2,sticky=tk.W)
        __row += 1

        # ###################################################################
        self.emailtasks = tk.IntVar()
        self.emailtasks.set(0)
        self.checkbuttask = tk.Checkbutton(self.canvas, variable=self.emailtasks, bg=self.bgcolor1,text="Tasks")
        self.checkbuttask.grid(row=__row, column=1, sticky=tk.W)

        self.emailcompletion = tk.IntVar()
        self.emailcompletion.set(1)
        self.checkbutcomp = tk.Checkbutton(self.canvas, variable=self.emailcompletion, bg=self.bgcolor1,text="Completion")
        self.checkbutcomp.grid(row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.emailcommands = tk.IntVar()
        self.emailcommands.set(0)
        self.checkbutcomm = tk.Checkbutton(self.canvas, variable=self.emailcommands, bg=self.bgcolor1, text="Commands")
        self.checkbutcomm.grid(row=__row, column=1, sticky=tk.W)

        self.emailerror = tk.IntVar()
        self.emailerror.set(0)
        self.checkbuterr = tk.Checkbutton(self.canvas, variable=self.emailerror, bg=self.bgcolor1, text="Error")
        self.checkbuterr.grid( row=__row, column=2, sticky=tk.W)
        __row += 1

        # ###################################################################
        self.submitlabel = tk.Label(self.canvas, bg=self.bgcolor3,text="Submit Job To Tractor")
        self.submitlabel.grid(row=__row, column=0,columnspan=4, sticky=tk.W + tk.E)
        __row += 1

        # ###################################################################
        # tk.Buttons
        self.cbutton = tk.Button(self.canvas, bg=self.bgcolor1,text='SUBMIT', command=lambda: self.submit())
        self.cbutton.grid(row=__row, column=3, sticky=tk.W + tk.E)
        self.vbutton = tk.Button(self.canvas, bg=self.bgcolor1, text='VALIDATE', command=lambda: self.validate())
        self.vbutton.grid(row=__row, column=1, columnspan=2, sticky=tk.W + tk.E)
        self.vbutton = tk.Button(self.canvas, bg=self.bgcolor1,text='CANCEL', command=lambda: self.cancel())
        self.vbutton.grid(row=__row, column=0, sticky=tk.W + tk.E)

        self.master.mainloop()

    # def openfile(self):
    #     self.filename = tkFileDialog.askopenfilename(parent=self.master,
    #                                                  initialdir=self.dirname,
    #                                                  title=self.filetext,
    #                                                  filetypes=[('maya ascii', '.ma'),
    #                                                             ('maya binary', '.mb')])
    #                                                             # filename not filehandle
    #     self.filebut["text"] = str(self.filename) if self.filename else self.filetext

    # def opendirectory(self):
    #     self.dirname = tkFileDialog.askdirectory(parent=self.master,
    #                                              initialdir=self.initialProjectPath,
    #                                              title=self.dirtext)
    #     self.dirbut["text"] = str(self.dirname) if self.dirname else self.dirtext
    #     _possible = "%s/workspace.mel" % self.dirname
    #     if os.path.exists(_possible):
    #         self.workspace = _possible
    #         self.workspacebut["text"] = str(self.workspace) if self.workspace else self.workspacetext
    #     else:
    #         self.workspacebut["text"] = self.workspaceerrortext


    def openshow(self):

        if self.envtype.get() == "work":
            # print "work"
            self.envshowpick = tkFileDialog.askdirectory(parent=self.master,
                                                    initialdir=os.path.join(self.dabrenderpath.get(),
                                                                            self.envtype.get()),
                                                    title=self.envshowtext)
            self.envshowbut["text"] = os.path.basename(str(self.envshowpick)) if self.envshowbut else self.envshowtext
            self.envprojectbut["text"] = self.renderusername

        elif self.envtype.get() == "project":
            # print "project"
            self.envshowpick = tkFileDialog.askdirectory(parent=self.master,
                                                    initialdir=os.path.join(self.dabrenderpath.get(),
                                                                            self.envtype.get()),
                                                    title=self.envshowtext)

            self.envshowbut["text"] = os.path.basename(str(self.envshowpick)) if self.envshowbut else self.envshowtext

    def settype(self):
        if self.cbxenvtype.get() == "work":
            print "fix show"
            self.envshowbut["text"] = self.renderusername
        else:
            print "dont fix show"
            self.envshowbut["text"] = self.envshowtext

    def opentype(self):
        print "work"
        self.envtypepick = tkFileDialog.askdirectory(parent=self.master,
                                                    initialdir=self.dabrenderpath.get(),
                                                    title=self.envprojecttext)
        self.envtypebut["text"] = os.path.basename(str(self.envtypepick)) if self.envtype else self.envtypetext
        if self.envtypebut["text"] == "work":
            self.envshowbut["text"] = self.renderusername
            self.envshow.set(self.renderusername)

    def openproj(self):
        if self.envtype.get() == "work":
            print "openproj work"
            self.envprojectpick = tkFileDialog.askdirectory(parent=self.master,
                                                        initialdir=os.path.join(self.dabrenderpath.get(),
                                                                                self.envtype.get(),
                                                                                self.renderusername),
                                                        title=self.envprojecttext)
            self.envprojectbut["text"] = os.path.basename(str(self.envprojectpick)) if self.envprojectbut else \
                self.envprojecttext

        # _possible = "%s/workspace.mel" % self.envprojectpick
        # if os.path.exists(_possible):
        #     print "workspace found"
        #     self.workspace = _possible
        #     # self.workspacebut["text"] = str(self.workspace) if self.workspace else self.workspacetext
        # else:
        #     print "no workspace"
        #     # self.workspacebut["text"] = self.workspaceerrortext

    def openscene(self):
        if self.envtype.get() == "work":
            print "work"
            self.envscenepick = tkFileDialog.askopenfilename(parent=self.master,
                                                             initialdir=os.path.join(self.dabrenderpath.get(),
                                                                                  self.envtype.get(),
                                                                                  # self.renderusername,
                                                                                  self.envshow.get(),
                                                                                  self.envproject.get(),
                                                                                  "scenes"),
                                                             title=self.envscenetext,
                                                             filetypes=[('maya ascii', '.ma'),
                                                                        ('maya binary', '.mb')])

            self.envscenefullpath = os.path.dirname(self.envscenepick)
            self.envscenesplit = os.path.splitext(os.path.basename(self.envscenepick))
            self.envscene = self.envscenesplit[0]
            self.envscenebut["text"] = str(self.envscene) if self.envscene else self.envscenetext


    def openworkspace(self):
        self.workspace = tkFileDialog.askopenfilename(parent=self.master,
                                                      initialdir=self.initialProjectPath,
                                                      title=self.workspacetext,
                                                      filetypes=[('maya workspace', '.mel')])
                                                      # filename not filehandle
        self.dirname = os.path.dirname(self.workspace)
        # self.workspacebut["text"] = str(self.workspace) if self.workspace else self.workspacetext
        # self.dirbut["text"] = str(self.dirname) if self.dirname else self.dirtext

    def validate(self):
        # try:
        logger.info("Validate")
        logger.info("Type: %s" % self.envtype.get())
        logger.info("Show: %s" % self.envshow.get())
        logger.info("Project: %s" % self.envproject.get())
        logger.info("Scene: %s" % self.envscene.get())
        logger.info("SceneFullPath: %s" % self.envscenefullpath)
        logger.info("Start: %s" % self.sf.get())
        logger.info("End: %s" % self.ef.get())
        logger.info("By: %s" % self.bf.get())
        logger.info("Skip Existing Frames:" % self.skipframes)
        logger.info("Make Proxy:" % self.makeproxy)
        self.spooljob = False
        self.validatejob = True
        self.master.destroy()

        # except Exception, validateError:
        #     logger.warn("Problem validating %s" % validateError)

    def submit(self):
        try:
            logger.info("Submit")
            logger.info("Project: %s" % self.envproject.get())
            logger.info("SceneFile: %s" % self.filename)
            logger.info("Start: %s" % self.sf.get())
            logger.info("End: %s" % self.ef.get())
            logger.info("By: %s" % self.bf.get())
            logger.info("Skip Existing Frames:" % self.skipframes)
            logger.info("Make Proxy:" % self.makeproxy)

            self.spooljob = True
            self.validatejob = False
            self.master.destroy()
        except Exception, submiterror:
            logger.warn("Problem submitting %s" % submiterror)

    def cancel(self):
        logger.info("Camcelled")
        self.master.destroy()



if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    window = WindowPrman()