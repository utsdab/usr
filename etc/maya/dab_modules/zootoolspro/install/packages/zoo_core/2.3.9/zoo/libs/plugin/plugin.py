"""This module contains the base Plugin class and the metric stats for the plugin.
"""
import inspect
import timeit

from zoo.libs.utils import env


class Plugin(object):
    """Base plugin class that all plugins inherent from. The client should subclass this to provide a standard
    interface when needed.

    .. code-block:: python

        Class CustomPlugin(Plugin):
            id = "CustomPlugin.example"
            def execute(self):
                print "executed plugin: {}".format(self.id)

    """
    # the UUID of the plugin, usually it's best to create a descriptive id.
    id = ""
    # The plugin's creator
    creator = ""

    def __init__(self, manager=None):
        """
        :param manager: The Plugin manager instance
        :type manager: :class:`zoo.libs.plugin.pluginmanager.PluginManager`
        """
        self.manager = manager
        self.stats = PluginStats(self)


class PluginStats(object):
    def __init__(self, plugin):
        """
        :param plugin: The Plugin instance
        :type plugin: :class:`Plugin`
        """
        self.plugin = plugin  # type: Plugin
        self.id = self.plugin.id  # type: str
        self.startTime = 0.0
        self.endTime = 0.0
        self.executionTime = 0.0

        self.info = {}
        self._init()

    def _init(self):
        """Initializes some basic info about the plugin and the use environment
        Internal use only.
        """
        self.info.update({"name": self.plugin.__class__.__name__,
                          "creator": self.plugin.creator,
                          "module": self.plugin.__class__.__module__,
                          "filepath": inspect.getfile(self.plugin.__class__),
                          "id": self.id,
                          "application": env.application()
                          })
        self.info.update(env.machineInfo())

    def start(self):
        """Sets the start time for metrics.
        """
        self.startTime = timeit.default_timer()

    def finish(self, traceback=None):
        """Called when the plugin has finish executing.

        :param traceback:
        :type traceback:
        """
        self.endTime = timeit.default_timer()
        self.executionTime = self.endTime - self.startTime
        self.info["executionTime"] = self.executionTime
        self.info["lastUsed"] = self.endTime
        if traceback:
            self.info["traceback"] = traceback
