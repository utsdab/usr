import collections

# --------- All stylesheet Keys (SK) Add/Edit more here ----------
# Must match all themes in zoo_preferences/preferences/data/stylesheet.pref
# Main Colors
SK_MAIN_BACKGROUND_COLOR = "$MAIN_BACKGROUND_COLOR"
SK_MAIN_FOREGROUND_COLOR = "$MAIN_FOREGROUND_COLOR"
SK_VIEW_BACKGROUND_COLOR = "$VIEW_BACKGROUND_COLOR"
SK_SECONDARY_FOREGROUND_COLOR = "$SECONDARY_FOREGROUND_COLOR"
SK_SECONDARY_BACKGROUND_COLOR = "$SECONDARY_BACKGROUND_COLOR"
# Window Frameless
SK_FRAMELESS_WINDOW_CONTENTS = "$FRAMELESS_WINDOW_CONTENTS"
SK_FRAMELESS_TITLEBAR_COLOR = "$FRAMELESS_TITLEBAR_COLOR"
SK_FRAMELESS_TITLELABEL_COLOR = "$FRAMELESS_TITLELABEL_COLOR"
SK_FRAMELESS_ROUNDED_CORNERS = "$FRAMELESS_ROUNDED_CORNERS"
SK_WINDOW_LOGO_HIGHLIGHT_COLOR = "$WINDOW_LOGO_HIGHLIGHT_COLOR"  # not is qss could be elsewhere
SK_HOVER_BACKGROUND_COLOR = "$HOVER_BACKGROUND_COLOR"  # needs to be broken up too generic
SK_TITLE_MINIMIZED_FONTSIZE = "$TITLE_MINIMIZED_FONTSIZE"
# Table Tree Widgets
SK_TBL_TREE_HEADER_COLOR = "$TBL_TREE_HEADER_COLOR"
SK_TBL_TREE_BG_COLOR = "$TBL_TREE_BG_COLOR"
SK_TBL_TREE_BORDER_COLOR = "$TBL_TREE_GRID_COLOR"
SK_TBL_TREE_ALT_COLOR = "$TBL_TREE_ALT_COLOR"
SK_TBL_TREE_ACTIVE_COLOR = "$TBL_TREE_ACTIVE_COLOR"
SK_TBL_TREE_ACT_TEXT_COLOR = "$TBL_TREE_ACT_TEXT_COLOR"
SK_TBL_TREE_HOVER_COLOR = "$TBL_TREE_HOVER_COLOR"
SK_WIDGET_ROUNDED_CORNERS = "$WIDGET_ROUNDED_CORNERS"  # not sure which widgets?
SK_COMPONENT_TREE_SEL_COL = "$COMPONENT_TREE_SEL_COL"
SK_COMPONENT_TREE_BG = "$COMPONENT_TREE_BG"
SK_COMPONENT_ITEM_FONT = "$COMPONENT_ITEM_FONT"
SK_TREEITEM_DRAG_TINT = "$TREEITEM_DRAG_TINT"
# Titles text
SK_DEFAULT_FONTSIZE = "$DEFAULT_FONTSIZE"
SK_TEXT_BOX_FG_COLOR = "$TEXT_BOX_FG_COLOR"
SK_TEXT_INACTIVE_COLOR = "$TEXT_INACTIVE_COLOR"
SK_TITLE_LARGE_COLOR = "$TITLE_LARGE_COLOR"
SK_TITLE_FONTSIZE = "$TITLE_FONTSIZE"
SK_HEADER_FONTSIZE = "$HEADER_FONTSIZE"
# Text Box
SK_TEXT_BOX_BG_COLOR = "$TEXT_BOX_BG_COLOR"
# Slider
SK_SLIDER_BG_COLOR = "$SLIDER_BG_COLOR"
SK_SLIDER_BORDER_RADIUS = "$SLIDER_BORDER_RADIUS"
SK_SLIDER_HANDLE_BORDER_RADIUS = "$SLIDER_HANDLE_BORDER_RADIUS"
SK_SLIDER_SIZE = "$SLIDER_SIZE"
SK_SLIDER_GROOVE_BORDER_RADIUS = "$SLIDER_GROOVE_BORDER_RADIUS"
SK_SLIDER_HANDLE_SIZE = "$SLIDER_HANDLE_SIZE"
SK_SLIDER_HANDLE_MARGIN = "$SLIDER_HANDLE_MARGIN"
SK_SLIDER_INACTIVE = "$SLIDER_INACTIVE"
SK_SLIDER_DISABLED = "$SLIDER_DISABLED"
SK_SLIDER_BG_COLOR_DISABLED = "$SLIDER_BG_COLOR_DISABLED"
# Highlights
SK_HIGHLIGHT_ACTIVE_COLOR = "$HIGHLIGHT_ACTIVE_COLOR"
# Icons (mostly buttons)
SK_ICON_HOVER_COLOR = "$ICON_HOVER_COLOR"
SK_ICON_PRIMARY_COLOR = "$ICON_PRIMARY_COLOR"
SK_DIAGONALBG_ICON = "$DIAGONALBG_ICON"
# Image Button
SK_IMAGEBUTTON_HOVER_COLOR = "$IMAGEBUTTON_HOVER_COLOR"
# Button Reg
SK_BUTTON_TEXT_COLOR = "$BUTTON_TEXT_COLOR"
SK_BTN_HOVER_COLOR = "$BTN_HOVER_COLOR"
SK_BTN_PRESS_COLOR = "$BTN_PRESS_COLOR"
SK_BTN_BACKGROUND_COLOR = "$BTN_BACKGROUND_COLOR"
SK_BUTTON_BORDER_RADIUS = "$BUTTON_BORDER_RADIUS"
SK_BTN_PADDING = "$BTN_PADDING"
SK_DISABLED_COLOR = "$DISABLED_COLOR"  # and checkbox and radio
SK_BUTTON_ICON_COLOR = "$BUTTON_ICON_COLOR"  # not sure what this affects, doesn't seem to do much
SK_COLOR_BTN_RADIUS = "$COLOR_BTN_RADIUS"  # new from Keen
# Icon Button
SK_SHADOWEDBTN_BGCOLOR = "$SHADOWEDBTN_BGCOLOR"
SK_SHADOWEDBTN_BGCOLOR_HOVER = "$SHADOWEDBTN_BGCOLOR_HOVER"
SK_SHADOWEDBTN_IMAGEBG = "$SHADOWEDBTN_IMAGEBG"
SK_SHADOWEDBTN_SHADOWBG = "$SHADOWEDBTN_SHADOWBG"
SK_SHADOWEDBTN_HOVER_SHADOWBG = "$SHADOWEDBTN_HOVER_SHADOWBG"
SK_SHADOWEDBTN_HOVER_IMAGEBG = "$SHADOWEDBTN_HOVER_IMAGEBG"
SK_SHADOWEDBTN_TEXT_HOVER = "$SHADOWEDBTN_TEXT_HOVER"
SK_SHADOWEDBTN_BGCOLOR_PRESSED = "$SHADOWEDBTN_BGCOLOR_PRESSED"
SK_SHADOWEDBTN_TEXT_PRESSED = "$SHADOWEDBTN_TEXT_PRESSED"
SK_SHADOWEDBTN_PRESSED_SHADOWBG = "$SHADOWEDBTN_PRESSED_SHADOWBG"
SK_SHADOWEDBTN_PRESSED_IMAGEBG = "$SHADOWEDBTN_PRESSED_IMAGEBG"
SK_SHADOWEDBTN_HOVER_ICON = "$SHADOWEDBTN_HOVER_ICON"
SK_SHADOWEDBTN_PRESSED_ICON = "$SHADOWEDBTN_PRESSED_ICON"
SK_COMMAND_BTN_HEIGHT = "$COMMAND_BTN_HEIGHT"
# Resizer Button
SK_RESIZER_BTN_COLOR = "$RESIZER_BTN_COLOR"
SK_RESIZER_BTN_HOVER = "$RESIZER_BTN_HOVER"
# Round Button (white minimise UI elements)
SK_ROUNDBUTTON_BGCOLOR = "$ROUNDBUTTON_BGCOLOR"
SK_ROUNDBUTTON_BGCOLOR_HOVER = "$ROUNDBUTTON_BGCOLOR_HOVER"
# Combo Drop Down
SK_COMBO_SIZE = "$COMBO_SIZE"
SK_COMBO_COLOR = "$COMBO_COLOR"
SK_COMBO_HOVER_COLOR = "$COMBO_HOVER_COLOR"
SK_COMBO_LEFTBORDER = "$COMBO_LEFTBORDER"
SK_COMBO_ICON_SIZE = "$COMBO_ICON_SIZE"
SK_COMBO_ICON = "$COMBO_ICON"
# Checkbox
SK_CHECKBOX_BG_COLOR = "$CHECKBOX_BG_COLOR"
SK_CHECKBOX_SIZE = "$CHECKBOX_SIZE"
SK_CHECKBOX_UNCHECKED_ICON = "$CHECKBOX_UNCHECKED_ICON"
SK_CHECKBOX_CHECKED_ICON = "$CHECKBOX_CHECKED_ICON"
SK_PRIMARY_COLOR = "$PRIMARY_COLOR"
SK_RADIO_SIZE = "$RADIO_SIZE"
SK_RADIO_UNCHECKED_SIZE = "$RADIO_UNCHECKED_SIZE"
SK_RADIO_UNCHECKED_RADIUS = "$RADIO_UNCHECKED_RADIUS"
# Toolsets
SK_TOOLSET_LOGO_INACTIVE_COLOR = "$TOOLSET_LOGO_INACTIVE_COLOR"
SK_TOOLSET_LOGO_HIGHLIGHT_OFFSET = "$TOOLSET_LOGO_HIGHLIGHT_OFFSET"
SK_TLSET_BORDER_DESELECT = "$TLSET_BORDER_DESELECT"
SK_TLSET_ICON_POPUP_BG = "$TLSET_ICON_POPUP_BG"
SK_TLSET_BORDER_HOVER = "$TLSET_BORDER_HOVER"
SK_TOOLSET_RESIZER_HANDLE_COLOR = "$TOOLSET_RESIZER_HANDLE_COLOR"
# hotkeys
SK_HOTKEY_ADMIN_LOGO_COLOR = "$HOTKEY_ADMIN_LOGO_COLOR"  # this should be for all windows green Z while in ADMIN
# stackitem
SK_TITLE_REG_TEXT_COLOR = "$TITLE_REG_TEXT_COLOR"
SK_STACKITEM_BACKGROUND_COLOR = "$STACKITEM_BACKGROUND_COLOR"
SK_STACKITEM_HEADER_FOREGROUND = "$STACKITEM_HEADER_FOREGROUND"
SK_STACK_TITLE_DISABLED = "$STACK_TITLE_DISABLED"
SK_STACK_BORDER_WIDTH = "$STACK_BORDER_WIDTH"
# Tooltips
SK_TOOLTIP_BG = "$TOOLTIP_BG"
SK_TOOLTIP_FONT_COLOR = "$TOOLTIP_FONT_COLOR"
SK_TOOLTIP_BORDER_COLOR = "$TOOLTIP_BORDER_COLOR"
SK_TOOLTIP_BORDER_SIZE = "$TOOLTIP_BORDER_SIZE"
# Expanded Tooltips
SK_EXP_TOOLTIP_BG = "$EXP_TOOLTIP_BG"
SK_EXP_TOOLTIP_FONT_SIZE = "$EXP_TOOLTIP_FONT_SIZE"
SK_EXP_TOOLTIP_TITLE_SIZE = "$EXP_TOOLTIP_TITLE_SIZE"
# Embedded Window
SK_EMBED_WINDOW_BG = "$EMBED_WINDOW_BG"
SK_EMBED_WINDOW_BORDER_COL = "$EMBED_WINDOW_BORDER_COL"
# Browser
SK_DIRECTORIES_WIDGET = "$DIRECTORIES_WIDGET"
SK_SETTINGS_TWEAK_BAR = "$SETTINGS_TWEAK_BAR"

