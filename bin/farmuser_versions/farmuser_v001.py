#!/usr/bin/python

"""###!/opt/pixar/Tractor-2.0/bin/rmanpy
    This code handles the creation of a user area.
    At UTS the $USER is a number and there is no nice name exposed at all.
    However we can query this from the ldap database using ldapsearch.
    Thus we can definr the concept of renderusername and renderusernumber
"""
import os
import sys
import logging
import subprocess
import string
import platform

###############################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
# sh.setLevel(logging.DEBUG)
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(filename)s as %(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
###############################################################


class FarmUser(object):
    """
    This class represents the farm as configured for the user
    """

    def __init__(self):
        """
        Define farm host and user relationship
        :return:
        """

        self.renderusernumber = ""
        self.renderusername = ""
        self.renderuser = ""
        self.dabrendermount = ""
        self.renderhome = ""
        self.platform = ""

        try:
            self.renderusernumber = os.getenv('USER')
        except Exception, err:
            logger.critical("Cant find $USER or set usernumber, sorry: %s" % err)

        try:
            self.renderusername = "nobody"
            self.whoami()
        except Exception, err:
            logger.critical("Cant set user name: %s" % err)

        try:
            self.platform = platform.system()
            logger.info("Running on %s" % self.platform)

            if self.platform == "Darwin":
                self.dabrendermount = "/Volumes/dabrender"
            elif self.platform == "Linux":
                self.dabrendermount = "/dabrender"
                # this could be set as env var in profile.d script

        except Exception, err:
            logger.warn("Cant figure out the dabrendermount: %s" % err)

        try:
            if os.path.isdir(self.dabrendermount):
                os.rmdir(self.dabrendermount)
                logger.info("Removed directory %s" % self.dabrendermount)
        except Exception, err:
            logger.info("... no directories where mounts should be")

        self.renderuser = "_".join([self.renderusernumber, self.renderusername])
        self.renderhome = "/".join([self.dabrendermount, "work", self.renderuser])

        try:
            if not os.path.ismount(self.dabrendermount):
                logger.critical("Cant find mount %s" % self.dabrendermount)
                raise
            else:
                logger.info("Found mount %s" % self.dabrendermount)

                try:
                    #os.makedirs(self.renderhome, mode=0755)
                    os.makedirs(self.renderhome)
                    logger.info("Created %s" % self.renderhome)
                except Exception, err:
                    logger.info("Didnt make directory: %s" % self.renderhome)
		
                try:
		    os.chown(self.renderhome,710,20)
                    logger.info("Changed ownership %s" % self.renderhome)
                except:
                    logger.info("Didnt make change ownership: %s" % self.renderhome)



        except Exception, err:
            logger.critical("Couldnt confirm the dabrender is a mounted file system")

        logger.debug("%s %s" % (self.renderuser, self.renderhome))

        os.environ["RENDERHOME"] = self.renderhome
        os.environ["RENDERNAME"] = self.renderusername
        os.environ["RENDERNUMBER"] = self.renderusernumber

        logger.info("$RENDERHOME: %s" % os.getenv("RENDERHOME"))
        logger.info("$RENDERNAME: %s" % os.getenv("RENDERNAME"))
        logger.info("$RENDERNUMBER: %s" % os.getenv("RENDERNUMBER"))

    def getusername(self):
        return self.renderusername

    def getusernumber(self):
        return self.renderusernumber

    def getrenderhome(self):
        return self.renderhome

    def whoami(self):
        """
        Query the ldap data base
        :return: username eg 120988_matthewgidney
        """
        try:
            p = subprocess.Popen(["ldapsearch", "-h", "moe-ldap1.itd.uts.edu.au", "-LLL", "-D",
                                  "uid=%s,ou=people,dc=uts,dc=edu,dc=au" % self.renderusernumber,
                                  "-Z", "-b", "dc=uts,dc=edu,dc=au", "-s", "sub", "-W",
                                  "uid=%s" % self.renderusernumber, "uid", "cn"], 
                                  stdout=subprocess.PIPE)
            result = p.communicate()[0].splitlines()
            logger.debug(">>>%s<<<<" % result)
            nicename = result[2].split(":")[1]
            compactnicename = nicename.lower().translate(None, string.whitespace)
            logger.debug(">>>%s<<<<" % compactnicename)
            self.renderusername = compactnicename
            return self.renderusername

        except Exception, err:
            logger.warn("Cant get ldapsearch to work: %s" % err)

if __name__ == '__main__':

    logger.debug("hello")
    try:
        auser = FarmUser()
        logger.info("Woo hoo ---> %s %s" % (auser.renderusernumber, auser.renderusername))
        sys.exit(0)
    except Exception, err:
        logger.warn("Problem getting user from ldap or finding dabrender volume: %s" % err)
        sys.exit("farmuser.py error")

