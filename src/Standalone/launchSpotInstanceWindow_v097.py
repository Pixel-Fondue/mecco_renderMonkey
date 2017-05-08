#!/usr/bin/python


from PySide.QtGui import *
from PySide.QtCore import *
import time
from datetime import datetime,timedelta,tzinfo
import thread
from threading import Thread
import threading

class getZones(QObject):
    zoneResults = Signal(list)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud
        print 'zone object'

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         zoneList = self.cloud.getAvailabilityZones();
         self.zoneResults.emit(zoneList)
         print zoneList
         #return status 

class getPrices(QObject):
    priceResults = Signal(dict)
    def __init__(self,cloud,type):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud
        self.type = type

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         history = self.cloud.getSpotPriceHistory(self.type);
         self.priceResults.emit(history)
         #return status 


class lsiDialog(QDialog):
 def __init__(self, cloud,stylesheet, parent = None):
				super(lsiDialog, self).__init__(parent)

				self.setModal(True)
				
				self.cloud = cloud
				
				self.setWindowTitle("Launch Spot Request")
				
				#layout = QGridLayout()
				
				self.layout = QVBoxLayout(self);
				
				self.stylesheet = stylesheet
		
				instanceLabel = QLabel("Configure Instance:")
				pcLabel = QLabel()
				pcLabel.setText("Pick Computer Type")
				pcLabel.setFixedWidth(150)
		
				computerTypes=["m4.large","m4.xlarge","m4.2xlarge","m4.4xlarge","m4.10xlarge","m4.16xlarge","c3.xlarge","c4.large","c4.xlarge","c4.4xLarge","c4.8xlarge","c3.8xlarge"]
				self.computerType = QComboBox()
				computerType = self.computerType
				computerType.setFixedWidth(150)
				computerType.connect(computerType, SIGNAL('currentIndexChanged(int)'), self.getSpotPriceHistory)
				ctlv = QListView()
				self.computerType.setView(ctlv)

				self.vSize = QSpinBox()
				vSize = self.vSize
				vSize.setValue(8);
				vSize.setMinimum(8);
				vSize.setMaximum(16384);
				vSize.setFixedWidth(150)
				vSizeLabel = QLabel("Storage Size (GB)")
				vSizeLabel.setFixedWidth(150)

				self.numInstances = QSpinBox()
				numInstances = self.numInstances
				numInstances.setFixedWidth(150)
				numInstLabel = QLabel("Number of Instances")
				numInstLabel.setFixedWidth(150)
		
				self.bid = QDoubleSpinBox()
				bid = self.bid
				bid.setDecimals(3)
				bid.setPrefix("$")
				bidLabel = QLabel("Max. Bid Price")
				bidLabel.setFixedWidth(150)
				bid.setFixedWidth(150)
				bid.setSingleStep(.001)
				
				self.alarmToggle = QCheckBox("Set CPU Activity Alarm")
				self.alarmToggle.connect(self.alarmToggle, SIGNAL('stateChanged(int)'), self.alarmToggleChanged)
				
				self.alarmPeriodLabel=QLabel("Status Check Interval (60 second intervals)")
				self.alarmPeriod=QSpinBox()
				self.alarmPeriod.setSingleStep(60)
				self.alarmPeriod.setMinimum(60)
				self.alarmPeriod.setMaximum(50000)
				self.apLineEdit = self.alarmPeriod.lineEdit()
				self.apLineEdit.setReadOnly(1)
				
				
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

				alarmPeriodLayout = QHBoxLayout()
				alarmPeriodLayout.addWidget(self.alarmPeriodLabel)
				alarmPeriodLayout.addWidget(self.alarmPeriod)
				
				alarmPeriodCountLayout = QHBoxLayout()
				alarmPeriodCountLayout.addWidget(self.alarmPeriodCountLabel)
				alarmPeriodCountLayout.addWidget(self.alarmPeriodCount)

				alarmThresholdLayout = QHBoxLayout()
				alarmThresholdLayout.addWidget(self.alarmThresholdLabel)
				alarmThresholdLayout.addWidget(self.alarmThreshold)
	
				compTypeLayout = QHBoxLayout()
				compTypeLayout.addWidget(pcLabel)
				compTypeLayout.addWidget(computerType)
				compTypeLayout.addStretch(1)
				
				vSizeLayout = QHBoxLayout()
				vSizeLayout.addWidget(vSizeLabel)
				vSizeLayout.addWidget(vSize)
				vSizeLayout.addStretch(1)
				
				numInstLayout = QHBoxLayout()
				numInstLayout.addWidget(numInstLabel)
				numInstLayout.addWidget(numInstances)
				numInstLayout.addStretch(1)
		
				bidLayout = QHBoxLayout()
				bidLayout.addWidget(bidLabel)
				bidLayout.addWidget(bid)
				bidLayout.addStretch(1)

				instConfigLayout = QVBoxLayout()
				instConfigLayout.addWidget(instanceLabel)
				instConfigLayout.addLayout(compTypeLayout)
				instConfigLayout.addLayout(vSizeLayout)
				instConfigLayout.addLayout(numInstLayout)
				instConfigLayout.addLayout(bidLayout)
				instConfigLayout.addWidget(self.alarmToggle)
				instConfigLayout.addLayout(alarmPeriodLayout)
				instConfigLayout.addLayout(alarmPeriodCountLayout)
				instConfigLayout.addLayout(alarmThresholdLayout)
				instConfigLayout.addStretch(1)
				
				priceHistoryLayout = QVBoxLayout()
				

				availabilityZoneLabel = QLabel("Availability Zone:")				
				
				self.availabilityZone = QComboBox()
				availabilityZone = self.availabilityZone
				availabilityZone.setFixedWidth(150)
				availabilityZone.connect(availabilityZone, SIGNAL('currentIndexChanged(int)'), self.getSpotPriceHistory)

				azlv = QListView()
				self.availabilityZone.setView(azlv)

			
				priceLabel = QLabel("Spot Price History:")
				
				self.priceHistory = QTreeWidget()
				priceHistory = self.priceHistory
				priceHistory.setHeaderLabels(["Computer Type","Date (M-D-Y)","Time","Cost","Availability Zone"])
				#priceHistory.setColumnCount(4)
				priceHistory.setFixedWidth(500)
				
				#priceHistoryLayout.addWidget(availabilityZoneLabel)
				#priceHistoryLayout.addWidget(availabilityZone)
				priceHistoryLayout.addWidget(priceLabel)
				priceHistoryLayout.addWidget(priceHistory)


				# OK and Cancel buttons
				buttons = QDialogButtonBox(
								QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
								Qt.Horizontal, self)
				buttons.accepted.connect(self.accept)
				buttons.rejected.connect(self.reject)
