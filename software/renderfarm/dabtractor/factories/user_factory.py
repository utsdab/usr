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
import pickle
import shutil
import subprocess
import string
import platform
from dabtractor.factories import utils_factory as utils
from pprint import pprint
from dabtractor.factories import configuration_factory as config

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
        try:

            self.mapfilejson = os.path.join(mapfilepath,"map_file.json")
            self.tractorcrewlist = os.path.join(mapfilepath,"crelist.txt")
            self.oldmaplist = os.path.join(mapfilepath,"oldmaplist.txt")

            self.mapfilepickle= os.path.join(mapfilepath,"map_file.pickle")
            self.backuppath = os.path.join(mapfilepath,"backups")

            logger.info("Map File: {}".format(self.mapfilejson))

            if not os.path.exists(self.mapfilejson):
                open(self.mapfilejson, 'w').close()
            if not os.path.exists(self.backuppath):
                os.mkdir(self.backuppath)

        except Exception,err:
            logger.critical("No Map Path {}".format(err))

    def test(self):
        number="120988"
        name="matthewgidney"
        a = {number: {'number': number, 'name': name}}
        number="222222"
        name="secondyearstudent"
        c = {number: {'number': number, 'name': name, 'year': 2014}}
        a.update(c)
        number="333333"
        name="thirdyearstudent"
        c = {number: {'number': number, 'name': name, 'year': 2013}}
        a.update(c)
        number="444444"
        name="fourthyearstudent"
        c = {number: {'number': number, 'name': name, 'year': 2012}}
        a.update(c)

        # print(json.dumps(a, indent=4))


        ######## JSON SERIALISATION
        with open(self.mapfilejson, 'w') as outfile:
            json.dump(a, outfile, sort_keys = True, indent = 4,)
        with open(self.mapfilejson) as json_data:
            d = json.load(json_data)

        all = d
        allkeys = all.keys()

        ###  print for crews.config file
        for i, student in enumerate(allkeys):
            print '"{number}", # {index} {student} {name} {year}'.format(index= i,
                                                               student = student,
                                                               number=all[student].get("number","NONE"),
                                                               name=all[student].get("name","NONE"),
                                                               year=all[student].get("year","NONE"))

        # example query of name
        number = "222222"
        with open(self.mapfilejson) as json_data:
            all = json.load(json_data)
        try:
            print "Found student {} named {}".format(number, all[number].get("name","ZIP"))
        except:
            print "{} not found".format(number)


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



    def getoldmapformat(self):

        with open(self.mapfilejson) as json_data:
            all = json.load(json_data)
        allkeys = all.keys()
        ###  print for crews.config file

        if not os.path.exists(self.oldmaplist):
            open(self.oldmaplist, 'w').close()

        ###  print for _oldmaplist format soon to be deprecated

        _oldmaplist = open(self.oldmaplist, 'w')
        for i, student in enumerate(allkeys):
            _line = '{number}_{name}'.format(index= i,
                                                               student = student,
                                                               number=all[student].get("number","NONE"),
                                                               name=all[student].get("name","NONE"),
                                                               year=all[student].get("year","NONE"))
            # print _line
            _oldmaplist.write("{}\n".format(_line))
        _oldmaplist.close()

    def getallusers(self):

        with open(self.mapfilejson) as json_data:
            all = json.load(json_data)
        allkeys = all.keys()
        ###  print for crews.config file
        for i, student in enumerate(allkeys):
            print '"{number}", # {index} {student} {name} {year}'.format(index= i,
                                                               student = student,
                                                               number=all[student].get("number","NONE"),
                                                               name=all[student].get("name","NONE"),
                                                               year=all[student].get("year","NONE"))

    def getuser(self, usernumber):

        with open(self.mapfilejson) as json_data:
            all = json.load(json_data)
        try:
            number=all[usernumber].get("number","ZIP")
            name=all[number].get("name","ZIP")
            year=all[number].get("year","ZIP")
            print "Found student {} named {} from {}".format(number, name, year)
            return number,name,year
        except:
            print "{} not found".format(usernumber)
            return None

    def backup(self):
        source=self.mapfilejson
        now=utils.getnow()
        if not os.path.isdir(self.backuppath):
            os.mkdir( self.backuppath, 0775 );
        dest=os.path.join(self.backuppath,
                          "{}-{}".format(os.path.basename(self.mapfilejson),now))
        print source
        print dest
        shutil.copy2(source, dest)

    def adduser(self, number, name, year):
        if not self.getuser(number):
            self.backup()
            print "No one by that number {}, adding".format(number)

            with open(self.mapfilejson) as json_data:
                all = json.load(json_data)

            new={number:{"name":name,"number":number,"year":year}}
            all.update(new)

            with open(self.mapfilejson, 'w') as outfile:
                json.dump(all, outfile, sort_keys = True, indent = 4,)




