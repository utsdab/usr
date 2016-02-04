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
from software.renderfarm.dabtractor.factories import user_factory as ufac
from software.renderfarm.dabtractor.factories import configuration_factory as config
import software.renderfarm.dabtractor


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


class WindowMentalray(WindowBase):
    """
    Ui Class for render submit
    """

    def __init__(self):
        """Construct the main window interface
        """
        super(WindowMentalray, self).__init__()
        self.dirtext = 'Select your project folder, or...'
        self.filetext = 'Select your maya scene file'
        self.workspacetext = 'Select the workspace.mel file in your project'
        self.workspaceerrortext = 'Warning - no workspace.mel found!'
        self.filename = ""
        self.dirname = ""
        self.workspace = ""
        self.bgcolor0 = "light cyan"
        self.bgcolor1 = "white"
        self.bgcolor2 = "lemon chiffon"
        self.bgcolor3 = "light grey"
        self.master.configure(background=self.bgcolor1)
        self.user = os.getenv("USER")
        self.master.title("Maya/MentalRay Render Tractor Submit: {u}".format(u=self.user))

        # ################ Options for buttons and canvas ####################
        self.button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}
        self.canvas = tk.Canvas(self.master, height=200, width=300)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        imagepath = os.path.join(os.path.dirname(dabtractor.__file__),"icons","Maya_logo.gif")
        imagetk = tk.PhotoImage(file=imagepath)
        # keep a link to the image to stop the image being garbage collected
        self.canvas.img = imagetk
        tk.Label(self.canvas, image=imagetk).grid(row=0, column=0, columnspan=4,
                                                  sticky=tk.NW + tk.NE)
        __row = 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor3,
                 text="(Maya) Render -r (mr,maya)").grid(row=__row, column=0,
                                                         columnspan=4,
                                                         sticky=tk.W + tk.E)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Project Dir").grid(row=__row, column=0, sticky=tk.E)
        self.dirbut = tk.Button(self.canvas, text=self.dirtext, bg=self.bgcolor2, fg='black',
                                command=self.opendirectory)
        self.dirbut.pack(**self.button_opt)  # must pack separately to get the value to dirbut
        self.dirbut.grid(row=__row, column=1, columnspan=4, sticky=tk.W + tk.E)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Workspace.mel").grid(row=__row, column=0)
        self.workspacebut = tk.Button(self.canvas, bg=self.bgcolor2,
                                      text=self.workspacetext, fg='black',
                                      command=self.openworkspace)
        self.workspacebut.pack(**self.button_opt)
        # must pack separately to get the value to dirbut

        self.workspacebut.grid(row=__row, column=1, columnspan=4, sticky=tk.W + tk.E)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Scene File").grid(row=__row, column=0)
        self.filebut = tk.Button(self.canvas, text=self.filetext,
                                 fg='black', command=self.openfile)
        self.filebut.pack(**self.button_opt)
        self.filebut.grid(row=__row, column=1, columnspan=4, sticky=tk.W + tk.E)
        __row += 1

        tk.Label(self.canvas, bg=self.bgcolor3,
                 text="Maya Generic Details").grid( row=__row,
                                                    column=0,
                                                    columnspan=4,
                                                    rowspan=1,
                                                    sticky=tk.W + tk.E)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Maya Version").grid(row=__row, column=0)
        self.mayaversion = tk.StringVar()
        self.mayaversion.set(config.CurrentConfiguration().mayaversion)
        combobox = ttk.Combobox(self.canvas, textvariable=self.mayaversion)
        combobox.config(values=config.CurrentConfiguration().mayaversions)
        combobox.grid(row=__row, column=1, sticky=tk.W)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Project Group").grid(row=__row, column=0)
        self.projectgroup = tk.StringVar()
        self.projectgroup.set(config.CurrentConfiguration().projectgroup)
        combobox = ttk.Combobox(self.canvas, textvariable=self.projectgroup)
        combobox.config(values=config.CurrentConfiguration().projectgroups)
        # combobox.current(0)
        combobox.grid(row=__row, column=1, sticky=tk.W)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Frame Start").grid(row=__row, column=0, sticky=tk.E)
        self.sf = tk.StringVar()
        self.sf.set("1")
        self.bar3 = tk.Entry(self.canvas, bg=self.bgcolor2,
                             textvariable=self.sf, width=8).grid(row=__row, column=1,
                                                                 sticky=tk.W)

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Frame End").grid(row=__row, column=3, sticky=tk.W)
        self.ef = tk.StringVar()
        self.ef.set("4")
        self.bar4 = tk.Entry(self.canvas, bg=self.bgcolor2,
                             textvariable=self.ef, width=8).grid(row=__row, column=2,
                                                                 sticky=tk.E)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="By").grid(row=__row, column=0, sticky=tk.E)
        self.bf = tk.StringVar()
        self.bf.set("1")
        self.bar5 = tk.Entry(self.canvas, bg=self.bgcolor2,
                             textvariable=self.bf, width=8).grid(row=__row, column=1,
                                                                 sticky=tk.W)

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Frames per Subjob").grid(row=__row, column=3, sticky=tk.W)
        self.fch = tk.StringVar()
        self.fch.set("4")
        self.bar6 = tk.Entry(self.canvas, bg=self.bgcolor2,
                             textvariable=self.fch, width=8).grid(row=__row, column=2,
                                                                  sticky=tk.E)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Resolution").grid(row=__row, column=0, sticky=tk.E)
        self.resolution = tk.StringVar()
        self.resolution.set("720p")
        combobox = ttk.Combobox(self.canvas, textvariable=self.resolution)
        combobox.config(values=("720p", "1080p", "540p","108p", "SCENE"))
        combobox.grid(row=__row, column=1, sticky=tk.W)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Output Format").grid(row=__row, column=0)
        self.outformat = tk.StringVar()
        self.outformat.set("exr")
        combobox = ttk.Combobox(self.canvas, textvariable=self.outformat)
        combobox.config(values=("exr", "jpg", "tif", "png"))
        combobox.grid(row=__row, column=1, sticky=tk.W)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor3,
                 text="Renderer Specific Details").grid(row=__row, column=0,
                                                        columnspan=4,
                                                        sticky=tk.W + tk.E)
        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,text="Renderer").grid(row=__row, column=0, sticky=tk.E)
        self.renderer = tk.StringVar()
        self.renderer.set(config.CurrentConfiguration().mayarenderer)
        combobox = ttk.Combobox(self.canvas, textvariable=self.renderer)
        combobox.config(values=config.CurrentConfiguration().mayarenderers)
        combobox.grid(row=__row, column=1, sticky=tk.W)
        __row += 1
        # ###################################################################

        self.skipframes = tk.IntVar()
        self.skipframes.set(0)
        tk.Checkbutton(self.canvas, bg=self.bgcolor1, text="Skip Existing Frames",
                       variable=self.skipframes).grid(row=__row, column=1, sticky=tk.W)
        __row += 1
        # ###################################################################










        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Other Options").grid(row=__row, column=0)
        self.options = tk.StringVar()
        self.options.set("")
        self.bar7 = tk.Entry(self.canvas, bg=self.bgcolor2, textvariable=self.options,
                             width=40).grid(row=__row,column=1, columnspan=4,
                                            sticky=tk.W + tk.E)

        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor3,
                 text="Make Proxy").grid(row=__row,
                                      column=0,
                                      columnspan=4,
                                      sticky=tk.W + tk.E)
        __row += 1

        # ###################################################################
        self.makeproxy = tk.IntVar()
        self.makeproxy.set(1)
        tk.Checkbutton(self.canvas, bg=self.bgcolor1, text="Make Proxy Movie",
                       variable=self.makeproxy).grid(row=__row, column=1, sticky=tk.W)
        __row += 1

        # ###################################################################
        tk.Label(self.canvas, bg=self.bgcolor3,
                 text="Tractor Notifications ... not yet fully implemented").grid(row=__row,
                                                                                  column=0,
                                                                                  columnspan=4,
                                                                                  sticky=tk.W + tk.E)
        __row += 1
        # ###################################################################

        self.emailjob = tk.IntVar()
        self.emailjob.set(1)
        tk.Checkbutton(self.canvas, variable=self.emailjob, bg=self.bgcolor1,
                       text="Job").grid(row=__row, column=1, sticky=tk.W)

        self.emailstart = tk.IntVar()
        self.emailstart.set(0)
        tk.Checkbutton(self.canvas, variable=self.emailstart, bg=self.bgcolor1,
                       text="Start").grid(row=__row, column=2,sticky=tk.W)

        __row += 1
        # ###################################################################

        self.emailtasks = tk.IntVar()
        self.emailtasks.set(0)
        tk.Checkbutton(self.canvas, variable=self.emailtasks, bg=self.bgcolor1,
                       text="Tasks").grid(row=__row, column=1, sticky=tk.W)

        self.emailcompletion = tk.IntVar()
        self.emailcompletion.set(1)
        tk.Checkbutton(self.canvas, variable=self.emailcompletion, bg=self.bgcolor1,
                       text="Completion").grid(row=__row, column=2, sticky=tk.W)

        __row += 1
        # ###################################################################

        self.emailcommands = tk.IntVar()
        self.emailcommands.set(0)
        tk.Checkbutton(self.canvas, variable=self.emailcommands, bg=self.bgcolor1,
                       text="Commands").grid(row=__row, column=1, sticky=tk.W)

        self.emailerror = tk.IntVar()
        self.emailerror.set(0)
        tk.Checkbutton(self.canvas, variable=self.emailerror, bg=self.bgcolor1,
                       text="Error").grid(row=__row, column=2, sticky=tk.W)

        __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor3,
                 text="Submit Job To Tractor").grid(row=__row, column=0,
                                                    columnspan=4, sticky=tk.W + tk.E)

        __row += 1
        # ###################################################################

        # tk.Buttons
        self.cbutton = tk.Button(self.canvas, bg=self.bgcolor1,
                                 text='SUBMIT', command=lambda: self.submit())
        self.cbutton.grid(row=__row, column=3, sticky=tk.W + tk.E)
        self.vbutton = tk.Button(self.canvas, bg=self.bgcolor1,
                                 text='VALIDATE', command=lambda: self.validate())
        self.vbutton.grid(row=__row, column=1, columnspan=2, sticky=tk.W + tk.E)
        self.vbutton = tk.Button(self.canvas, bg=self.bgcolor1,
                                 text='CANCEL', command=lambda: self.cancel())
        self.vbutton.grid(row=__row, column=0, sticky=tk.W + tk.E)

        self.master.mainloop()

    def openfile(self):
        self.filename = tkFileDialog.askopenfilename(parent=self.master,
                                                     initialdir=self.initialProjectPath,
                                                     title=self.filetext,
                                                     filetypes=[('maya ascii', '.ma'),
                                                                ('maya binary', '.mb')])
                                                                # filename not filehandle
        self.filebut["text"] = str(self.filename) if self.filename else self.filetext

    def opendirectory(self):
        self.dirname = tkFileDialog.askdirectory(parent=self.master,
                                                 initialdir=self.initialProjectPath,
                                                 title=self.dirtext)
        self.dirbut["text"] = str(self.dirname) if self.dirname else self.dirtext
        _possible = "%s/workspace.mel" % self.dirname
        if os.path.exists(_possible):
            self.workspace = _possible
            self.workspacebut["text"] = str(self.workspace) if self.workspace else self.workspacetext
        else:
            self.workspacebut["text"] = self.workspaceerrortext

    def openworkspace(self):
        self.workspace = tkFileDialog.askopenfilename(parent=self.master,
                                                      initialdir=self.initialProjectPath,
                                                      title=self.workspacetext,
                                                      filetypes=[('maya workspace', '.mel')])
                                                      # filename not filehandle
        self.dirname = os.path.dirname(self.workspace)
        self.workspacebut["text"] = str(self.workspace) if self.workspace else self.workspacetext
        self.dirbut["text"] = str(self.dirname) if self.dirname else self.dirtext

    def validate(self):
        try:
            logger.info("Validate")
            logger.info("Project: %s" % self.dirname)
            logger.info("SceneFile: %s" % self.filename)
            logger.info("Start: %s" % self.sf.get())
            logger.info("End: %s" % self.ef.get())
            logger.info("By: %s" % self.bf.get())
            logger.info("Skip Existing Frames:" % self.skipframes)
            logger.info("Make Proxy:" % self.makeproxy)
            self.spooljob = False
            self.validatejob = True
            self.master.destroy()

        except Exception, validateError:
            logger.warn("Problem validating %s" % validateError)

    def submit(self):
        try:
            logger.info("Submit")
            logger.info("Project: %s" % self.dirname)
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
