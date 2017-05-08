#!python

from PySide.QtGui import *
from PySide.QtCore import *

class sjDialog(QDialog):
 def __init__(self,parent,renderFileList,softwareList,stylesheet):
				super(sjDialog, self).__init__(parent)
				
				self.setWindowTitle("Enter Render Job Info")
				
				self.setModal(True)
				
				self.stylesheet = stylesheet

				layout = QVBoxLayout(self)
				
				self.renderFile = None;
				
				self.softwarelabel = QLabel("Select Software")
				self.selectSoftware = QComboBox()
				self.selectSoftware.addItems(softwareList)

				sslv = QListView()
				self.selectSoftware.setView(sslv)
				
				softwareLayout = QHBoxLayout()
				softwareLayout.addWidget(self.softwarelabel)
				softwareLayout.addWidget(self.selectSoftware)			
		
				
				self.filelabel = QLabel("Select File")
				
				self.selectRenderFile = QComboBox()
				#self.selectRenderFile.setFixedWidth(150)
				self.selectRenderFile.addItems(renderFileList)
				#self.cloud.renderFile = str(fileText)
				
				srflv = QListView()
				self.selectRenderFile.setView(srflv)

				
				fileLayout = QHBoxLayout()
				fileLayout.addWidget(self.filelabel)
				fileLayout.addWidget(self.selectRenderFile)			

				self.frameslabel = QLabel("Enter Frames To Render")
				self.frames = QLineEdit()

				framesLayout = QHBoxLayout()
				framesLayout.addWidget(self.frameslabel)
				framesLayout.addWidget(self.frames)			

				self.outputlabel = QLabel("Enter Render File Name")
				self.output = QLineEdit()

				outputLayout = QHBoxLayout()
				outputLayout.addWidget(self.outputlabel)
				outputLayout.addWidget(self.output)
				
				self.passesToggle = QCheckBox("Render Passes")
				self.passesToggle.connect(self.passesToggle, SIGNAL('stateChanged(int)'), self.checkPassesToggle)
				self.passLabel = QLabel("Enter Pass Name")
				self.passName = QLineEdit()
				self.passLabel.setEnabled(False)
				self.passName.setEnabled(False)
				
				passNameLayout = QHBoxLayout()
				passNameLayout.addWidget(self.passLabel)
				passNameLayout.addWidget(self.passName)
				
				passesLayout = QVBoxLayout()
				passesLayout.addWidget(self.passesToggle)
				passesLayout.addLayout(passNameLayout)
			
				self.layersToggle = QCheckBox("Render Layered File")
				self.layersToggle.connect(self.layersToggle, SIGNAL('stateChanged(int)'), self.checkToggle)

				self.rdetToggle = QCheckBox("Monitor Render Details")
				#self.rdetToggle.connect(self.layersToggle, SIGNAL('stateChanged(int)'), self.rdetToggle)


					
				#self.passToggle = QCheckBox("Render Passes")
				
				self.layerDepth = QComboBox()
				layerDepthItems = ["16-bit","32-bit"]
				self.layerDepth.addItems(layerDepthItems)
				self.layerDepth.setEnabled(False);
				
				ldlv = QListView()
				self.layerDepth.setView(ldlv)
				
				layersLayout = QVBoxLayout()
				#layersLayout.addWidget(self.rdetToggle)
				layersLayout.addWidget(self.layersToggle)
				layersLayout.addWidget(self.layerDepth)
				
				layout.addLayout(softwareLayout)				
				layout.addLayout(fileLayout)
				layout.addLayout(framesLayout)
				layout.addLayout(outputLayout)
				layout.addLayout(passesLayout)
				layout.addLayout(layersLayout)


				# OK and Cancel buttons
				buttons = QDialogButtonBox(
								QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
								Qt.Horizontal, self)
				buttons.accepted.connect(self.accept)
				buttons.rejected.connect(self.reject)
				layout.addWidget(buttons)
				

 def rdetToggle(self,toggle):
  toggle = self.rdetToggle.isChecked()
  #print toggle
  if toggle is True:
   self.layerDepth.setEnabled(True);
   self.setStyleSheet(self.stylesheet)
  else:
   self.layerDepth.setEnabled(False);
   self.setStyleSheet(self.stylesheet)


 def checkToggle(self,toggle):
  toggle = self.layersToggle.isChecked()
  #print toggle
  if toggle is True:
   self.layerDepth.setEnabled(True);
   self.setStyleSheet(self.stylesheet)   
  else:
   self.layerDepth.setEnabled(False);
   self.setStyleSheet(self.stylesheet)

 def checkPassesToggle(self,toggle):
  toggle = self.passesToggle.isChecked()
  #print toggle
  if toggle is True:
   self.passLabel.setEnabled(True);
   self.passName.setEnabled(True);
   self.setStyleSheet(self.stylesheet)
  else:
   self.passLabel.setEnabled(False);
   self.passName.setEnabled(False);
   self.setStyleSheet(self.stylesheet)

 def checkFields(self):
  emptyFields = []
  
  if self.selectRenderFile.currentText() == "":
   emptyFields.append("File")

  if self.frames.text() == "":
   emptyFields.append("Frames")

  if self.output.text() == "":
   emptyFields.append("Render File Name")

  
  return emptyFields