class FarmUser(object):
    """
    This class represents the farm as configured for the user
    """

    def __init__(self, queryuser=None):
        """
        Define farm host and user relationship
        :return:
        """
        self.number = ""
        self.name = ""
        self.dabrendermount = ""
        self.renderhome = ""
        self.mountname = "dabrender"
        self.work = "work"
        self.mapfilename = "user_map"
        self.queryuser = queryuser
        self.match = False
        self.matchedusername = ""
        self.matchedusernumber = ""


        try:
            self.number = os.getenv('USER')
        except Exception, error1:
            logger.critical("Cant find $USER or set usernumber, sorry: %s" % error1)
            sys.exit("No $USER available")

        try:
            if platform.system() == "Darwin":
                self.dabrendermount = "/Volumes/%s" % self.mountname
            elif platform.system() == "Linux":
                self.dabrendermount = "/%s" % self.mountname

            self.dabrenderwork = os.path.join(self.dabrendermount, self.work)
            self.usermapfile = os.path.join(self.dabrendermount, "usr", "map", self.mapfilename)
            logger.debug("Running on %s" % platform.system())

        except Exception, error3:
            logger.warn("    Cant figure out the dabrendermount: %s" % error3)
            sys.exit("Cant work out mounts")

        try:
            if os.path.isdir(self.dabrendermount):
                os.rmdir(self.dabrendermount)
                logger.debug("    Removed directory %s" % self.dabrendermount)

        except Exception, error4:
            logger.debug("TEST: no directories where mounts should be %s" % error4)

        # ############## query only
        if self.queryuser:
            self.query()
            self.usermapfile = os.path.join(self.dabrendermount, "usr", "map", self.mapfilename)
            self.renderhome = os.path.join(self.dabrendermount, self.work, self.matchedusername)
        else:
            self.name = self.whoami()
            self.userkeypair = "_".join([self.number, self.name])
            self.renderhome = os.path.join(self.dabrenderwork, self.name)
            self.usermapfile = os.path.join(self.dabrendermount, "usr", "map", self.mapfilename)

            self.build()


    def query(self):
        logger.info("QUERY: User %s making query about user %s" % (self.number, self.queryuser))
        matchedusers = []
        try:
            with open(self.usermapfile, "r") as myfile:
                lines = set(myfile.readlines())
                # lines.add("%s\n"%self.userkeypair)
                sortedlines = sorted(lines)
                logger.debug("Read %s" % self.usermapfile)
                logger.debug("user_keys: %s" % sortedlines)
                myfile.close()

            for i, user in enumerate(sortedlines):
                usernumber = user.split("_")[0]
                # print i,user,usernumber
                if self.queryuser:
                    if str(user).startswith(self.queryuser):
                        matchedusers.append(user)
            # if just one split it and pass back name
        except Exception, maperror:
            _error = "{} {}".format("User Map Error",maperror)
            logger.warn(_error)
            sys.exit(_error)
        logger.debug("QUERY: Found %s" % matchedusers)
        try:
            self.matchedusername = matchedusers[0].split("_")[1].strip("\n")
            self.matchedusernumber = matchedusers[0].split("_")[0].strip("\n")
            self.match = True
            return self.matchedusernumber,self.matchedusername
        except Exception, nameerror:
            logger.warn("Cant match the query of %s" % (self.queryuser))
            return self.matchedusernumber,None

    def getusername(self):
        return self.matchedusername

    def getusernumber(self):
        return self.matchedusernumber

    def getrenderhome(self):
        return self.renderhome

    def getrenderworkpath(self):
        return self.dabrenderwork

    def getrendermountpath(self):
        return self.dabrendermount

    def whoami(self):
        """
        ldapsearch -h moe-ldap1.itd.uts.edu.au -LLL -D
        uid=120988,ou=people,dc=uts,dc=edu,dc=au -Z -b
        dc=uts,dc=edu,dc=au -s sub -W uid=120988 uid mail
        """

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
            logger.debug(">>>%s<<<<" % cleancompactnicename)
            self.name = cleancompactnicename
            return self.name

        except Exception, error7:
            logger.warn("    Cant get ldapsearch to work: %s" % error7)
            sys.exit("Ldap search not working")

    def build(self):

        if not os.path.ismount(self.dabrendermount):
            logger.critical("BUILD: Cant find mount %s" % self.dabrendermount)
            raise

        if not os.path.isdir(self.renderhome):
            logger.info("BUILD: Found mount %s" % self.dabrendermount)

            os.makedirs(self.renderhome, mode=0755)
            logger.info("BUILD: Created %s" % self.renderhome)
            # print self.usermapfile
        else:
            logger.info("BUILD: Directory already exists %s" % self.renderhome)

        with open(self.usermapfile, "r") as myfile:
            lines = set(myfile.readlines())
            lines.add("%s\n" % self.userkeypair)
            sortedlines = sorted(lines)
            logger.debug("Read %s" % self.usermapfile)
            logger.debug("user_keys: %s" % sortedlines)
            myfile.close()

        with open(self.usermapfile, "w") as myfile:
            logger.debug("Updated %s" % self.usermapfile)
            for eachline in sortedlines:
                myfile.write(eachline)
            myfile.close()

        logger.info("BUILD: Done ")

    def spoolbuild(self):
        ''' spool a job to the farm so pixar user will build the directories '''
        pass



