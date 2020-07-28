from Qt import QtWidgets, QtGui, QtCore


class Config(QtCore.QObject):
    def __init__(self):
        super(Config, self).__init__()
        self.gridSize = 50
        self.zoomFactor = 1.15
        self.maxZoom = 6
        self.minZoom = 0.4
        self.gridLineWidth = 1
        self.drawGrid = True
        self.drawMainGridAxis = True
        self.graphBackgroundColor = QtGui.QColor(50, 50, 50)
        self.gridColor = QtGui.QColor(0.0, 0.0, 0.0)
        self.overlayAxisPen = QtGui.QPen(QtGui.QColor(255, 50, 50, 255), self.gridLineWidth)
        self.thinGridLinePen = QtGui.QPen(QtGui.QColor(80, 80, 80, 255), 0.5)
        self.selectionRectOutlinerPen = QtGui.QPen(QtGui.QColor(70, 70, 150))
        self.selectionRectColor = QtGui.QColor(60, 60, 60, 150)

    def serialize(self):
        overlayAxisPen = self.overlayAxisPen.color
        thinGridLinePen = self.thinGridLinePen.color
        selectionRectOutlinerPen = self.selectionRectOutlinerPen.color
        selectionRectColor = self.selectionRectColor

        return {"gridSize": self.gridSize,
                "zoomFactor": self.zoomFactor,
                "maxZoom": self.minZoom,
                "minZoom": self.maxZoom,
                "gridLineWidth": self.gridLineWidth,
                "drawGrid": self.drawGrid,
                "drawMainGridAxis": self.drawMainGridAxis,
                "graphBackgroundColor": (self.graphBackgroundColor.red, self.graphBackgroundColor.green,
                                         self.graphBackgroundColor.blue),
                "gridColor": (self.gridColor.red, self.gridColor.green,
                              self.gridColor.blue),
                "overlayAxisPen": (overlayAxisPen.red, overlayAxisPen.green,
                                   overlayAxisPen.blue),
                "thinGridLinePen": (thinGridLinePen.red, thinGridLinePen.green,
                                    thinGridLinePen.blue),
                "selectionRectOutlinerPen": (selectionRectOutlinerPen.red, selectionRectOutlinerPen.green,
                                             selectionRectOutlinerPen.blue),
                "selectionRectColor": (selectionRectColor.red, selectionRectColor.green,
                                       selectionRectColor.blue)}
