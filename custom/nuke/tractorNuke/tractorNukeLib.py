import nuke
import os
import commands
import sys
import re
import time

import sys
import socket
import select
import struct
import errno

import platform
import optparse
import datetime
import getpass

import ConfigParser

TrFileRevisionDate = "$DateTime: 2009/04/23 17:17:43 $"

##-------------------------------------------------------------- ##
##
## tractorNukeLib.py - a python script for Nuke to spool Nuke
## jobs to Pixar's Tractor
##
## 
## author: Ian Hsieh, ihsieh@pixar.com (2011/07/21)
##
##-------------------------------------------------------------- ##

## ------------------------------------------------------------- ##

class TrHttpRPC (object):

    def __init__(self, host, port=80, logger=None,
                apphdrs={}, urlprefix="/Tractor/", timeout=30.0):

        self.host = host
        self.port = port
        self.logger = logger
        self.appheaders = apphdrs
        self.urlprefix = urlprefix
        self.timeout = timeout

        if port <= 0:
            h,c,p = host.partition(':')
            if p:
                self.host = h
                self.port = int(p)

        # embrace and extend errno values
        if not hasattr(errno, "WSAECONNRESET"):
            errno.WSAECONNRESET = 10054
        if not hasattr(errno, "WSAECONNREFUSED"):
            errno.WSAECONNREFUSED = 10061


    def Transaction (self, tractorverb, formdata, parseCtxName=None,
                        xheaders={}, analyzer=None):
        """
        Make an HTTP request and retrieve the reply from the server.
        An implementation using a few high-level methods from the
        urllib2 module is also possible, however it is many times
        slower than this implementation, and pulls in modules that
        are not always available (e.g. when running in maya's python).
        """
        outdata = None
        errcode = 0
        s = None

        try:
            # like:  http://tractor-engine:80/Tractor/task?q=nextcmd&...
            # we use POST when making changes to the destination (REST)
            req = "POST " + self.urlprefix + tractorverb + " HTTP/1.0\r\n"
            for h in self.appheaders:
                req += h + ": " + self.appheaders[h] + "\r\n"
            for h in xheaders:
                req += h + ": " + xheaders[h] + "\r\n"

            t = ""
            if formdata:
                t = formdata.strip()
                if t and "Content-Type: " not in req:
                    req += "Content-Type: application/x-www-form-urlencoded\r\n"

            req += "Content-Length: %d\r\n" % len(t)
            req += "\r\n"  # end of http headers
            req += t

            # error checking?  why be a pessimist?
            # that's why we have exceptions!

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect( (self.host, self.port) )
            s.sendall(req)

            mustTimeWait = False

            t = ""  # build up the reply text
            while 1:
                r,w,x = select.select([s], [], [], self.timeout)
                if r:
                    if 0 == len(r):
                        self.Debug("time-out waiting for http reply")
                        mustTimeWait = True
                        break
                    else:
                        r = s.recv(4096)
                if not r:
                    break
                else:
                    t += r

            # Attempt to reduce descriptors held in TIME_WAIT on the
            # engine by dismantling this request socket immediately
            # if we've received an answer.  Usually the close() call
            # returns immediately (no lingering close), but the socket
            # persists in TIME_WAIT in the background for some seconds.
            # Instead, we force it to dismantle early by turning ON
            # linger-on-close() but setting the timeout to zero seconds.
            #
            if not mustTimeWait:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                                 struct.pack('ii', 1, 0))
            s.close()

            if t and len(t):
                n = t.find("\r\n\r\n")
                h = t[0:n] # headers

                n += 4
                outdata = t[n:].strip()  # body, or error msg, no CRLF

                n = h.find(' ') + 1
                e = h.find(' ', n)
                errcode = int( h[n:e] )

                if errcode == 200:
                    errcode = 0

                    # expecting a json dict?  parse it
                    if outdata and parseCtxName:
                        try:
                            outdata = self.parseJSON(outdata)

                        except Exception:
                            errcode = -1
                            self.Debug("json parse:\n" + outdata)
                            outdata = "parse %s: %s" % \
                                        (parseCtxName, self.Xmsg())

                if analyzer:
                    analyzer( h )

            else:
                outdata = "no data received"
                errcode = -1

        except Exception, e:
            if e[0] in (errno.ECONNREFUSED, errno.WSAECONNREFUSED):
                outdata = "connection refused"
                errcode = e[0]
            elif e[0] in (errno.ECONNRESET, errno.WSAECONNRESET):
                outdata = "connection dropped"
                errcode = e[0]
            else:
                errcode = -1
                outdata = "http transaction: " + self.Xmsg()

        return (errcode, outdata)


    def parseJSON(self, json):
        #
        # A simpleminded "converter" from inbound json to python dicts.
        #
        # Expect a JSON object, which of course also happens to be the
        # same format as a python dictionary:
        #  { "user": "yoda", "jid": 123, ..., "cmdline": "pixar ..." }
        #
        # NOTE: python eval() will *fail* on strings ending in CRLF (\r\n),
        # they must be stripped!  (by our caller, if necessary)
        #
        # We add local variables to stand in for the three JSON
        # "native" types that aren't available in python, however
        # these types aren't expected to appear in tractor data.
        #
        null = None
        true = True
        false = False

        return eval( json )


    def Debug (self, txt):
        if self.logger:
            self.logger.debug(txt)

    def Xmsg (self):
        if self.logger and hasattr(self.logger, 'Xcpt'):
            return self.logger.Xcpt()
        else:
            errclass, excobj = sys.exc_info()[:2]
            return "%s - %s" % (errclass.__name__, str(excobj))

