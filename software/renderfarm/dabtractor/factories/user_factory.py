#!/usr/bin/python

"""
    This code handles the creation of a user area.
    At UTS the $USER is a number and there is no nice name exposed at all.
    However we can query this from the ldap database using ldapsearch.
    Thus we can definr the concept of renderusername and renderusernumber
    this just need to be in the path some place  dabanim/usr/bin
"""
import os
import sys
import json
import shutil
import string
import subprocess
from software.renderfarm.dabtractor.factories import utils_factory as utils
from software.renderfarm.dabtractor.factories import configuration_factory as config
import tractor.api.author as author

# ##############################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(filename)s as %(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################

class Map(object):
    """
    This class is the mapping of students
    """
    def __init__(self, mapfilepath=config.CurrentConfiguration().usermapfilepath):
        logger.debug("Map File Path {}".format(mapfilepath))
        try:

            self.mapfilejson = os.path.join(mapfilepath,"user_map.json")
            self.tractorcrewlist = os.path.join(mapfilepath,"crewlist.txt")
            self.oldmaplist = os.path.join(mapfilepath,"oldmaplist.txt")

            # self.mapfilepickle= os.path.join(mapfilepath,"map_file.pickle")
            self.backuppath = os.path.join(mapfilepath,"backups")

            logger.debug("Map File: {}".format(self.mapfilejson))

            if not os.path.exists(self.mapfilejson):
                open(self.mapfilejson, 'w').close()
            if not os.path.exists(self.backuppath):
                os.mkdir(self.backuppath)

        except Exception,err:
            logger.critical("No Map Path {}".format(err))
            raise

    def getcrewformat(self):
        with open(self.mapfilejson) as json_data:
            all = json.load(json_data)

        allkeys = all.keys()

        if not os.path.exists(self.tractorcrewlist):
            open(self.tractorcrewlist, 'w').close()

        ###  print for crews.config file
        _crewlist = open(self.tractorcrewlist, 'w')
        for i, student in enumerate(allkeys):
            _line='"{number}", # {index} {student} {name} {year}'.format(index= i,
                                                               student = student,
                                                               number=all[student].get("number","NONE"),
                                                               name=all[student].get("name","NONE"),
                                                               year=all[student].get("year","NONE"))
            # print _line
            _crewlist.write("{}\n".format(_line))
        _crewlist.close()

    def getallusers(self):
        # get all the users printed out - debugging
        with open(self.mapfilejson) as json_data:
            all = json.load(json_data)
        allkeys = all.keys()
        ###  print for crews.config file
        for i, student in enumerate(allkeys):
            logger.info('"{number}", # {index} {student} {name} {year}'.format(index= i,
                                                               student = student,
                                                               number=all[student].get("number","NONE"),
                                                               name=all[student].get("name","NONE"),
                                                               year=all[student].get("year","NONE")))

    def getuser(self, usernumber):
        # query user in the map file and return the dictionary
        with open(self.mapfilejson) as json_data:
            all = json.load(json_data)
        try:
            _result=all[usernumber]
            logger.debug("Found in Map: {}".format(_result))
            return _result
        except Exception, e:
            logger.warn("{} not found {}".format(usernumber,e))
            return None

    def getusername(self,usernumber):
        return self.getuser(usernumber).get("name")

    def removeuser(self, usernumber):
        # remove a user from the map
        if self.getuser(usernumber):
            # self.backup()
            logger.info("Removing user {}".format(usernumber))

            with open(self.mapfilejson) as json_data:
                all = json.load(json_data)

            # print all.keys()
            all.pop(usernumber, None)
            # print all.keys()

            with open(self.mapfilejson, 'w') as outfile:
                json.dump(all, outfile, sort_keys = True, indent = 4,)

    def backup(self):
        # backup the existing map
        source=self.mapfilejson
        now=utils.getnow()
        if not os.path.isdir(self.backuppath):
            os.mkdir( self.backuppath, 0775 );
        dest=os.path.join(self.backuppath,
                          "{}-{}".format(os.path.basename(self.mapfilejson),now))
        logger.info("Backup: source {}".format(source))
        logger.info("Backup: dest {}".format(dest))
        shutil.copy2(source, dest)

    def adduser(self, number, name, year):
        # add a new user to the map
        if not self.getuser(number):
            # self.backup()
            logger.info("No one by that number {}, adding".format(number))

            try:
                with open(self.mapfilejson) as json_data:
                    all = json.load(json_data)

                new={number:{"name":name,"number":number,"year":year}}
                all.update(new)

                with open(self.mapfilejson, 'w') as outfile:
                    json.dump(all, outfile, sort_keys = True, indent = 4,)
            except Exception,err:
                logger.warn("Error adding user {}".format(err))
                raise
        else:
            logger.info("User {} already in map file".format(number))




