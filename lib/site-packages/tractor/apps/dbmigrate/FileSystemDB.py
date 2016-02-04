"""
This file provides an interface for reading the Tractor 1.x filesystem-oriented job database.
"""

import json, os, re, datetime, ast, collections
import tractor.base.EngineDB as EngineDB

# states as represented by characters in the filesystem based job database
STATE_CHAR_BLOCKED = "B"
STATE_CHAR_ACTIVE = "A"
STATE_CHAR_ERROR = "E"
STATE_CHAR_DONE = "D"

# string which indicates to json parser outer bounds of task tree
OUTER_TASK_TREE_SENTINAL = "<@JobInfo@>"

class FileSystemDBError(Exception):
    pass

def listIndexSetValue(l, index, value):
    """Set the value at the given index; if the list isn't that long, prepopulate with None."""
    if len(l) <= index:
        l.extend([None] * (index - len(l) + 1))
    l[index] = value

def JSONDecoderJobInfo(dct):
    job = EngineDB.Job()
    job.jid = dct.get("jid", 0)
    job.owner = dct.get("user", "")
    job.spoolhost = dct.get("spoolhost", "")
    job.spoolfile = dct.get("sourcefile", "")
    job.spoolcwd = dct.get("cwd", "")
    job.spooladdr = dct.get("spooladdr", "")
    job.spooltime = datetime.datetime.fromtimestamp(dct.get("spooltime", 0))
    job.title = dct.get("title", "")
    
    job.priority = dct.get("priority", 0)
    if job.priority < 0:
        job.priority = abs(job.priority)
        # currently the pausetime is not stored, so let's just set it to the spooltime
        job.pausetime = job.spooltime
    job.crews = dct.get("crews", [])
    job.tags = dct.get("tags", [])
    job.service = dct.get("service", "")
    job.envkey = dct.get("envkey", [])
    job.editpolicy = dct.get("editpolicy", "")
    job.minslots = dct.get("atleast", 1)
    job.maxslots = dct.get("atmost", 1)
    job.etalevel = dct.get("etalevel", 1)
    job.afterjids = dct.get("afterJids", [])
    if dct.has_key("afterTime"):
        job.aftertime = datetime.datetime.fromtimestamp(dct.get("afterTime"))

    job.metadata = dct.get("metadata", "")
    job.comment = dct.get("comment", "")
    return job

def JSONDecoderTaskTree(dct):
    if dct.has_key("tid"):
        task = EngineDB.Task()
        task.tid = dct.get("tid")
        task.id = dct.get("id")
        task.title = dct.get("title")
        task.service = dct.get("service")
        task.minslots = dct.get("atleast", 1)
        task.maxslots = dct.get("atmost", 1)
        task.serialsubtasks = True if dct.get("serialsubtasks", False) == 1 else False
        task.ptids = [0]
        if dct.has_key("ants"):
            task.__dict__["instanceTids"] = dct.get("ants")
        task.cids = dct.get("cids", [])
        return task
    elif dct.has_key("data") and dct.has_key("children") \
             and dct["data"] != OUTER_TASK_TREE_SENTINAL:
        # this puts the subtasks as a member of a task object (which is dct["data"])
        dct["data"].children = dct["children"]
        return dct["data"]
    elif dct.has_key("data") and dct["data"] == OUTER_TASK_TREE_SENTINAL:
        # this ensures the top-level JSON wrapper just returns a list of tasks
        return dct["children"]
    else:
        raise FileSystemDBError, "invalid task tree"

def JSONDecoderCmdList(dct):
    if dct.has_key("cid"):
        cmd = EngineDB.Command()
        cmd.cid = dct.get("cid")
        cmd.argv = dct.get("argv", [])
        cmdtype = dct.get("type", "RC")
        if len(cmdtype) < 2:
            cmdtype = "RC"
        cmd.local = True if cmdtype[0] == "L" else False
        cmd.cleanup = True if cmdtype[1] == "D" else False
        cmd.expand = True if len(cmdtype) > 2 and cmdtype[2] == "X" else False
        cmd.msg = dct.get("msg")
        cmd.service = dct.get("service")
        tagstr = dct.get("tags")
        cmd.tags = tagstr.split() if tagstr else []
        cmd.id = dct.get("id")
        cmd.refersto = dct.get("refersto")
        cmd.minslots = dct.get("atleast", 1)
        cmd.maxslots = dct.get("maxThreads", 1)
        cmd.envkey = dct.get("envkey", [])
        cmd.retryrcodes = dct.get("retryrc", [])
        return cmd
    else:
        return dct.values()