## ------------------------------------------------------------- ##

def trAbsPath (path):
    '''
    Generate a canonical path for tractor.  This is an absolute path
    with backslashes flipped forward.  Backslashes have been known to
    cause problems as they flow through system, especially in the 
    Safari javascript interpreter.
    '''
    return os.path.abspath( path ).replace('\\', '/')

## ------------------------------------------------------------- ##

def jobSpool (jobfile, options):
    '''
    Transfer the given job (alfred script) to the central job queue.
    '''

    if options.ribspool:
        alfdata = options.ribjobtxt
    else:
        # usual case, read the alfred jobfile
        f = open(jobfile, "rb")
        alfdata = f.read()
        f.close()

    hdrs = {
        'Content-Type':         'application/tractor-spool',
        'X-Tractor-User':       options.uname,
        'X-Tractor-Spoolhost':  options.hname,
        'X-Tractor-Dir':        options.jobcwd,
        'X-Tractor-Jobfile':    trAbsPath(jobfile),
        'X-Tractor-Priority':   str(options.priority)
    }

    return TrHttpRPC(options.mtdhost,0).Transaction("spool",alfdata,None,hdrs)

## ------------------------------------------------------------- ##

def jobDelete (options):
    '''
    Request that a job be deleted from the tractor queue
    '''
    sjid = str( options.jdel_id )

    q = "queue?q=jdelete&jid=" + sjid
    q += "&user=" + options.user
    q += "&hnm=" + options.hname

    rc, msg = TrHttpRPC(options.mtdhost,0).Transaction(q)

    if 0 == rc:
        print "J" + sjid + " delete OK"
    else:
        print msg

    return rc

## ------------------------------------------------------------ ##

##
## Spool function. This code is taken from 
## the Tractor blade's tractor-spool.py script, with a couple
## of the options removed (Ex: -rib).
##

