#!/usr/bin/python


from PySide.QtGui import *
from PySide.QtCore import *

class liDialog(QDialog):
 def __init__(self, cloud,stylesheet, parent = None):
				super(liDialog, self).__init__(parent)

				self.setModal(True)

				
				self.cloud = cloud
				
				self.setWindowTitle("Launch On-Demand Request")
				
				layout = QGridLayout(self)

				
				self.stylesheet = stylesheet
				
				instConfigLayout = QVBoxLayout()
				
				instanceLabel = QLabel("Configure Instance:")
				pcLabel = QLabel()
				pcLabel.setText("Pick Computer Type")
				pcLabel.setFixedWidth(150)
		
				computerTypes=["t2.micro","t2.small","t2.large","t2.xlarge","t2.2xlarge","m3.medium","m4.large","m4.xlarge","m4.2xlarge","m4.4xlarge","m4.10xlarge","m4.16xlarge","c3.xlarge","c4.large","c4.xlarge","c4.4xLarge","c4.8xlarge","c3.8xlarge"]
				self.computerType = QComboBox()
				computerType = self.computerType
				computerType.setFixedWidth(150)
				#computerType.connect(computerType, SIGNAL('currentIndexChanged(int)'), self.getSpotPriceHistory)

				ctlv = QListView()
				self.computerType.setView(ctlv)


				self.numInstances = QSpinBox()
				numInstances = self.numInstances
				numInstances.setFixedWidth(150)
				numInstLabel = QLabel("Number of Instances")
				numInstLabel.setFixedWidth(150)

				self.vSize = QSpinBox()
				vSize = self.vSize
				vSize.setValue(8);
				vSize.setMinimum(8);
				vSize.setMaximum(16384);
				vSize.setFixedWidth(150)
				vSizeLabel = QLabel("Storage Size (GB)")
				vSizeLabel.setFixedWidth(150)
				
				#alarmToggleLabel=QLabel("Attach Alarm")
				self.alarmToggle = QCheckBox("Set CPU Activity Alarm")
				self.alarmToggle.connect(self.alarmToggle, SIGNAL('stateChanged(int)'), self.alarmToggleChanged)
				
				self.alarmPeriodLabel=QLabel("Status Check Interval (60 second intervals)")
				self.alarmPeriod=QSpinBox()
				self.alarmPeriod.setSingleStep(60)
				self.alarmPeriod.setMinimum(60)
				self.alarmPeriod.setMaximum(50000)
				self.apLineEdit = self.alarmPeriod.lineEdit()
				self.apLineEdit.setReadOnly(1)
				
				
				self.alarmPeriod.connect(self.alarmPeriod, SIGNAL('valueChanged(int)'), self.alarmPeriodChanged)
				self.alarmPeriodCountLabel=QLabel("Status Fail Count (for Alarm Activation)")
				self.alarmPeriodCount=QSpinBox()
				self.alarmThresholdLabel=QLabel("CPU Activity Status Fail Limit (Percent)")
				self.alarmThreshold=QDoubleSpinBox()
				self.alarmThreshold.setDecimals(2)
				self.alarmThreshold.setSingleStep(.01)

				self.alarmPeriodLabel.setEnabled(False);			
				self.alarmPeriod.setEnabled(False);
				self.alarmPeriodCountLabel.setEnabled(False);			
				self.alarmPeriodCount.setEnabled(False);
				self.alarmThresholdLabel.setEnabled(False);			
				self.alarmThreshold.setEnabled(False);

				
				compTypeLayout = QHBoxLayout()
				compTypeLayout.addWidget(pcLabel)
				compTypeLayout.addWidget(computerType)
				compTypeLayout.addStretch(1)
		
				numInstLayout = QHBoxLayout()
				numInstLayout.addWidget(numInstLabel)
				numInstLayout.addWidget(numInstances)
				numInstLayout.addStretch(1)

				instConfigLayout.addWidget(instanceLabel)
				instConfigLayout.addLayout(compTypeLayout)
				instConfigLayout.addLayout(numInstLayout)
				instConfigLayout.addStretch(1)
								
				
				layout.addWidget(instanceLabel,0,0)
				layout.addWidget(pcLabel,1,0)
				layout.addWidget(computerType,1,1)
				layout.addWidget(vSizeLabel,2,0)
				layout.addWidget(vSize,2,1)
				layout.addWidget(numInstLabel,3,0)
				layout.addWidget(numInstances,3,1)
				layout.addWidget(self.alarmToggle,4,0)
				layout.addWidget(self.alarmThresholdLabel,5,0)
				layout.addWidget(self.alarmThreshold,5,1)				
				layout.addWidget(self.alarmPeriodLabel,6,0)
				layout.addWidget(self.alarmPeriod,6,1)
				layout.addWidget(self.alarmPeriodCountLabel,7,0)
				layout.addWidget(self.alarmPeriodCount,7,1)



				# OK and Cancel buttons
				buttons = QDialogButtonBox(
								QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
								Qt.Horizontal, self)
				buttons.accepted.connect(self.accept)
				buttons.rejected.connect(self.reject)
				layout.addWidget(buttons,9,5)
				
				
				self.show()
				
				computerType.addItems(computerTypes)
				
				#self.getSpotPriceHistory();

 def alarmToggleChanged(self,toggle):
  toggle = self.alarmToggle.isChecked()
  #print toggle
  if toggle is True:
				self.alarmPeriodLabel.setEnabled(True);			
				self.alarmPeriod.setEnabled(True);
				self.alarmPeriodCountLabel.setEnabled(True);			
				self.alarmPeriodCount.setEnabled(True);
				self.alarmThresholdLabel.setEnabled(True);			
				self.alarmThreshold.setEnabled(True);
				self.setStyleSheet(self.stylesheet)

  else:
				self.alarmPeriodLabel.setEnabled(False);			
				self.alarmPeriod.setEnabled(False);
				self.alarmPeriodCountLabel.setEnabled(False);			
				self.alarmPeriodCount.setEnabled(False);
				self.alarmThresholdLabel.setEnabled(False);			
				self.alarmThreshold.setEnabled(False);
				self.setStyleSheet(self.stylesheet)
				

 def alarmPeriodChanged(self,value):
  print value

 
 
 def checkFields(self):
  emptyFields = []
  
  if self.computerType.currentText() == "":
   emptyFields.append("Computer Type")

  if self.numInstances.text() == "":
   emptyFields.append("Number of Instances")
  
  return emptyFields
