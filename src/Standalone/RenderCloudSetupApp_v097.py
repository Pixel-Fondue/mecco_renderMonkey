#!/usr/bin/python

import sys
import os
import boto3
import botocore
import json
import thread
import threading
from boto3.s3.transfer import S3Transfer
from threading import Thread
from time import time
import time
import startupScripts

from sys import platform
from PySide.QtGui import *
from PySide.QtCore import *


class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self.percentage = 0.0

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            self.percentage = (self._seen_so_far / self._size) * 100
            #sys.stdout.write("\r%s  %s / %s  (%.2f%%)" % (self._filename, self._seen_so_far, self._size,percentage))
            #sys.stdout.flush()

class createRenderNodeObject(QObject):
    status = Signal(str)
    def __init__(self,session,setupText):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.session = session
        self.sqs = self.session.resource('sqs')
        self.client = self.session.client('ec2')
        self.ec2Resource = self.session.resource('ec2')
        self.ccq = None
        self.setupText = setupText
        self.amicheck = False
        self.checkCount = "."

    def getMessages(self):
     messages = self.ccq.receive_messages(MaxNumberOfMessages=10,WaitTimeSeconds=3);
     if len(messages) > 0:
      print len(messages)
      for message in messages:
       m = message.body
       print("message there");
       print m
       message.delete();
       return m
     else:
      return None

    def checkAMI(self,amiName):
     response = self.client.describe_images(Filters=[{'Name':'name','Values':[amiName]}])
     imageList = response['Images']

     if len(imageList)>0:
      for image in imageList:
       if image['State'] == 'pending':
        return 'pending'
       if image['State'] == 'available':
        return 'available'
     else:
      return 'image not found'

    def terminateRenderNodeSetup(self):
     instName = "RenderNodeSetup"
     response = self.client.describe_instances(Filters=[{'Name':'tag:Name','Values':[instName]},{'Name':'instance-state-name','Values':['running']}])
     print response

     if len(response['Reservations'])>0:
      imageList = response['Reservations'][0]['Instances']
      imageID = imageList[0]['InstanceId']
      print imageID
      self.ec2Resource.instances.filter(InstanceIds=[imageID]).terminate()
      self.ccq.purge();
      self.ccq.delete();

    def createRenderNodeSetup(self):
     ccq = self.sqs.get_queue_by_name(QueueName='mrc_cloud_commands')
     setupText = self.setupText
     userdata = setupText
     response = self.client.describe_images(Filters=[{'Name':'root-device-type','Values':['ebs']},{'Name':'architecture','Values':['x86_64']},{'Name':'name','Values':['*hvm-ssd/ubuntu-trusty-14.04*']}])
     ami = response["Images"][0]["ImageId"]
     type = 't2.micro'
     ec2 = self.ec2Resource
     instances = ec2.create_instances(ImageId=ami, MinCount=1,MaxCount=1,InstanceType=type,UserData=userdata,IamInstanceProfile = {'Name': 'RenderNode'})
     for instance in instances:
      print(instance.id, instance.instance_type)
      ec2.create_tags(Resources=[instance.id],Tags=[{'Key':'Name','Value':'RenderNodeSetup'}])

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:

         self.ccq = self.sqs.get_queue_by_name(QueueName='mrc_cloud_commands')

         self.createRenderNodeSetup()

         while True:
          statusmessage = "Checking setup status%s" %self.checkCount

          self.emit(SIGNAL('status(QString)'),statusmessage)

          if self.amicheck is False:
           message = self.getMessages()
           if message != None:
            self.checkCount = ".";
            self.emit(SIGNAL('status(QString)'),message)
            if message == "AMI creation initialized.":
             self.amicheck = True;
             self.checkCount = "."
           else:
            self.emit(SIGNAL('status(QString)'),"No status update at this time.")


          else:
           amiState = self.checkAMI("RenderNodeAMI");

           print amiState;
           if amiState=="image not found":
            print("Setup has not started")
            self.emit(SIGNAL('status(QString)'),"AMI setup waiting to start.")

           elif amiState=="pending":
            print("Setup still in progress...")
            self.emit(SIGNAL('status(QString)'),"AMI setup in progress%s" %self.checkCount)

           elif amiState=="failed":
            self.emit(SIGNAL('status(QString)'),"AMI creation failed. Wait a few minutes and click Create Render Node AMI again.")
            self.terminateRenderNodeSetup();

           elif amiState=="available":
            print("Setup complete!")
            self.emit(SIGNAL('status(QString)'),"Setup Complete.")
            self.terminateRenderNodeSetup();
            break

          time.sleep(10)
          self.checkCount += "."


