import argparse
import logging

logger = logging.getLogger(__name__)


class Action(object):
    id = ""

    def __init__(self, config):
        """
        :param config: The zoo config manager instance.
        :type config: :class:`zoo.core.manager.Zoo`
        """
        self.config = config
        self._argumentParser = None  # type: argparse.ArgumentParser
        self.options = None  # type: argparse.Namespace

    def processArguments(self, parentParser):
        self._argumentParser = parentParser.add_parser(self.id,
                                                       help=self.__doc__,
                                                       )
        self._argumentParser.set_defaults(func=self._execute)
        self.arguments(self._argumentParser)

    def _execute(self, args):
        self.options = args
        logger.debug("Running command with arguments: \n{}".format(args))
        self.run()

    def arguments(self, subParser):
        """Method that adds arguments to the argument parser

        :param subParser:
        :type subParser: :class:`argparse.ArgumentParser`
        """
        pass

    def run(self):
        pass

    def cleanup(self):
        pass
