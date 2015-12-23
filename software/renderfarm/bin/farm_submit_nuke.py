#!/usr/bin/env rmanpy

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
__version__ = '1.00'

from Tkinter import *
import ttk
import tkMessageBox
import datetime
import tkFileDialog, Tkconstants
import tractor.api.author as author
from software.renderfarm.dabtractor.factories import configuration_factory as config
from software.renderfarm.dabtractor.factories import utils_factory as utils

from dabtractor.factories import user_factory as ufac
import os, sys

################################
_thisuser = os.getenv("USER")
(_usernumber,_username) =  ufac.FarmUser(_thisuser).query()

if not _username:
    sys.exit("Sorry you dont appear to be a registered farm user {}, try running farm_user.py and then contact matt - "
             "matthew.gidney@uts.edu.au".format(_thisuser))
################################

author.setEngineClientParam(hostname="tractor-engine", port=5600, user="mattg", debug=True)
user = os.getenv("USER")


class Window(object):
    def __init__(self, master):
        """Construct the main window interface
        """
        self.master = master
        self.filetext = 'Select your nuke script file'
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

        Label(master, text="Nuke Script to Render").grid(row=3, column=0)
        self.filebut = Button(self.master, text=self.filetext, fg='black',command=self.openfile)
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

        Label(master, text="Render Chunks of").grid(row=9, column=0)
        self.fch = StringVar()
        self.fch.set("5")
        self.bar6 = Entry(self.master, textvariable=self.fch, width=8).grid(row=9, column=1, sticky=W)

        Label(self.master, text="Nuke Version").grid(row=10, column=0)
        self.mversion = StringVar()
        self.mversion.set(config.CurrentConfiguration().nukeversion)
        combobox = ttk.Combobox(master, textvariable=self.mversion)
        combobox.config(values=config.ConfigurationBase().nukeversions)
        combobox.grid(row=10, column=1, sticky=W)


        Label(self.master, text="Output Nodes").grid(row=12, column=0)
        self.outputname = StringVar()
        self.outputname.set("Output")
        combobox = ttk.Combobox(master, textvariable=self.outputname)
        combobox.config(values=("Output","All Write Nodes"))
        combobox.grid(row=12, column=1, sticky=W + E)

        Label(master, text="Other Valid Nuke Options").grid(row=14, column=0)
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
        self.filename = tkFileDialog.askopenfilename(parent=self.master, initialdir=self.dabrender,
                                                     title=self.filetext,
                                                     filetypes=[('nuke script', '.nk')])  ## filename not filehandle
        self.filebut["text"] = str(self.filename) if self.filename else self.filetext


    def validate(self):
        logger.info("Validate")
        try:
            logger.info("SceneFile: %s" % self.filename)
            logger.info("Start: %s" % self.sf.get())
            logger.info("End: %s" % self.ef.get())
            logger.info("By: %s" % self.bf.get())
            self.spooljob = False
            self.validatejob = True
            self.master.destroy()

        except Exception, validateError:
            logger.warn("Problem validating %s" % validateError)

    def submit(self):
        logger.info("Submit")
        try:
            logger.info("SceneFile: %s" % self.filename)
            logger.info("Start: %s" % self.sf.get())
            logger.info("End: %s" % self.ef.get())
            logger.info("By: %s" % self.bf.get())
            self.spooljob = True
            self.validatejob = False
            self.master.destroy()
        except Exception, submiterror:
            logger.warn("Problem submitting %s" % submiterror)

    def cancel(self):
        logger.info("Camcelled")
        self.master.destroy()

    def selectRenderHome(self):
        logger.info("Select render home")