class Window(QMainWindow):

 def __init__(self):
  super(Window,self).__init__()
  self.resize(400,500)
  self.setWindowTitle("Render Cloud Setup::BETA_v097")
  self.centralWidget = QWidget()

  self.sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
  self.sizePolicy.setHorizontalStretch(0)
  self.sizePolicy.setVerticalStretch(0)
  self.layout = QVBoxLayout()
  self.layout.setContentsMargins(0,0,0,0)

  self.setCentralWidget(self.centralWidget)

  self.frozen = False
  if getattr(sys, 'frozen', False):
        # we are running in a bundle
        self.frozen = True
        bundle_dir = sys._MEIPASS
  else:
        # we are running in a normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

  self.keyid = None
  self.secretkey = None
  self.sqs = None
  self.s3 = None
  self.ec2 = None
  self.client = None
  self.modoinstall = None
  self.modoinstallpath = ""
  self.bucketname = None
  self.bucketList = {}
  self.keypair = None
  self.cwd = None
  self.region = None
  self.regions = []
  self.session = None

  self.ccq = None

  self.savepem = True;

  self.amicheck = False;
  self.checkCount = ".";
  self.checkStatus = True;

  self.progMonitor = None ;

  self.renderNode = startupScripts.renderNode()

  self.cloudRenderNodeSetup = startupScripts.cloudRenderNodeSetup()

  self.softwareSetupText = startupScripts.cloudSetupSoftware()

  self.softwareDict = {}
  self.uploadCount = 0;

  self.createRenderNodeActive = False;

  self.stylesheet = """


            QWidget{
   										background-color:rgb(73, 73, 70);
   										font: thin;
   										font-family: Lato;
   										color:rgb(240, 240, 240);
  										}

            QWidget QDialog{
   										background-color:rgb(73, 73, 70);
   										font: thin;
   										font-family: Lato;
   										color:rgb(240, 240, 240);
  										}

  										QMenuBar {
   										background-color:rgb(73, 73, 70);
   										font: thin;
   										font-family: Lato;
   										color:rgb(240, 240, 240);
  										}


  										QMenuBar::item {
   										background-color:rgb(73, 73, 70);
   										font: thin;
   										font-family: Lato;
   										color:rgb(240, 240, 240);
  										}

  										QMenu {
   										background-color:rgb(240, 240, 240);
   										font: thin;
   										font-family: Lato;
   										color:rgb(73, 73, 70);
                                        border: 1px solid white;
                                        left: 25px;
                                        }

  										QMenu::item {
   										background-color:rgb(240, 240, 240);
   										font: thin;
   										font-family: Lato;
   										color:rgb(73, 73, 70);
  										}


            QTabWidget{
            border:0px;
  										}

            QTabWidget QWidget{
            border:0px;
  										}


  										QComboBox{
  										background-color:rgb(120, 120, 120);
    								border: 1px rgb(80, 80, 80);
    								border-style:solid;
    								border: 1px solid rgb(150, 150, 150);
  										}



  										QComboBox::drop-down{
  										border-left: 1px;
  										border-style:solid;
    								border-color:rgb(150, 150, 150);
  										}

  										QComboBox QListView {
  										margin-top:0;
  										padding-top:0;
  										background:white;
  										color:black;

  										}



  										QComboBox QListView::item:!selected {
  										color:black;
  										}


  										QComboBox QListView::item:selected {
  										background-color:rgb(120, 120, 120);
  										color:white;
  										}



  										QTreeView {
  										background-color:rgb(183, 183, 180);
    								border: 1px rgb(80, 80, 80);
    								border-style:solid;
    								margin:-0px;
    								padding:0px;
    								color:rgb(43,43,40);
    								}

  										QHeaderView {
  										background-color:rgb(183, 183, 180);
    								border: 0px rgb(80, 80, 80);
    								border-style:solid;
    								margin:-0px;
    								padding:0px;
    								color:rgb(43,43,40);
    								}

  										QTreeView:item {
    								padding: 0px;
    								}

  										QTreeView QScrollBar:vertical {
  										border: 0px solid green;
  										width: 15px;
  										background:none;
    								}

    								QScrollBar::handle:vertical {
    								background: gray;
    								}

  										QTreeView QScrollBar::add-line:vertical,QTreeView QScrollBar::sub-line:vertical {
  										border: 0px solid rgb(80, 80, 80);
  										background-color:rgb(40, 40, 40);

    								}

  										QTreeView QScrollBar::down-arrow:vertical,QTreeView QScrollBar::up-arrow:vertical {
  										 width:5px;
  										 height:5px;
  										 background:white;
    								}


  										QTreeView:branch {
    								padding: 5px;
    								}

  										QTreeView:item:first {
    								border-top-width:0px ;
    								}

  										QTreeView:item:selected {
    								color:white;
  										background-color:rgb(103, 103, 100);
  										padding-left:0px;
    								}

  										QTreeView:branch:selected {
  										background-color:rgb(103, 103, 100);
    								}

  										QPushButton {
  										background-color:rgb(123, 123, 120);
    								border: 1px solid rgb(150, 150, 150);
    								border-radius:4px;
    								padding: 8px;
    								margin-right:6px;
    								margin-left:6px;
    								}

    								QPushButton:pressed {
    								color:rgb(80,80,80);
  										background-color:rgb(200, 200, 200);
    								}

    								QPushButton:disabled {
    								color:rgb(80,80,80);
  										background-color:rgb(100, 100, 100);
    								border: 1px solid rgb(100, 100, 100);
    								}

    								QTabWidget::tab-bar {
    								/*left: 5px;  move to the right by 5px */
    								}

  										QTabBar::tab {
  										color:rgb(43,43,40);
   									background-color:rgb(123, 123, 120);
    								border-width:1 1 0 1;
    								border-color:rgb(80, 80, 80);
    								border-style:solid;
    								border-top-left-radius: 4px;
    								border-top-right-radius: 4px;
    								padding:5px;
    								margin-top:20px;
  										}

  										QTabBar::tab:selected {
  										margin-left:0px;
  										margin-right:0px;
  										color:rgb(250, 250, 250);
  										border: 1px solid rgb(150, 150, 150);
  										border-bottom-width:3px;
   									border-bottom-color:rgb(56, 100, 120); /* same as pane color */
  										}

  										QTabBar::tab:first:selected {
  										margin-left: 0; /* the first selected tab has nothing to overlap with on the left */
  										}

  										QTabBar::tab:last:selected {
  										margin-right: 0; /* the last selected tab has nothing to overlap with on the right */
  										}

  										QTabBar::tab:!selected {
  										margin-top: 25px; /* make non-selected tabs look smaller */
  										}

  										QStatusBar {
  										color: rgb(250, 250, 250);
  										}

  										"""


  self.setStyleSheet(self.stylesheet);


  self.show()


  self.home()

  #self.t1 = Thread(target=self.home)
  self.t2 = Thread(target=self.sysCheckTimer,args=())
  self.t2.daemon = True

  self.t3 = Thread(target=self.uploadThread,args=())
  self.t3.daemon = True





 def home(self):

  btnFont = QFont()
  btnFont.setPointSize(10);

  headerFont = QFont()
  headerFont.setPointSize(18);

  stepOneLabel = QLabel("Step 1: Enter AWS Credentials")

  selCredBtn = QPushButton("Enter AWS Credentials")
  #selCredBtn.setFixedWidth(190)
  #selCredBtn.clicked.connect(self.selCredFile)
  selCredBtn.clicked.connect(self.credSetup)

  self.createKeyPairBtn = QPushButton("Create Key Pair")
  createKeyPairBtn = self.createKeyPairBtn
  #createKeyPairBtn.setFixedWidth(190)
  createKeyPairBtn.clicked.connect(self.createKeyPair)
  createKeyPairBtn.setDisabled(True);

  stepTwoLabel = QLabel("Step 2: Select Initial Region")

  self.regDropdown = QComboBox()
  regDropdown = self.regDropdown
  #regDropdown.setFixedWidth(150)
  regDropdown.connect(regDropdown, SIGNAL('activated(int)'), self.regionChanged)
  rdlv = QListView()
  self.regDropdown.setView(rdlv)

  stepThreeLabel = QLabel("Step 3: Setup Cloud Structure")

  bucketBtn = QPushButton("Create Root Bucket")
  #bucketBtn.setFixedWidth(190)
  bucketBtn.clicked.connect(self.createRootBucket)

  qBtn = QPushButton("Create Message Queues")
  #qBtn.setFixedWidth(190)
  qBtn.clicked.connect(self.createQueues)

  pBtn = QPushButton("Create Permissions Profile")
  #pBtn.setFixedWidth(190)
  pBtn.clicked.connect(self.createIamRole)


  stepFourLabel = QLabel("Step 4: Select Modo Software Installer(s) (Linux)")

  self.softwareListModel = QStandardItemModel()
  self.softwareListTree =  QTreeView()
  self.softwareListTree.setModel(self.softwareListModel)
  self.softwareListTree.setHeaderHidden(True)


  selModoBtn = QPushButton("Add")
  #selModoBtn.setFixedWidth(190)
  selModoBtn.clicked.connect(self.selModoFile)

  delModoBtn = QPushButton("Remove")
  #selModoBtn.setFixedWidth(190)
  delModoBtn.clicked.connect(self.delModoFile)

  softwareLayout = QHBoxLayout()
  #softwareLayout.addStretch(1)
  softwareLayout.addWidget(selModoBtn)
  softwareLayout.addWidget(delModoBtn)


  stepFiveLabel = QLabel("Step 5: Create Render Node")
  uploadBtn = QPushButton("Upload Setup Files")
  #uploadBtn.setFixedWidth(190)
  uploadBtn.clicked.connect(self.uploadFiles)


  self.uploadStatus = QProgressBar()
  self.uploadStatus.setVisible(0)


  self.creatRNBtn = QPushButton("Create Render Node AMI")
  creatRNBtn = self.creatRNBtn
  #creatRNBtn.setFixedWidth(190)
  creatRNBtn.clicked.connect(self.createRenderNode)
  creatRNBtn.setDisabled(True)

  stepOneLabel.setFont(headerFont)
  stepTwoLabel.setFont(headerFont)
  stepThreeLabel.setFont(headerFont)
  stepFourLabel.setFont(headerFont)
  stepFiveLabel.setFont(headerFont)


  selCredBtn.setFont(btnFont)
  createKeyPairBtn.setFont(btnFont)
  bucketBtn.setFont(btnFont)
  qBtn.setFont(btnFont)
  pBtn.setFont(btnFont)
  uploadBtn.setFont(btnFont)
  selModoBtn.setFont(btnFont)
  delModoBtn.setFont(btnFont)
  creatRNBtn.setFont(btnFont)


  quitbtn = QPushButton("Quit",self)
  quitbtn.clicked.connect(QCoreApplication.instance().quit)

  self.screen01Layout = QVBoxLayout()
  self.screen02Layout = QVBoxLayout()
  self.screen03Layout = QVBoxLayout()
  self.screen04Layout = QVBoxLayout()
  self.screen05Layout = QVBoxLayout()
  self.screen06Layout = QVBoxLayout()

  self.screen01Layout.addStretch(1)
  self.screen01Layout.addWidget(stepOneLabel)
  self.screen01Layout.addWidget(selCredBtn)
  self.screen01Layout.addStretch(1)

  self.screen02Layout.addStretch(1)
  self.screen02Layout.addWidget(stepTwoLabel)
  self.screen02Layout.addWidget(regDropdown)
  self.screen02Layout.addStretch(1)

  self.screen03Layout.addStretch(1)
  self.screen03Layout.addWidget(stepThreeLabel)
  self.screen03Layout.addWidget(bucketBtn)
  self.screen03Layout.addWidget(qBtn)
  self.screen03Layout.addWidget(pBtn)
  self.screen03Layout.addWidget(createKeyPairBtn)
  self.screen03Layout.addStretch(1)

  self.screen04Layout.addStretch(1)
  self.screen04Layout.addWidget(stepFourLabel)
  self.screen04Layout.addWidget(self.softwareListTree)
  self.screen04Layout.addLayout(softwareLayout)
  self.screen04Layout.addStretch(1)

  self.screen05Layout.addStretch(1)
  self.screen05Layout.addWidget(stepFiveLabel)
  self.screen05Layout.addWidget(uploadBtn)
  self.screen05Layout.addWidget(creatRNBtn)
  self.screen05Layout.addWidget(self.uploadStatus)
  self.screen05Layout.addStretch(1)

  self.screen01Widget = QWidget()
  self.screen02Widget = QWidget()
  self.screen03Widget = QWidget()
  self.screen04Widget = QWidget()
  self.screen05Widget = QWidget()

  self.screen01Widget.setLayout(self.screen01Layout)
  self.screen02Widget.setLayout(self.screen02Layout)
  self.screen03Widget.setLayout(self.screen03Layout)
  self.screen04Widget.setLayout(self.screen04Layout)
  self.screen05Widget.setLayout(self.screen05Layout)


  self.screenLayout = QStackedLayout()
  screenLayout = self.screenLayout
  screenLayout.addWidget(self.screen01Widget)
  screenLayout.addWidget(self.screen02Widget)
  screenLayout.addWidget(self.screen03Widget)
  screenLayout.addWidget(self.screen04Widget)
  screenLayout.addWidget(self.screen05Widget)

  centeringLayout = QHBoxLayout()
  centeringLayout.addStretch(1)
  centeringLayout.addLayout(screenLayout)
  centeringLayout.addStretch(1)


  forwardBtn = QPushButton(">>")
  forwardBtn.clicked.connect(self.stepForward)

  backBtn = QPushButton("<<")
  backBtn.clicked.connect(self.stepBack)

  self.stepProgLabel = QLabel('Step')

  navLayout = QHBoxLayout()
  navLayout.addStretch(1)
  navLayout.addWidget(backBtn)
  navLayout.addWidget(self.stepProgLabel)
  navLayout.addWidget(forwardBtn)
  navLayout.addStretch(1)

  centralLayout = QVBoxLayout()
  centralLayout.addLayout(centeringLayout)
  centralLayout.addLayout(navLayout)


  self.centralWidget.setLayout(centralLayout)

  exitAction = QAction('Quit', self)
  exitAction.setShortcut('Ctrl+Q')
  exitAction.setStatusTip('Exit application')
  exitAction.triggered.connect(self.close)

  menubar = self.menuBar()
  fileMenu = menubar.addMenu('&File')
  fileMenu.addAction('Exit',self.close)
  self.setMenuBar(menubar)

