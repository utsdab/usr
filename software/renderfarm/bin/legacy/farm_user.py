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

import subprocess
import string
import platform

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

        logger.debug("QUERY: Found %s" % matchedusers)
        try:
            self.matchedusername = matchedusers[0].split("_")[1].strip("\n")
            self.matchedusernumber = matchedusers[0].split("_")[0].strip("\n")
            self.match = True
        except Exception, nameerror:
            logger.warn("Cant match the query of %s" % (self.queryuser))

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


if __name__ == '__main__':

    sh.setLevel(logging.DEBUG)
    auser = FarmUser(os.getenv("USER"))
    logger.debug("getusernumber ---> %s" % auser.getusernumber())
    logger.debug("getusername ---> %s" % auser.getusername())
    logger.debug("getrenderhome ---> %s" % auser.getrenderhome())