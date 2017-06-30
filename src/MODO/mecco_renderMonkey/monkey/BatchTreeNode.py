
import lumberjack, os
from symbols import *

# TODO remove after display_name and display_value refactoring
def markup(pre, string):
    return '\03({}:{})'.format(pre, string)

COL_NAME = "Name"
COL_VALUE = "Value"

GRAY = markup('c', '4113')
FONT_BOLD = markup('f', 'FONT_BOLD')

IMAGE_FORMAT = 'image_format'

class BatchTreeNode(lumberjack.TreeNode):

    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        
        self._key = kwargs['key']
        self._value = kwargs.get('value', None)
        self._node_region = kwargs.get('node_region', None)
        self._value_type = kwargs.get('value_type', None)
        self._selectable = kwargs.get('selectable', True)
        self._ui_only = kwargs.get('ui_only', False)
        self._tooltips = {}

        self.columns[COL_NAME] = lumberjack.TreeValue()
        self.columns[COL_NAME].input_region = self._node_region
        self.columns[COL_NAME].value = self.display_name

        self.columns[COL_VALUE] = lumberjack.TreeValue()
        self.columns[COL_VALUE].input_region = self._node_region
        self.columns[COL_VALUE].value = self.display_value

    # TODO refactor to use font and color attrs from TreeNodeValue
    def display_name(self):
        m = ''
        if self._node_region == REGIONS[1]:
            m = ''
        elif self._ui_only:
            m = GRAY
        elif self._node_region == REGIONS[7]:
            m = FONT_BOLD
        elif isinstance(self._key, int):
            m = GRAY

        if self._node_region == REGIONS[1]:
            k = os.path.basename(self.__class__.child_by_key(self, SCENE_PATH).raw_value())
        elif isinstance(self._key, int):
            k = str(self._key + 1)
        else:
            k = str(self._key)
            k = k.replace('_', ' ')
            k = k.title() if "." not in k else k
        
        return m + k

    def display_value(self):
        m = ''
        if self._value_type in (list.__name__, dict.__name__, tuple.__name__):
            m = GRAY
        elif self._node_region == REGIONS[1]:
            m = GRAY
        elif self._node_region == REGIONS[5]:
            m = GRAY

        if self._node_region == REGIONS[1]:
            v = self.__class__.child_by_key(self, SCENE_PATH).raw_value()
        elif self._value_type == IMAGE_FORMAT:
            v = monkey.util.get_imagesaver(self._value)[1]
        else:
            v = str(self._value)

        return m + v            
        
    def set_tooltip(self, idx, tip):
        self._tooltips[idx] = tip

    def tooltip(self, idx):
        if idx in self._tooltips:
            return self._tooltips[idx]

    @staticmethod
    def child_by_key(root, key):
        for child in root._children:
            if key == child.key():
                return child
        return None

    def ui_only(self):
        return self._ui_only

#    def set_ui_only(self, ui_only=True):
#        self._ui_only = ui_only

    def raw_value(self):
        return self._value

    def key(self):
        return str(self._key)

#    def set_key(self, key):
#        self._key = key

#    def node_region(self):
#        return str(self._node_region)

#    def set_node_region(self, node_region):
#        self._node_region = node_region
#        return self._node_region

#    def set_value(self,value):
#        self._value = value

    def value_type(self):
        return self._value_type

 #   def set_value_type(self, value_type):
 #       self._value_type = value_type
 #       return self._value_type

 #   def selectable(self):
 #       return self._selectable

  #  def set_selectable(self, selectable=True):
  #      self._selectable = selectable


#    def ancestors(self, path=None):
#        if self._parent:
#            return self._parent.ancestors() + [self]
#        else:
#            return path if path else []

#    def ancestor_keys(self):
#        return [ancestor.key() for ancestor in self.ancestors()[1:]]



   # def select_shift_up(self):
   #     if self.parent_child_index() > 0:
   #         self.set_selected(False)
   #         self.parent().children()[self.parent_child_index() - 1].set_selected()

  #  def select_shift_down(self):
  #      if self.parent_child_index() + 1 < len(
  #              [i for i in self.parent().children() if not i.ui_only()]
  #      ):
  #          self.set_selected(False)
  #          self.parent().children()[self.parent_child_index() + 1].set_selected()

 #   def update_child_keys(self):
 #       if self.value_type() in (list.__name__, tuple.__name__):
 #           legit_kids = [child for child in self.children() if not child.ui_only()]
 #           for key, child in enumerate(sorted(legit_kids, key=lambda x: x.key())):
 #               child.set_key(key if isinstance(key, int) else child.key())

#    def tier(self):
#        return len(self.ancestors())