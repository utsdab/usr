#!/usr/bin/env rmanpy

"""
To do:
    cleanup routine for rib
    create a ribgen then prman version
    check and test options
    run farmuser to check is user is valid


    from maya script editor.......
    import sys
    sys.path.append("/Users/Shared/UTS_Dev/gitRepositories/utsdab/usr")
    sys.path.append("/Applications/Pixar/Tractor-2.2/lib/python2.7/site-packages")
    from software.maya.uts_tools import tractor_submit_maya_UI as ts
    import rmanpy
    ts.main()

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

import os, sys
import tractor.api.author as author
from software.renderfarm.dabtractor.factories import user_factory as ufac
from software.maya.uts_tools import tractor_submit_maya_UI as ts
import tractor.api.query as tq


################################
_thisuser = os.getenv("USER")
# (_usernumber,_username) =  ufac.FarmUser(_thisuser).query()
# try:
#     u = ufac.FARMuser()
#     _usernumber = u.number
#     _username = u.name
# except:
#     sys.exit("Sorry you dont appear to be a registered farm user {}, try running farm_user.py and then contact matt - "
#              "matthew.gidney@uts.edu.au".format(_thisuser))
################################

tq.setEngineClientParam(hostname="tractor-engine", port=5600, user="pixar", debug=True)

def getjobs():
    job = tq.jobs("owner in [pixar] and spooltime < -1d",columns=["jid", "title","metadata","numerror"],
                  sortby=["title"])
    '''
    jobs = tq.jobs("owner in [freddie brian john roger] and spooltime < -8d")
    tq.jobs(columns=["jid", "owner", "title", "metadata"])
    tq.jobs("active or ready", sortby=["-priority", "spooltime"])
    tq.jobs("active", sortby=["-numactive"], limit=10)
    tq.tasks("state=error and Job.spooltime > -24h", columns=["Job.spooltime", "Job.title"], sortby=["Job.priority"])
    '''
    # jobs=job.keys()
    jids=[]
    for i,j in enumerate(job):
        # print i,j.values()
        jids.append( j.get("jid") )
    return jids

def gettimes():
    jids=getjobs()
    report=[]
    for i,j in enumerate(jids):
        invocation = tq.invocations("jid={}".format(j),columns=["elapsedreal",
                                                                "numslots"])
        totalseconds = 0.0
        title=tq.jobs("jid={}".format(j),columns=["title","numerror","numtasks","numdone"])
        errors=tq.jobs("jid={}".format(j),columns=["numerror","numtasks","numdone"])
        # print errors
        #err=errors.get("numerror")
        # err=errors[0]
        # done=errors[2]
        # tasks=errors[1]
        # done=errors.get("numdone")
        # tasks=errors.get("numtasks")
        for i,inv in enumerate(invocation):
            # print i,j.values()
            try:
                totalseconds=totalseconds+(inv.get("elapsedreal")*inv.get("numslots"))
            except:
                pass
        # print "total {} core seconds".format(totalseconds)
        corehours=totalseconds/60.0/60.0
        report.append( ",{},${:.2f},{}".format(j,
                                                        # tasks,done,err,
                                                        corehours*0.2,title[0].get("title") ))

    for i,r in enumerate(report):
        print i,r
def getstuff(days=1):

    report=[]
    jobs=tq.jobs("owner in [pixar] and spooltime > -{}d".format(int(days)),
                 columns=["jid","title","numerror","numtasks","numdone","elapsedsecs","maxslots"],
                 # limit=5,
                 sortby=["elapsedsecs"])
    for i,j in enumerate(jobs):
        # print j
        jid=j.get("jid")
        tasks=j.get("numtasks")
        errors=j.get("numerror")
        done=j.get("numdone")
        title=j.get("title")
        elapsedsecs=j.get("elapsedsecs")
        # maxslots=j.get("maxslots")

        invocation = tq.invocations("jid={}".format(jid),columns=["elapsedreal","numslots"])
        totalseconds = 0.0


        for i,inv in enumerate(invocation):
            # print i,j.values()
            try:
                totalseconds=totalseconds+(inv.get("elapsedreal")*inv.get("numslots"))
            except:
                pass
        # print "total {} core seconds".format(totalseconds)
        corehours=totalseconds/60.0/60.0
        cost=corehours*0.2
        report.append( "jid={}, tasks={}, errors={}, done={}, cost=${:.2f}, title={}, sec={:.0f}".format(jid,
                                                        tasks,errors,done,
                                                        cost,title,
                                                        elapsedsecs ))

    for i,r in enumerate(report):
        print i,r
if __name__ == '__main__':
    getstuff(7)