#				layout.addWidget(buttons,5,1)
				
				mainui = QHBoxLayout()
				
				mainui.addLayout(instConfigLayout)
				mainui.addLayout(priceHistoryLayout)
				
				self.layout.addLayout(mainui)
				self.layout.addWidget(buttons)
				
				self.show()
				
				computerType.addItems(computerTypes)
				
				#self.getAvailabilityZones();
				
 def checkFields(self):
  badFields = []
  
  if self.computerType.currentText() == "":
   badFields.append("Computer Type")

  if self.numInstances.text() == "0":
   badFields.append("Number of Instances must be greater than zero.\n")

  if self.bid.text().strip("$") == "0.000":
   badFields.append("Max Bid Price must be greater than zero.")
  
  return badFields
   
 
 def getSpotPriceHistory(self):
  priceHistoryThread = Thread(target=self.getSpotPriceHistoryThread,args=())
  priceHistoryThread.daemon = True
  priceHistoryThread.start();
 
 def getSpotPriceHistoryThread(self):
  getprice = getPrices(self.cloud,self.computerType.currentText());
  getprice.priceResults.connect(self.spotPriceResults)
  getprice()

 
 def spotPriceResults(self,history):
  tree = self.priceHistory
  tree.clear();
  #priceHistory = ''
  utcoffset = datetime.utcnow()-datetime.now();
  i=0
  for price in history:
   #priceHistory+=price['InstanceType']+" at "+str(price['Timestamp'])+" was "+price['SpotPrice']+" in zone: "+price['AvailabilityZone']+'\n'
   pricetime = price['Timestamp']
   pricetimeutc = pricetime - utcoffset
   row = QTreeWidgetItem();
   row.setText(0,price['InstanceType'])
   row.setText(1,pricetimeutc.strftime('%m-%d-%Y'))
   row.setText(2,pricetimeutc.strftime('%H:%M'))
   row.setText(3,"$"+price['SpotPrice'])
   row.setText(4,price['AvailabilityZone'])
   tree.addTopLevelItems([row])
   tree.resizeColumnToContents(0)
   tree.resizeColumnToContents(1)
   tree.resizeColumnToContents(2)
   tree.resizeColumnToContents(3)
   tree.resizeColumnToContents(4)

   i+=1;
  
  #self.priceHistory.append(priceHistory) 
  #self.priceHistory.verticalScrollBar().setValue(0);
  
 def getAvailabilityZones(self):
  availableZoneThread = Thread(target=self.getAvailabilityZonesThread,args=())
  availableZoneThread.daemon = True
  availableZoneThread.start();
  
 def getAvailabilityZonesThread(self):
  print 'start zones'
  getzones = getZones(self.cloud);
  getzones.zoneResults.connect(self.availableZoneResults)
  getzones()

  
 def availableZoneResults(self,zoneList):
  print 'called'
  self.availabilityZone.addItems(zoneList)
 
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

