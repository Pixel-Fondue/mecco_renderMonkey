# python

import lx
from Color import Color
from Font import Font


class TreeValue(object):
    """Contains all of the necessary properties for a TreeView
    cell value, including internal value, display value, and metadata
    like color and font information.

    NOTE: Technically the rich text system in MODO allows for multiple fonts, colors,
    and icons in a given string. In practice, however, this is rarely used in treeviews.
    Typically there is only one icon at the beginning of the string, and the entire cell
    has the same color and font. To keep things simple, the font, color, and icon
    properties are all designed to work this way. If you need something more complex,
    you'll need to provide a custom `display_value` to override our default construct."""

    def __init__(self, **kwargs):
        self._value = value if 'value' in kwargs else None
        self._cell_command = cell_command if 'cell_command' in kwargs else None
        self._batch_command = batch_command if 'batch_command' in kwargs else None
        self._datatype = datatype if 'datatype' in kwargs else None
        self._use_cell_command_for_display = use_cell_command_for_display if 'use_cell_command_for_display' in kwargs else False
        self._display_value = display_value if 'display_value' in kwargs else None
        self._input_region = input_region if 'input_region' in kwargs else None
        self._color = color if 'color' in kwargs else Color()
        self._font = font if 'font' in kwargs else Font()
        self._icon_resource = icon_resource if 'icon_resource' in kwargs else None
        self._tooltip = tooltip if 'tooltip' in kwargs else None

    def use_cell_command_for_display():
        doc = """Boolean is True if `cell_command` is a query and should be used
        instead of `display_value` in TreeView. For example, your `cell_command`
        could fire `user.value myBoolean ?` and display a checkmark representing
        the result."""
        def fget(self):
            return self._use_cell_command_for_display
        def fset(self, use_cell_command_for_display):
            self._use_cell_command_for_display = use_cell_command_for_display
        return locals()

    use_cell_command_for_display = property(**use_cell_command_for_display())

    def value():
        doc = """The actual cell value. Note that this can be overridden by
        `display_value()` when displayed in a TreeView, and will be ignored
        if a `cell_command` is defined."""
        def fget(self):
            return self._value
        def fset(self, value):
            self._value = value
        return locals()

    value = property(**value())

    def icon_resource():
        doc = """Icon resource to display at the beginning of the string.

        Built-in examples:
        MIMG_NONE
        MIMG_ARROWUP
        MIMG_ARROWDOWN
        MIMG_ARROWUPDOWN
        MIMG_ARROWCORNER_LL
        MIMG_CHECKMARK
        MIMG_ARROWLEFTRIGHT
        MIMG_ARROWLEFT
        MIMG_ARROWRIGHT
        MIMG_ARROWFOURWAY
        MIMG_MENU
        MIMG_BULLET1
        MIMG_BULLET2
        MIMG_BULLET3
        MIMG_POPUPARROW
        MIMG_POPOUTARROW
        MIMG_CHILDPLUS
        MIMG_CHILDMINUS
        MIMG_ATTRPLUS
        MIMG_ATTRMINUS
        MIMG_THUMB
        MIMG_OPTION
        MIMG_LOCK
        MIMG_KEY
        MIMG_STATICKEY
        MIMG_ANIMNOKEY
        MIMG_LISTPAD
        MIMG_CIRCLEX
        MIMG_CIRCLEPLUS
        MIMG_CIRCLEDOT
        MIMG_CIRCLEEQUAL
        MIMG_CIRCLEPROPORTIONAL
        MIMG_CONNECT

        You can also define your own 13px icon resources for use here, but note
        that in all versions prior to MODO 11, they MUST NOT contain `.` characters."""
        def fget(self):
            return self._icon_resource
        def fset(self, icon_resource):
            self._icon_resource = icon_resource
        return locals()

    icon_resource = property(**icon_resource())

    def cell_command():
        doc = """Cells can contain commands similar to Forms, and this is especially
        useful with query commands like booleans. Note that in order for the `cell_command`
        to work, we must also specify a `batch_command` for multi-selections."""
        def fget(self):
            return self._cell_command
        def fset(self, cell_command):
            self._cell_command = cell_command
        return locals()

    cell_command = property(**cell_command())

    def batch_command():
        doc = """Similar to `cell_command`, except this one is fired on batch selections.
        For `cell_command` to work properly, an accompanying `batch_command` is required."""
        def fget(self):
            return self._batch_command
        def fset(self, batch_command):
            self._batch_command = batch_command
        return locals()

    batch_command = property(**batch_command())

    def datatype():
        doc = """The datatype for the value. Can be any of the normal MODO value
        display types expressed as lowercase strings: 'acceleration', 'angle',
        'angle3', 'axis', 'boolean', 'color', 'color1', 'date', 'datetime',
        'filepath', 'float', 'float3', 'force', 'integer', 'light', 'mass',
        'percent', 'percent3', 'speed', 'string', 'time', 'uvcoord', 'vertmapname'"""
        def fget(self):
            if self._datatype:
                return self._datatype
            else:
                internal_type = type(self._value)
                if isinstance(internal_type, basestring):
                    return 'string'
                elif isinstance(internal_type, int):
                    return 'integer'
                elif isinstance(internal_type, float):
                    return 'float'
                elif isinstance(internal_type, bool):
                    return 'boolean'
        def fset(self, value):
            self._datatype = value
        return locals()

    datatype = property(**datatype())

    def display_value():
        doc = """The value as it will be used in the treeview, including any formatting,
        fonts, colors, etc.

        MODO uses a "rich text" system to encode color and font information:
        Colors are done with "\x03(c:color)", where "color" is a string representing a
        decimal integer computed with 0x01000000 | ((r << 16) | (g << 8) | b).
        Italics and bold are done with "\x03(c:font)", where "font" is the string
        FONT_DEFAULT, FONT_NORMAL, FONT_BOLD or FONT_ITALIC. Icons have an 'i' flag,
        followed by a 13px icon resource name, e.g. "\x03(i:iconResourceName)".

        All of this should be handled internally by the value object unless explicitly
        overridden.

        Setting this value sets a literal string to be displayed
        in the cell regardless of the actual cell value. Automatically prepends the
        `Value` object's color and font markup as appropriate."""
        def fget(self):
            if self._display_value is not None:
                display_string = str(self._display_value)
            elif self._value is not None:
                if hasattr(self._value, '__call__'):
                    display_string = str(self._value())
                else:
                    display_string = str(self._value)
            else:
                display_string = ''

            # This is a hack.
            # If for any reason all cells in a row are empty, MODO displays
            # the row as a tiny sliver 3px tall. That's weird.
            # Hack is to always provide a space character if the string is empty.
            display_string = display_string if display_string else " "

            markup = '\x03(i:%s)' % self._icon_resource if self._icon_resource else ''
            markup += self._font.markup() if self._font else ''
            markup += self._color.markup() if self._color else ''
            markup += display_string
            return markup
        def fset(self, value):
            self._display_value = value
        return locals()

    display_value = property(**display_value())

    def intput_region():
        doc = """Region for input-mapping. Must correspond to one of the input_region
        strings provided during the `Lumberjack().bless()` operation."""
        def fget(self):
            return self._intput_region
        def fset(self, value):
            self._intput_region = value
        return locals()

    intput_region = property(**intput_region())

    def color():
        doc = "Should be a Lumberjack `Color()` object. Default: None"
        def fget(self):
            return self._color
        def fset(self, value):
            self._color = value
        return locals()

    color = property(**color())

    def font():
        doc = "Should be a Lumberjack `Font()` object. Default: None"
        def fget(self):
            return self._font
        def fset(self, value):
            self._font = value
        return locals()

    font = property(**font())

    def tooltip():
        doc = """Tooltip to display for the cell. Should be a message table lookup
        if at all possible. (e.g. @table@message@)"""
        def fget(self):
            return self._tooltip
        def fset(self, value):
            self._tooltip = value
        return locals()

    tooltip = property(**tooltip())