class EnvType(object):
    # this is the user work area either work/number or projects/projectname
    def __init__(self,userid=None,projectname=None):
        self.dabrenderpath=config.CurrentConfiguration().dabrender

        if userid:
            self.envtype="user_work"
            self.userid=userid
            self.map=Map()
            self.userdict=self.map.getuser(self.userid)
            self.usernumber=self.userdict.get("number")
            self.username=self.userdict.get("name")
            self.enrol=self.userdict.get("year")
            logger.debug("Usernumber {}, Username {}, Enrolled {}".format (self.usernumber,self.username,self.enrol))

        if projectname:
            self.envtype="project_work"
            self.projectname=projectname

    def makedirectory(self):
        #
        try:
            if self.envtype == "user_work":
                os.mkdir( os.path.join(self.dabrenderpath,self.envtype,self.username))
                logger.info("Made {} under user_work".format(self.username))
            elif self.envtype == "projects":
                os.mkdir( os.path.join(self.dabrenderpath,self.envtype,self.projectname))
                logger.info("Made {} under user_projects".format(self.projectname))
            else:
                logger.info("Made no directories")
                raise
        except Exception, e:
            logger.warn("Made nothing {}".format(e))



class TractorUserConfig(object):
    # this is the crew.config for tractor
    def __init__(self):
        pass


class UTSuser(object):
    def __init__(self):
        self.name=None
        self.number = os.getenv("USER")
        self.job=None

        try:
            p = subprocess.Popen(["ldapsearch", "-h", "moe-ldap1.itd.uts.edu.au", "-LLL", "-D",
                                  "uid=%s,ou=people,dc=uts,dc=edu,dc=au" % self.number,
                                  "-Z", "-b", "dc=uts,dc=edu,dc=au", "-s", "sub", "-W",
                                  "uid=%s" % self.number, "uid", "mail"], stdout=subprocess.PIPE)
            result = p.communicate()[0].splitlines()

            # logger.debug(">>>%s<<<<" % result)
            niceemailname = result[2].split(":")[1]
            nicename = niceemailname.split("@")[0]
            compactnicename = nicename.lower().translate(None, string.whitespace)
            cleancompactnicename = compactnicename.translate(None, string.punctuation)
            logger.info("UTS thinks you are: %s" % cleancompactnicename)
            self.name = cleancompactnicename

        except Exception, error7:
            logger.warn("    Cant get ldapsearch to work: %s" % error7)
            sys.exit("UTS doesnt seem to know you")

    def addtomap(self):

        if self.number in config.CurrentConfiguration().superuser:
            logger.info("Your are a superuser - yay")
        else:
            logger.warn("You need to be a superuser to mess with the map file sorry")
            sys.exit("You need to be a superuser to mess with the map file sorry")

        try:
            author.setEngineClientParam(hostname="tractor-engine", port=5600, user="pixar", debug=True)

            # ################ TRACTOR JOB ################
            self.base = ["bash", "-c","add_farm_user.py",]
            self.args = ["-n","33333","-u","spog","-y","2016"]
            self.command = self.base+self.args
            self.job = author.Job(title="New User Request: {}".format(self.name),
                                  priority=100,
                                  metadata="user={} realname={}".format(self.number, self.name),
                                  comment="New User Request is {} {} {}".format(self.number,
                                                self.name,self.number),
                                  projects=["admin"],
                                  tier="admin",
                                  tags=["theWholeFarm"],
                                  service="ShellServices")
            # ############## 2  RUN COMMAND ###########
            task_parent = author.Task(title="Parent")
            task_parent.serialsubtasks = 1
            task_bash = author.Task(title="Command")
            bashcommand = author.Command(argv=self.command)
            task_bash.addCommand(bashcommand)
            task_parent.addChild(task_bash)

            # ############## 7 NOTIFY ###############
            task_notify = author.Task(title="Notify")
            task_notify.addCommand(self.mail("JOB", "COMPLETE", "blah"))
            task_parent.addChild(task_notify)
            self.job.addChild(task_parent)
        except Exception, joberror:
            logger.warn(joberror)

    def validate(self):
        if self.job:
            logger.info("\n\n{:_^80}\n{}\n{:_^80}".format("snip", self.job.asTcl(), "snip"))

    def mail(self, level="Level", trigger="Trigger", body="Render Progress Body"):
        bodystring = "Add New User: \nLevel: {}\nTrigger: {}\n\n{}".format(level, trigger, body)
        subjectstring = "FARM JOB: %s " % (self.command)
        mailcmd = author.Command(argv=["sendmail.py", "-t", "%s@uts.edu.au" % self.number,
                                       "-b", bodystring, "-s", subjectstring])
        return mailcmd

    def spool(self):
        try:
            self.job.spool(owner="pixar")
            logger.info("Spooled correctly")
        except Exception, spoolerr:
            logger.warn("A spool error %s" % spoolerr)