SK_BROWSER_SELECTED_COLOR = "$BROWSER_SELECTED_COLOR"
SK_BROWSER_TEXT_COLOR = "$BROWSER_TEXT_COLOR"
SK_BROWSER_TEXT_BG_COLOR = "$BROWSER_TEXT_BG_COLOR"
SK_BROWSER_BORDER_HOVER_COLOR = "$BROWSER_BORDER_HOVER_COLOR"
SK_BROWSER_ICON_BG_COLOR = "$BROWSER_ICON_BG_COLOR"

SK_BROWSER_BG_COLOR = "$BROWSER_BG_COLOR"
SK_BROWSER_BG_SELECTED_COLOR = "$BROWSER_BG_SELECTED_COLOR"
SK_BROWSER_BORDER_SELECTED_COLOR = "$BROWSER_BORDER_SELECTED_COLOR"
# Hive
SK_HIVE_INDICATOR_BUILT = "$HIVE_INDICATOR_BUILT"
SK_HIVE_TOOLBAR_ICON_HUESHIFT = "$HIVE_TOOLBAR_ICON_HUESHIFT"
SK_HIVE_COLOR = "$HIVE_COLOR"
SK_HIVE_TOOLBAR_ICON_COLOR = "$HIVE_TOOLBAR_ICON_COLOR"
SK_HIVE_INDICATOR_NOTBUILT = "$HIVE_INDICATOR_NOTBUILT"
SK_HIVE_TEMPLATE_COLOR = "$HIVE_TEMPLATE_COLOR"
SK_HIVE_COMPONENT_COLOR = "$HIVE_COMPONENT_COLOR"
# Other
SK_NEG_ONE_PIXEL = "$NEG_ONE_PIXEL"
SK_ONE_PIXEL = "$ONE_PIXEL"
SK_TWO_PIXELS = "$TWO_PIXELS"
SK_THREE_PIXELS = "$THREE_PIXELS"
SK_FOUR_PIXELS = "$FOUR_PIXELS"
SK_FIVE_PIXELS = "$FIVE_PIXELS"
SK_DEBUG_1 = "$DEBUG_1"
SK_DEBUG_2 = "$DEBUG_2"
SK_TEAROFF_LINES = "$TEAROFF_LINES"
SK_TEAROFF_BG = "$TEAROFF_BG"
SK_TEAROFF_HOVER = "$TEAROFF_HOVER"
SK_TEAROFF_FONT_SIZE = "$TEAROFF_FONT_SIZE"
SK_SCROLL_BAR_COLOR = "$SCROLL_BAR_COLOR"
SK_SCROLL_BAR_BG = "$SCROLL_BAR_BG"

