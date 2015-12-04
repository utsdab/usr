#!/opt/pixar/Tractor-2.0/bin/rmanpy
__author__ = '120988'


import sys
import os
import argparse
import unittest
import utsdab.renderfarm.tractor.python.factories.mayaRenderArguments as mb
import utsdab.renderfarm.tractor.python.factories.ffmpegArguments as ffmpeg

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

logger.info("Name = %s"%(__name__))


def parseArguments():
    parser = argparse.ArgumentParser(description= "Generic Maya Farm Job",
                                     epilog = "This has a matching UI")

    parser.add_argument("-o","--outputpath",    dest="outputpath",
                        action="append",        default=None,
                        help="Output file path")

    parser.add_argument("-s","--framestart",       dest="start",
                        action="append",        default=1,
                        help="Start frame of Sequence")

    parser.add_argument("-e", "--frameend",        dest="end",
                        action="append",        default=100,
                        help="End frame of sequence")

    parser.add_argument("-c", "--framechunk",      dest="chunk",
                        action="append",        default=4,
                        help="Number of frames in a subjob")

    parser.add_argument("-p", "--projectpath",     dest="projectpath",
                        action="append",        default="/a/b/c/",
                        help="Full path of the maya project")

    parser.add_argument("-f", "--scenefile",      dest="scenefile",
                        action= "append",      default="/a/b/c/d.ma",
                        help="Maya scene file")

    parser.add_argument("-r", "--renderer",      dest="renderer",
                        action= "append",      default="mr",
                        help="Renderer to use, mr, rman, maya")

    parser.add_argument("--passthru",           dest="passthru",
                        default=None,
                        help='''   ''')

    return parser.parse_args()



class MayaBatch(object):
    '''
    Basic maya batch render job
    '''
    def __init__(self):
        self.startframe
        self.endframe
        self.byframe
        self.projectpath
        self.scenefilepath


class MayaMentalRayBatch(MayaBatch):
    '''

    '''



class MayaRenderManStudioBatch(MayaBatch):
    '''

    '''


#####################################################
if __name__ == '__main__':

    arguments = parseArguments()

    if not (parseArguments()):
        logger.critical("Cant parse args %s"%(arguments))
        sys.exit(1)

    else:
        # utils.Helper.printDict(arguments.__dict__,"ARGS")

        # inputthing = arguments.input[0]
        # audiofilepath = None
        logger.info(arguments)

        mrjob = mb.MentalRay(proj="xxx", scene="yyy", startframe=1, endframe=1000, chunk=5)
        # print mrjob.arguments()
        print mrjob.generate()

        rmsjob = mb.Renderman(proj="", scene="qqq.mb", startframe=10, endframe=100, chunk=10)
        # print rmsjob.arguments()
        print rmsjob.generate()


        # d = ffmpeg.Base()
        # e = ffmpeg.Prores()