#  self.statusBar().showMessage('Ready')

  self.statusBar().showMessage(sys.executable)

  self.checkCredsExist();

  self.screenArr = []

  self.totalScreens = self.screenLayout.count()

  print self.totalScreens

  progmessage = 'Step %s of %s' %(1,self.totalScreens)
  self.stepProgLabel.setText(progmessage)



 def closeEvent(self,event):
  print("closing")
  self.regionEditConfig();
  print(event)


 def stepForward(self):
  print 'Forward'
  currentIndex = self.screenLayout.currentIndex()
  print currentIndex
  if currentIndex<(self.totalScreens-1):
   self.screenLayout.setCurrentIndex(currentIndex+1)
   progmessage = 'Step %s of %s' %(self.screenLayout.currentIndex()+1,self.totalScreens)
   self.stepProgLabel.setText(progmessage)


 def stepBack(self):
  print 'Back'
  currentIndex = self.screenLayout.currentIndex()
  if currentIndex>0:
   self.screenLayout.setCurrentIndex(currentIndex-1)
   progmessage = 'Step %s of %s' %(self.screenLayout.currentIndex()+1,self.totalScreens)
   self.stepProgLabel.setText(progmessage)


 def checkCredsExist(self):
  print("parsing")

  if platform == "linux" or platform == "linux2":
   pass
  elif platform == "darwin":
   # OS X
   abspath = sys.executable
   abspathArray = abspath.split("/")
   abspathArray.pop(-1)
   abspathArray.pop(-1)
   abspathArray.pop(-1)
   abspathArray.pop(-1)
   cwd = "/".join(abspathArray)
   if self.frozen is True:
    os.chdir(cwd)
  elif platform == "win32":
   pass

  cwd = os.getcwd()
  self.cwd = cwd
  print cwd
  credfilepath = cwd+"/Data/creds.txt"

  if os.path.exists(credfilepath):
   print "Creds file exists"
   self.parseCredFile(credfilepath)

 def checkConfigExists(self):
  cwd = self.cwd
  print cwd
  configfilepath = cwd+"/Data/config.txt"
  bucketSetup = False;

  if os.path.exists(configfilepath):
   print "Config file exists"
   self.parseConfig(configfilepath)
  else:
   self.initCloud();


 def parseCredFile(self,credfilepath):
  print("parsing")
  file = open(credfilepath,'r+');
  filecontents = file.read();
  file.close()
  credLinesArray = filecontents.splitlines()

  for cred in credLinesArray:
   credArray = cred.split("=")
   if credArray[0] == "AWSAccessKeyId":
    self.keyid = credArray[1]
    #print self.keyid
   if credArray[0] == "AWSSecretKey":
    self.secretkey = credArray[1]
    #print self.secretkey
   if credArray[0] == "AWSKeyPair":
    self.key = credArray[1]
    #print self.key
  self.checkConfigExists()


 def parseConfig(self,configfilepath):
		print "File exists"
		file = open(configfilepath,'r+');
		filecontents = file.read();
		file.close()
		configLinesArray = filecontents.splitlines()

		for config in configLinesArray:
		 configArray = config.split("=")
		 if configArray[0] == "Buckets" and configArray[1]:
		  print 'Bucket Setup Already Complete'
		  bucketlist = configArray[1].split(",")
		  for b in bucketlist:
		   bArr = b.split(":")
		   self.bucketList[bArr[0]] = bArr[1]



		 if configArray[0] == "Region" and configArray[1]:
			 self.region = configArray[1]
			 print self.region

		if self.bucketList:
		 self.bucketname = self.bucketList[self.region]


		self.initCloud()


 def createKeyPair(self):
  d = keyPairDialog(self)
  d.setStyleSheet(self.stylesheet)
  result = d.exec_()
  if result == True:
   emptyCheck = d.checkFields()
   if len(emptyCheck)>0:
    for check in emptyCheck:
     print check + " field is empty. Please enter information in field."
    self.keyPairDialog()
   else:
    response = self.client.create_key_pair(KeyName=d.keypair.text())
    print 'key pair created'
    self.statusBar().showMessage("Key Pair Created.",5000)

    keyname = response['KeyName']
    keyfile = response['KeyMaterial']

    cwd = self.cwd
    print cwd

    if self.savepem is True:
     pempath = cwd+"/Data/"
     if os.path.exists(pempath):
      pemfilepath = cwd+"/Data/%s.pem" %keyname
      file = open(pemfilepath,'a+');
      file.write("%s" %keyfile)
      file.close()
      os.chmod("%s/Data/%s.pem"%(cwd,keyname),0400)
     else:
      pass

    configfilepath = cwd+"/Data/config.txt"

    if not os.path.exists(configfilepath):
     configfilepath = cwd+"/Data/config.txt"
     file = open(configfilepath,'a+');
     file.write("KeyPair=%s\n" %d.keypair.text())
     file.close()
    else:
  			print "File exists"
  			file = open(configfilepath,'r');
  			lines = file.readlines();
  			file.close()


  			keyExists = False
  			i = 0
  			for line in lines:
  				print line;
  				linearray = line.split("=")
  				if linearray[0] == "KeyPair":
  					lines[i] = "KeyPair=%s\n" %d.keypair.text()
  					keyExists = True
  				i+=1;

  			if keyExists is False:
  			 lines.append("KeyPair=%s\n" %d.keypair.text())


  			file = open(configfilepath,'w');
  			file.writelines(lines);
  			file.close()


 def initCloud(self):
  if self.region == None:
   self.region = 'us-east-1'
  self.session = boto3.Session(region_name=self.region,aws_access_key_id=self.keyid,aws_secret_access_key=self.secretkey)
  self.s3 = self.session.resource('s3')
  self.sqs = self.session.resource('sqs')
  self.client = self.session.client('ec2')
  self.ec2resource = self.session.resource('ec2')
  self.statusBar().showMessage("Credentials Successfully Loaded")
  self.createKeyPairBtn.setDisabled(False)
  self.getRegions();



 def connectCloud(self):
  self.session = boto3.Session(region_name=self.region,aws_access_key_id=self.keyid,aws_secret_access_key=self.secretkey)
  self.s3 = self.session.resource('s3')
  self.sqs = self.session.resource('sqs')
  self.client = self.session.client('ec2')
  self.ec2resource = self.session.resource('ec2')

 def getRegions(self):
	 response = self.client.describe_regions()

	 for region in response["Regions"]:
	  self.regions.append(region['RegionName'])

	 self.regDropdown.addItems(self.regions)

	 regionCount = self.regDropdown.count()
	 for i in range(regionCount):
	  if self.regDropdown.itemText(i) == self.region:
	   self.regDropdown.setCurrentIndex(i)


 def regionChanged(self,index):
  self.region = self.regDropdown.currentText()
  print self.region
  self.connectCloud();



 def sysCheckTimer(self):
  print "sysCheckTimerStarted"
  while self.checkStatus is True:
   self.sysCheck()
   time.sleep(10)
   #self.statusBar().clearMessage();
   self.checkCount += ".";

 def sysCheck(self):
  self.statusBar().showMessage("Checking setup status%s" %self.checkCount)
  if self.amicheck is True:
   amiStatus = self.checkRNodeSetup();
   if amiStatus == "not started":
    print "not started"
   elif amiStatus == "in progress":
    print "in progress";
    self.statusBar().showMessage("AMI setup in progress%s" %self.checkCount)
   elif amiStatus == "failed":
    print 'failed'
    self.statusBar().showMessage("AMI creation failed. Wait a few minutes and click Create Render Node AMI again.");
   elif amiStatus == "complete":
    print "complete";
    self.checkStatus = False;
  else:
   message = self.getMessages()
   if message != None:
    self.checkCount = ".";
    self.statusBar().showMessage(message)
    if message == "AMI creation initialized.":
     self.amicheck = True;
     self.checkCount = "."
   else:
    self.statusBar().showMessage("No status update at this time.")



 def getMessages(self):
  messages = self.ccq.receive_messages(MaxNumberOfMessages=10,WaitTimeSeconds=3);
  if len(messages) > 0:
   print len(messages)
   for message in messages:
    m = message.body
    print("message there");
    print m
    message.delete();
    #self.processMessage(messageInfo)
    return m
  else:
   return None


 def selModoFile(self):
  print 'select file'
  dialog = QFileDialog()
  dialog.setFileMode(QFileDialog.AnyFile)
  dir = QDir(os.getcwd())
  fname, _ = dialog.getOpenFileName()
  print(fname)
  destLoc = ""
  fnameArray = fname.split("/")
  self.modoinstall = fnameArray[-1]
  self.modoinstallpath = fname
  treeRoot = self.softwareListModel.invisibleRootItem()
  software = QStandardItem(self.modoinstall)
  self.softwareDict[self.modoinstall] = fname
  treeRoot.appendRow(software)
  self.softwareListTree.resizeColumnToContents(0)
  print self.softwareDict
  self.statusBar().showMessage("Modo Install File Selected.")

 def delModoFile(self):
  print 'remove file'
  selIndexes= self.softwareListTree.selectedIndexes()
  for index in selIndexes:
   item = index.model().itemFromIndex(index)
   itemText = item.text()
   del self.softwareDict[itemText]
   parent = self.softwareListModel.parent(index)
   self.softwareListModel.removeRow(index.row(),parent)

  print self.softwareDict
  self.statusBar().showMessage("Modo Install File Removed.")



 def setupCloud(self):
  self.createRootBucket()
  self.createQueues();
  self.createIamRole();



 def createRootBucket(self):
  print('set up cloud')
  if self.bucketname == None and self.keyid != None:
			reply = QInputDialog.getText(self, "Create Root Folder","Enter Root Folder Name:")
			if reply[1]:
				bucketname = "%s--%s" %(reply[0],self.region)
				print(bucketname)
				try:
				 s3Resource = self.session.resource('s3',self.region);
				 newbucket = s3Resource.Bucket(bucketname)
				 if self.region == "us-east-1":
				  response = newbucket.create(bucketname)
				 else:
				  response = newbucket.create(bucketname,CreateBucketConfiguration={'LocationConstraint': self.region})
				except botocore.exceptions.ClientError as e:
					print("Bucket cannot be created please try another name",5000)
					print e;
					self.statusBar().showMessage("Bucket cannot be created please try another name.",5000)
					self.createRootBucket()
				else:
				 self.bucketname = bucketname
				 cwd = self.cwd
				 print cwd
				 configfilepath = cwd+"/Data/config.txt"
				 file = open(configfilepath,'a+');
				 file.write('Buckets=%s:%s\n' %(self.region,bucketname))
				 file.close()
				 self.statusBar().showMessage("Storage bucket successfully completed.",5000)
			else:
			 return


 def createIamRole(self):
  name = 'RenderNode'
  client = self.session.client('iam')

  #there has to be a instance profile for an ec2 to use iam roles
  #this script's order is: create role, then create profile, then attach role to profile

  rolepolicydata = {"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":["ec2.amazonaws.com"]},"Action":["sts:AssumeRole"]}]}

  json_rolepolicy = json.dumps(rolepolicydata)

  roleresponse = client.create_role(RoleName=name,AssumeRolePolicyDocument=json_rolepolicy)

  ec2policyresponse = client.attach_role_policy(RoleName=name,PolicyArn='arn:aws:iam::aws:policy/AmazonEC2FullAccess')
  s3policyresponse = client.attach_role_policy(RoleName=name,PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess')
  sqspolicyresponse = client.attach_role_policy(RoleName=name,PolicyArn='arn:aws:iam::aws:policy/AmazonSQSFullAccess')

  profileresponse = client.create_instance_profile(
      InstanceProfileName=name)

  attachresponse = client.add_role_to_instance_profile(
      InstanceProfileName=name,
      RoleName=name
  )
  self.statusBar().showMessage("Permissions role created successfully.",5000)

 def createQueues(self):
  try:
   self.sqs.create_queue(QueueName="mrc_cloud_commands", Attributes={'DelaySeconds': '0'})
  except botocore.exceptions.ClientError as e:
   print e
  except botocore.exceptions.EndpointConnectionError as e:
   pass
  else:
   self.ccq = self.sqs.get_queue_by_name(QueueName='mrc_cloud_commands')
   self.statusBar().showMessage("Message queues created successfully.",5000)

 def uploadThread(self):
  s3 = self.s3
  bucketname = self.bucketname
  bucketnameprefix = self.bucketname.split("--")[0]
  keypair = self.keypair

  newfilecontents = self.renderNode.replace("*bucketnamepointer",bucketnameprefix)
  uploadName = 'renderNode.py'
  s3.Object(bucketname, uploadName).put(Body=newfilecontents)
  sDict = self.softwareDict

  for soft in sDict:
   key = soft
   filename = soft
   file = sDict[soft]
   self.progMonitor = ProgressPercentage(file)
   s3 = self.session.client('s3')
   transfer = S3Transfer(s3)
   print filename
   thread = Thread(target=self.uploadMonitorThread,args=(filename,))
   thread.daemon = True
   thread.start()
   transfer.upload_file(file, bucketname, key, callback=self.progMonitor)

 def uploadMonitorThread(self,filename):
   while self.progMonitor.percentage < 100:
    #print self.progMonitor.percentage
    self.statusBar().showMessage("%s File Upload %.2f %% complete" %(filename,self.progMonitor.percentage))
    time.sleep(.3)
   print("files uploaded")
   self.statusBar().showMessage("Setup files successfully uploaded.")
   self.uploadCount+=1;
   if len(self.softwareDict) == self.uploadCount:
    self.creatRNBtn.setDisabled(False)


 def uploadFiles(self):
  setupDir=self.cwd
  s3 = self.s3
  bucketname = self.bucketname
  keypair = self.keypair

  if bucketname != "" and keypair != "" and self.modoinstall != None:
   self.softwareAppendConfig();
   self.t3.start();
  else:
   print("variables not set")
   self.statusBar().showMessage("Upload Cancelled.Make sure credentials, storage setup, and Modo installer selection are complete.",5000)

 def softwareAppendConfig(self):
  cwd = self.cwd
  print cwd
  configfilepath = cwd+"/Data/config.txt"

  if os.path.exists(configfilepath):
  	print "Config file exists"
  	softwareString = "Software="
  	softwareList=[]
  	sDict = self.softwareDict
  	for item in sDict:
  	 softwareList.append(item[:-4])
  	softwareString += ",".join(softwareList)
  	file = open(configfilepath,'a+');
  	file.write(softwareString+"\n")
  	file.close()

 def regionEditConfig(self):
  cwd = self.cwd
  print cwd
  configfilepath = cwd+"/Data/config.txt"

  if os.path.exists(configfilepath):
			print "File exists"
			file = open(configfilepath,'r');
			lines = file.readlines();
			file.close()
			regExists = False
			aregsExists = False

			i = 0
			for line in lines:
				print line;
				linearray = line.split("=")
				if linearray[0] == "Region":
					lines[i] = "Region=%s\n" %self.region
					regExists = True

				if linearray[0] == "ActiveRegions":
				 lines[i] = "ActiveRegions=%s\n" %self.region
				 aregsExists = True

				i+=1;

			if regExists is False:
			 lines.append("Region=%s\n" %self.region)

			if aregsExists is False:
			 lines.append("ActiveRegions=%s\n" %self.region)

			file = open(configfilepath,'w');
			file.writelines(lines);
			file.close()

 def checkAMI(self,amiName):
  response = self.client.describe_images(Filters=[{'Name':'name','Values':[amiName]}])
  imageList = response['Images']

  if len(imageList)>0:
   for image in imageList:
    #print image['ImageId']
    #print image['State']
    if image['State'] == 'pending':
     return 'pending'
    if image['State'] == 'available':
     return 'available'
  else:
   return 'image not found'


 def prepSoftwareText(self):
  softwareText = self.softwareSetupText

  newSoftware = ""
  sDict = self.softwareDict

  for soft in sDict:
   softName = soft[:-4]
   print soft
   print softName
   newSoftware += softwareText.replace("*modoinstall",soft).replace("*bucketname",self.bucketname).replace("*modoname",softName)



  print newSoftware

  print "==========================="
  setupText = self.cloudRenderNodeSetup.replace("*bucketname",self.bucketname).replace("*region",self.region).replace("*softwareinstall",newSoftware)

  print setupText
  return setupText

 def createAMI(self):
  print 'create AMI'
  self.uploadFiles()

 def createRenderNode(self):
  if self.createRenderNodeActive is False:
   createRenderNodeThread = Thread(target=self.createRenderNodeThread,args=())
   createRenderNodeThread.daemon = True
   createRenderNodeThread.start();
   self.createRenderNodeActive = True;
  else:
   self.statusBar().showMessage('Render node creation was already started.')


 def createRenderNodeThread(self):
  setupText = self.prepSoftwareText()
  createrendernode = createRenderNodeObject(self.session,setupText)
  createrendernode.status.connect(self.createRenderNodeUpdate)
  createrendernode()

 def createRenderNodeUpdate(self,status):
  print status
  self.statusBar().showMessage(status)




 def credSetup(self):

  d = credDialog(self)
  result = d.exec_()
  if result == True:
   emptyCheck = d.checkFields()
   if len(emptyCheck)>0:
    for check in emptyCheck:
     print check + " field is empty. Please enter information in field."
    self.credDialog()
   else:
    cwd = self.cwd
    print cwd

    creddir = cwd+"/Data/"

    if not os.path.exists(creddir):
     os.makedirs(creddir)

    credfilepath = creddir+"creds.txt"

    if os.path.exists(credfilepath):
     print "File exists"
    else:
     filecontents = "AWSAccessKeyId=%s\n"%d.keyid.text()
     filecontents += "AWSSecretKey=%s\n"%d.secretkey.text()

     file = open(credfilepath, 'w')
     file.write(filecontents)
     file.close()
     self.checkCredsExist()

class credDialog(QDialog):
 def __init__(self, parent = None):
				super(credDialog, self).__init__(parent)

				self.setWindowTitle("Enter AWS Info")

				layout = QVBoxLayout(self)

				self.keyidlabel = QLabel("Enter Key ID")
				self.keyid = QLineEdit()

				keyIDLayout = QHBoxLayout()
				keyIDLayout.addWidget(self.keyidlabel)
				keyIDLayout.addWidget(self.keyid)

				self.secretkeylabel = QLabel("Enter Secret Key")
				self.secretkey = QLineEdit()

				secretKeyLayout = QHBoxLayout()
				secretKeyLayout.addWidget(self.secretkeylabel)
				secretKeyLayout.addWidget(self.secretkey)

				layout.addLayout(keyIDLayout)
				layout.addLayout(secretKeyLayout)


				# OK and Cancel buttons
				buttons = QDialogButtonBox(
								QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
								Qt.Horizontal, self)
				buttons.accepted.connect(self.accept)
				buttons.rejected.connect(self.reject)
				layout.addWidget(buttons)

 def checkFields(self):
  emptyFields = []

  if self.keyid.text() == "":
   emptyFields.append("Key ID")

  if self.secretkey.text() == "":
   emptyFields.append("Secret Key")


  return emptyFields

class keyPairDialog(QDialog):
 def __init__(self, parent = None):
				super(keyPairDialog, self).__init__(parent)

				self.setWindowTitle("Create Key Pair")

				layout = QVBoxLayout(self)

				self.keypairlabel = QLabel("Enter Key Pair Name")
				self.keypair = QLineEdit()

				keyPairLayout = QHBoxLayout()
				keyPairLayout.addWidget(self.keypairlabel)
				keyPairLayout.addWidget(self.keypair)

				layout.addLayout(keyPairLayout)

				# OK and Cancel buttons
				buttons = QDialogButtonBox(
								QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
								Qt.Horizontal, self)
				buttons.accepted.connect(self.accept)
				buttons.rejected.connect(self.reject)
				layout.addWidget(buttons)

 def checkFields(self):
  emptyFields = []

  if self.keypair.text() == "":
   emptyFields.append("Key Pair")

  return emptyFields

def run():
 app = QApplication(sys.argv)
 GUI = Window()
 sys.exit(app.exec_())

run()
