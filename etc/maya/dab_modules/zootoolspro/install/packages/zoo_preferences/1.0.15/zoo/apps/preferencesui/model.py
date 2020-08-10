import os

from Qt import QtWidgets, QtCore

from zoo.libs.plugin import pluginmanager
from zoo.libs.pyqt.models import datasources
from zoo.preferences.core import preference


class Model(QtCore.QObject):
    def __init__(self, qmodel, order=None):
        """ Gathers the available preferences from the different packages

        :param qmodel:
        :type qmodel:
        :param order: The order in which the preferences should be shown.
        todo: maybe order this should be preference id rather than preference title
        :type order: list[basestring]
        """
        self.pluginManager = pluginmanager.PluginManager(interface=SettingWidget)
        self.model = qmodel
        self.root = None  # type: PathDataSource
        self.order = order or []
        self.reload()

    def _reloadDataSources(self):
        # sort by category title
        validResults = sorted(self.pluginManager.plugins.values(), key=lambda x: x.categoryTitle)
        self.root = PathDataSource("root", model=self.model, parent=None)

        # Move the ones specified by order to the top
        for o in reversed(self.order):
            for v in validResults:
                if v.categoryTitle == o:
                    validResults.insert(0, validResults.pop(validResults.index(v)))
                    break

        # Add the data sources
        for wid in validResults:
            categoryTitle = wid.categoryTitle
            if not categoryTitle:
                continue
            # slice the relativePath which will end up being a tree in the view
            slicedpath = categoryTitle.split("/")
            # skip the last value as thats going to hold our widget, others are just text
            parent = self.root
            for name in slicedpath[:-1]:
                source = PathDataSource(name.title(), model=self.model, parent=parent)
                # source.model = self.model
                parent.children.append(source)
                parent = source
            # now add the leaf
            source = SettingDataSource(slicedpath[-1].title(), widget=wid, model=self.model, parent=parent)
            # source.model = self.model
            parent.children.append(source)

    def reload(self):
        # if we already have loaded the inital plugins just refresh the dataSources
        if self.pluginManager.plugins:
            self._reloadDataSources()
            return
        # loop the zootools package preferences and find the widgets
        pluginPaths = set()
        for preferencePath in preference.iterPackagePreferenceRoots():

            widgets = preferencePath / "widgets"
            # skip if widgets py package wasn't found
            if not widgets.exists():
                continue
            pluginPaths.add(str(widgets))

        if pluginPaths:
            self.pluginManager.registerPaths(pluginPaths)
            self._reloadDataSources()

        self.model.root = self.root


class SettingWidget(QtWidgets.QWidget):
    """Main inheritance widget for preference UI which will appear on the right
    """
    categoryTitle = ""

    def __init__(self, parent=None):
        super(SettingWidget, self).__init__(parent)

    def serialize(self):
        pass

    def applySettings(self, settings):
        pass

    def revert(self):
        pass


class PathDataSource(datasources.BaseDataSource):
    """A data source that contains no widget, basically just an item with text
    """

    def __init__(self, label, model=None, parent=None):
        super(PathDataSource, self).__init__(model, parent)
        self._text = label

    def data(self, index):
        return self._text

    def columnCount(self):
        return 1

    def isEnabled(self, index):
        return True

    def isEditable(self, *args, **kwargs):
        return False

    def widget(self):
        return None

    def save(self):
        pass


class SettingDataSource(datasources.BaseDataSource):
    """Main SettingsDataSource, this class should be linked to a preferences widget from the library
    """

    def __init__(self, label, widget, model=None, parent=None):
        super(SettingDataSource, self).__init__(headerText=label, model=model, parent=parent)
        self.label = label
        self._widget = widget()
        self._widget.hide()

    def save(self):
        self._widget.serialize()

    def data(self, *args, **kwargs):
        return self.label

    def revert(self):
        self._widget.revert()

    def isEditable(self, *args, **kwargs):
        return False

    def widget(self):
        return self._widget