class User(object):
    def __init__(self):
        # the user details as defined in the map
        self.user = os.getenv("USER")
        usermap = Map()
        _userdict=usermap.getuser(self.user)
        self.name=_userdict.get("name")
        self.number=_userdict.get("number")
        self.year=_userdict.get("year")
        logger.debug("User: {}".format( usermap.getuser(self.user) ))
        self.username = self.name
        self.usernumber = self.number
        self.dabrender = config.CurrentConfiguration().dabrender  # "/Volumes/dabrender"
        self.dabuserworkpath = os.path.join(self.dabrender, "user_work", self.name)

    def getusername(self):
        return self.name

    def getusernumber(self):
        return self.number

    def getenrolmentyear(self):
        return self.year




if __name__ == '__main__':

    sh.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)

    m = Map()

    logger.debug("-------- TEST MAP ------------")
    try:
        logger.debug("getuser:{} getusername:{}".format( m.getuser("120988"), m.getusername("120988")) )
    except Exception, err:
        logger.warn(err)


    logger.debug("-------- TEST adduser ------------")
    try:
        # m.getallusers()
        m.backup()
        m.adduser("1209880","mattgidney","2020")
        m.adduser("0000000","nextyearstudent","2016")
        m.adduser("9999999","neveryearstudent","2016")

    except Exception, err:
        logger.warn(err)


    logger.debug("-------- TEST getuser ------------")
    try:
        m.getuser("9999999")
    except Exception, err:
        logger.warn(err)

    logger.debug("-------- TEST removeuser ------------")
    try:
        m.removeuser("9999999")
        m.getuser("9999999")
    except Exception, err:
        logger.warn(err)


    u = User()
    uts = Utsuser()
    print uts.name
    print uts.number


    '''
    logger.debug("-------- TEST show __dict__ ------------")
    try:
        logger.debug("MAP: {}".format(m.__dict__))
        logger.debug("   : {}".format(dir(m)))
    except Exception, err:
        logger.warn(err)

    logger.debug("-------- TEST USER------------")
    try:
        u=User()
        logger.debug("USER: {}".format(u.__dict__))
        logger.debug("    : {}".format(dir(u)))
    except Exception, err:
        logger.warn(err)

    logger.debug("-------- TEST ENVTYPE ------------")
    try:
        e=EnvType(userid="120988")
        e.makedirectory()
        e=EnvType(projectname="albatross")
        e.makedirectory()
        logger.debug("ENVTYPE: {}".format(e.__dict__))
        logger.debug("       : {}".format(dir(e)))
    except Exception, err:
        logger.warn(err)
    '''
