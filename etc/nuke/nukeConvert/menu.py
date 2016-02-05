import nukeConvertGUI

nuke.menu('Nuke').addCommand('MyMenu/Image batch convert', 'nukeConvertGUI.showWindow()','',icon='StickyNote.png')