def Spool (argv):
    '''
    tractor-spool - main - examine options, connect to engine, transfer job
    '''
    appName =        "tractor-spool"
    appVersion =     "TRACTOR_VERSION"
    appProductDate = "TRACTOR_BUILD_DATE"
    appDir = os.path.dirname( os.path.realpath( __file__ ) )

    defaultMtd  = "tractor-engine:80"

    spoolhost = socket.gethostname().split('.')[0] # options can override
    user = getpass.getuser()

    # ------ # 

    if not appProductDate[0].isdigit():
        appProductDate = " ".join(TrFileRevisionDate.split()[1:3])
        appVersion = "dev"

    appBuild = "%s %s (%s)" % (appName, appVersion, appProductDate)

    optparser = optparse.OptionParser(version=appBuild,
                                      usage="%prog [options] JOBFILE...\n"
                                        "%prog [options] --rib RIBFILE...\n"
                                        "%prog [options] --jdelete JOB_ID" )

    optparser.add_option("--priority", dest="priority",
            type="float", default=1.0,
            help="priority of the new job")

    optparser.add_option("--engine", dest="mtdhost",
            type="string", default=defaultMtd,
            help="hostname[:port] of the master tractor daemon, "
                 "default is '"+defaultMtd+"' - usually a DNS alias")

    optparser.add_option("--hname", dest="hname",
            type="string", default=spoolhost,
            help="the origin hostname for this job, used to find the "
                 "'home blade' that will run 'local' Cmds; default is "
                 "the locally-derived hostname")

    optparser.add_option("--user", dest="uname",
            type="string", default=user,
            help="alternate job owner, default is user spooling the job")

    optparser.add_option("--jobcwd", dest="jobcwd",
            type="string", default=trAbsPath(os.getcwd()),
            help="blades will attempt to chdir to the specified directory "
                 "when launching commands from this job; default is simply "
                 "the cwd at time when tractor-spool is run")

    optparser.add_option("--nrm", dest="ribspool",
            action="store_const", const="nrm",
            help="a variant of --rib, above, that causes the generated "
                 "tractor job to use netrender on the local blade rather "
                 "than direct rendering with prman on a blade; used when "
                 "the named RIBfile is not accessible from the remote "
                 "blades directly")

    optparser.add_option("--skey", dest="ribservice",
            type="string", default="pixarRender",
            help="used with --rib to change the service key used to "
                 "select matching blades, default: pixarRender")

    optparser.add_option("--jdelete", dest="jdel_id",
            type="string", default=None,
            help="delete the requested job from the queue")

    optparser.set_defaults(loglevel=1)
    optparser.add_option("-v",
            action="store_const", const=2, dest="loglevel",
            help="verbose status")
    optparser.add_option("-q",
            action="store_const", const=0, dest="loglevel",
            help="quiet, no status")

    optparser.add_option("--paused", dest="paused",
            action="store_true", default=False,
            help="submit job in paused mode")

    rc = 0
    xcpt = None

    try:
        options, jobfiles = optparser.parse_args( argv )

        if options.jdel_id:
            if len(jobfiles) > 0:
                optparser.error("too many arguments for jdelete")
                return 1
            else:
                return jobDelete(options)

        if 0 == len(jobfiles):
            optparser.error("no job script specified")
            return 1

        if options.loglevel > 1:
            print "%s\nCopyright (c) 2007-%d Pixar. All rights reserved." \
                    % (appBuild, datetime.datetime.now().year)

        if options.mtdhost != defaultMtd:
            h,n,p = options.mtdhost.partition(":")
            if not p:
                options.mtdhost = h + ':80'

        # paused starting is represented by a negative priority
        # decremented by one. This allows a zero priority to pause
        if options.paused:
            try:
                options.priority = str( -float( options.priority ) -1 )
            except Exception:
                options.priority = "-2"

        #
        # now spool new jobs
        #
        for filename in jobfiles:
            rc, xcpt = jobSpool(filename, options)
            if rc:
                break

    except KeyboardInterrupt:
        xcpt = "received keyboard interrupt"

    except SystemExit, e:
        rc = e

    except:
        errclass, excobj = sys.exc_info()[:2]
        xcpt = "job spool: %s - %s" % (errclass.__name__, str(excobj))
        rc = 1

    if xcpt:
        print >>sys.stderr,xcpt

    return rc

## ----------------------------------------------------------------------- ##

