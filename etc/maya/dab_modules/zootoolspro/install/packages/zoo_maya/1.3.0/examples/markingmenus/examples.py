from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.api import nodes
from zoo.libs.utils import zlogging

logger = zlogging.getLogger(__name__)



class DynamicMMBySelectionExample(menu.MarkingMenu):
    """Example Class for dynamically creating marking menus.
    """
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "dynamicMMBySelectionExample"

    def show(self, layout, menu, parent):
        """Example override creating a linear menu with passing arguments down to the MMCommands.

        :param layout: The layout instance to update.
        :type layout: :class:`menu.Layout`
        :param menu: The parent menu which items will be parented to
        :type menu: str
        :param parent: the top level parent menu or parent widget.
        :type parent: str
        """
        # grab the nodes value which comes from the marking menu executor
        selNodes = self.commandArguments.get("nodes")
        if not selNodes:
            return
        # build a dict which contains our commands
        # each command must be specfied in the format of {"type": "command", "id": "mycommandid"}
        items = []
        for i in selNodes:
            name = nodes.nameFromMObject(i.object(), partialName=False, includeNamespace=False)
            items.append({"type": "command", "id": "printNodePath",
                          "arguments": {"node": i, "label": name}})
        # finally update the layout object
        layout.update({"items": {"generic": items
                                           }
                                 })
        # ensure the layout has been solved to contain our commands
        layout.solve()
        super(DynamicMMBySelectionExample, self).show(layout, menu, parent)


class PrintNodePath(menu.MarkingMenuCommand):
    """Example Command class which demonstrates how to dynamically change the UI Label and to have
    a UI.
    Specifying a Docstring for the class will act as the tooltip.
    """
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "printNodePath"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        label = arguments.get("label", "None")
        return {"icon": "eye",
                "label": label,
                "bold": False,
                "italic": True,
                "optionBox": True,
                "optionBoxIcon": "eye"
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        node = arguments.get("node")
        if operation == "print":
            if node is not None:
                print(nodes.nameFromMObject(node.object()))
            else:
                print("example argument")
        elif operation == "log":
            if node is not None:
                logger.info(nodes.nameFromMObject(node.object()))
            else:
                logger.info("example argument")
        else:
            print(nodes.nameFromMObject(node.object()))


    def executeUI(self, arguments):
        """The executeUI method is called when the user triggering the box icon on the right handle side
        of the action item.

        For this method to be called you must specify in the UIData method "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "print":
            node = arguments.get("node")
            print(nodes.nameFromMObject(node.object()))
