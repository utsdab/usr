"""
Created on May 23, 2015

@author: dave
"""

from Qt import QtWidgets


class GraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent=None, defaultSize=(400, 600)):
        super(GraphicsScene, self).__init__(parent)
        self.defaultSize = defaultSize

    def setSize(self, width, height):
        """Will set scene size with proper center position
        """
        self.setSceneRect(-width * 0.5, -height * 0.5, width, height)

    def setDefaultSize(self):
        self.setSize(*self.defaultSize)

    def boundingRect(self, margin=0):
        """
        Return scene content bounding box with specified margin
        """
        # Get item boundingBox
        scene_rect = self.itemsBoundingRect()

        # Stop here if no margin
        if not margin:
            return scene_rect

        # Add margin
        scene_rect.setX(scene_rect.x() - margin)
        scene_rect.setY(scene_rect.y() - margin)
        scene_rect.setWidth(scene_rect.width() + margin)
        scene_rect.setHeight(scene_rect.height() + margin)

        return scene_rect
