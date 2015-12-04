#!/usr/bin/env rmanpy


'''

PixarRender	cmd requires RPS (prman) to be installed on the blades
PixarNRM	cmd requires RPS to be installed, and a running netrender server (tractor-blade.py is also a netrender server, so in practice this usually equivalent to PixarRender, but it helps distinguish netrender commands)
RfMRender	cmd requires an appropriate intalled Maya on the blade, plus RfM or RMS must also be installed; the cmd consumes a render license
RfMRibGen	cmd requires Maya and RfM/RMS, no render license needed




Service Key Expression Operators

Operator	        Use	Example
keyname	            keynames are replaced with 1 if they match a name in the blade's "Provides"
                    list, or 0 if they do not
                    PixarRender
"keynamePattern"	like keynames, above, with additional support for pattern matching
                    using the wildcard characters * and ? "rack-15?" || '192.168.0.*'
                    (Note the required double or single quotation marks)
&&, (comma)         boolean AND
                    PixarRender && Linux
                    PixarRender,NorthAnnex
||	                boolean OR	Linux || OSX
!	                boolean NOT	PixarRender && !Desktops
(subexpr)	        parenthetical sub-expressions	PixarRender && (Linux || OSX)
@. blade_metric	    numeric blade metric value	see table below
+ - * /	            numeric add, subtract, multiply, divide	for blade metrics, see table below
< <= == != >= >	    numeric comparison, less, greater, equal, etc	for blade metrics, see table below


Service Key Expression Blade Metrics

Metric	Meaning	Example
@.disk	available disk space, in gigabytes	PixarRender && @.disk > 5
@.mem	available physical RAM, in gigabytes	PixarRender && ((1024 * @.mem) > 2048)
@.nCPUs	number of CPU cores reported by the OS	Windows7_32bit && (@.nCPUs >= 4)
@.cpu	current CPU usage, normalized by nCPUs	@.cpu < .75
@.sa	number of abstract "slots" available	(@.sa > 2) && (PixarRender || PixarNRM)



Substitutions
The following symbols are expanded at launch time when they occur within launch or message expressions:

~	            home directory expansion, as in csh(1)
%h	            substitute the hostnames bound to the current Cmd via the dynamic -service mechanism.
                This is a simple blank-delimited list of hostnames (useful for rsh, etc).
%H	            like %h, but formatted as -h hostname pairs (as required by netrender).
%n	            converted to the count of bound slots; an integer indicating how many slots were bound to this command.
%j	            expands to the internal dispatcher Job identifier (aka "jid") for the current job.
                Tractor engine creates unique ids for jobs in its queue.
%t	            expands to the Task identifier (aka "tid") for the current task, it is unique only within each job.
%c	            expands to the Command identifier (aka "cid") for the current command, it is unique only within each job.
%r	            the recover mode, expands to 0 when a task is beginning a fresh start, and to an integer
                greater than zero when the user or system is requesting a recover from checkpoint
%R	            expands to the "loop count" for commands that are being restarted due to the -resumewhile construct
%q	            the quality hint, expands to the value 1.0 when a task is being executed due to final
                quality runs from the subtasks it depends upon; it will be less than 1.0 if some subtask only
                reached a checkpoint during the current resumewhile loop
% idref (host)	like %h but using the hostnames from the command whose -id value is idref.
% idref (-host)	as above, formatted as -h hostname pairs.
%D (path)	    DirMaps, apply per-architecture remapping of paths using a site-defined mapping table.
%%	            a single percent-sign is substituted.


Assign frmdir {/usr/people/buzz/projects/toys/ribfiles}
Cmd {render $frmdir/frame.0.rib}

Cmd {/bin/sh -e "cd /tmp/frames; ls -1 | xargs -I+ cp + /DDR"}

find ~bob -type f -name 'preview.*' -exec /bin/rm {} \;
Cmd {find ~bob -type f -name preview.* -exec /bin/rm \{\} ;}

'''

import datetime
from pytz import timezone
import tractor.api.author as author

au_tz = timezone('Australia/Sydney')
print 'Australia/Sydney   Now:', datetime.datetime.now(tz=au_tz)
# date_str = "2009-05-05 22:28:15"
# datetime_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
# datetime_obj_utc = datetime_obj.replace(tzinfo=au_tz)
# print datetime_obj_utc.strftime("%Y-%m-%d %H:%M:%S %Z%z")
delay = 2
dt = datetime.timedelta(hours=delay)
now = datetime.datetime.now(tz=au_tz)
then = now + dt
print 'Australia/Sydney Start: {}\n'.format(then)

