from zoo.libs import iconlib


from zoo.libs.utils import colour, env


# Imports so we can use the other widgets from elements (eg elements.IconMenuButton())
from zoo.libs.pyqt.widgets.radiobuttongroup import RadioButtonGroup
from zoo.libs.pyqt.widgets.slider import Slider, HSlider, VSlider, FloatSlider
from zoo.libs.pyqt.widgets.spacer import Divider, QHLine, QVLine, Spacer
from zoo.libs.pyqt.widgets.popups import SaveDialog, InputDialog, MessageBox_ok, MessageBox_save, FileDialog_directory
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton, iconMenuButtonCombo
from zoo.libs.pyqt.widgets.label import Label, LabelDivider
from zoo.libs.pyqt.widgets.textedit import TextEdit
from zoo.libs.pyqt.widgets.layouts import (hBoxLayout,
                                           vBoxLayout,
                                           GridLayout,
                                           hGraphicsLinearLayout,
                                           vGraphicsLinearLayout,
                                           formLayout)

from zoo.libs.pyqt.widgets.extendedbutton import ExtendedButton
from zoo.libs.pyqt.widgets.extendedmenu import ExtendedMenu
from zoo.libs.pyqt.widgets.frameless import FramelessWindow
from zoo.libs.pyqt.widgets.buttons import (OkCancelButtons,
                                           buttonRound,
                                           styledButton,
                                           buttonExtended,
                                           regularButton,
                                           iconShadowButton)
from zoo.libs.pyqt.widgets.searchwidget import SearchLineEdit
from zoo.libs.pyqt.widgets.stringedit import StringEdit, FloatEdit, IntEdit
from zoo.libs.pyqt.extended.combobox import ComboBox, ComboBoxRegular, ComboBoxSearchable, ExtendedComboBox
from zoo.libs.pyqt.extended.combobox.comboeditwidget import ComboEditWidget, ComboEditRename, EditChangedEvent, \
    IndexChangedEvent
from zoo.libs.pyqt.extended.spinbox import VectorSpinBox, Transformation, Matrix
from zoo.libs.pyqt.extended.lineedit import LineEdit, FloatLineEdit, IntLineEdit, VectorLineEdit
from zoo.libs.pyqt.extended.menu import MenuCreateClickMethods
from zoo.libs.pyqt.extended.checkbox import CheckBox
from zoo.libs.pyqt.extended.hotkeydetectedit import HotkeyDetectEdit
from zoo.libs.pyqt.extended.color import LabelColorBtn, ColorPaletteColorList
from zoo.libs.pyqt.extended.embeddedwindow import EmbeddedWindow
from zoo.libs.pyqt.extended.clippedlabel import ClippedLabel
from zoo.libs.pyqt.widgets.imagebutton import ImageButton
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton
from zoo.libs.pyqt.extended.combobox.combomenupopup import ComboCustomEvent



if env.isInMaya():
    from zoo.libs.maya.qt.cmdswidgets import MayaColorBtn, MayaColorHsvBtns, CollapsableFrameLayout, MayaColorSlider
    from zoo.libs.maya.qt.changerendererui import checkRenderLoaded, globalChangeRenderer
    from zoo.libs.pyqt.extended.imageview.thumbnail.thumbnailwidget import ThumbnailWidget, ThumbScrollBar
    from zoo.libs.pyqt.extended.imageview.thumbnail.minibrowser import ThumbnailSearchWidget, MiniBrowser
    from zoo.libs.pyqt.extended.snapshotui import SnapshotUi







