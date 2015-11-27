# This example creates a custom view using PySide Qt and adds a simple render button to it.
# Either run this code from the script editor or save it to a file inside a lxserv server in the user scripts- or
# your kit's directory.
#
# Then set any viewport to use the "My Render Button" custom view server

import lx
import lxifc
import PySide
from PySide.QtGui import *


def onClicked():
    lx.eval("render")


# To create our custom view, we subclass from lxifc.CustomView
class MyRenderButton(lxifc.CustomView):

    def customview_Init(self, pane):

        if pane is None:
            return False

        custPane = lx.object.CustomPane(pane)

        if not custPane.test():
            return False

        # get the parent object
        parent = custPane.GetParent()

        # convert to PySide QWidget
        widget = lx.getQWidget(parent)

        # Check that it succeeds
        if widget is not None:

            # Here we create a new layout and add a button to it
            layout = PySide.QtGui.QVBoxLayout()
            table = QTableWidget()
            renderButton = QPushButton("RENDER!")

            # Increasing the font size for the button
            f = renderButton.font()
#            f.setPointSize(30)
            renderButton.setFont(f)
  
            table.setRowCount(5)
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(['Path','Dest','Format','Group'])

            # This connects the "clicked" signal of the button to the onClicked function above
            renderButton.clicked.connect(onClicked)

            # Adds the button to our layout and adds the layout to our parent widget
            layout.addWidget(table)
            layout.addWidget(renderButton)
            layout.setContentsMargins(2, 2, 2, 2)
            widget.setLayout(layout)
            return True

        return False

# Finally, register the new custom view server to Modo
lx.bless(MyRenderButton, "Render Monkey Editor")