# --------- Color Group Labels (CG) (Color Swatch Labels inside the top section in the stylesheet UI) ---------
CG_BACKGROUND = "Background Primary"
CG_BACKGROUND_2 = "Background Secondary"
CG_BACKGROUND_3 = "Background Tertiary"
CG_TEXT = "Text"
CG_TEXT_INACTIVE = "Text Inactive"
CG_TEXT_ACTIVE = "Text Active"
CG_TITLE_REG = "Title Regular"
CG_TITLE_LRG = "Title Large"
CG_TITLE_WINDOW = "Title Window"
CG_ICON_PRIMARY = "Icon Primary"
CG_ICON_HOVER = "Icon Hover"
CG_BUTTON = "Button Primary"
CG_BUTTON_2 = "Button Secondary"
CG_BUTTON_WHITE = "Button Resizer"
CG_BUTTON_WHITE_HOVER = "Button Resizer Hover"
CG_BUTTON_PRESS = "Button Press"
CG_BUTTON_SECONDARY_PRESS = "Button Secondary Press"
CG_BUTTON_HOVER = "Button Hover"
CG_BUTTON_SECONDARY_HOVER = "Button Secondary Hover"
CG_WINDOW_TOP_BAR = "Window Top Bar"
CG_HIGHLIGHT_ACTIVE = "Highlight Active"
CG_HIGHLIGHT_PRIMARY = "Highlight Primary"
CG_TEXTBOX_BACKGROUND = "Text/Box Background"
CG_STACK_BACKGROUND = "Stack Bar Background"
CG_STACK_HOVER_BACKGROUND = "Stack Bar Hover"
CG_TABLE_TREE_HEADER = "Table/Tree Header"
CG_TABLE_TREE_BORDER = "Table/Tree Border"
CG_EMBED_BORDER = "Embed Window Border"
CG_COMBO = "Combo Box Primary"
CG_COMBO_HOVER = "Combo Box Hover"
CG_SCROLL_BAR = "Scroll Bar"
CG_SCROLL_BG = "Scroll Background"

