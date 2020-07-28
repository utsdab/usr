import inspect

from Qt import QtWidgets
from zoo.libs import iconlib
from zoo.libs.command import executor


class CommandViewer(QtWidgets.QWidget):
    def __init__(self, executor, parent=None):
        super(CommandViewer, self).__init__(parent=parent)
        self.executor = executor
        layout = QtWidgets.QVBoxLayout(self)
        self.scrollWidget = QtWidgets.QScrollArea(self)
        layout.addWidget(self.scrollWidget)
        scrollLayout = QtWidgets.QVBoxLayout(self)
        self.scrollWidget.setLayout(scrollLayout)
        self.listWidget = QtWidgets.QListWidget(self)
        scrollLayout.addWidget(self.listWidget)
        self.setLayout(layout)
        self.setup()

    def refresh(self):
        self.listWidget.clear()
        self.setup()

    def setup(self):
        toolTip = """Name: {name}
path: {path}
Icon: {icon}
tooltip: {tooltip}
label: {label}
color: {color}
background: {backgroundColor}"""
        for command in self.executor.commands.values():
            uiData = command.uiData
            item = QtWidgets.QListWidgetItem()
            item.setText(uiData.get("label", ""))
            icon = iconlib.icon(uiData.get("icon", ""))
            data = {"name": command.id, "path": inspect.getfile(command)}
            data.update(uiData)
            info = toolTip.format(**data)
            item.setToolTip(info)
            if icon is not None:
                item.setIcon(icon)
            self.listWidget.addItem(item)


windowInstance = None


def launch(parent=None):
    global windowInstance
    try:
        windowInstance.close()
    except (RuntimeError, AttributeError):
        pass
    exe = executor.Executor()
    exe.registerEnv("ZOO_COMMAND_LIB")
    windowInstance = CommandViewer(exe, parent=parent)
    windowInstance.show()
    return windowInstance
