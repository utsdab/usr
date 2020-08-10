from zoo.libs.command import command
from zoo.libs.maya.qt import nodeeditor

ALIGN_LEFT = 0
ALIGN_RIGHT = 1
ALIGN_TOP = 2
ALIGN_BOTTOM = 3
ALIGN_CENTER_X = 4
ALIGN_CENTER_Y = 5


class NodeAlignmentCommand(command.ZooCommand):
    id = "zoo.maya.nodeEditor.alignment"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "horizontalAlignLeft",
              "tooltip": "Align's the selected nodes in the node editor to be at the farthest left point",
              "label": "Align Nodes",
              "color": "",
              "backgroundColor": ""
              }
    _previousNodePositions = None
    _nodeEditor = None

    def resolveArguments(self, arguments):
        editor = arguments.get("nodeEditor")

        if not editor:
            # defaults to the primary editor
            editor = nodeeditor.NodeEditorWrapper()
        nodes = editor.selectedNodeItems()
        self._nodeEditor = editor
        self._previousNodePositions = [(n, n.pos()) for n in nodes]
        if not arguments.get("align"):
            arguments["align"] = ALIGN_LEFT
        if len(nodes) < 2:
            self.cancel("Must have more then 2 nodes selected! canceling command.")
        arguments.update({"nodeEditor": editor, "nodeItems": nodes})
        return arguments

    def doIt(self, nodeEditor=None, nodeItems=None, align=ALIGN_LEFT):
        """Create the meta node based on the type parameter, if the type isn't specified then the baseMeta class will
        be used instead
        """
        if align == ALIGN_LEFT:
            nodeEditor.alignLeft(nodeItems)
        elif align == ALIGN_RIGHT:
            nodeEditor.alignRight(nodeItems)
        elif align == ALIGN_TOP:
            nodeEditor.alignTop(nodeItems)
        elif align == ALIGN_BOTTOM:
            nodeEditor.alignBottom(nodeItems)
        elif align == ALIGN_CENTER_X:
            nodeEditor.alignCenterX(nodeItems)
        elif align == ALIGN_CENTER_Y:
            nodeEditor.alignCenterY(nodeItems)
        return True

    def undoIt(self):
        if self._previousNodePositions is not None and self._nodeEditor.exists():
            for n, pos in self._previousNodePositions:
                n.setPos(pos)