def test_short():
    """This test shows how a two task job can be created with as few
    statements as possible.
    """
    job = author.Job(title="two layer job", priority=10,
                     after=datetime.datetime(2012, 12, 14, 16, 24, 5))
    compTask = job.newTask(title="comp", argv="comp fg.tif bg.tif final.tif")
    fgTask = compTask.newTask(title="render fg", argv="prman foreground.rib")
    bgTask = compTask.newTask(title="render bg", argv="prman foreground.rib")
    print job


def job_upload_project():
    """This job could be to upload a maya project to dabrender
    """

    job = author.Job()
    job.title = "Upload Project Job"
    job.priority = 10
    job.after = then

    dabrender = "source"
    project = "project"

    job.newDirMap(src="/Volumes/dabrender", dst="dabrender/", zone="LINUX")
    job.newDirMap(src="/dabrender", dst="/Volumes/dabrender", zone="OSX")

    job.newAssignment(dabrender, "/Volumes/dabrender")
    job.newAssignment(project, "/Volumes/dabrender")

    job.comment = "Uploader to render place"
    job.metadata = "user=mattg project=dotty"
    job.editpolicy = "undergraduate"

    fgTask = author.Task()
    fgTask.title = "render fg"
    fgCommand = author.Command()
    fgCommand.argv = "prman foreground.rib"
    fgTask.addCommand(fgCommand)

    bgTask = author.Task()
    bgTask.title = "render bg"
    bgCommand = author.Command()
    bgCommand.argv = "prman background.rib"
    bgTask.addCommand(bgCommand)

    compTask = author.Task()
    compTask.title = "render comp"
    compCommand = author.Command()
    compCommand.argv = "comp fg.tif bg.tif final.tif"
    compCommand.argv = ["comp"]
    compTask.addCommand(compCommand)

    compTask.addChild(fgTask)
    compTask.addChild(bgTask)
    job.addChild(compTask)

    print job.asTcl()


def test_all():
    """This test covers setting all possible attributes of the Job, Task,
    Command, and Iterate objects.
    """
    job = author.Job()
    job.title = "all attributes job"
    job.after = datetime.datetime(2012, 12, 14, 16, 24, 5)
    job.afterjids = [1234, 5678]
    job.paused = True
    job.tier = "express"
    job.projects = ["animation"]
    job.atleast = 2
    job.atmost = 4
    job.newAssignment("tempdir", "/tmp")
    job.newDirMap(src="X:/", dst="//fileserver/projects", zone="UNC")
    job.newDirMap(src="X:/", dst="/fileserver/projects", zone="NFS")
    job.etalevel = 5
    job.tags = ["tag1", "tag2", "tag3"]
    job.priority = 10
    job.service = "linux||mac"
    job.envkey = ["ej1", "ej2"]
    job.comment = "this is a great job"
    job.metadata = "show=rat shot=food"
    job.editpolicy = "canadians"
    job.addCleanup(author.Command(argv="/bin/cleanup this"))
    job.newCleanup(argv=["/bin/cleanup", "that"])
    job.addPostscript(author.Command(argv=["/bin/post", "this"]))
    job.newPostscript(argv="/bin/post that")

    compTask = author.Task()
    compTask.title = "render comp"
    compTask.resumeblock = True
    compCommand = author.Command()
    compCommand.argv = "comp /tmp/*"
    compTask.addCommand(compCommand)

    job.addChild(compTask)

    for i in range(2):
        task = author.Task()
        task.title = "render layer %d" % i
        task.id = "id%d" % i
        task.chaser = "chase file%i" % i
        task.preview = "preview file%i" % i
        task.service = "services&&more"
        task.atleast = 7
        task.atmost = 8
        task.serialsubtasks = 0
        task.addCleanup(author.Command(argv="/bin/cleanup file%i" % i))

        command = author.Command()
        command.argv = "prman layer%d.rib" % i
        command.msg = "command message"
        command.service = "cmdservice&&more"
        command.tags = ["tagA", "tagB"]
        command.metrics = "metrics string"
        command.id = "cmdid%i" % i
        command.refersto = "refersto%i" % i
        command.expand = 0
        command.atleast = 1
        command.atmost = 5
        command.samehost = 1
        command.envkey = ["e1", "e2"]
        command.retryrc = [1, 3, 5, 7, 9]
        command.resumewhile = ["/usr/bin/grep", "-q", "Checkpoint", "file.%d.exr" % i]
        command.resumepin = bool(i)

        task.addCommand(command)
        compTask.addChild(task)

    iterate = author.Iterate()
    iterate.varname = "i"
    iterate.frm = 1
    iterate.to = 10
    iterate.addToTemplate(
        author.Task(title="process task", argv="process command"))
    iterate.addChild(author.Task(title="process task", argv="ls -l"))
    job.addChild(iterate)

    instance = author.Instance(title="id1")
    job.addChild(instance)

    print job.asTcl()


