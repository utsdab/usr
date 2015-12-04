#!/usr/bin/env rmanpy

import argparse
import os,sys
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

from dabtractor.factories import proxy_runner as pr


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    defaultproxy = config.CurrentConfiguration().nukedefaultproxytemplate

    parser.add_argument("-p", "--proxytemplate", default=defaultproxy,
                    help="The nuke proxy template to use.  Found in $DABRENDER/usr/proxys  default is {}".format(defaultproxy[0]))
    parser.add_argument("-s", "--startingpoint",
                    help="The top level starting point containing images or an image in a sequence")

    args = parser.parse_args()
    pt = pr.Proxytemplate(defaultproxy)

    if args.startingpoint:
        if os.path.isdir(args.startingpoint):
            d = pr.ImageSequence(args.startingpoint)
            d.runlsseq()
            d.buildcommand(proxytemplate=args.proxytemplate)
            d.runcommand()

        elif os.path.isfile(args.startingpoint):
            f = pr.ImageSequence(args.startingpoint)
        else:
            logger.critical("Proxy Run cant find a directory or a file to start from")
            sys.exit("Proxy Run cant find a directory or a file to start from")
    else:
        logger.warn("Need to provide a directory as a top level starting point - not a directory")
        parser.print_help()
        sys.exit("Proxy Run needs to have an input to start from")