class BatchJob(object):

    def __init__(self):
        self.version = "9.0v6"
        self.nukescriptfullpath = 'scene.0001.nk'
        self.startframe = 100
        self.endframe = 200
        self.byframe = 1
        self.framechunks = 10
        self.options = ""
        self.dabrender = "/Volumes/dabrender"
        self.user = os.getenv("USER")
        self.spooljob = False
        self.job = ""

        try:
            # get the names of the central render location for the user
            ru = ufac.Student()
            self.renderusernumber = ru.number
            self.renderusername = ru.name
            self.dabrender = ru.dabrender
            self.dabrenderworkpath = ru.dabrenderwork
            self.initialProjectPath = ru.dabrenderwork

        except Exception, erroruser:
            logger.warn("Cant get the users name and number back %s" % erroruser)
            sys.exit("Cant get the users name")


    def getValues(entries):
        for entry in entries:
            field = entry[0]
            text = entry[1].get()
            logger.info('%s: "%s"' % ( field, text))

    def build(self):
        _nuke_proxy_template = "{d}/usr/custom/nuke/proxy_script_templates/nuke_proxy_v002.nk".format(d=self.dabrender)
        _nuke_version = "Nuke{}".format(config.CurrentConfiguration().nukeversion)
        _nuke_envkey = "nuke{}".format(config.CurrentConfiguration().nukeversion)
        _nuke_executable="/Applications/{n}/{n}.app/Contents/MacOS/{n}".format(n=_nuke_version)
        _nuke_range="{start}-{end}".format(start=self.startframe, end=self.endframe)
        _nukescriptbaseonly = os.path.basename(self.nukescriptfullpath)

        self.job = author.Job(title="Nuke Render Job: {} {}".format(self.renderusername, _nukescriptbaseonly),
                              priority=100,
                              envkey=[_nuke_envkey],
                              metadata="user={} realname={}".format(self.user,self.renderusername),
                              comment="LocalUser is {} {} {}".format(self.user, self.renderusername,
                                                                     self.renderusernumber),
                              service="NukeRender")


        # ############## 1 NUKE RENDER ###############
        parent = author.Task(title="Nuke Rendering",service="NukeRender")
        parent.serialsubtasks = 0

        if (self.endframe - self.startframe) < self.framechunks:
            self.framechunks = 1
            _chunkend = self.endframe
        else:
            _chunkend = self.startframe + self.framechunks

        _chunkstart = self.startframe

        while self.endframe >= _chunkstart:
            if _chunkend >= self.endframe:
                _chunkend = self.endframe

            t1 = "{}  {}-{}".format("Nuke Batch Render", _chunkstart, _chunkend)
            thischunk = author.Task(title=t1, service="NukeRender")

            commonargs = [_nuke_executable, "-x" ]
            userspecificargs = [
                utils.expandargumentstring(self.options),
            ]
            filespecificargs = [self.nukescriptfullpath, "{}-{}".format( _chunkstart, _chunkend)]

            finalargs = commonargs + userspecificargs + filespecificargs

            render = author.Command(argv=finalargs,
                                    service="NukeRender",
                                    envkey=[_nuke_envkey]
                                    )
            thischunk.addCommand(render)
            _chunkstart = _chunkend + 1
            _chunkend += self.framechunks
            parent.addChild(thischunk)

        self.job.addChild(parent)

    def validate(self):

        logger.info("\n\n{:_^80}\n{}\n{:_^80}".format("snip", self.job.asTcl(), "snip"))


    def mail(self, level="Level", trigger="Trigger", body="Render Progress Body"):
        bodystring = "{}  Progress: \nLevel: {}\nTrigger: {}\n\n{}".format(self.renderername,level,
                                                                                         trigger,
                                                                                         body)
        subjectstring = "FARM JOB: %s %s" % (str(self.mayascenenamebase), self.renderusername)
        mailcmd = author.Command(argv=["sendmail.py", "-t", "%s@uts.edu.au" % self.user,
                                       "-b", bodystring, "-s", subjectstring], service="Ffmpeg")
        return mailcmd

    def spool(self):
        try:
            logger.info("Spooled correctly")
            self.job.spool(owner="pixar")
        except Exception, err:
            logger.warn("A spool error %s" % err)