## 
## renderPanel function
##
## Creates the UI Panel in Nuke. This is the function
## that should be called from Nuke.
##
def renderPanel(debug=False):
    panel = nuke.Panel("Tractor Spool")
    dire = ''
    
    ## Get .nuke directory
    if not 'HOME' in os.environ.keys():
        dire = os.environ['USERPROFILE']
    else:
        dire = os.environ['HOME']
    dire += '/.nuke/tractorNuke'
    if not os.path.exists(dire):
        os.makedirs(dire)

    script = nuke.root().name() 

    iniFile = dire + '/tractorNuke.ini'

    engine = 'tractor-engine'
    port = 80
    if 'TRACTOR_ENGINE' in os.environ.keys():
        name = os.environ['TRACTOR_ENGINE']
        engine,n,p = name.partition(":")
        if p: 
            port = p

    style = 'Local Remote'
    startPaused = False
    delJobScript = False
    jobPriority = 1
    nthreads = 1
    RAM = '0' 
    jobServerAttributes = 'NukeRender'
    jobCmdTags = ''
    envKey = ''
    jobDoneCmd = ''
    jobErrorCmd = ''
    crews = ''
    extraJobOptions = ''
    ff = nuke.value('first_frame')
    lf = nuke.value('last_frame')
    nukeX = False
    selected_only = False
    saveBeforeRender = True

    Config = ConfigParser.ConfigParser()

    ## Get values from ini file, tractorNuke.ini, if it exists
    if os.path.exists(iniFile):
        Config.read(iniFile)
        if Config.has_option('Options', 'Engine'):
            engine = Config.get('Options', 'Engine')
        if Config.has_option('Options', 'Port'):
            port = Config.getint('Options', 'Port')
        if Config.has_option('Options', 'Start Paused'):
            startPaused = Config.getboolean('Options', 'Start Paused')
        if Config.has_option('Options', 'Delete Job'):
            delJobScript = Config.getboolean('Options', 'Delete Job')
        if Config.has_option('Options', 'Priority'):
            jobPriority = Config.getfloat('Options', 'Priority')
        if Config.has_option('Options', 'Threads'):
            nthreads = Config.getint('Options', 'Threads')
        if Config.has_option('Options', 'Max RAM'):
            RAM = Config.get('Options', 'Max RAM')
        if Config.has_option('Options', 'Job Server Attributes'):
            jobServerAttributes = Config.get('Options', 'Job Server Attributes')
        if Config.has_option('Options', 'Job Cmd Tags'):
            jobCmdTags = Config.get('Options', 'Job Cmd Tags')
        if Config.has_option('Options', 'Env Key'):
            envKey = Config.get('Options', 'Env Key')
        if Config.has_option('Options', 'Job Done Cmd'):
            jobDoneCmd = Config.get('Options', 'Job Done Cmd')
        if Config.has_option('Options', 'Job Error Cmd'):
            jobErrorCmd = Config.get('Options', 'Job Error Cmd')
        if Config.has_option('Options', 'Crews'):
            crews = Config.get('Options', 'Crews')
        if Config.has_option('Options', 'Extra Job Options'):
            extraJobOptions = Config.get('Options', 'Extra Job Options')
        if Config.has_option('Options', 'Render with NukeX'):
            nukeX = Config.getboolean('Options', 'Render with NukeX')
        if Config.has_option('Options', 'Selected Only'):
            selected_only = Config.getboolean('Options', 'Selected Only')
        if Config.has_option('Options', 'Save Before Render'):
            saveBeforeRender = Config.getboolean('Options', 'Save Before Render')


    panel.addSingleLineInput('Tractor Engine', engine)
    panel.addSingleLineInput('Port', port)
    panel.addSingleLineInput('Threads', nthreads)
    panel.addSingleLineInput('Max RAM Usage (in MB, 0 for default)', RAM)
    panel.addSingleLineInput('Script',script)
    panel.addEnumerationPulldown('Style', style)
    panel.addBooleanCheckBox('Start Paused', startPaused)
    panel.addBooleanCheckBox('Delete Job Script', delJobScript)
    panel.addSingleLineInput('Job Priority', jobPriority)
    panel.addSingleLineInput('Job Server Attributes', jobServerAttributes)
    panel.addSingleLineInput('Job Cmd Tags', jobCmdTags)
    panel.addSingleLineInput('Environment Key', envKey)
    panel.addSingleLineInput('Job Done Command', jobDoneCmd)
    panel.addSingleLineInput('Job Error Command', jobErrorCmd)
    panel.addSingleLineInput('Crews', crews)
    panel.addSingleLineInput('Extra Job Options', extraJobOptions)
    panel.addSingleLineInput('First Frame',  ff)
    panel.addSingleLineInput('Last Frame',  lf)
    panel.addBooleanCheckBox('Render with NukeX', nukeX)
    panel.addBooleanCheckBox('Selected Only', selected_only)
    panel.addBooleanCheckBox('Save before Render', saveBeforeRender)
    panel.addButton('Cancel')
    panel.addButton('Spool Job')
    result = panel.show()
   
    if debug: print 'result:'+str(result)

    saveBeforeRender = panel.value('Save before Render')
    
    if saveBeforeRender:
            print 'Saving script before Render '+script
            nuke.scriptSave()
            
    selected_only = panel.value('Selected Only')    
    ff = int(panel.value('First Frame'))
    lf = int(panel.value('Last Frame'))
    engine = panel.value('Tractor Engine')
    port = int(panel.value('Port'))
    style = panel.value('Style')
    startPaused = panel.value('Start Paused')
    delJobScript = panel.value('Delete Job Script')
    jobPriority = float(panel.value('Job Priority'))
    jobServerAttributes = panel.value('Job Server Attributes')
    jobCmdTags = panel.value('Job Cmd Tags')
    envKey = panel.value('Environment Key')
    jobDoneCmd = panel.value('Job Done Command')
    jobErrorCmd = panel.value('Job Error Command')
    crews = panel.value('Crews')
    extraJobOptions = panel.value('Extra Job Options')
    nukeX = panel.value('Render with NukeX')
    nthreads = int(panel.value('Threads'))
    RAM = int(panel.value('Max RAM Usage (in MB, 0 for default)'))

    if style == 'Local':
        style = 'Cmd'
    else:
        style = 'RemoteCmd'

    if result == 0:
        return

    ## Write to ini file
    if not 'Options' in Config.sections():
        Config.add_section('Options')
    Config.set('Options', 'Engine', engine)
    Config.set('Options', 'Port', port)
    Config.set('Options', 'Start Paused', startPaused)
    Config.set('Options', 'Delete Job', delJobScript)
    Config.set('Options', 'Priority', jobPriority)
    Config.set('Options', 'Threads', nthreads)
    Config.set('Options', 'Max RAM', RAM)
    Config.set('Options', 'Job Server Attributes', jobServerAttributes)
    Config.set('Options', 'Job Cmd Tags', jobCmdTags)
    Config.set('Options', 'Env Key', envKey)
    Config.set('Options', 'Job Done Cmd', jobDoneCmd)
    Config.set('Options', 'Job Error Cmd', jobErrorCmd)
    Config.set('Options', 'Crews', crews)
    Config.set('Options', 'Extra Job Options', extraJobOptions)
    Config.set('Options', 'Render with NukeX', nukeX)
    Config.set('Options', 'Selected Only', selected_only)
    Config.set('Options', 'Save Before Render', saveBeforeRender)
    newiniFile = open(iniFile, 'w')
    Config.write(newiniFile)
    newiniFile.close()
    ## write frame range to project settings
    nuke.root().knob('first_frame').setValue(ff)
    nuke.root().knob('last_frame').setValue(lf)

    args = []
    args.append('--engine=' + engine + ':' + str(port))
    args.append('--style='+style)
    if startPaused:
        args.append('--paused')
    if delJobScript:
        args.append('--delJobScript')
    args.append('--jobPriority='+str(jobPriority))
    args.append('--jobServerAttributes='+str(jobServerAttributes))
    args.append('--jobCmdTags='+str(jobCmdTags))
    args.append('--envkey='+str(envKey))
    args.append('--jobDoneCmd='+str(jobDoneCmd))
    args.append('--jobErrorCmd='+str(jobErrorCmd))
    args.append('--crews='+str(crews))
    args.append('--extraJobOptions='+str(extraJobOptions))
    args.append('--dir='+str(dire))
    args.append('--ff='+str(ff))
    args.append('--lf='+str(lf))
    if selected_only:
        args.append('--selected_only')
    if debug:
        args.append('--debug')
    if nukeX:
        args.append('--nukeX')
    args.append('--script='+str(script))
    args.append('--threads='+str(nthreads))
    args.append('--ram='+str(RAM))

    render(args)