# --------- Section Labels (SL) (Lower Section Header Labels in the Stylesheet UI) ---------
SL_MAIN = "Main"
SL_BUTTON = "Button"
SL_BUTTON_SHADOW = "Button Shadow"
SL_COMBOBOX = "Combo Box (Drop Down)"
SL_CHECKBOX = "Check Box/Radio"
SL_TEXTBOX = "Text Box"
SL_SLIDER = "Slider"
SL_FRAMELESS = "Zoo Main Windows (Frameless)"
SL_STACK = "Stack Item/Collapsable"
SL_TBLTREE = "Table/Tree Item"
SL_TOOLSETS = "Toolsets"
SL_BROWSER = "Image Browser"
SL_HIVE = "Hive"
SL_HOTKEYS = "Hotkeys"
SL_EMBED_WINDOW = "Embeded Window"
SL_TOOLTIP = "Tooltip"
SL_EXP_TOOLTIP = "Expanded Tooltip"
SL_OTHER = "Other"

# The Global Offset Color Dictionary, keys (label names), values (stylesheet keys connected to global groups)
# Categorizes the top section of the preferences GUI.
COLORGROUP_ODICT = collections.OrderedDict([(CG_BACKGROUND, [SK_SECONDARY_FOREGROUND_COLOR,
                                                             SK_MAIN_BACKGROUND_COLOR,
                                                             SK_FRAMELESS_WINDOW_CONTENTS,
                                                             SK_TLSET_BORDER_DESELECT,
                                                             SK_SETTINGS_TWEAK_BAR]),
                                            (CG_BACKGROUND_2, [SK_VIEW_BACKGROUND_COLOR,
                                                               SK_TBL_TREE_BG_COLOR,
                                                               SK_TBL_TREE_ALT_COLOR,
                                                               SK_SCROLL_BAR_BG,
                                                               SK_TBL_TREE_BG_COLOR]),
                                            (CG_BACKGROUND_3, [SK_EMBED_WINDOW_BG]),
                                            (CG_WINDOW_TOP_BAR, [SK_FRAMELESS_TITLEBAR_COLOR]),
                                            (CG_TEXTBOX_BACKGROUND, [SK_TEXT_BOX_BG_COLOR,
                                                                     SK_CHECKBOX_BG_COLOR,
                                                                     SK_BROWSER_TEXT_BG_COLOR,
                                                                     SK_BROWSER_BG_COLOR,
                                                                     SK_SLIDER_BG_COLOR]),
                                            (CG_TEXT, [SK_MAIN_FOREGROUND_COLOR,
                                                       SK_TEXT_BOX_FG_COLOR,
                                                       SK_BUTTON_TEXT_COLOR,
                                                       SK_ICON_PRIMARY_COLOR,
                                                       SK_SLIDER_INACTIVE]),
                                            (CG_TEXT_INACTIVE, [SK_TEXT_INACTIVE_COLOR,
                                                                SK_BROWSER_TEXT_COLOR]),
                                            (CG_TEXT_ACTIVE, [SK_TBL_TREE_ACT_TEXT_COLOR,
                                                              SK_SHADOWEDBTN_TEXT_HOVER,
                                                              SK_SHADOWEDBTN_TEXT_PRESSED]),
                                            (CG_TITLE_REG, [SK_TITLE_REG_TEXT_COLOR,
                                                            SK_STACKITEM_HEADER_FOREGROUND,
                                                            SK_BROWSER_BORDER_HOVER_COLOR]),
                                            (CG_TITLE_LRG, [SK_TITLE_LARGE_COLOR]),
                                            (CG_TITLE_WINDOW, [SK_TITLE_LARGE_COLOR]),
                                            (CG_EMBED_BORDER, [SK_EMBED_WINDOW_BORDER_COL]),
                                            (CG_ICON_PRIMARY, [SK_ICON_PRIMARY_COLOR,
                                                               SK_SLIDER_INACTIVE,
                                                               SK_BUTTON_ICON_COLOR]),
                                            (CG_ICON_HOVER, [SK_ICON_HOVER_COLOR,
                                                             SK_SHADOWEDBTN_HOVER_ICON,
                                                             SK_SHADOWEDBTN_PRESSED_ICON]),
                                            (CG_BUTTON, [SK_BTN_BACKGROUND_COLOR,
                                                         SK_SCROLL_BAR_COLOR,
                                                         SK_RESIZER_BTN_COLOR,
                                                         SK_SHADOWEDBTN_BGCOLOR,
                                                         SK_TOOLSET_RESIZER_HANDLE_COLOR]),
                                            (CG_BUTTON_2, [SK_SHADOWEDBTN_IMAGEBG,
                                                           SK_SHADOWEDBTN_SHADOWBG]),
                                            (CG_BUTTON_HOVER, [SK_BTN_HOVER_COLOR,
                                                               SK_RESIZER_BTN_COLOR,
                                                               SK_SHADOWEDBTN_BGCOLOR_HOVER]),
                                            (CG_BUTTON_SECONDARY_HOVER, [SK_SHADOWEDBTN_HOVER_IMAGEBG,
                                                                         SK_SHADOWEDBTN_HOVER_SHADOWBG]),
                                            (CG_BUTTON_PRESS, [SK_BTN_PRESS_COLOR,
                                                               SK_SHADOWEDBTN_BGCOLOR_PRESSED]),
                                            (CG_BUTTON_SECONDARY_PRESS, [SK_SHADOWEDBTN_PRESSED_IMAGEBG,
                                                                         SK_SHADOWEDBTN_PRESSED_SHADOWBG]),
                                            (CG_BUTTON_WHITE, [SK_ROUNDBUTTON_BGCOLOR]),
                                            (CG_BUTTON_WHITE_HOVER, [SK_ROUNDBUTTON_BGCOLOR_HOVER]),
                                            (CG_COMBO, [SK_COMBO_COLOR]),
                                            (CG_COMBO_HOVER, [SK_COMBO_HOVER_COLOR]),
                                            (CG_HIGHLIGHT_ACTIVE, [SK_HIGHLIGHT_ACTIVE_COLOR,
                                                                   SK_TBL_TREE_ACTIVE_COLOR,
                                                                   SK_TREEITEM_DRAG_TINT,
                                                                   SK_BROWSER_SELECTED_COLOR]),
                                            (CG_HIGHLIGHT_PRIMARY, [SK_PRIMARY_COLOR,
                                                                    SK_TBL_TREE_HOVER_COLOR,
                                                                    SK_TLSET_BORDER_HOVER,
                                                                    SK_BROWSER_SELECTED_COLOR,
                                                                    SK_BROWSER_SELECTED_COLOR]),
                                            (CG_STACK_BACKGROUND, [SK_STACKITEM_BACKGROUND_COLOR]),
                                            (CG_STACK_HOVER_BACKGROUND, [SK_HOVER_BACKGROUND_COLOR]),
                                            (CG_TABLE_TREE_HEADER, [SK_TBL_TREE_HEADER_COLOR]),
                                            (CG_TABLE_TREE_BORDER, [SK_TBL_TREE_BORDER_COLOR]),
                                            (CG_SCROLL_BAR, [SK_SCROLL_BAR_COLOR]),
                                            (CG_SCROLL_BG, [SK_SCROLL_BAR_BG])
                                            ])

