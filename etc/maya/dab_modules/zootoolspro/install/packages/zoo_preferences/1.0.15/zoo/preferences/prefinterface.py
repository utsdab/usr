class PreferenceInterface(object):
    """Preference interface class which is responsible for interfacing to .pref files within zoo.

    PreferenceInterface shouldn't be instanced directly but through
    :class:`zoo.preferences.core.PreferenceManager` instance.

    It's the intention for interface subclasses to handle creating and manipulating one 
    or more .pref belonging to the installed zoo package. 
    As a general rule of thumb the interface shouldn't manipulate a .pref outside it's 
    own package but can request it from the external interface 
    via self.preference.interface() method however do this at your own risk.

    The .pref internal data structure may change over the life of zootools so it is 
    recommended that the interface provides the necessary methods to handle manipulating
    the data structure over the client directly making the changes.

    See :class:`preference.interface.preference_interface.ZooToolsPreference` for 
    example usage.
    """
    # the unique identifier for the interface which will be used for lookup by 
    # client code and for registry 
    id = ""

    def __init__(self, preference):
        """
        :param preference: The main zoo preference manager
        :type preference: :class:`zoo.preferences.core.PreferenceManager`
        """
        self.preference = preference  # type: zoo.preferences.core.PreferenceManager
