#!/usr/bin/python

# ##############################################################
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
# sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################

import argparse
import os
import sys


def sendmail(mailto,
             mailsubject,
             mailbody,
             mailfrom):
    logger.debug("%s %s %s %s" % (mailto,
                                  mailsubject,
                                  mailbody,
                                  mailfrom))

    sendmail_location = "/usr/sbin/sendmail"  # sendmail location
    p = os.popen("%s -t" % sendmail_location, "w")
    p.write("From: %s\n" % str(mailfrom[0]))
    p.write("To: %s\n" % str(mailto[0]))
    p.write("Subject: %s\n" % str(mailsubject[0]))
    p.write("\n")  # blank line separating headers from body
    p.write("%s" % str(mailbody[0]))
    status = p.close()
    if status != 0:
        print "Sendmail exit status", status
    return status


def parseArguments():
    parser = argparse.ArgumentParser(description="Simple sendmail wrapper",
                                     epilog="This is a pain to get right")

    parser.add_argument("-s", dest="mailsubject",
                        action="append",
                        default=["Subject"],
                        help="The Subject of the mail")
    parser.add_argument("-b", dest="mailbody",
                        action="append",
                        default=["Body"],
                        help="What you are sending")
    parser.add_argument("-t", dest="mailto",
                        action="append",
                        default=["120988@uts.edu.au"],
                        help="who you are sending to")
    parser.add_argument("-f", dest="mailfrom",
                        action="append",
                        default=["pixar@uts.edu.au"],
                        help="Who you are sending as or from")

    return parser.parse_args()

# #####################################################################################################
if __name__ == '__main__':

    arguments = parseArguments()
    logger.debug("%s" % arguments)

    if not (parseArguments()):
        logger.critical("Cant parse args %s" % (arguments))
        sys.exit("ERROR Cant parse arguments")
    else:
        # exitstatus=sendMail(mailto="120988@uts.edu.au",mailsubject="Subject",mailbody="Body of the mail",mailfrom="pixar@uts.edu.au")
        exitstatus = sendmail(mailto=arguments.mailto[-1:],
                              mailsubject=arguments.mailsubject[-1:],
                              mailbody=arguments.mailbody[-1:],
                              mailfrom=arguments.mailfrom[-1:])

        sys.exit(exitstatus)





