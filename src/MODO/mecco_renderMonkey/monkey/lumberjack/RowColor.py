# python


class RowColor(object):
    """Stores a bitwise color flag for treeview rows. Unlike rich text, rows can
    only be one of 18 pre-defined colors in MODO. We set them by name, but get them
    by bitwise int.

    The following names are available:
    ```
    - 'none'
    - 'red'
    - 'magenta'
    - 'pink'
    - 'brown'
    - 'orange'
    - 'yellow'
    - 'green'
    - 'light_g'
    - 'cyan'
    - 'blue'
    - 'light_blue'
    - 'ultrama'
    - 'purple'
    - 'light_pu'
    - 'dark_grey'
    - 'grey'
    - 'white'
    ```"""

    _current_color_name = None

    _lookup = {
        # LXmTREEITEM_ROWCOLOR_MASK
        # 'mask':       0x001F0000 # The bits used for a colors

        # LXfTREEITEM_ROWCOLOR_NONE
        'none':       0x00000000, # No color
        # LXfTREEITEM_ROWCOLOR_RED
        'red':        0x00010000,
        # LXfTREEITEM_ROWCOLOR_MAGENTA
        'magenta':    0x00020000,
        # LXfTREEITEM_ROWCOLOR_PINK
        'pink':       0x00030000,
        # LXfTREEITEM_ROWCOLOR_BROWN
        'brown':      0x00040000,
        # LXfTREEITEM_ROWCOLOR_ORANGE
        'orange':     0x00050000,
        # LXfTREEITEM_ROWCOLOR_YELLOW
        'yellow':     0x00060000,
        # LXfTREEITEM_ROWCOLOR_GREEN
        'green':      0x00070000,
        # LXfTREEITEM_ROWCOLOR_LIGHT_G
        'light_g':    0x00080000,
        # LXfTREEITEM_ROWCOLOR_CYAN
        'cyan':       0x00090000,
        # LXfTREEITEM_ROWCOLOR_BLUE
        'blue':       0x000A0000,
        # LXfTREEITEM_ROWCOLOR_LIGHT_BLUE
        'light_blue': 0x000B0000,
        # LXfTREEITEM_ROWCOLOR_ULTRAMA
        'ultrama':    0x000C0000,
        # LXfTREEITEM_ROWCOLOR_PURPLE
        'purple':     0x000D0000,
        # LXfTREEITEM_ROWCOLOR_LIGHT_PU
        'light_pu':   0x000E0000,
        # LXfTREEITEM_ROWCOLOR_DARK_GREY
        'dark_grey':  0x000F0000,
        # LXfTREEITEM_ROWCOLOR_GREY
        'grey':       0x00100000,
        # LXfTREEITEM_ROWCOLOR_WHITE
        'white':      0x00110000
    }

    def __init__(self, color = None):
        self._current_color_name = color

    def name():
        doc = """The name of the row color. Use `None` for no color.

        The following names are available:
        ```
        - 'none'
        - 'red'
        - 'magenta'
        - 'pink'
        - 'brown'
        - 'orange'
        - 'yellow'
        - 'green'
        - 'light_g'
        - 'cyan'
        - 'blue'
        - 'light_blue'
        - 'ultrama'
        - 'purple'
        - 'light_pu'
        - 'dark_grey'
        - 'grey'
        - 'white'
        ```"""
        def fget(self):
            return self._current_color_name
        def fset(self, value):
            self._current_color_name = value
        return locals()

    name = property(**name())

    def bitwise():
        doc = """The bitwise int for the row color."""
        def fget(self):
            name = self.name if self._current_color_name is not None else 'none'
            return self._lookup[name]
        return locals()

    bitwise = property(**bitwise())
