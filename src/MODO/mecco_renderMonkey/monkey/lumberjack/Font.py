# python


class Font(object):
    """Special class for storing and retrieving font flags for use in treeviews."""

    _font = None

    def markup(self):
        """Returns the markup string for use in treeview cells."""
        if self._font:
            return '\x03({}:{})'.format('f', self._font)
        return ''

    def set_bold(self):
        self._font = 'FONT_BOLD'

    def set_italic(self):
        self._font = 'FONT_ITALIC'

    def set_normal(self):
        self._font = 'FONT_NORMAL'

    def set_default(self):
        self._font = 'FONT_DEFAULT'