def test_instance():
    """This test checks that an instance will be created when a task is
    added as a child to more than one task.
    """
    job = author.Job(title="two layer job")
    compTask = job.newTask(title="comp", argv="comp fg.tif bg.tif final.tif")
    fgTask = compTask.newTask(title="render fg", argv="prman foreground.rib")
    bgTask = compTask.newTask(title="render bg", argv="prman foreground.rib")
    ribgen = author.Task(title="ribgen", argv="ribgen 1-10")
    fgTask.addChild(ribgen)
    bgTask.addChild(ribgen)
    print job


def test_double_add():
    """This test verifies that an interate object cannot be a child to
    more than one task.
    """
    iterate = author.Iterate()
    iterate.varname = "i"
    iterate.frm = 1
    iterate.to = 10
    iterate.addToTemplate(
        author.Task(title="process task", argv="process command"))
    iterate.addChild(author.Task(title="process task", argv="ls -l"))

    t1 = author.Task(title="1")
    t2 = author.Task(title="2")

    t1.addChild(iterate)
    try:
        t2.addChild(iterate)
    except author.ParentExistsError, err:
        print "Good, we expected to get an exception for adding a iterate " \
              "to two parents: %s" % str(err)


def test_bad_attr():
    """This test verifies that an exception is raised when trying to set
    an invalid attribute.
    """
    job = author.Job()
    try:
        job.title = "okay to set title"
        job.foo = "not okay to set foo"
    except AttributeError, err:
        print "Good, we expected to get an exception for setting an invalid " \
              "attribute: %s" % str(err)


def test_spool():
    """This testing the spool method on a job."""
    job = author.Job(
        title="two layer job", priority=10,
        after=datetime.datetime(2012, 12, 14, 16, 24, 5))
    compTask = job.newTask(
        title="comp", argv="comp fg.tif bg.tif out.tif", service="pixarRender")
    fgTask = compTask.newTask(
        title="render fg", argv="prman foreground.rib", service="pixarRender")
    bgTask = compTask.newTask(
        title="render bg", argv="prman foreground.rib", service="pixarRender")
    # setEngineClientParam(port=8080)
    job.spool()


def test_postscript():
    """This builds a job with varios postscript commands.  Submit the
    job to ensure that only the "none", "always", and "done"
    postscript commands run.
    """
    job = author.Job(title="Test Postscript Done")
    job.newTask(title="sleep", argv="sleep 1", service="pixarRender")
    job.newPostscript(argv="touch /tmp/postscript.none.%j", service="pixarRender")
    job.newPostscript(argv="touch /tmp/postscript.done.%j", when="done", service="pixarRender")
    job.newPostscript(argv="touch /tmp/postscript.error.%j", when="error", service="pixarRender")
    job.newPostscript(argv="touch /tmp/postscript.always.%j", when="always", service="pixarRender")
    try:
        job.newPostscript(argv="touch /tmp/postscript.always.%j", when="nope")
    except TypeError, err:
        print "Good, we caught an invalid value for when: %s" % str(err)
    print job.asTcl()


def test_postscript_error():
    """This builds a job with varios postscript commands.  Submit the
    job to ensure that only the "none", "always", and "error"
    postscript commands run.
    """
    job = author.Job(title="Test Postscript Error")
    job.newTask(title="fail", argv="/bin/false", service="pixarRender")
    job.newPostscript(argv="touch /tmp/postscript.none.%j", service="pixarRender")
    job.newPostscript(argv="touch /tmp/postscript.done.%j", when="done", service="pixarRender")
    job.newPostscript(argv="touch /tmp/postscript.error.%j", when="error", service="pixarRender")
    job.newPostscript(argv="touch /tmp/postscript.always.%j", when="always", service="pixarRender")
    try:
        job.newPostscript(argv="touch /tmp/postscript.always.%j", when="nope")
    except TypeError, err:
        print "Good, we caught an invalid value for when: %s" % str(err)
    print job.asTcl()


if __name__ == "__main__":
    """Run testing."""
    job_upload_project()
    # test_spool()


