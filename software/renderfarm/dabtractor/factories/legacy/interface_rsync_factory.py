#!/usr/bin/env rmanpy
"""
To do:


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
import socket
import tkFileDialog
import Tkconstants
import os
import sys
from software.renderfarm.dabtractor.factories import user_factory as ufac
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

    @staticmethod
    def usedirmap(inputstring):
        # wraps a command string up as per dirmap needs in pixar tractor eg. %D(mayabatch)
        return '%D({thing})'.format(thing=inputstring)

    @staticmethod
    def expandargumentstring(inputargs=""):
        """
        This takes a string like "-r 2 -l 4" and returns
        {-r} {2} {-l} {4} which is what tractor wants for arguments
        """
        arglist = inputargs.split(" ")
        outputstring = "} {".join(arglist)
        return outputstring


class WindowRsync(WindowBase):
    """
    Ui Class for render submit
    """

    def __init__(self):
        """Construct the main window interface
        """
        super(WindowRsync, self).__init__()
        self.spath = 'Select your source path'
        self.tpath = 'Select your target path'
        # self.filename = ""
        self.sdirname = ""
        self.tdirname = ""

        self.bgcolor0 = "light cyan"
        self.bgcolor1 = "white"
        self.bgcolor2 = "lemon chiffon"
        self.bgcolor3 = "light grey"
        self.master.configure(background=self.bgcolor1)

        self.hostname = socket.gethostname()
        self.ipaddress = socket.gethostbyname(self.hostname)
        self.master.title("Rsync for {u} on {h} {ip}".format(u=os.getenv("USER"),
                                                             h=self.hostname,
                                                             ip=self.ipaddress))

        # ################ Options for buttons ####################
        self.button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}
        self.canvas = tk.Canvas(self.master, height=200, width=300)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # dabrender = os.getenv("DABRENDERPATH")
        imagepath = os.path.join(os.path.dirname(dabtractor.__file__),"icons","Rsync_logo.gif")
        imagetk = tk.PhotoImage(file=imagepath)
        # keep a link to the image to stop the image being garbage collected
        self.canvas.img = imagetk
        tk.Label(self.canvas, image=imagetk).grid(row=0, column=0, columnspan=4,
                                                  sticky=tk.NW + tk.NE)
        __row = 1

        tk.Label(self.canvas,
                 bg=self.bgcolor3,
                 text="Copy data using rsync. \
                 Source can be file or directory").grid(row=__row,
                                                        column=0,
                                                        columnspan=4,
                                                        sticky=tk.W + tk.E)
        __row += 1

        tk.Label(self.canvas, bg=self.bgcolor2, text="Source Path").grid(row=__row, column=0)
        self.sdirbut = tk.Button(self.canvas, text=self.spath, bg=self.bgcolor1, fg='black',
                                 command=self.opensourcedirectory)
        self.sdirbut.pack(**self.button_opt)  # must pack separately to get the value to dirbut
        self.sdirbut.grid(row=__row, column=1, sticky=tk.W + tk.E)
        __row += 1


        tk.Label(self.canvas,
                 bg=self.bgcolor3,
                 text="Target must be a directory").grid(row=__row,
                                                         column=0,
                                                         columnspan=4,
                                                         sticky=tk.W + tk.E)
        __row += 1

        tk.Label(self.canvas, bg=self.bgcolor2, text="Target Path").grid(row=__row, column=0)
        self.tdirbut = tk.Button(self.canvas,
                                 text=self.tpath,
                                 bg = self.bgcolor1,
                                 fg='black',
                                 command=self.opentargetdirectory)
        self.tdirbut.pack(**self.button_opt)  # must pack separately to get the value to dirbut
        self.tdirbut.grid(row=__row, column=1, sticky=tk.W + tk.E)
        __row += 1


        tk.Label(self.canvas,
                 bg=self.bgcolor3,
                 text="Rsync Specific Details").grid(row=__row,
                                                     column=0,
                                                     columnspan=4,
                                                     sticky=tk.W + tk.E)
        __row += 1


        tk.Label(self.canvas, bg=self.bgcolor2, text="Other Options").grid(row=__row, column=0)
        self.options = tk.StringVar()
        self.options.set("")
        self.bar7 = tk.Entry(self.canvas, bg=self.bgcolor1,
                             textvariable=self.options,
                             width=40).grid(row=__row, column=1, sticky=tk.W + tk.E)

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

    # def openfile(self):
    #     self.filename = tkFileDialog.askopenfilename(parent=self.master,
    #                                                  initialdir=self.dirname,
    #                                                  title=self.filetext,
    #                                                  filetypes=[('maya ascii', '.ma'),
    #                                                             ('maya binary', '.mb')])
    #                                                             # filename not filehandle
    #     self.filebut["text"] = str(self.filename) if self.filename else self.filetext
    #
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

    def opensourcedirectory(self):
        self.sdirname = tkFileDialog.askdirectory(parent=self.master,
                                                  initialdir=self.initialProjectPath,
                                                  title=self.spath)
        self.sdirbut["text"] = str(self.sdirname) if self.sdirname else self.sdirtext


    def opentargetdirectory(self):
        self.tdirname = tkFileDialog.askdirectory(parent=self.master,
                                                  initialdir=self.initialProjectPath,
                                                  title=self.tpath)
        self.tdirbut["text"] = str(self.tdirname) if self.tdirname else self.tdirtext


    def validate(self):
        try:
            logger.info("Validate")
            logger.info("Source: %s" % self.sdirname)
            logger.info("Target: %s" % self.tdirname)
            logger.info("Options: %s" % self.options.get())
            self.spooljob = False
            self.validatejob = True
            self.master.destroy()
        except Exception, validateError:
            logger.warn("Problem validating %s" % validateError)

    def submit(self):
        try:
            logger.info("Submit")
            logger.info("Source: %s" % self.sdirname)
            logger.info("Target: %s" % self.tdirname)
            logger.info("Options: %s" % self.options.get())

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