if __name__ == '__main__':
    root = Tk()
    root.title("Tractor Nuke Batch Submit {u} {f}".format(u=user, f="DAB"))
    window = Window(root)
    root.mainloop()

    if window.spooljob or window.validatejob is True:

        job = BatchJob()
        job.nukescriptfullpath = window.filename
        job.framechunks = int(window.fch.get())
        job.startframe = int(window.sf.get())
        job.endframe = int(window.ef.get())
        job.byframe = int(window.bf.get())
        job.options = window.options.get()

    try:
        job.build()
    except Exception, buildError:
        logger.warn("Something wrong building job %s" % buildError)

    if window.spooljob is True:
        try:
            job.validate()
            job.spool()
        except Exception, spoolError:
            logger.warn("Something wrong building job %s" % spoolError)

    if window.validatejob is True:
        try:
            job.validate()
        except Exception, validateError:
            logger.warn("Something wrong validating job %s" % validateError)

    '''
        ###################################################################################################
        This is a nuke batch job
        nuke -F 1-100 -x myscript.nk
        -a  Formats default to anamorphic.
        -b  Background mode. This launches Nuke and returns control to the terminal, so you get your prompt back. This is
        equivalent to appending a command with an & to run in the background.
        --crashhandling 1
        --crashhandling 0
        Breakpad crash reporting allows you to submit crash dumps to The Foundry in the unlikely event of a crash. By
         default, crash reporting is enabled in GUI mode and disabled in terminal mode.

        Use --crashhandling 1 to enable crash reporting in both GUI and terminal mode.
        Use --crashhandling 0 to disable crash reporting in both GUI and terminal mode.
        -c size (k, M, or G) Limit the cache memory usage, where size equals a number in bytes. You can specify a
        different unit by appending k (kilobytes), M (megabytes), or G (gigabytes) after size.
        -d <x server name> This allows Nuke to be viewed on one machine while run on another. (Linux only and requires
        some setting up to allow remote access to the X Server on the target machine).
        -f Open Nuke script at full resolution. Scripts that have been saved displaying proxy images can be opened to
        show the full resolution image using this flag. See also -p.

        -F Frame numbers to execute the script for. All -F arguments must precede the script name argument. Here are
        some examples:
        -F 3 indicates frame 3.
        -F 1-10 indicates frames 1, 2, 3, 4, 5, 6, 7, 8, 9, and 10.
        -F 1-10x2 indicates frames 1, 3, 5, 7, and 9.
        You can also use multiple frame ranges:
        nuke -F 1-5 -F 10 -F 30-50x2 -x myscript.nk

        -h Display command line help.
        -help Display command line help.
        -i Use an interactive (nuke_i) FLEXlm license key. This flag is used in conjunction with background rendering
        scripts using -x. By default -x uses a nuke_r license key, but -ix background renders using a nuke_i license key.
        -l New read or write nodes have the colorspace set to linear rather than default.
        -m # Set the number of threads to the value specified by #.
        -n Open script without postage stamps on nodes.
        --nocrashprompt  When crash handling is enabled in GUI mode, submit crash reports automatically without displaying
        a crash reporter dialog.
        --nukeassist  Launch Nuke Assist, which is licensed as part of a NukeX Maintenance package and is intended for use
        as a workstation for artists performing painting, rotoscoping, and tracking. Two complimentary licenses are
        included with every NukeX license.
        See the Meet the Nuke Product Family chapter in the Nuke Getting Started Guide for more information.
        -p  Open Nuke script at proxy resolution. Scripts that have been saved displaying full resolution images can be
        opened to show the proxy resolution image using this flag. See also -f.
        -P  Linux only. Measure your nodes performance metrics and show them in the Node Graph.
        --pause  Initial Viewers in the script specified on the command line should be paused.
        --ple Runs Nuke in Personal Learning Edition mode.
        --priority p Runs Nuke with a different priority, you can choose from:
        high (only available to the super user on Linux/OS X)
        medium
        low
        --python-no-root-knobdefaults  Prevents the application of knob defaults to the root node when executing
        a Python script.
        -q  Quiet mode. This stops all printing to the shell.
       -remap  Allows you to remap file paths in order to easily share Nuke projects across different operating systems.
       This is the command-line equivalent of setting the Path Remaps control in the Preferences dialog. The -remap flag
       takes a comma-separated list of paths as an argument. The paths are arranged in pairs where the first path of each
       pair maps to the second path of each pair. For example, if you use:
        nuke -t -remap "X:/path,Y:,A:,B:/anotherpath"
        Any paths starting with X:/path are converted to start with Y:.
        Any paths starting with A: are converted to start with B:/anotherpath.
        The -remap flag throws an error if:
        it is defined when starting GUI mode, that is, without -x or -t.
        the paths do not pair up. For example, if you use:
        nuke -t -remap "X:/path,Y:,A:"
        A: does not map to anything, and an error is produced.
        The -remap flag gives a warning (but does not error) if you give it no paths. For example:
        nuke -t -remap ""
        NOTE:  Note that the mappings are only applied to the Nuke session that is being started. They do not affect
        the Preferences.nk file used by the GUI.
        -s #  Sets the minimum stack size, or the node tree stach cache size for each thread in bytes. This defaults
        to 16777216 (16 MB). The smallest allowed value is 1048576 (1 MB).
        --safe   Running Nuke in this mode stops the following loading at startup:
        Any scripts or plug-ins in ~/.nuke
        Any scripts or plug-ins in $NUKE_PATH or %NUKE_PATH%
        Any OFX plug-in (including FurnaceCore)
        --sro  Forces Nuke to obey the render order of Write nodes so that Read nodes can use files created by earlier
         Write nodes.
       -t   Terminal mode (without GUI). This allows you to enter Python commands without launching the GUI.
        A >>> command prompt is displayed during this mode. Enter quit() to exit this mode and return to the shell prompt.
        This mode uses a nuke_r license key by default, but you can get it to use a nuke_i key by using the -ti flag combo.
        --tg  Terminal Mode. This also starts a QApplication so that Pyside/PyQt can be used. This mode uses an interactive
         license, and on Linux requires an X Windows display session.
        -V level   Verbose mode. In the terminal, youll see explicit commands as each action is performed in Nuke. Specify
         the level to print more in the Terminal, select from:
        0 (not verbose)
        1 (outputs Nuke script load and save)
        2 (outputs loading plug-ins, Python, TCL, Nuke scripts, progress and buffer reports)
        -v  This command displays an image file inside a Nuke Viewer. Heres an example:
        nuke -v image.tif
        --view v   Only execute the specified views. For multiple views, use a comma separated list:
    left,right
        --version   Display the version information in the shell.
        -x   eXecute mode. Takes a Nuke script and renders all active Write nodes.
        Note that it is not possible to render a PLE (Personal Learning Edition) script with -x from the command line,
        that is, using the syntax:
        nuke -x myscript.nk
        Note also that this mode uses a FLEXlm nuke_r license key. To use a nuke_i license key, use -xi. This is the
        syntax:
        nuke -xi myscript.nk
        On Windows, you can press Ctrl+Break to cancel a render without exiting if a render is active, or exit if not.
         Ctrl/Cmd+C exits immediately.
        On Mac and Linux, Ctrl/Cmd+C always exits.
        -X node   Render only the Write node specified by node.
        --   End switches, allowing script to start with a dash or be just - to read from stdin


        '''

