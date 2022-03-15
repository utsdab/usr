#Example menu.py for autoSlate

################################
#          AUTOSLATE           #
#     by DAVID EMENY 2013      #
################################


#AutoSlate is not a gizmo, it is a group node inside a nuke script. The function and command below tell nuke to import the script and then show the resulting group node in the properties bin. It behaves exactly like a gizmo but with none of the drawbacks when it comes to sharing your scripts with other people. If you prefer to use it as a gizmo, simply load the nuke script and export the group as a gizmo.

#Tip: You can use this function with other tools that you make, just pass the name of the tool. To create a tool, make a group, do your stuff, select it, then "Export Nodes As Script..."


#Replace the temporary path with the path to autoSlate.nk

def addGroupTool(toolName):
    g = nuke.nodePaste("/home/user/.nuke/gizmos/" + toolName)
    nuke.show(g)

toolbar = nuke.menu('Nodes')
toolbar.addCommand('AutoSlate', 'addGroupTool("autoSlate.nk")' , icon='Ramp.png')


