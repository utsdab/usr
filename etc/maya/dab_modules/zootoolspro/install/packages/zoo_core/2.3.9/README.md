zoocore
=========

Core python api for zootools

## Environment Variables
Zoo adds to the current environment, These variables accept multiple paths just make sure you create them before the
startup process.

- ZOO_BASE_PATHS
- ZOO_ICON_PATHS
- ZOO_COMMAND_LIB


# ZOO QT
Zoo uses the follow third party wrapper.
https://github.com/mottosso/Qt.py.git

The location in zoo is expected to change to the thirdparty package under zoo but until then here's how you currently import it
```python
from zoo.libs.pyqt.qt import QtWidgets
```

Zoo.pyqt has a number of extensions to qt widgets, views and models.