class FarmUser2(FarmUser):

    def build(self):
        pass
        map=Map()
        map.adduser(number, name, year)



class Student(object):
    def __init__(self):
        self.user = os.getenv("USER")

        # get the names of the central render location for the user
        student = FarmUser(self.user)
        # student.query()

        self.name = student.getusername()  # "matthewgidney"
        self.number = student.getusernumber()  # "120988"
        self.dabrender = student.getrendermountpath()  # "/Volumes/dabrender"
        self.dabrenderwork = student.getrenderhome()  # "/Volumes/dabrender/work"

class SpoolJob(object):
    # simple command spooled to a tractor job so that pixar user can execute it.

    def __init__(self):
        pass




if __name__ == '__main__':

    sh.setLevel(logging.INFO)
    logger.info("-------- OLD FARM USER MAP ------------")
    ausers = [os.getenv("USER"), "11724135", "99999999"]

    for i, each in enumerate(ausers):
        try:
            student,number = FarmUser(each).query()
            logger.warn("User {} is {}".format(student,number))
        except Exception, nouser:
            logger.warn("No user {}".format(each))


    #logger.debug("-------- NEW JSON FARM USER MAP ------------")
    # m=Map()
    # # m.test()
    # m.getuser("120988")
    # m.getallusers()
    # m.backup()
    # m.adduser("1209880","mattgidney","2020")
    # m.adduser("0000000","nextyearstudent","2016")
    # m.getallusers()
    # # testing here
    # me = Student()
    # logger.debug("Testing name={}".format(me.name))
    # logger.debug("Testing number={}".format(me.number))
    # logger.debug("Testing dabrenderwork={}".format(me.dabrenderwork))