class JobDB(object):
    """The JobDB class interprets the files in the tractor database for a single job
    and represents them in objects.
    """

    JOB_INFO_FILENAME = "jobinfo.json"
    TASK_TREE_FILENAME = "tasktree.json"
    ACTIVITY_LOG_FILENAME = "activity.log"
    CMD_LIST_FILENAME = "cmdlist.json"
    VISIBLE_FILENAME = ".visible"
    STATE_FILENAME = "state.json"

    def __init__(self, path, readFiles=True):
        # build paths
        self.jobDirPath = path
        self.jobInfoPath = os.path.join(path, self.JOB_INFO_FILENAME)
        self.taskTreePath = os.path.join(path, self.TASK_TREE_FILENAME)
        self.activityLogPath = os.path.join(path, self.ACTIVITY_LOG_FILENAME)
        self.cmdListPath = os.path.join(path, self.CMD_LIST_FILENAME)
        self.visiblePath = os.path.join(path, self.VISIBLE_FILENAME)
        self.statePath = os.path.join(path, self.STATE_FILENAME)
        # members for job and task objects
        self.job = None
        self.tasks = []
        self.commands = []
        self.invocations = []
        self.taskByTid = {}
        self.commandByCid = {}
        self.invocationsByCid = collections.defaultdict(list)
        # populate Job and Task objects
        if readFiles:
            self.readJobInfo()
            self.readTaskInfo()
            self.readCmdList()
            self.readActivityLog()
            self.countStates()

    def setJid(self, newjid):
        """Set the job id of job and all tasks, commands, and invocations."""
        self.job.jid = newjid
        for task in self.tasks:
            task.jid = newjid
        for command in self.commands:
            command.jid = newjid
        for invocation in self.invocations:
            invocation.jid = newjid
            
    def modTime(self):
        """Returns the most recent timestamp of all files in job directory."""
        times = []
        for path in (self.jobInfoPath, self.taskTreePath, self.activityLogPath, self.jobDirPath):
            try:
                times.append(os.path.getmtime(path))
            except (IOError, OSError), err:
                print str(err)
        return max(times) if times else 0

    def readJobInfo(self):
        """Read the job info file and populate the job object."""
        try:
            f = open(self.jobInfoPath)
        except (IOError, OSError), err:
            raise FileSystemDBError, "Unable to read %s: %s" % (self.jobInfoPath, str(err))
        try:
            self.job = json.load(f, object_hook=JSONDecoderJobInfo)
        except Exception, err:
            f.close()
            msg = "Problem reading json from %s: %s" % (self.jobInfoPath, str(err))
            raise FileSystemDBError(msg)
        f.close()
        # set the deletetime of the job
        if not self.isDeleted():
            # assume the modtime of the job directory represents the deletetime
            modtime = os.path.getmtime(self.jobDirPath)
            self.job.deletetime = datetime.datetime.fromtimestamp(modtime)

    def readTaskInfo(self):
        """Read the task info file and populate new Task objects and Job state counters."""
        try:
            f = open(self.taskTreePath)
        except (IOError, OSError), err:
            raise FileSystemDBError, "Unable to read %s: %s" % (self.taskTreePath, str(err))
        try:
            taskTree = json.load(f, object_hook=JSONDecoderTaskTree)
        except Exception, err:
            f.close()
            msg = "Problem reading json from %s: %s" % (self.taskTreePath, str(err))
            raise FileSystemDBError(msg)
        f.close()
        # traverse task tree and express tasks as updates
        taskStack = taskTree
        while taskStack:
            task = taskStack.pop()
            task.jid = self.job.jid
            self.tasks.append(task)
            if hasattr(task, "children"):
                taskStack.extend(task.children)
                # put parent tid in all children
                for child in task.children:
                    child.ptids = [task.tid]

        # create a task with tid 0 for containing job-level commands
        zeroTask = EngineDB.Task()
        zeroTask.jid = self.job.jid
        zeroTask.tid = 0
        zeroTask.title = "LAST"
        # NOTE: we're not yet maintaining the zero task's list of children
        zeroTask.children = []
        self.tasks.append(zeroTask)
 
        # populate task LUT
        for task in self.tasks:
            self.taskByTid[task.tid] = task

        # extend the ptids list for tasks that are referred to by other tasks as instances
        for task in self.tasks:
            for tid in task.__dict__.get("instanceTids", []):
                childTask = self.taskByTid.get(tid)
                if childTask:
                    childTask.ptids.append(task.tid)

    def taskWasRetried(self, task, timestamp):
        # set the task state to ready and clear current status of its invocations
        task.state = EngineDB.STATE_READY
        task.statetime = timestamp
        task.readytime = timestamp
        if task.cids:
            task.currcid = task.cids[0]
        task.activetime = None

        # clear current status of last invocation
        for cid in task.cids:
            invocations = self.invocationsByCid.get(cid)
            if invocations:
                invocations[-1].current = False

    def readytimeForTask(self, task, timestamp):
        """Returns the readytime for the specified task; returns None if all children are not done."""

        # if task has no children, then it is considered ready
        if not task.children:
            return timestamp

        isReady = True
        readytime = timestamp
        # we can infer the readytime of a task from the statetime of all of its completed children
        for child in task.children:
            if child.state == EngineDB.STATE_DONE and child.statetime and child.statetime > readytime:
                readytime = child.statetime
            else:
                isReady = False
                break # for child
        return readytime if isReady else None

    def countStates(self):
        """Tally the number of tasks in each state."""
        counts = collections.defaultdict(int)
        for task in self.tasks:
            counts[task.state] += 1
        self.job.numblocked = counts[EngineDB.STATE_BLOCKED]
        self.job.numready =  counts[EngineDB.STATE_READY]
        self.job.numactive =  counts[EngineDB.STATE_ACTIVE]
        self.job.numdone =  counts[EngineDB.STATE_DONE]
        self.job.numerror =  counts[EngineDB.STATE_ERROR]
        self.job.numtasks = sum(counts.values())

    def readCmdList(self):
        """Read the cmdlist.json file and represent as Command objects."""
        try:
            f = open(self.cmdListPath)
        except (IOError, OSError), err:
            raise FileSystemDBError, "Unable to read %s: %s" % (self.cmdListPath, str(err))
        try:
            self.commands = json.load(f, object_hook=JSONDecoderCmdList)
        except Exception, err:
            f.close()
            msg = "Problem reading json from %s: %s" % (self.cmdListPath, str(err))
            raise FileSystemDBError(msg)
        f.close()
        # create mapping of cid to tid
        tidByCid = {}
        for task in self.tasks:
            for cid in task.cids:
                tidByCid[cid] = task.tid
        # populate command's jid and tid values
        for command in self.commands:
            command.jid = self.job.jid
            command.tid = tidByCid.get(command.cid, 0)
            self.commandByCid[command.cid] = command

    def readActivityLog(self):
        # need mapping by tid so state changes from activity log can be applied
        try:
            f = open(self.activityLogPath)
        except (IOError, OSError), err:
            raise FileSystemDBError, "Unable to read %s: %s" % (self.cmdListPath, str(err))
        activityStr = f.read()
        f.close()
        activities = ast.literal_eval("[%s]" % activityStr)
        for activity in activities:
            if len(activity) == 13:
                timestamp, exitcode, jid, tid, cid, stateChar, hasLog, host, bladePort, \
                           totaltasks, nactive, ndone, nerror = activity
                elapsedSecs = None
                estTotalSecs = None
            elif len(activity) == 15:
                timestamp, exitcode, jid, tid, cid, stateChar, hasLog, host, bladePort, \
                           totaltasks, nactive, ndone, nerror, elapsedSecs, estTotalSecs = activity
            else:
                raise FileSystemDBError, "unknown activity format: %s" % str(activity)

            timestamp = datetime.datetime.fromtimestamp(timestamp)
            # special case: job was deleted
            if host == "deleted":
                self.job.deletetime = timestamp
                continue # for activity

            if elapsedSecs is not None:
                self.job.elapsedsecs = elapsedSecs
                self.job.esttotalsecs = estTotalSecs

            # when tid is 0, entry is typically overall job-related
            if tid == 0:
                continue # for activity
            
            # tid != 0
            task = self.taskByTid.get(tid)
            if not task:
                continue # for activity

            if stateChar == STATE_CHAR_ACTIVE:
                task.state = EngineDB.STATE_ACTIVE
                task.statetime = timestamp
                if not self.job.starttime:
                    self.job.starttime = timestamp
                if not task.activetime:
                    task.activetime = timestamp
                if cid:
                    task.currcid = cid
                    # new command invocation
                    invocation = EngineDB.Invocation()
                    invocation.jid = task.jid
                    invocation.tid = task.tid
                    invocation.cid = cid
                    invocation.blade = host.split("/")[0]
                    invocation.starttime = timestamp
                    invocation.current = True
                    # prior invocation is no longer current
                    if len(self.invocationsByCid[invocation.cid]):
                        prevInvocation = self.invocationsByCid[invocation.cid][-1]
                        prevInvocation.current = False
                        invocation.iid = prevInvocation.iid + 1
                    else:
                        invocation.iid = 1
                    self.invocationsByCid[invocation.cid].append(invocation)
                    self.invocations.append(invocation)

            elif stateChar == STATE_CHAR_DONE:
                task.state = EngineDB.STATE_DONE
                task.statetime = timestamp
                self.job.stoptime = timestamp
                if cid:
                    invocations = self.invocationsByCid.get(cid)
                    if invocations:
                        invocation = invocations[-1]
                        invocation.stoptime = timestamp
                        invocation.rcode = exitcode
                    
                else: # cid == 0 -> entire task is done
                    # set parent task to ready if all siblings are done
                    for ptid in task.ptids:
                        parentTask = self.taskByTid.get(ptid)
                        if parentTask:
                            parentTask.readytime = self.readytimeForTask(parentTask, timestamp)
                            parentTask.state = EngineDB.STATE_READY
                
            elif stateChar == STATE_CHAR_ERROR:
                task.state = EngineDB.STATE_ERROR
                task.statetime = timestamp
                self.job.stoptime = timestamp
                if cid:
                    invocations = self.invocationsByCid.get(cid)
                    if invocations:
                        invocation = invocations[-1]
                        invocation.stoptime = timestamp
                        invocation.rcode = exitcode
                
            elif stateChar == STATE_CHAR_BLOCKED:
                if cid and task.cids and cid == task.cids[0]:
                    # this was a retry
                    self.taskWasRetried(task, timestamp)

            if hasLog:
                task.haslog = True
        # for activity

    def isDeleted(self):
        """Returns true if the job has been deleted."""
        return not os.path.exists(self.visiblePath)
        
    def isComplete(self):
        """Returns true if all tasks of the job are done."""
        try:
            f = open(self.statePath)
        except (IOError, OSError), err:
            raise FileSystemDBError, "Unable to read %s: %s" % (self.statePath, str(err))
        try:
            stateInfo = json.load(f)
        except Exception, err:
            f.close()
            msg = "Problem reading json from %s: %s" % (self.statePath, str(err))
            raise FileSystemDBError(msg)
        f.close()

        taskStates = stateInfo.get("taskstates", ["."])
        return taskStates[0] == "D"
        
    def __repr__(self):
        return str(self.job) + str(self.tasks)

if __name__=="__main__":
    #jobDB = JobDB("/var/spool/tractor/jobs/2012-04/13/adamwg/1204130001")
    #jobDB = JobDB("/tmp/1303120002")
    jobDB = JobDB("/net/c4596/scratch/tractor/jobs/2013-03/20/adamwg/1303200001")
    print jobDB.job
    for obj in jobDB.invocations:
        command = jobDB.commandByCid[obj.cid]
        print obj.jid, obj.tid, obj.cid, command.argv
