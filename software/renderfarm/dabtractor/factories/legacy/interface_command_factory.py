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
sh.setLevel(logging.DEBUG)
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


class WindowCommand(WindowBase):
    """
    Ui Class for render submit
    """

    def __init__(self):
        """Construct the main window interface
        """
        super(WindowCommand, self).__init__()
        self.dirtext = 'Select your starting folder for the command to run in'
        self.dirname = "/var/tmp"
        self.bgcolor1 = "white"
        self.bgcolor2 = "lemon chiffon"
        self.bgcolor3 = "white"
        self.master.configure(background=self.bgcolor1)
        self.master.title("Tractor Shell Command Submit {u} {f}".format(u=os.getenv("USER"), f="DAB"))


        ################
        self.canvas = tk.Canvas(self.master, height=200, width=300)
        self.canvas.pack(expand=True, fill=tk.BOTH)
        imagepath = os.path.join(os.path.dirname(dabtractor.__file__),"icons","UTS_logo.gif")
        image1 = tk.PhotoImage(file=imagepath)

        # keep a link to the image to stop the image being garbage collected
        self.canvas.img = image1
        self.canvas.create_image(0, 0, anchor=tk.NW, image=image1)

        __row = 1

        tk.Label(self.canvas).grid(row=__row, sticky=tk.W)
        __row += 1
        tk.Label(self.canvas).grid(row=__row, sticky=tk.W)
        __row += 1
        tk.Label(self.canvas).grid(row=__row, sticky=tk.W)
        __row += 1
        tk.Label(self.canvas).grid(row=__row, sticky=tk.W)
        __row += 1
        tk.Label(self.canvas).grid(row=__row, sticky=tk.W)
        __row += 1
        tk.Label(self.canvas).grid(row=__row, sticky=tk.W)
        __row += 1
        tk.Label(self.canvas).grid(row=__row, sticky=tk.W)
        __row += 1
        tk.Label(self.canvas).grid(row=__row, sticky=tk.W)
        __row += 1
        tk.Label(self.canvas).grid(row=__row, sticky=tk.W)
        __row += 1
        tk.Label(self.canvas).grid(row=__row, sticky=tk.W)
        __row += 1
        # tk.Label(self.canvas, bg=self.bgcolor1, text=" --MAYA---> ").grid(row=__row, column=0)
        tk.Label(self.canvas, bg=self.bgcolor1, text="Bash Shell Commands to Run").grid(
            row=__row, column=1)
        __row += 1
        # ################ Options for buttons ####################

        self.button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Start Dir").grid(row=__row, column=0, sticky=tk.E)
        self.dirbut = tk.Button(self.canvas, text=self.dirtext, bg=self.bgcolor2, fg='black',
                                command=self.opendirectory)
        self.dirbut.pack(**self.button_opt)  # must pack separately to get the value to dirbut
        self.dirbut.grid(row=__row, column=1, columnspan=4, sticky=tk.W + tk.E)
        __row += 1
        # ###################################################################

        # tk.Label(self.canvas, bg=self.bgcolor1, text="Command").grid(row=__row, column=0)
        # self.command = tk.StringVar()
        # self.command.set("")
        # self.bar7 = tk.Entry(self.canvas, bg=self.bgcolor2,
        #                      textvariable=self.command, width=40).grid(row=__row, column=1, columnspan=4, sticky=tk.W + tk.E)
        # __row += 1
        # ###################################################################

        tk.Label(self.canvas, bg=self.bgcolor1,
                 text="Commands").grid(row=__row, column=0)
        self.command = tk.StringVar()
        _common_commands = [
            "du -sg /Volumes/dabrender/work/* | sort -rn | mail 120988@uts.edu.au",
            "du -sg /Volumes/dabrender/projects/* | sort -rn | mail 120988@uts.edu.au",

        ]
        self.command.set(_common_commands[0])
        combobox = ttk.Combobox(self.canvas, textvariable=self.command)
        combobox.config(values=_common_commands)
        # combobox.current(0)
        combobox.grid(row=__row, column=1, columnspan=4, sticky=tk.W + tk.E)
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

        tk.Label(self.canvas, bg=self.bgcolor1, text="------- Submit Job To Tractor  -------").grid(row=__row, column=1)
        __row += 1

        # tk.Buttons
        self.cbutton = tk.Button(self.canvas, bg=self.bgcolor1, text='SUBMIT', command=lambda: self.submit())
        self.cbutton.grid(row=__row, column=3, sticky=tk.W + tk.E)

        self.vbutton = tk.Button(self.canvas, bg=self.bgcolor1, text='VALIDATE', command=lambda: self.validate())
        self.vbutton.grid(row=__row, column=1, sticky=tk.W + tk.E)

        self.vbutton = tk.Button(self.canvas, bg=self.bgcolor1, text='CANCEL', command=lambda: self.cancel())
        self.vbutton.grid(row=__row, column=0, sticky=tk.W + tk.E)

        self.master.mainloop()

    def opendirectory(self):
        self.dirname = tkFileDialog.askdirectory(parent=self.master,
                                                 initialdir=self.initialProjectPath,
                                                 title=self.dirtext)
        self.dirbut["text"] = str(self.dirname) if self.dirname else self.dirtext
        # _possible = "%s/workspace.mel" % self.dirname
        # if os.path.exists(_possible):
        #     self.workspace = _possible
        #     self.workspacebut["text"] = str(self.workspace) if self.workspace else self.workspacetext
        # else:
        #     self.workspacebut["text"] = self.workspaceerrortext

    def validate(self):
        try:
            logger.info("Validate")
            logger.info("Command: %s" % self.command.get())
            # logger.info("Options: %s" % self.options.get())
            self.spooljob = False
            self.validatejob = True
            self.master.destroy()

        except Exception, validateError:
            logger.warn("Problem validating %s" % validateError)

    def submit(self):
        try:
            logger.info("Validate")
            logger.info("Command: %s" % self.command)
            # logger.info("Options: %s" % self.options)
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
