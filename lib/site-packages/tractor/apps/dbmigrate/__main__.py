"""
This program is used to migrate jobs in the 1.x (filesystem-based) format
to the 2.x (postgresql) format.
"""

import sys, os, ast, subprocess, time, shutil, StringIO

import tractor.base.rpg
import rpg.sql.PGFormat as PGFormat
import rpg.CmdLineTool as CmdLineTool
import rpg.OptionParser as OptionParser
import rpg.sql

import tractor.apps.dbctl.ddl as ddl
import tractor.base.EngineDB as EngineDB
import tractor.base.EngineConfig as EngineConfig
import FileSystemDB

RELATIVE_PATH_TO_INSTALL_ROOT = "../../../../../.." 
PROGRAM_NAME = "tractor-dbmigrate"
MIGRATE_USER = "dispatcher"
MIGRATE_PASSWORD = ""

class DBMigrateToolError(CmdLineTool.CmdLineToolError):
    pass

class DBMigrateTool(CmdLineTool.BasicCmdLineTool):
    description = """
    This program is used to migrate jobs in a Tractor 1.x data directory
    to the Tractor 2.x relational database.
    """

    options = [
        CmdLineTool.BooleanOption ("--complete",dest="complete", help="migrate completed jobs"),
        CmdLineTool.BooleanOption ("--incomplete",dest="incomplete", help="migrate incomplete (not done) jobs"),
        CmdLineTool.BooleanOption ("--deleted",dest="deleted", help="migrate deleted jobs"),
        CmdLineTool.BooleanOption ("--all",dest="all", help="migrate all jobs (complete, incomplete, and deleted)"),
        CmdLineTool.StringOption ("--src-data-dir", dest="dataDir",
                                  help="path to tractor 1.0 data directory"),
        CmdLineTool.StringOption ("--dest-config-dir", dest="configDir",
                                  help="path to tractor 2.0 config directory"),
        ] + CmdLineTool.BasicCmdLineTool.options

    def __init__(self, *args, **kwargs):
        super(DBMigrateTool, self).__init__(*args, **kwargs)
        self.config = None

    def parseArgs(self, *args, **kwargs):
        """This method gets called before execute() to validate command line arguments."""
        result = super(DBMigrateTool, self).parseArgs(*args, **kwargs)
        # no additional args should be supplied on the command line once flags have been removed
        if self.args:
            raise CmdLineTool.HelpRequest, self.getHelpStr()
        if self.opts.configDir:
            if not os.path.exists(self.opts.configDir):
                raise OptionParser.OptionParserError("Config dir %s does not exist" % self.opts.configDir)
        if not self.opts.complete and not self.opts.incomplete and not self.opts.deleted and not self.opts.all:
            raise OptionParser.OptionParserError("One of --complete, --incomplete, --deleted, or --all must be specified.")
        if not self.opts.dataDir:
            raise OptionParser.OptionParserError("--src-data-dir must be specified.")
        if not self.opts.configDir:
            raise OptionParser.OptionParserError("--dest-config-dir must be specified.")
        if self.opts.all:
            self.opts.complete = True
            self.opts.incomplete = True
            self.opts.deleted = True
        return result

    def execute(self):
        """This method gets called automatically by CmdLineTool, and is the core logic of the program."""
        # this enables the postgresql server to find the proper python
        self.config = EngineConfig.EngineConfig(self.opts.configDir, self.installDir())
        self.sync()

    def installDir(self):
        """Return the full path to this tractor installation."""
        thisScriptPath = os.path.dirname(sys.argv[0])
        installDir = os.path.join(thisScriptPath, RELATIVE_PATH_TO_INSTALL_ROOT)
        installDir = os.path.realpath(installDir)
        return installDir

    def isDebugMode(self):
        """Returns True if debug mode is turned on by way of config file or command line option."""
        return self.opts.debug or (self.config and self.config.isDbDebug())

    def dprint(self, msg, inverse=False):
        if self.isDebugMode() and not inverse or not self.isDebugMode() and inverse:
            sys.stderr.write(msg)
            sys.stderr.write("\n")

    def log(self, msg):
        sys.stderr.write(msg)
        sys.stderr.write("\n")

    def runCommand(self, argv, input=None, errIsOut=False, **kw):
        """Run the specified command, returning the return code, stdout, and stderr."""
        self.dprint("running %s" % argv)
        stdin = subprocess.PIPE if input is not None else None
        stderr = subprocess.STDOUT if errIsOut else subprocess.PIPE
        proc = subprocess.Popen(argv, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr, **kw)
        # NOTE: http://docs.python.org/2/library/subprocess.html warns that input to Popen.communicate() shouldn't be "large"
        out, err = proc.communicate(input=input)
        rcode = proc.wait()
        self.dprint(out)
        if not errIsOut:
            self.dprint(err)
        return rcode, out, err

    def sync(self):
        self.log("synchronizing with filesystem")

        def jobDirSort(a, b):
            jidA = a.split("/")[-1]
            dateA = jidA[:8]

            jidB = b.split("/")[-1]
            dateB = jidB[:8]

            if dateA != dateB:
                return -cmp(dateA, dateB)
            else:
                jidA = jidA[8:]
                jidA = int(jidA) if jidA.isdigit() else 0
                jidB = jidB[8:]
                jidB = int(jidB) if jidB.isdigit() else 0
                return -cmp(jidA, jidB)
            
        
        # establish connection with postgres database
        db = EngineDB.EngineDB(dbhost=self.config.dbHostname(), db=self.config.dbDatabaseName(), 
                               user=MIGRATE_USER, password=MIGRATE_PASSWORD)
        try:
            db.open()
        except rpg.sql.SQLError, err:
            raise DBMigrateToolError, str(err)

        # first walk the job data directory so that newer jobs can be processed first
        jobDirs = []
        jobsDir = os.path.join(self.opts.dataDir, "jobs")
        self.dprint("jobsDir = %s" % jobsDir)
        joroots = []
        for root, dirs, files in os.walk(jobsDir):
            if FileSystemDB.JobDB.JOB_INFO_FILENAME in files:
                # it's a job database
                jobDirs.append(root)

        # process each job directory in reverse date + jobid order (newest jobs first)
        jobDirs.sort(jobDirSort)
        for jobDir in jobDirs:
            self.dprint("process job in %s" % jobDir)

            # extract job id from job directory
            parts = jobDir.split("/")
            jid = parts[-1]
            if not jid.isdigit():
                self.log("Job directory does not end in a job id: %s" % jobDir)
                continue # for jobDir
            jid = int(jid)

            # set up a JobDB to analyze job
            jobDB = FileSystemDB.JobDB(jobDir, readFiles=False)

            # don't process deleted jobs if deemed so
            isDeleted = jobDB.isDeleted()
            if isDeleted:
                if not self.opts.deleted:
                    self.dprint("Skipping deleted job %d." % jid)
                    continue # for jobDir
            else:
                # don't process non-deleted jobs if complete/incomplete flags haven't been set
                if not self.opts.complete and not self.opts.incomplete:
                    self.dprint("Skipping non-deleted job %d." % jid)
                    continue # for jobDir

            # do not process job if it's already in database
            jobInDB = db._execute("SELECT jid FROM oldjob WHERE oldjid=%d" % jid)
            rows = db.cursor.fetchall()
            if len(rows) > 0:
                self.log("Skipping migrated job %d." % jid)
                continue # for jobDir

            # read job info 
            try:
                jobDB.readJobInfo()
            except FileSystemDB.JobDBError, err:
                self.log(str(err))
                continue # for jobDir

            # filter out complete/incomplete jobs
            isComplete = jobDB.isComplete()
            if not isDeleted:
                if isComplete:
                    if not self.opts.complete:
                        self.dprint("Skipping complete job %d." % jid)
                        continue # for jobDir
                else:
                    if not self.opts.incomplete:
                        self.dprint("Skipping incomplete job %d." % jid)
                        continue # for jobDir

            # read remaining info files
            jobDB.readTaskInfo()
            jobDB.readCmdList()
            jobDB.readActivityLog()
            jobDB.countStates()

            # deleted jobs need to go in an archive partition
            if isDeleted:
                db._execute("SELECT TractorPartitionCreate('%s') as suffix" % jobDB.job.spooltime.strftime("%Y-%m-%d"))
                result = db.cursor.fetchall()
                if not len(result):
                    self.log("Skipping deleted job %d with spooltime %s due to problems creating archive partition."
                             % (jid, str(jobDB.job.spooltime)))
                    continue # for jobDir
                suffix = result[0]["suffix"]
            else:
                suffix = ""

            # bulk insert records on a per-table basis using postgresql's COPY FROM

            db._execute("begin");
            db._execute("SELECT TractorNewJid() as nextjid")
            result = db.cursor.fetchall()
            nextjid = result[0]["nextjid"]
            # set job id of job as well as tasks, commands, and invocations
            jobDB.setJid(nextjid)
            s = StringIO.StringIO(PGFormat.formatObjsForCOPY([jobDB.job]))
            db.cursor.copy_from(s, "job" + suffix)
            s = StringIO.StringIO(PGFormat.formatObjsForCOPY(jobDB.tasks))
            db.cursor.copy_from(s, "task" + suffix)
            s = StringIO.StringIO(PGFormat.formatObjsForCOPY(jobDB.commands))
            db.cursor.copy_from(s, "command" + suffix)
            s = StringIO.StringIO(PGFormat.formatObjsForCOPY(jobDB.invocations))
            db.cursor.copy_from(s, "invocation" + suffix)
            # add entry to oldjob table to show it has been migrated
            db._execute("INSERT INTO oldjob VALUES (%d, %d)" % (nextjid, jid))
            db._execute("end");
        db.close()

        # TODO: write some checkpoint showing the timestamp of the 

def main():
    try:
        return DBMigrateTool(lock=True).run()
    except (CmdLineTool.CmdLineToolError, OptionParser.OptionParserError) , err:
        print >>sys.stderr, err
        return 2

if __name__ == '__main__':
    sys.exit(main())
