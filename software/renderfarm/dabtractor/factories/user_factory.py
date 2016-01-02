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
import subprocess
import string
import platform
from software.renderfarm.dabtractor.factories import utils_factory as utils
from software.renderfarm.dabtractor.factories import configuration_factory as config

# ##############################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
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

            self.mapfilejson = os.path.join(mapfilepath,"map_file.json")
            self.tractorcrewlist = os.path.join(mapfilepath,"crelist.txt")
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

            with open(self.mapfilejson) as json_data:
                all = json.load(json_data)

            new={number:{"name":name,"number":number,"year":year}}
            all.update(new)

            with open(self.mapfilejson, 'w') as outfile:
                json.dump(all, outfile, sort_keys = True, indent = 4,)


class EnvType(object):
    # this is the user work area either work/number or projects/projectname
    def __init__(self,userid=None,projectname=None):
        self.dabrenderpath=config.CurrentConfiguration().dabrenderpath

        if userid:
            self.envtype="work"
            self.userid=userid
            self.map=Map()
            self.userdict=self.map.getuser(self.userid)
            self.usernumber=self.userdict.get("number")
            self.username=self.userdict.get("name")
            self.enrol=self.userdict.get("yeay")
            logger.debug("Usernumber {}, Username {}, Enrolled {}".format (self.usernumber,self.username,self.enrol))

        if projectname:
            self.envtype="projects"
            self.projectname=projectname

    def makedirectory(self):
        #
        try:
            if self.envtype == "work":
                os.mkdir( os.path.join(self.dabrenderpath,self.envtype,self.username))
                logger.info("Made {} under work".format(self.username))
            elif self.envtype == "projects":
                os.mkdir( os.path.join(self.dabrenderpath,self.envtype,self.projectname))
                logger.info("Made {} under projects".format(self.projectname))
            else:
                logger.debug("Made no directories")
        except Exception, e:
            logger.warn("Made nothing {}".format(e))



class TractorUserConfig(object):
    # this is the crew.config for tractor
    def __init__(self):
        pass





class User(object):
    def __init__(self):
        # the user details as defined in the map
        self.user = os.getenv("USER")
        m=Map()
        _userdict=m.getuser(self.user)
        self.name=_userdict.get("name")
        self.number=_userdict.get("number")
        self.year=_userdict.get("year")
        logger.debug("User: {}".format( m.getuser(self.user) ))
        self.username = self.name
        self.usernumber = self.number
        self.dabrender = config.CurrentConfiguration().dabrenderpath  # "/Volumes/dabrender"
        self.dabuserworkpath = os.path.join(self.dabrender,"work",self.name)

    def getusername(self):
        return self.name

    def getusernumber(self):
        return self.number

    def getenrolmentyear(self):
        return self.year

class SpoolJob(object):
    # simple command spooled to a tractor job so that pixar user can execute it.

    def __init__(self):
        pass




if __name__ == '__main__':

    sh.setLevel(logging.DEBUG)
    logger.debug("-------- TEST MAP ------------")
    m=Map()
    m.getuser("120988")
    print m.getusername("120988")
    # m.getallusers()
    # m.backup()
    m.adduser("1209880","mattgidney","2020")
    m.adduser("0000000","nextyearstudent","2016")
    m.adduser("9999999","neveryearstudent","2016")
    m.getuser("9999999")
    m.removeuser("9999999")
    m.getuser("9999999")
    logger.debug("MAP: {}".format(m.__dict__))
    logger.debug("   : {}".format(dir(m)))

    logger.debug("-------- TEST USER------------")
    u=User()
    logger.debug("USER: {}".format(u.__dict__))
    logger.debug("    : {}".format(dir(u)))

    logger.debug("-------- TEST ENVTYPE ------------")
    e=EnvType(userid="120988")
    e.makedirectory()
    e=EnvType(projectname="albatross")
    e.makedirectory()
    logger.debug("ENVTYPE: {}".format(e.__dict__))
    logger.debug("       : {}".format(dir(e)))
