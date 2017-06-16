# python

class Color(object):

    def __init__(self):
        self._internal_rgb = []
        self._special = None

    # Markup for rich text
    def markup(self):
        """Returns the markup string for use in treeview cells."""
        if self._special:
            return '\x03({}:{})'.format('c', self._special)
        if self._internal_rgb:
            return '\x03({}:{})'.format('c', self.bitwise_rgb())
        return ''

    # Bitwise
    def bitwise_rgb(self):
        """Returns the bitwise RGB string for the Color object's current internal RGB."""
        r, g, b = [int(n * 255) for n in self._internal_rgb]
        return str(0x01000000 | ((r << 16) | (g << 8 | b)))

    # Set Explicit Color
    def set_with_8bit(self, r, g, b):
        """Sets internal RGB with three int values between 0-255."""
        self._internal_rgb = [(n / 255) for n in (r, g, b)]

    def set_with_float(self, r, g, b):
        """Sets internal RGB with three decimal values 0.0-1.0"""
        self._internal_rgb = [r, g, b]

    def set_with_hex(self, h):
        """Sets internal RGB using a 16-bit hex code string, e.g. "#ffffff"""
        h = h.strip()
        if h[0] == '#':
            h = h[1:]
        r, g, b = h[:2], h[2:4], h[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        self._internal_rgb = [r, g, b]

    # Set Special Color
    def special_by_int():
        doc = """Certain specific color codes are built-in to MODO for common UI
        conventions, such as 4113 for grayed out text. Should be a string. If
        unsure, leave this alone."""
        def fget(self):
            return self._special_by_int
        def fset(self, value):
            self._special_by_int = value
            self._internal_rgb = []
        return locals()

    special_by_int = property(**special_by_int())

    def special_by_name(self, name):
        """Sets special MODO colors by human-readable names."""
        if name in ['gray', 'grey']:
            # 4113 is a special color for grayed-out text in MODO
            self._special = 4113
        elif name == 'default':
            self._special = None
        elif name == 'black':
            self._special = None
            self._internal_rgb = [0,0,0]