## ------------------------------------------------------------------------ ##

##
## render function
##
## called from renderPanel function passing all of the arguments
## that the user set in the UI.
##
def render(argv):


    ## Parse arguments
    optparser = optparse.OptionParser()
    optparser.add_option("--jobPriority", dest="pbias",
            type="float", default=1.0)
    optparser.add_option("--engine", dest="engine",
            type="string", default="tractor-engine:80")
    optparser.add_option("--ff", dest="ff",
            type="int", default=int(nuke.value('first_frame')))
    optparser.add_option("--lf", dest="lf",
            type="int", default=int(nuke.value('last_frame')))
    optparser.add_option("--dir", dest="dire",
            type="string", default=os.getcwd())
    optparser.add_option("--style", dest="style",
            type="string", default="Cmd")
    optparser.add_option("--paused", dest="paused",
            action="store_true")
    optparser.add_option("--delJobScripts", dest="delJob",
            action="store_true")
    optparser.add_option("--jobServerAttributes", dest="jobServerAttributes",
            type="string", default='')
    optparser.add_option("--jobCmdTags", dest="jobCmdTags",
            type="string", default='')
    optparser.add_option("--envkey", dest="envkey",
            type="string", default='')
    optparser.add_option("--jobDoneCmd", dest="jobDoneCmd",
            type="string", default='')
    optparser.add_option("--jobErrorCmd", dest="jobErrorCmd",
            type="string", default='')
    optparser.add_option("--crews", dest="crews",
            type="string", default='')
    optparser.add_option("--extraJobOptions", dest="extraJobOptions",
            type="string", default='')
    optparser.add_option("--selected_only", dest="selected_only",
            action="store_true")
    optparser.add_option("--debug", dest="debug",
            action="store_true")
    optparser.add_option("--nukeX", dest="nukeX",
            action="store_true")
    optparser.add_option("--script", dest="script",
            type="string", default=nuke.root().name())
    optparser.add_option("--threads", dest="threads",
            type="int", default=1)
    optparser.add_option("--ram", dest="RAM",
            type="int", default=0)

    (opts, args) = optparser.parse_args( argv )
    
    # nodes to render
    nodes = None
    if opts.selected_only:
        nodes = nuke.selectedNodes()
    else:
        nodes = nuke.root().nodes()
            
    #look for Write nodes
    if opts.debug: print 'Scanning %d nodes'%len(nodes)
    write_nodes = list()
    for node in nodes:
        if opts.debug: print node.fullName()+' '+str(node.Class())
        if node.Class() == 'Write':
             write_nodes.append(node)
             continue
        try:
            for subnode in node.nodes():
                #I think this is fully recursive
                if subnode.Class() == 'Write':
                    write_nodes.append(subnode)
        except AttributeError:
            #thrown by nodes() on non-group or gizmo
            pass            

    print ''
    if (len(write_nodes) < 1):
        print 'tractorNuke: No renderable nodes selected'
        return
                
    #for each write node, get its name for the -X arg of nuke              
    write_node_names = list()
    for node in write_nodes: 
            write_node_names.append(node.fullName())

    #for each write node, compute the frame name for each frame
    #this accounts for expressions, offsets, etc    
    image_names = dict()
    for frame in range(opts.ff, opts.lf+1):
        #nuke.Root.setFrame(frame)
        nuke.frame(frame) #deprecated but seems to work better than using Root
        image_names[frame] = list()
        for node in write_nodes:      
                filename = nuke.filename(node,nuke.REPLACE)           
                print filename
                image_names[frame].append(filename)
 
    if opts.debug:
        print 'Submitting:'
        print opts.script
        print write_node_names
        print image_names

    only_nodes_cmd = '' #this will remain empty if all nodes are to be rendered
    if write_node_names:
         only_nodes_cmd = ' -X '+','.join(write_node_names)

    ## Open file for writing and write the Job file
    currentTime = time.strftime('%a, %d %b %Y %H:%M:%S +0000', time.gmtime())
    fnm = ''
    fnm = opts.dire.replace('\\', '/') + '/tmpNuke_' + str(time.time()) + '.alf'
    jobFile = open(fnm, 'w')

    cmdtail = '-service { ' + opts.jobServerAttributes + '} -envkey { ' 
    cmdtail = cmdtail + ' ' + opts.envkey + '}'
    
    jobFile.write('##AlfredToDo 3.0\n')
    jobFile.write('##\n')
    jobFile.write('## Generated: ' + str(currentTime) +'\n')
    jobFile.write('## Nuke Script: ' + opts.script + '\n')
    jobFile.write('##\n\n')

    jobFile.write('Job -title {' + opts.script + '}')
    jobFile.write(' -pbias ' + str(opts.pbias) + '')
    jobFile.write(' -tags { ' + opts.jobCmdTags + '}')
    jobFile.write(' -service {' + opts.jobServerAttributes + '}')
    jobFile.write(' -crews {' + opts.crews + '}')
    jobFile.write(' -envkey {' + opts.envkey + '}')
    jobFile.write(' -whendone {' + opts.jobDoneCmd + '}')
    jobFile.write(' -whenerror {' + opts.jobErrorCmd + '}')
    jobFile.write(' ' + opts.extraJobOptions + ' ')
    jobFile.write('-subtasks {\n')

    jobFile.write('Task -title {Job} -serialsubtasks 0 -subtasks {\n')

    ##---------------------------------------------------------------------

    ## Query for the path to Nuke's executable.
    ## If sites are running different OS's, they should uncomment the second
    ## line so that the command only contains the Nuke executable. 
    ## Then, they should add an evironment key that includes the Nuke version
    ## For example:
    ##  nuke6.3v1
    ##
    nuke_exe = nuke.env['ExecutablePath']
    nuke_exe = os.path.basename(nuke_exe)

    ##--------------------------------------------------------------------

    for frame in range(opts.ff, opts.lf+1): 

        title = ''
        title = 'Frame ' + str(frame)

        jobFile.write('   Task -title {' + title + '} -cmds {\n')
        cmd = '"' + nuke_exe + '" -F %d -m %d -t %s '%(frame, opts.threads, only_nodes_cmd)
        if opts.RAM != 0:
            cmd = cmd + ' -c %dM'%(opts.RAM)
        if opts.nukeX:
            cmd = cmd + ' --nukex '
        cmd = cmd + ' -x "%s"'%(opts.script)
        jobFile.write( '        ' + opts.style + ' {' + cmd + '} ' + cmdtail + '\n')
        jobFile.write('   }\n')

    jobFile.write('} -cleanup {\n')
    if opts.delJob:
        jobFile.write('     File delete "' + fnm + '"\n')
    jobFile.write('}\n')
    jobFile.write('}\n')
    jobFile.close()

    args = []
    args.append('--engine=' + opts.engine)
    if opts.paused:
        args.append('--paused')
    args.append(fnm)
    
    ## Spool job
    Spool(args)