# Categorizes the stylesheet's keys into the lower stylesheet UI sections, modify this to edit sections and order
# If keys are missing here a warning will appear and they will be added to the SL_OTHER section
SECTION_ODICT = collections.OrderedDict([(SL_MAIN, [SK_MAIN_BACKGROUND_COLOR,
                                                    SK_SECONDARY_BACKGROUND_COLOR,
                                                    SK_MAIN_FOREGROUND_COLOR,
                                                    SK_SECONDARY_FOREGROUND_COLOR,
                                                    SK_VIEW_BACKGROUND_COLOR,
                                                    SK_HOVER_BACKGROUND_COLOR,
                                                    SK_PRIMARY_COLOR,
                                                    SK_HIGHLIGHT_ACTIVE_COLOR,
                                                    SK_DISABLED_COLOR,
                                                    SK_WINDOW_LOGO_HIGHLIGHT_COLOR,
                                                    SK_DEFAULT_FONTSIZE,
                                                    SK_HEADER_FONTSIZE,
                                                    SK_TITLE_FONTSIZE,
                                                    SK_TITLE_LARGE_COLOR]),
                                         (SL_BUTTON, [SK_BTN_BACKGROUND_COLOR,
                                                      SK_BTN_PRESS_COLOR,
                                                      SK_BTN_HOVER_COLOR,
                                                      SK_BUTTON_TEXT_COLOR,
                                                      SK_COMMAND_BTN_HEIGHT,
                                                      SK_BUTTON_BORDER_RADIUS,
                                                      SK_BTN_PADDING,
                                                      SK_ICON_PRIMARY_COLOR,
                                                      SK_BUTTON_ICON_COLOR,
                                                      SK_ICON_HOVER_COLOR,
                                                      SK_ROUNDBUTTON_BGCOLOR,
                                                      SK_ROUNDBUTTON_BGCOLOR_HOVER,
                                                      SK_RESIZER_BTN_COLOR,
                                                      SK_RESIZER_BTN_HOVER,
                                                      SK_COLOR_BTN_RADIUS,
                                                      SK_IMAGEBUTTON_HOVER_COLOR]),
                                         (SL_BUTTON_SHADOW, [SK_SHADOWEDBTN_BGCOLOR,
                                                             SK_SHADOWEDBTN_SHADOWBG,
                                                             SK_SHADOWEDBTN_IMAGEBG,
                                                             SK_SHADOWEDBTN_BGCOLOR_HOVER,
                                                             SK_SHADOWEDBTN_HOVER_SHADOWBG,
                                                             SK_SHADOWEDBTN_HOVER_IMAGEBG,
                                                             SK_SHADOWEDBTN_HOVER_ICON,
                                                             SK_SHADOWEDBTN_TEXT_HOVER,
                                                             SK_SHADOWEDBTN_BGCOLOR_PRESSED,
                                                             SK_SHADOWEDBTN_PRESSED_SHADOWBG,
                                                             SK_SHADOWEDBTN_PRESSED_IMAGEBG,
                                                             SK_SHADOWEDBTN_PRESSED_ICON,
                                                             SK_SHADOWEDBTN_TEXT_PRESSED]),
                                         (SL_COMBOBOX, [SK_COMBO_COLOR,
                                                        SK_COMBO_SIZE,
                                                        SK_COMBO_ICON,
                                                        SK_COMBO_ICON_SIZE,
                                                        SK_COMBO_LEFTBORDER,
                                                        SK_COMBO_HOVER_COLOR]),
                                         (SL_CHECKBOX, [SK_CHECKBOX_BG_COLOR,
                                                        SK_CHECKBOX_SIZE,
                                                        SK_CHECKBOX_CHECKED_ICON,
                                                        SK_CHECKBOX_UNCHECKED_ICON,
                                                        SK_RADIO_SIZE,
                                                        SK_RADIO_UNCHECKED_SIZE,
                                                        SK_RADIO_UNCHECKED_RADIUS]),
                                         (SL_TEXTBOX, [SK_TEXT_BOX_BG_COLOR,
                                                       SK_TEXT_BOX_FG_COLOR,
                                                       SK_TEXT_INACTIVE_COLOR]),
                                         (SL_SLIDER, [SK_SLIDER_BG_COLOR,
                                                      SK_SLIDER_INACTIVE,
                                                      SK_SLIDER_DISABLED,
                                                      SK_SLIDER_BG_COLOR_DISABLED,
                                                      SK_SLIDER_BORDER_RADIUS,
                                                      SK_SLIDER_HANDLE_BORDER_RADIUS,
                                                      SK_SLIDER_HANDLE_SIZE,
                                                      SK_SLIDER_SIZE,
                                                      SK_SLIDER_GROOVE_BORDER_RADIUS,
                                                      SK_SLIDER_HANDLE_MARGIN
                                                      ]),
                                         (SL_FRAMELESS, [SK_FRAMELESS_ROUNDED_CORNERS,
                                                         SK_FRAMELESS_TITLELABEL_COLOR,
                                                         SK_FRAMELESS_WINDOW_CONTENTS,
                                                         SK_FRAMELESS_TITLEBAR_COLOR,
                                                         SK_TITLE_MINIMIZED_FONTSIZE]),
                                         (SL_STACK, [SK_STACKITEM_BACKGROUND_COLOR,
                                                     SK_TITLE_REG_TEXT_COLOR,
                                                     SK_STACKITEM_HEADER_FOREGROUND,
                                                     SK_STACK_TITLE_DISABLED,
                                                     SK_STACK_BORDER_WIDTH]),
                                         (SL_TBLTREE, [SK_TBL_TREE_HEADER_COLOR,
                                                       SK_TBL_TREE_BG_COLOR,
                                                       SK_TBL_TREE_BORDER_COLOR,
                                                       SK_TBL_TREE_ALT_COLOR,
                                                       SK_TBL_TREE_ACTIVE_COLOR,
                                                       SK_TBL_TREE_ACT_TEXT_COLOR,
                                                       SK_TBL_TREE_HOVER_COLOR,
                                                       SK_COMPONENT_TREE_SEL_COL,
                                                       SK_COMPONENT_TREE_BG,
                                                       SK_COMPONENT_ITEM_FONT,
                                                       SK_TREEITEM_DRAG_TINT]),
                                         (SL_TOOLSETS, [SK_TOOLSET_LOGO_HIGHLIGHT_OFFSET,
                                                        SK_TOOLSET_LOGO_INACTIVE_COLOR,
                                                        SK_TLSET_BORDER_HOVER,
                                                        SK_TLSET_BORDER_DESELECT,
                                                        SK_TLSET_ICON_POPUP_BG,
                                                        SK_TOOLSET_RESIZER_HANDLE_COLOR]),
                                         (SL_BROWSER, [SK_DIRECTORIES_WIDGET,
                                                       SK_SETTINGS_TWEAK_BAR,
                                                       SK_BROWSER_TEXT_BG_COLOR,
                                                       SK_BROWSER_TEXT_COLOR,
                                                       SK_BROWSER_SELECTED_COLOR,
                                                       SK_BROWSER_BORDER_HOVER_COLOR,
                                                       SK_BROWSER_ICON_BG_COLOR,
                                                       SK_BROWSER_BG_COLOR,
                                                       SK_BROWSER_BORDER_SELECTED_COLOR,
                                                       SK_BROWSER_BG_SELECTED_COLOR]),
                                         (SL_HIVE, [SK_HIVE_COLOR,
                                                    SK_HIVE_INDICATOR_BUILT,
                                                    SK_HIVE_TOOLBAR_ICON_HUESHIFT,
                                                    SK_HIVE_TOOLBAR_ICON_COLOR,
                                                    SK_HIVE_INDICATOR_NOTBUILT,
                                                    SK_HIVE_TEMPLATE_COLOR,
                                                    SK_HIVE_COMPONENT_COLOR]),
                                         (SL_HOTKEYS, [SK_HOTKEY_ADMIN_LOGO_COLOR]),
                                         (SL_TOOLTIP, [SK_TOOLTIP_BG,
                                                       SK_TOOLTIP_FONT_COLOR,
                                                       SK_TOOLTIP_BORDER_COLOR,
                                                       SK_TOOLTIP_BORDER_SIZE]),
                                         (SL_EXP_TOOLTIP, [SK_EXP_TOOLTIP_BG,
                                                           SK_EXP_TOOLTIP_FONT_SIZE,
                                                           SK_EXP_TOOLTIP_TITLE_SIZE]),
                                         (SL_EMBED_WINDOW, [SK_EMBED_WINDOW_BG,
                                                            SK_EMBED_WINDOW_BORDER_COL]),
                                         (SL_OTHER, [SK_NEG_ONE_PIXEL,
                                                     SK_ONE_PIXEL,
                                                     SK_TWO_PIXELS,
                                                     SK_THREE_PIXELS,
                                                     SK_FOUR_PIXELS,
                                                     SK_FIVE_PIXELS,
                                                     SK_DEBUG_1,
                                                     SK_DEBUG_2,
                                                     SK_TEAROFF_LINES,
                                                     SK_TEAROFF_BG,
                                                     SK_TEAROFF_HOVER,
                                                     SK_TEAROFF_FONT_SIZE,
                                                     SK_DIAGONALBG_ICON,
                                                     SK_WIDGET_ROUNDED_CORNERS,
                                                     SK_SCROLL_BAR_COLOR,
                                                     SK_SCROLL_BAR_BG])])
