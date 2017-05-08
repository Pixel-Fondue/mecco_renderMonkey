#!/usr/bin/python

import sys
import os
import boto3
import botocore
import ConfigParser
import mrcConn_v097

from PySide.QtGui import *
from PySide.QtCore import *

import thread
from threading import Thread
import threading
from time import time
import time


import submitRenderJobWindow_v097
import launchSpotInstanceWindow_v097
import launchInstanceWindow_v097



class UploadPercentage(QObject):
    def __init__(self, filename):
        QObject.__init__(self)
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0.0
        self._lock = threading.Lock()
        self.percentage = 0.0
        fileArray = filename.split("/")
        self.file = fileArray[-1]
        print str(filename + " upload started")

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            self.percentage = (self._seen_so_far / self._size) * 100
            progress = str(self.file + " upload progress: %.2f%%" %self.percentage)
            self.emit(SIGNAL('progress(QString)'),progress)

            #sys.stdout.write("\r%s  %s / %s  (%.2f%%)" % (self._filename, self._seen_so_far, self._size,self.percentage))
            #sys.stdout.flush()

class DownloadPercentage(QObject):
    def __init__(self, key,keysize):
        QObject.__init__(self)
        self._filename = key
        self._size = keysize
        self._seen_so_far = 0.0
        self._lock = threading.Lock()
        self.percentage = 0.0
        fileArray = self._filename.split("/")
        self.file = fileArray[-1]
        print str(self._filename + " download started")

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            self.percentage = (self._seen_so_far / self._size) * 100
            progress = str(self.file + " download progress: %.2f%%" %self.percentage)
            if self.percentage == 100:
             progress = str(self.file + " downloaded.")
             self.emit(SIGNAL('progress(QString)'),progress)
            sys.stdout.write("\r%s  %s / %s  (%.2f%%)" % (self._filename, self._seen_so_far, self._size,self.percentage))
            sys.stdout.flush()


class CopyImageStatus(QObject):
    def __init__(self,region,keyid,secretkey,newAMI):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.monitortick = ""
        self.session = boto3.Session(region_name=region,aws_access_key_id=keyid,aws_secret_access_key=secretkey)
        self.ec2Client = self.session.client('ec2')
        self.ec2resource = self.session.resource('ec2')
        self.ami = self.ec2resource.Image(newAMI)

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         statusmessage = "Region activation pending..."
         self.monitortick += "."
         response = self.ec2Client.describe_images(Filters=[{'Name':'name','Values':['RenderNodeAMI']}])
         if len(response["Images"]) > 0:
          for image in response["Images"]:
           print image["State"]
           status = image["State"]
           statusmessage = "AMI copy in progress%s" %self.monitortick
         else:
          if len(self.ami.block_device_mappings) == 0:
           statusmessage = 'Waiting for snapshot creation.'
           status = "pending"
          else:
           response = self.ec2Client.describe_snapshots(Filters=[{'Name':'status','Values':['pending']}])
           if len(response['Snapshots'])>0:
            status = "pending"
            statusmessage = "Snapshot copy in progress"
         self.emit(SIGNAL('status(QString)'),statusmessage)
         return status


class checkJobs(QObject):
    jobs = Signal(object)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         joblist = self.cloud.checkJobs();
         if joblist != None:
          for job in joblist:
           self.jobs.emit(job)
          #return status

class updateQueueObject(QObject):
    complete = Signal(str,str,str,str,str)
    message = Signal(str)
    download = Signal(str,str)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud


    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         print("update")
         cloud = self.cloud
         cloud.updateJobs()
         q = cloud.renderQueue

         print "render queue has %s jobs" %len(q)

         if len(q)>0:
          cloud.sendFrames()
          for j in q.keys():
           #row = q[j].treeRow
           if j in q.keys():
            print q[j].rendering
            if q[j].rendering == True:

             if q[j].newFrame == True:
              framesComplete = str(q[j].framesComplete)
              totalFrames = str(q[j].totalFrames)
              lastFrame = str(q[j].lastFrame)
              lastFrameTime = str(q[j].lastFrameTime)
              jobID = str(q[j].id)
              self.complete.emit(totalFrames,framesComplete,lastFrame,lastFrameTime,jobID)

              if cloud.localDirectory != None:
               fileList = q[j].lastRenderFile.split(",")
               for filename in fileList:
                filepath = "job-"+jobID+"_renderframes/"+filename
                key = cloud.currentProject+"/"+filepath
                self.download.emit(key,filepath)
              q[j].newFrame = False;

              if framesComplete == totalFrames:
               q[j].rendering = False;

             else:
              self.message.emit("No new frames complete.")


class submitRenderJob(QObject):
    job = Signal(object)
    status = Signal(str)
    def __init__(self,cloud,file,frames,project,output,layers,depth,rdet,software,passes,passName):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud
        self.file = file
        self.frames = frames
        self.project = project
        self.output = output
        self.layers = layers
        self.depth = depth
        self.rdet = rdet
        self.software = software
        self.passes = passes
        self.passName = passName

    def sendFrames(self):
     if len(self.cloud.instanceList)>0: #if there are running instances
      for inst in self.cloud.instanceList: #loop through the instance list
       if len(self.cloud.renderFramesList)>0: #if there are frames to render
        if inst['rendering']==False: #then if the instance is not currently rendering
         if inst['active'] == True: #and if the instance is marked active, then send a render frame command
          q = inst['squeue']
          frame = self.cloud.renderFramesList.pop();
          self.cloud.sendFrame(q,frame)

          inst['rendering'] = True;

          status = 'Sent frame %s to instance: %s' %(frame.frameNum,inst['id'])
          self.status.emit(status)
          time.sleep(.2)

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         job = self.cloud.submitJob(self.file,self.frames,self.project,self.output,self.layers,self.depth,self.rdet,self.software,self.passes,self.passName)
         self.job.emit(job)
         self.sendFrames();
         #self.cloud.sendFrames()
          #return status

class clearFilesObject(QObject):
    complete = Signal(str)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud

    def clearFiles(self,fileList):
     if len(fileList)>0:
      fileListString = ",".join(fileList);
      for inst in self.cloud.instanceList:
       if inst['rendering']==False:
        q = inst['squeue']
        message = "Type:cmd\n"
        message += "Cmd:clearFile\n"
        message += "Args:%s" %fileListString
        q.send_message(MessageBody=message)
        status = 'Sending clear file command to node: %s' %inst['id']
        print 'Sending clear file command to node: %s' %inst['id']
       else:
        status = 'Instance:%s is busy. Command not sent.' %inst['id']
        print 'Instance:%s is busy. Command not sent.' %inst['id']

       self.complete.emit(status)


    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         tempList = self.cloud.projectFileList
         fileList = []
         for file in tempList:
          filepath = "%s/%s" %(self.cloud.currentProject,file)
          fileList.append(filepath)

         #clear = self.cloud.clearFiles(fileList)

         self.clearFiles(fileList)

         self.cloud.cloudRunning = True

         #if clear is True:
          #message = "Clear files command sent."
          #self.complete.emit(message)

class clearProjectObject(QObject):
    complete = Signal(str)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud

    def clearProject(self,project):
     if project != None:
      for inst in self.cloud.instanceList:
       print "======&&&&&&&&&&========"
       if inst['rendering']==False:
        q = inst['squeue']
        message = "Type:cmd\n"
        message += "Cmd:clearProject\n"
        message += "Args:%s" %project
        q.send_message(MessageBody=message)
        status = 'Sending clear project command to node: %s' %inst['id']
        print 'Sending clear project command to node: %s' %inst['id']
       else:
        status = 'Instance:%s is busy. Command not sent.' %inst['id']
        print 'Instance:%s is busy. Command not sent.' %inst['id']

       self.complete.emit(status)


    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         project = self.cloud.currentProject
         self.clearProject(project)

         self.cloud.cloudRunning = True;
#         clear = self.cloud.clearProject(project)

#         if clear is True:
#          message = "Clear project command sent."
#          self.complete.emit(message)



class getMessagesObject(QObject):
    complete = Signal(str,str,str,str,str)
    status = Signal(str)
    download = Signal(str,str)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud

    def sendFrames(self):
     if len(self.cloud.instanceList)>0: #if there are running instances
      for inst in self.cloud.instanceList: #loop through the instance list
       if len(self.cloud.renderFramesList)>0: #if there are frames to render
        if inst['rendering']==False: #then if the instance is not currently rendering
         if inst['active'] == True: #and if the instance is marked active, then send a render frame command
          q = inst['squeue']
          frame = self.cloud.renderFramesList.pop();
          self.cloud.sendFrame(q,frame)
          inst['rendering'] = True;

          status = 'Sent frame %s to instance: %s' %(frame.frameNum,inst['id'])
          self.status.emit(status)
          time.sleep(.2)

    def processMessage(self,msg):
     if msg['Type'] == "complete":
      id = msg['id']
      inst = msg['inst']
      inst['rendering'] = False;

      if inst['markedinactive']==True:
       inst['active'] = False;
       status = 'Instance : %s inactive.' %inst['id']

      q = self.cloud.renderQueue

      print msg

      try:
       job = q[id]
      except KeyError as e:
       print 'error is %s' %e
       return

      print "total frames = %s" %job.totalFrames
      print "frames complete = %s" %job.framesComplete
      job.newFrame = True;
      #update jobs frameList and frames complete
      frame = int(msg['Frame'])
      job.lastFrame = int(msg['Frame'])
      job.lastFrameTime = msg['Time']
      job.lastRenderFile = msg['FileList']
      print "Frame %s Complete!" %msg['Frame']
      print "Frame %s Render Time : %s" %(msg['Frame'],msg['Time'])
      job.framesComplete +=1
      job.frameList[frame].complete = True
      job.frameList[frame].renderTime = job.lastFrameTime;
      print "%s frames out of %s frames complete." %(job.framesComplete,job.totalFrames)

      if job.framesComplete == job.totalFrames:
       job.rendering = False;


      if self.cloud.localDirectory != None:
       fileList = job.lastRenderFile.split(",")
       for filename in fileList:
        filepath = "job-"+job.id+"_renderframes/"+filename
        key = self.cloud.currentProject+"/"+filepath
        self.download.emit(key,filepath)
        job.newFrame = False;

      totalFrames = str(job.totalFrames)
      framesComplete = str(job.framesComplete)
      lastFrame = str(job.lastFrame)
      lastFrameTime = str(job.lastFrameTime)
      jobID = job.id

      self.complete.emit(totalFrames,framesComplete,lastFrame,lastFrameTime,jobID)
      time.sleep(1)

      if len(self.cloud.renderFramesList)>0:
       #self.cloud.sendFrames()
       self.sendFrames()


     if msg['Type'] == 'status':
      #send progress message to local?
       print "Instance %s Status: %s" %(msg['instId'],msg['Status'])
       status = "Instance %s Status: %s" %(msg['instId'],msg['Status'])
       self.status.emit(status)

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         messages = self.cloud.getMessages()

         for msg in messages:
          self.processMessage(msg)
          time.sleep(1)




class launchInstancesObject(QObject):
    complete = Signal()
    updatetree = Signal(object)
    def __init__(self,cloud,count,ami,cpu,size,alarm):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud
        self.count = count
        self.ami = ami
        self.cpu = cpu
        self.size = size
        self.alarm = alarm

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         instList = self.cloud.launchInstances(self.count,self.ami,self.cpu,self.size,self.alarm)

         for instInfo in instList:
          #self.complete.emit()
          self.updatetree.emit(instInfo)

class launchSpotInstancesObject(QObject):
    complete = Signal()
    updatetree = Signal(object)
    def __init__(self,cloud,cost,count,ami,cpu,size,alarm):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud
        self.cost = cost
        self.count = count
        self.ami = ami
        self.cpu = cpu
        self.size = size
        self.alarm = alarm

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         spotRequestList = self.cloud.launchSpotInstances(self.cost,self.count,self.ami,self.cpu,self.size,self.alarm)
         #self.complete.emit()
         for spotInfo in spotRequestList:
          self.updatetree.emit(spotInfo)
          #return status

class terminateInstances(QObject):
    complete = Signal(bool)
    def __init__(self,cloud,compList,spotList):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud
        self.compList = compList
        self.spotList = spotList

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         self.cloud.terminateInstances(self.compList)
         self.cloud.cancelSpotRequests(self.spotList)
         self.complete.emit(False)
          #return status

class checkSpotRequestsObject(QObject):
    complete = Signal()
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         self.cloud.getSpotRequests()
         self.complete.emit()
          #return status

class initFarmTreeObject(QObject):
    add = Signal(dict)
    remove = Signal(dict)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         spots = self.cloud.getSpotRequests()
         instances = self.cloud.getInstances()
         if instances:
          for inst in instances:
           instInfo = inst
           self.add.emit(instInfo)
         if spots:
          for spot in spots:
           spotInfo = spot
           self.add.emit(spotInfo)

         self.cloud.cleanUpAlarms()


class updateFarmTreeObject(QObject):
    add = Signal(dict)
    remove = Signal(dict)
    update = Signal(dict)
    def __init__(self,cloud,instList,spotList,spotsOnly):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud
        self.instList = instList
        self.spotList = spotList
        self.spotsOnly = spotsOnly

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         spotcount = len(self.spotList)
         for spotid in self.spotList:
          spotInfo = self.cloud.getSpotRequestInfo(spotid)
          print spotInfo
          state = spotInfo['state']
          if state == 'active':
           newinstid = spotInfo['id']
           alarm = spotInfo['alarm']
           self.remove.emit(spotid)
           instInfo = self.cloud.initSpotInstance(newinstid,alarm)
           self.add.emit(instInfo)
           spotcount -= 1;

         if spotcount == 0:
          self.cloud.spotRequests = False;

         if self.spotsOnly is False:
          self.cloud.updateInstancesInfo(self.instList)

          for inst in self.instList:
           for instInfo in self.cloud.instanceList:
            if instInfo['id'] == inst:
             self.update.emit(instInfo);




class cloudConnect(QObject):
    cc = Signal(bool)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         if self.cloud.credValidate is True:
          self.cloud.connectCloud();
          if self.cloud.cloudConnect == True:
           self.cc.emit(True)
          else:
           self.cc.emit(False)
         else:
          self.cc.emit(False)
           #return status


class getProjItemsObject(QObject):
    items = Signal(object)
    deletecomplete = Signal(bool)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         dir = self.cloud.currentProject
         self.cloud.getCurrentProjectItems(dir)
         allCloudObjs = self.cloud.currentProjectItems
         self.items.emit(allCloudObjs);


class deleteCloudFiles(QObject):
    delete = Signal(str)
    deletecomplete = Signal(bool)
    def __init__(self,cloud,fileList):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud
        self.fileList = fileList
        self.totalFiles = len(fileList)

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         print("delete cloud Files")
         dir = self.cloud.currentProject+"/"
         bucket = self.cloud.s3.Bucket(self.cloud.bucketname)
         cloudFiles = bucket.objects.filter(Prefix=dir)
         i = 0;
         for file in self.fileList:
          filename = file;
          for cFile in cloudFiles:
           keystring = str(cFile.key)
           tempArray = keystring.split("/")
           if tempArray[-1]==filename:
            cFile.delete()
            i+=1;
            currentFileCount = str(i)
            totalFileCount = str(self.totalFiles)
            #print currentFileCount
            #print totalFileCount
            #print filename
            message = "File %s deleted.......%s of %s files." % (filename,currentFileCount,totalFileCount)
            print message
            self.delete.emit(message);
            break

         self.deletecomplete.emit(True);


class createCloudProjectObject(QObject):
    createcomplete = Signal(str)
    def __init__(self,cloud,projName):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud
        self.projName = projName

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         projName = self.projName
         cloud = self.cloud
         cloud.currentProject = projName
         cloud.projects = []
         cloud.createProject(projName);
         cloud.populateProjectsList()
         projList = cloud.projects #gets cloud projects
         print("projList = %s" %projList)
         self.createcomplete.emit(projName)


class deleteCloudProjectObject(QObject):
    deletecomplete = Signal(str)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         print "proceed with delete"
         projName = self.cloud.currentProject
         self.cloud.deleteProject()
         self.deletecomplete.emit(projName)

class ScanRegion(QObject):
    regionstatus = Signal(bool,str,bool,str,str,bool,str)
    def __init__(self,region,cloud,key,keyid,secretkey):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.region = region
        self.cloud = cloud
        self.key = key
        self.monitortick = ""
        self.session = boto3.Session(region_name=self.region,aws_access_key_id=keyid,aws_secret_access_key=secretkey)
        self.client = self.session.client('ec2')
        self.s3Client = self.session.client('s3')

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         response = self.client.describe_images(Filters=[{'Name':'name','Values':['RenderNodeAMI']}])
         imageList = response["Images"]
         if len(imageList)>0:
          imagestatus = True
          image = imageList[0]["ImageId"]
         else:
          imagestatus = False
          image = None

         response = self.client.describe_key_pairs(Filters=[{'Name':'key-name','Values':[self.key]}])
         keyList = response['KeyPairs']
         if len(keyList)>0:
          keystatus = True
          key = keyList[0]['KeyName']
         else:
          keystatus = False
          key = None

         response = self.s3Client.list_buckets()
         bucketnameList = []
         bucketname = "%s--%s" %(self.cloud.bucketname.split("--")[0],self.region)
         print bucketname

         if self.region in self.cloud.bucketList:
          bucketstatus = True
          bucket = self.cloud.bucketList[self.region]
         else:
          bucketstatus = False
          bucket = bucketname
#===============
#          if len(response['Buckets'])>0:
#           for bucket in response['Buckets']:
#            print bucket['Name']
#            bucketnameList.append(bucket['Name'])
#
#          if bucketname in bucketnameList:
#           print 'bucket exists.'
#           bucketstatus = True;
#           bucket = bucketname
#          else:
#           print 'bucket does not exist.'
#           bucketstatus = False;
#           bucket = bucketname
#==================

         self.regionstatus.emit(imagestatus,image,keystatus,key,self.region,bucketstatus,bucket)

class createBucketObject(QObject):
    bucketstatus = Signal(bool,str,str)
    def __init__(self,cloud,region,newbucketname):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.region = region
        self.cloud = cloud
        self.newbucketname = newbucketname

    def __call__(self):
        print 'create bucket %s' %self.newbucketname
        print self.region
        s3Resource = self.cloud.session.resource('s3',self.region);
        try:
         newbucket = s3Resource.Bucket(self.newbucketname)
         if self.region == "us-east-1":
          response = newbucket.create(newbucket)
         else:
          response = newbucket.create(newbucket,CreateBucketConfiguration={'LocationConstraint': self.region})
         print 'New Bucket Created'
         bucketstatus = True
         self.bucketstatus.emit(bucketstatus,self.newbucketname,self.region)
        except botocore.exceptions.ClientError as e:
         print e
         print("Bucket cannot be created please try another name")
         bucketstatus = False
         self.bucketstatus.emit(bucketstatus,self.newbucketname,self.region)



class initRegionsObject(QObject):
    activeregion = Signal(str)
    def __init__(self,cloud):
        QObject.__init__(self)
        self._lock = threading.Lock()
        self.cloud = cloud
        self.regions = self.cloud.regions
        self.key = self.cloud.key
        self.keyid = self.cloud.keyid
        self.secretkey = self.cloud.secretkey

    def __call__(self):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
         for region in self.regions:
          self.session = boto3.Session(region_name=region,aws_access_key_id=self.keyid,aws_secret_access_key=self.secretkey)
          self.client = self.session.client('ec2')

          response = self.client.describe_images(Filters=[{'Name':'name','Values':['RenderNodeAMI']}])
          imageList = response["Images"]
          if len(imageList)>0:
           imagestatus = True
          else:
           imagestatus = False

          response = self.client.describe_key_pairs(Filters=[{'Name':'key-name','Values':[self.key]}])
          keyList = response['KeyPairs']
          if len(keyList)>0:
           keystatus = True
          else:
           keystatus = False

          if (imagestatus is True) and (keystatus is True):
           self.activeregion.emit(region)



class Window(QMainWindow):

 def __init__(self):
  super(Window,self).__init__()
  self.resize(1200,600)
  self.setWindowTitle("Render Cloud::BETA_v097")

  exitAction = QAction('Quit', self)
  exitAction.setShortcut('Ctrl+Q')
  exitAction.setStatusTip('Exit application')
  exitAction.triggered.connect(self.close)


  menubar = self.menuBar()
  self.fileMenu = menubar.addMenu('&File')
  fileMenu = self.fileMenu
  fileMenu.addAction('Exit',self.close)
  self.setMenuBar(menubar)

  self.statusBar().showMessage('Initializing',5000)

  self.home()



 def home(self):


  #SMALL BUTTON STYLE

  smallBtnFont = QFont()
  smallBtnFont.setPointSize(8)

  #MANAGE FILE GUI ELEMENTS
  model = QFileSystemModel()
  self.localProjDirModel = QFileSystemModel()

  sfLabel = QLabel()
  sfLabel.setText("Select Files To Upload")

  setDirBtn = QPushButton("Set Directory")
  setDirBtn.setFixedWidth(110)
  setDirBtn.clicked.connect(self.setLocalProjectDir)

  localLabel = QLabel("Local Files")
  cloudLabel = QLabel("Cloud Files")
  projectLabel = QLabel("Project:")

  self.dirDropdown = QComboBox()
  dirDropdown = self.dirDropdown
  dirDropdown.setFixedWidth(150)
  dirDropdown.connect(dirDropdown, SIGNAL('currentIndexChanged(int)'), self.projListChanged)
  #dirDropdown.setContentsMargins(0,0,0,0)

  ddlv = QListView()
  dirDropdown.setView(ddlv)

  updateDirBtn = QPushButton("UPDATE")
  #updateDirBtn.setFixedWidth(110)
  updateDirBtn.setFont(smallBtnFont)
  updateDirBtn.clicked.connect(self.populateCloudTree)
  updateDirBtn.setContentsMargins(0,0,0,0)


  createProjBtn = QPushButton("Create Project")
  createProjBtn.setFixedWidth(110)
  createProjBtn.clicked.connect(self.createProject)

  deleteProjBtn = QPushButton("Delete Project")
  deleteProjBtn.setFixedWidth(110)
  deleteProjBtn.clicked.connect(self.deleteProject)

  deleteSelBtn = QPushButton("Delete Selected")
  deleteSelBtn.clicked.connect(self.deleteCloudFiles)

  self.localProjTree =  QTreeView()
  self.localProjTree.setModel(self.localProjDirModel)
  self.localProjTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
  header = self.localProjTree.header()
  header.setResizeMode(QHeaderView.ResizeToContents)
  self.localProjTree.setFocusPolicy(Qt.NoFocus)


  self.cloudProjTree =  QTreeView()
  cloudProjTree = self.cloudProjTree
  self.cloudProjTreemodel = QStandardItemModel()
  cloudProjTree.setModel(self.cloudProjTreemodel)
  cloudProjTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
  cloudProjTree.isHeaderHidden = 1
  cloudProjTree.setColumnHidden(1, True)
  cloudProjTree.setColumnHidden(2, True)
  cloudProjTree.setContentsMargins(0,0,0,0)
  cloudProjTree.setFocusPolicy(Qt.NoFocus)

  uploadBtn = QPushButton(">>")
  uploadBtn.clicked.connect(self.uploadFiles)

  downloadBtn = QPushButton("<<")
  downloadBtn.clicked.connect(self.getCloudFiles)

  uploadBtnLayout = QHBoxLayout()
  uploadBtnLayout.addStretch(1)
  uploadBtnLayout.addWidget(uploadBtn)

  localHeaderLayout = QHBoxLayout()
  localHeaderLayout.addWidget(localLabel)
  localHeaderLayout.addStretch(1)
  localHeaderLayout.setContentsMargins(0,4,0,12)

  localOpsLayout = QHBoxLayout()
  localOpsLayout.addWidget(setDirBtn)
  localOpsLayout.addStretch(1)

  localFilesLayout = QVBoxLayout()
  localFilesLayout.addLayout(localHeaderLayout)
  localFilesLayout.addWidget(self.localProjTree)
  localFilesLayout.addLayout(localOpsLayout)

  cloudHeaderLayout = QHBoxLayout()
  cloudHeaderLayout.addWidget(cloudLabel)
  cloudHeaderLayout.addStretch(1)
  cloudHeaderLayout.addWidget(projectLabel)
  cloudHeaderLayout.addWidget(dirDropdown)
  cloudHeaderLayout.addWidget(updateDirBtn)
  cloudHeaderLayout.setContentsMargins(0,0,0,0)

  cloudOpsLayout = QHBoxLayout()
  cloudOpsLayout.addWidget(createProjBtn)
  cloudOpsLayout.addWidget(deleteProjBtn)
  cloudOpsLayout.addStretch(1)
  cloudOpsLayout.addWidget(deleteSelBtn)
  #cloudOpsLayout.addStretch(1)

  cloudFilesLayout = QVBoxLayout()
  cloudFilesLayout.addLayout(cloudHeaderLayout)
  cloudFilesLayout.addWidget(cloudProjTree)
  cloudFilesLayout.addLayout(cloudOpsLayout)
  cloudHeaderLayout.setContentsMargins(0,0,0,0)


  fileOpsLayout = QVBoxLayout()
  fileOpsLayout.addStretch(1)
  fileOpsLayout.addWidget(uploadBtn)
  fileOpsLayout.addWidget(downloadBtn)
  fileOpsLayout.addStretch(1)

  headerLayout = QHBoxLayout()

  projLayout = QHBoxLayout()
  projLayout.addLayout(localFilesLayout)
  projLayout.addLayout(fileOpsLayout)
  projLayout.addLayout(cloudFilesLayout)

  # MANAGE FARM LAYOUT

  launchSpotFarmBtn = QPushButton("Launch Spot Instances")
  #launchSpotFarmBtn.setFixedWidth(150)
  launchSpotFarmBtn.clicked.connect(self.launchSpotInstances)

  launchFarmBtn = QPushButton("Launch On-Demand Instances")
  #launchFarmBtn.setFixedWidth(150)
  launchFarmBtn.clicked.connect(self.launchInstances)

  rfLabel = QLabel("Render Farm")

  self.renderFarmTree =  QTreeView()
  renderFarmTree = self.renderFarmTree
  renderFarmTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
  self.renderFarmTreemodel = QStandardItemModel()
  renderFarmTree.setModel(self.renderFarmTreemodel)
  self.renderFarmTreemodel.setHorizontalHeaderLabels(["Name","ID","Type","Price","Region"])
  #self.renderFarmTreemodel.rowsInserted.connect(self.updateFarmView)
  renderFarmTree.setFocusPolicy(Qt.NoFocus)


  shutdownBtn = QPushButton("Terminate Instances")
  shutdownBtn.setFixedWidth(150)
  shutdownBtn.clicked.connect(self.terminateInstances)

  clearFilesBtn = QPushButton("Clear Files")
  clearFilesBtn.setFixedWidth(150)
  clearFilesBtn.clicked.connect(self.clearFiles)

  clearProjectBtn = QPushButton("Clear Project")
  clearProjectBtn.setFixedWidth(150)
  clearProjectBtn.clicked.connect(self.clearProject)

  reloadFrmBtn = QPushButton("UPDATE")
  #reloadFrmBtn.setFixedWidth(150)
  #reloadFrmBtn.clicked.connect(self.updateFarmTree)
  reloadFrmBtn.clicked.connect(lambda: self.updateFarmTree(False))
  reloadFrmBtn.setFont(smallBtnFont)

  rfHeaderLayout = QHBoxLayout()
  rfHeaderLayout.addWidget(rfLabel)
  rfHeaderLayout.addStretch(1)
  rfHeaderLayout.addWidget(reloadFrmBtn)

  rfFooterLayout = QHBoxLayout()
  rfFooterLayout.addWidget(launchFarmBtn)
  rfFooterLayout.addWidget(launchSpotFarmBtn)
  rfFooterLayout.addWidget(shutdownBtn)
  rfFooterLayout.addStretch(1)
  rfFooterLayout.addWidget(clearFilesBtn)
  rfFooterLayout.addWidget(clearProjectBtn)

  unavailableLabel = QLabel("Region Not Available")

  self.unavailableLayout = QHBoxLayout()
  self.unavailableLayout.addWidget(unavailableLabel)

  rfLayout = QVBoxLayout()
  rfLayout.addLayout(rfHeaderLayout)
  rfLayout.addWidget(renderFarmTree)
  rfLayout.addLayout(rfFooterLayout)

  unavailableWidget = QWidget()
  unavailableWidget.setLayout(self.unavailableLayout)

  availableWidget = QWidget()
  availableWidget.setLayout(rfLayout);

  self.activeRegionLayout = QStackedLayout()
  activeRegionLayout = self.activeRegionLayout
  activeRegionLayout.addWidget(unavailableWidget)
  activeRegionLayout.addWidget(availableWidget)

  self.mfLayout = QHBoxLayout()
  self.mfLayout.addLayout(activeRegionLayout)



  #RENDER JOB GUI

  ffFont = QFont()
  ffFont.setPointSize(12);
  frameFieldLabel = QLabel("Enter single frames or ranges separated by comas e.g. 1,2,6,7-10,33")
  frameFieldLabel.setFixedWidth(250)
  frameFieldLabel.setWordWrap(True)
  frameFieldLabel.setFont(ffFont)
  self.frameField = QLineEdit()
  frameField = self.frameField
  frameField.setFixedWidth(250)



#  jobPropsFrame = QFrame()

#  jobPropsFrame.setLayout(renderGridLayout)
#  jobPropsFrame.setStyleSheet(".QFrame{border: 1px solid rgba(40, 40, 40, 255);border-radius: 6px}")


  #RENDER QUEUE GUI

  rqLabel = QLabel("Render Queue")

  self.renderQueueTree = QTreeWidget()
  renderQueueTree = self.renderQueueTree
  renderQueueTree.setHeaderLabels(["Render Job ID","File","Status","Frames Complete","Total Frames","Region"])
  renderQueueTree.setColumnCount(6)
  renderQueueTree.setFocusPolicy(Qt.NoFocus)


  reloadQueueBtn = QPushButton("UPDATE")
  #reloadQueueBtn.setFixedWidth(150)
  reloadQueueBtn.clicked.connect(self.updateQueue)
  reloadQueueBtn.setFont(smallBtnFont)

  renderBtn = QPushButton("Create Render Job")
  renderBtn.setFixedWidth(150)
  renderBtn.clicked.connect(self.submitRenderJob)


  deleteJobBtn = QPushButton("Delete Job")
  deleteJobBtn.setFixedWidth(150)
  deleteJobBtn.clicked.connect(self.deleteRenderJob)

  pBarLabel = QLabel("Render Progess")
  pBar = QProgressBar()

  renderQueueHeaderLayout = QHBoxLayout()
  renderQueueHeaderLayout.addWidget(rqLabel)
  renderQueueHeaderLayout.addStretch(1)
  renderQueueHeaderLayout.addWidget(reloadQueueBtn)


  rqFooterLayout = pBarLayout = QHBoxLayout()
  rqFooterLayout.addWidget(renderBtn)
  rqFooterLayout.addWidget(deleteJobBtn)
  rqFooterLayout.addStretch(1)

  pBarLayout = QHBoxLayout()
  pBarLayout.addWidget(pBarLabel)
  pBarLayout.addWidget(pBar)

  rqLayout = QVBoxLayout()
  rqLayout.addLayout(renderQueueHeaderLayout)
  rqLayout.addWidget(renderQueueTree)
  rqLayout.addLayout(rqFooterLayout)
  #rqLayout.addLayout(pBarLayout)

  renderLayout = QHBoxLayout()
  #renderLayout.addLayout(renderJobLayout)
  renderLayout.addLayout(rqLayout)

  #MAIN TABS GUI
  tabs = QTabWidget()

  tab1 = QWidget()
  self.tab2 = QWidget()
  tab3 = QWidget()

  tab1.setLayout(projLayout)
  self.tab2.setLayout(self.mfLayout)
  tab3.setLayout(renderLayout)

  tabs.addTab(tab1,"Manage Files")
  tabs.addTab(self.tab2,"Manage Farm")
  tabs.addTab(tab3,"Render")

  mytimer = QTimer()

  regionLabel = QLabel("Region:")

  self.regDropdown = QComboBox()
  regDropdown = self.regDropdown
  regDropdown.setFixedWidth(150)
  regDropdown.connect(regDropdown, SIGNAL('activated(int)'), self.regionChanged)
  regDropdown.connect(regDropdown, SIGNAL('currentIndexChanged(int)'), self.regionProgChanged)

  rdlv = QListView()
  self.regDropdown.setView(rdlv)

  self.previousRegion = [];

  regionHeaderLayout = QHBoxLayout()
  regionHeaderLayout.addStretch(1)
  regionHeaderLayout.addWidget(regionLabel)
  regionHeaderLayout.addWidget(regDropdown)


  self.centralLayout = QVBoxLayout()

  self.centralLayout.addLayout(regionHeaderLayout)
  self.centralLayout.addWidget(tabs)
  #self.centralLayout.addWidget(statusBar)
  #self.centralLayout.addWidget(quitbtn)

  self.stylesheet = """


            QWidget{
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

            QInputDialog{
   										background-color:rgb(73, 73, 70);
   										font: thin;
   										font-family: Lato;
   										color:rgb(240, 240, 240);
  										}

  										QSpinBox[enabled="false"],QDoubleSpinBox[enabled="false"] {
  										color: grey;
    								border: 1px solid rgb(150, 150, 150);
  										}

  										QSpinBox,QDoubleSpinBox {
  										color: grey;
    								border: 1px solid rgb(150, 150, 150);
  										}

  										QLabel[enabled="false"] {
  										color: grey;
  										border: grey;
  										}

  										QLineEdit[enabled="false"] {
  										color: grey;
  										border: 1px solid rgb(40 40 40);
  										}

  										QLineEdit {
  										background-color:rgb(120, 120, 120);
    								border: 1px solid rgb(150, 150, 150);
  										}


            QSpinBox,QDoubleSpinBox{
   										background-color:rgb(120, 120, 120);
   										font: thin;
   										font-family: Lato;
   										color:rgb(240, 240, 240);
  										}

  										QComboBox[enabled="false"] {
  										color: grey;
  										border: 1px solid rgb(40 40 40);
  										}

  										QComboBox{
  										background-color:rgb(120, 120, 120);
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

  										QTreeView:item {
    								padding: 0px;
    								}

  										QTreeView QScrollBar:vertical {
  										border: 0px solid green;
  										width: 15px;
  										background:none;
    								}

    								QHeaderView {
    								background-color:rgb(183, 183, 180);
    								border: 0px rgb(80, 80, 80);
    								border-style:solid;margin:-0px;
    								padding:0px;
    								color:rgb(43,43,40);
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

  self.centralWidget = QWidget()

  self.setCentralWidget(self.centralWidget)


  self.show()

  self.uploadQueue = [];

  self.cloud = mrcConn_v097.mRenderCloudObj(self.statusBar())

  regionAction = QAction('&ChangeRegion', self)
  regionAction.triggered.connect(lambda arg='us-east-2': self.changeRegion(arg))


  self.checkCount = "."
  self.checkStatus = True;
  self.checkInProgress = False;
  self.checkInterval = 10.0;
  t2 = Thread(target=self.sysCheckTimer,args=())
  t2.daemon = True
  t2.start()



  cloudConnectThread = Thread(target=self.cloudConnect,args=())
  cloudConnectThread.daemon = True
  cloudConnectThread.start();


 def setProgress(self, progress):
  self.statusBar().showMessage(progress,2000);
  print progress

 def setStatus(self, status):
  self.statusBar().showMessage(status,3000);
  print status

 def copyMonitor(self,status):
  self.statusBar().showMessage(status);

 def updateQueueMessage(self,message):
  self.statusBar().showMessage(message,2000);

 def sysCheckTimer(self):
  print "cc timer called"
  while self.checkStatus is True:
   self.checkInProgress = True
   self.sysCheck()
   self.checkInProgress = False
   time.sleep(self.checkInterval)
   #self.statusBar().clearMessage();
   self.checkCount += ".";


 def sysCheck(self):
  print 'sysCheck'
  if self.cloud.cloudRunning is True:
   self.updateQueue()
  if self.cloud.spotRequests is True:
   self.updateFarmTree(True)
   print 'spot requests update'
  else:
   print 'spot request stopped'

 def cloudConnect(self):
  cloudconnect = cloudConnect(self.cloud)
  cloudconnect.cc.connect(self.populateUI);
  cloudconnect();




 def populateUI(self,cloudStatus):
  if cloudStatus is True:
   self.centralWidget.setLayout(self.centralLayout)
   self.dirDropdown.clear()
   self.cloud.populateProjectsList()

   self.initFarm()

   projList = self.cloud.projects #gets cloud projects
   self.dirDropdown.addItems(projList) #adds them to dropdown list
   self.populateRegions();
   #self.initRegions();
   self.timer = QTimer()
   self.checkJobs();
  else:
   noInitWidget = QLabel("Setup Has Not Been Performed.")
   noInitLayout = QHBoxLayout()
   noInitLayout.addStretch(1)
   noInitLayout.addWidget(noInitWidget)
   noInitLayout.addStretch(1)
   self.centralWidget.setLayout(noInitLayout)


 def checkJobs(self):
  print 'check jobs';
  checkjobs = checkJobs(self.cloud);
  checkjobs.jobs.connect(self.reloadJobs)
  checkjobs()

 def reloadJobs(self,job):
  self.populateQueue(job)

 def backupJobs(self):
  self.cloud.backupJobs();

 #THESE NEXT TWO FUNCTIONS ARE FOR THE INITIAL POPULATION OF THE CLOUD TREE


 def parseTree(self,folderList,allCloudObjs,parentItem):
  cloudTree = self.cloudProjTreemodel
  acoList = allCloudObjs.items()
  cloudNum = len(acoList);
  #print acoList;
  itemList = [];

  for item in acoList:
   itemList.append(item[1])


  for item in itemList:
   #print item;
   parentItem = cloudTree.invisibleRootItem()
   if item['Path'] != '':
				pathArr = item['Path'].split("/")
				#print pathArr
				i = 0
				for path in pathArr:
				 #print path
				 if parentItem.hasChildren(): #DOES THE CURRENT PARENT ITEM HAVE CHILDREN
				  rcount = parentItem.rowCount()
				  #print parentItem.text()+" has "+str(rcount)+" rows."
				  match = None
				  for r in range(rcount): #DOES THE ITEM ALREADY EXIST IN THE CHILDREN TREE
				   #print str(r)+" = "+str(parentItem.child(r).text())
				   if path == parentItem.child(r).text(): #IF IT DOES THEN THAT ITEM SHOULD BE THE PARENT FOR NEXT TIME THROUGH THE LOOP
				    #print path+' exists'
				    match = parentItem.child(r);

				  #IF THE ITEM DOES NOT EXIST CREATE IT
				  if match is None:
				   newItem = QStandardItem(path)
				   parentItem.appendRow(newItem)
				   parentItem = newItem
				  else:
				   parentItem = match;
				 else: #IF THE CURRENT PARENT ITEM DOES NOT HAVE CHILDREN CREATE THE 'PATH' ITEM
				  newItem = QStandardItem(path)
				  parentItem.appendRow(newItem)
				  parentItem = newItem
				i+=1;

   file = QStandardItem(item['Name'])
   #print (file.text()+' was created.')
   parentItem.appendRow(file)




 def populateCloudTreeThread(self):
  getprojitems = getProjItemsObject(self.cloud)
  getprojitems.items.connect(self.populateCloudTreeUpdate)
  getprojitems()


 def populateCloudTree(self):
  print 'populate cloud tree'
  projChangedThread = Thread(target=self.populateCloudTreeThread,args=())
  projChangedThread.daemon = True
  projChangedThread.start();


 def populateCloudTreeUpdate(self,allCloudObjs):
  root = []
  cloudTreeModel = self.cloudProjTreemodel
  cloudTreeModel.clear()
  cloudTreeModel.setHorizontalHeaderLabels(["Name"])
  parentItem = cloudTreeModel.invisibleRootItem()
  self.parseTree(root,allCloudObjs,parentItem)

  tree = self.cloudProjTree
  tree.sortByColumn(0,Qt.AscendingOrder)
  tree.sortByColumn(1,Qt.AscendingOrder)


 def projListChanged(self,dirIndex):
  print("changed")
  print("dropdown index is %s" %dirIndex)
  self.cloud.currentProject = self.dirDropdown.itemText(dirIndex)
  print(self.cloud.currentProject)
  self.populateCloudTree()



 #THIS IS A RECURSIVE FUNCTION THAT DRILLS DOWN THROUGH ANY FOLDERS IN THE SELECTED FOLDER
 #AND RETURNS ALL THE CHILD ITEMS
 def getCloudTreeSelectionChildren(self,selItem):
  childNum = selItem.rowCount()
  folderItems = []

  for i in range(childNum):
   folder = selItem.child(i).hasChildren();
   if folder is True:
    childItems = self.getCloudTreeSelectionChildren(selItem.child(i))
    for child in childItems:
     folderItems.append(child);
    #print(selItem.child(i).text());
   else:
    folderItems.append(selItem.child(i))

  return folderItems;

 #THIS FUNCTION GETS THE SELECTED ITEM(S). IF THE ITEM IS A FOLDER
 #THE FUNCTION CALLS A RECURSIVE FUNCTION TO GET ALL THE ITEMS IN THAT FOLDER
 def getCloudTreeSelection(self):
  type = None
  tree = self.cloudProjTree
  model = self.cloudProjTreemodel
  selItems = tree.selectedIndexes()
  print(selItems)
  fileItems = []
  #figures out whether selected item is a file or folder
  for item in selItems:
   selItem = item.model().itemFromIndex(item)
   #print(selItem.hasChildren())
   folder = selItem.hasChildren()
   if folder is True:
    print("this is a folder")
    childList = self.getCloudTreeSelectionChildren(selItem);
    for child in childList:
     #print(child.text());
     fileItems.append(child);
   else:
    #if it is a file at it to the file list
    print("this is a file")
    fileItems.append(selItem)
  print(fileItems)
  return fileItems


 def getCloudFilesThread(self,key,localPath):
  dir = self.cloud.currentProject+"/"
  bucket = self.cloud.s3.Bucket(self.cloud.bucketname)
  s3Client = self.cloud.s3Client

  newfile = self.cloud.localDirectory+"/"+localPath

  print newfile
  d = os.path.dirname(newfile)
  if not os.path.exists(d):
   try:
    os.makedirs(d)
   except OSError as e:
    print 'error is %s' %e
    pass

  print key

  object = bucket.Object(key)
  keysize = object.content_length


  dlMonitor = DownloadPercentage(key,keysize)
  self.connect(dlMonitor, SIGNAL("progress(QString)"),self.setProgress)
  s3Client.download_file(self.cloud.bucketname,key,newfile,Callback=dlMonitor)



 #THIS FUNCTION GOES THROUGH ALL THE SELECTED ITEMS IN THE TREE AND CONSTRUCTS THE KEY PATH (PATH ON S3)
 #FOR EACH ONE BASED ON ITS PARENT ITEMS, THEN CALLS THE FUNCTION IN THE mrcConn FILE TO ACTUALLY DOWNLOAD THE FILE
 def getCloudFiles(self):
  fileItems = self.getCloudTreeSelection()
  #loop through file list and construct the file path based on tree hierarchy and download the file
  self.statusBar().showMessage("Downloading Files.")
  for file in fileItems:
   keypath = []
   #print('item row = %s' %file.row())
   filename = file.text()
   parent = file.parent()
   hasParent = True

   keypath.append(file.text())
   while hasParent == True:
    parent = file.parent()
    if parent is not None:
     keypath.append(parent.text())
     file = parent
    else:
     hasParent = False
   keypath.reverse()
   #key = self.cloud.bucketname+"/"+self.cloud.currentProject+"/"+"/".join(keypath)
   key = self.cloud.currentProject+"/"+"/".join(keypath)
   if len(keypath)>1:
    parentfolder = keypath[-2]
   else:
    parentfolder = ''
   print(key)
   localPath = "/".join(keypath)

   #Need a test here for local directory to make sure it has been set.
   if self.cloud.localDirectory == None:
    self.statusBar().showMessage("Local directory must be selected before download.")
    return
   else:
    downloadThread = Thread(target=self.getCloudFilesThread,args=(key,localPath))
    downloadThread.daemon = True
    downloadThread.start();


 def autoDownloadFiles(self,key,filepath):
   localPath = filepath
   downloadThread = Thread(target=self.getCloudFilesThread,args=(key,localPath))
   downloadThread.daemon = True
   downloadThread.start();



 def deleteCloudFileThread(self,fileItems):
  fileList = []
  for file in fileItems:
   filename = file.text()
   fileList.append(filename)
  #self.cloud.deleteCloudFiles(fileList);
  deletefiles = deleteCloudFiles(self.cloud,fileList)
  deletefiles.delete.connect(self.deleteUpdate)
  deletefiles.deletecomplete.connect(self.deleteComplete)
  deletefiles()

 def deleteUpdate(self,message):
  self.statusBar().showMessage(message,2000)


 def deleteComplete(self,complete):
  print 'delete complete'
  self.statusBar().showMessage('Delete Complete',2000)
  self.checkStatus = True;
  self.populateCloudTree()





 def deleteCloudFiles(self):
  message = "Are you sure you want to delete the selected files?\n"
  message += "Press 'Yes' to continue. Press 'No' to cancel the operation."
  flags = QMessageBox.StandardButton.Yes
  flags |= QMessageBox.StandardButton.No
  delete = QMessageBox()
  delete.setStyleSheet(self.stylesheet)
  reply = delete.question(self,"Delete Project?",message,flags)
  if reply==QMessageBox.Yes:
   print "proceed with delete"
   fileItems = self.getCloudTreeSelection()
   #print len(fileItems)

   self.checkStatus = False;

   deleteThread = Thread(target=self.deleteCloudFileThread,args=(fileItems,))
   deleteThread.daemon = True;
   deleteThread.start();

  else:
   print "cancel delete"




 def uploadThread(self,selItems,model):
  isDir = None;

  if len(selItems) > 0:
   for file in selItems:
    selFile = model.filePath(file)
    if model.isDir(file) == 1:
     isDir = 1
    else:
     isDir = 0

    file = selFile
    proj = self.cloud.currentProject
    filePathArray = file.split("/");
    keyname = filePathArray[-1];
    key = proj+"/"+keyname;
    bucketname = self.cloud.bucketname

    s3Client = self.cloud.s3Client

    if isDir == 1:
  	  for root,dirs,files in os.walk(file):
  	   for file in files:
  	    #print "root = %s" %root
  	    #print "folderfile = %s" %file
  	    ulMonitor = UploadPercentage(root+"/"+file)
  	    self.connect(ulMonitor, SIGNAL("progress(QString)"),self.setProgress)
  	    s3Client.upload_file(root+"/"+file, bucketname, key+"/"+file, Callback=ulMonitor)
    else:
     ulMonitor = UploadPercentage(file)
     self.connect(ulMonitor, SIGNAL("progress(QString)"),self.setProgress)
     s3Client.upload_file(file, bucketname, key, Callback=ulMonitor)

    print(key)
    print("Upload Files")
   self.populateCloudTree()


 def uploadFiles(self):
		selIndexes = self.localProjTree.selectedIndexes()
		selItems = []
		model = self.localProjDirModel
		cloud = self.cloud
		print(selIndexes)
		currentProjIndex = None

		print len(selIndexes)
		for file in selIndexes:
		 column = file.column();
		 if column == 0:
		  selItems.append(file)

		for file in selItems:
		 print(file.column())
		 print(model.fileName(file))
		 print(model.filePath(file))

		uploadThread = Thread(target=self.uploadThread,args=(selItems,model))
		uploadThread.daemon = True
		uploadThread.start();

 def createProjUpdate(self,projName):
  self.dirDropdown.insertItem(self.dirDropdown.count(),self.cloud.currentProject) #adds them to dropdown list
  self.dirDropdown.setCurrentIndex(self.dirDropdown.count()-1)
  self.statusBar().showMessage("Project %s created." %(projName),3000)


 def createProjectThread(self,cloud,projName):
  createproject = createCloudProjectObject(cloud,projName)
  createproject.createcomplete.connect(self.createProjUpdate)
  createproject()

 def createProject(self):
  currentProjectIndex = 0;

  input = QInputDialog()
  input.setFocusPolicy(Qt.NoFocus)
  input.setStyleSheet(self.stylesheet);
  reply = input.getText(self, "Create Project","Enter Project Name:")

  if reply[1]:
   #user clicked OK
   projName = str(reply[0]).replace(" ","")
   projName.replace(" ","")
   print(projName)
   projList = self.cloud.projects
   projUnique = True
   for proj in projList:
   	if proj == projName:
   		projUnique = False
   		message = "Project name already exists. Please pick a unique name.\n"
   		message += "Current project names are: \n"
   		for proj in projList:
   			message += proj+"\n"
   		reply = QMessageBox.information(self,"",message)

   if projUnique == True:
   	print("project is unique")
   	createProjectThread = Thread(target=self.createProjectThread,args=(self.cloud,projName))
   	createProjectThread.daemon = True
   	createProjectThread.start();

  else:
  	#user clicked Cancel
  	projName = reply[0] # which will be "" if they clicked Cancel


 def deleteProjectUpdate(self,projName):
  currentProjIndex = self.dirDropdown.currentIndex()
  self.dirDropdown.removeItem(currentProjIndex)
  self.statusBar().showMessage("Project %s deleted." %(projName),3000)


 def deleteProjectThread(self,cloud):
  deleteproject = deleteCloudProjectObject(cloud)
  deleteproject.deletecomplete.connect(self.deleteProjectUpdate)
  deleteproject()

 def deleteProject(self):
  message = "Are you sure you want to delete all files associated with this project?\n"
  message += "Press 'Yes' to continue. Press 'No' to cancel the operation."
  flags = QMessageBox.StandardButton.Yes
  flags |= QMessageBox.StandardButton.No
  msgBox = QMessageBox()
  msgBox.setStyleSheet(self.stylesheet)
  reply = msgBox.question(self,"Delete Project?",message,flags)
  if reply==QMessageBox.Yes:
   deleteProjectThread = Thread(target=self.deleteProjectThread,args=(self.cloud,))
   deleteProjectThread.daemon = True
   deleteProjectThread.start();
  else:
   print "cancel delete"


 def setLocalProjectDir(self):
  dialog = QFileDialog(self.centralWidget)
  dialog.setFileMode(QFileDialog.Directory)
  dir = QDir(os.getcwd())
  #fname, _ = dialog.getOpenFileName()
  fdir = dialog.getExistingDirectory()
  #print(fname)
  print(fdir)
  #fnameArray = fname.split("/")
  #fnameArray.pop(-1)
  #path = "/".join(fnameArray)
  path = fdir
  if path != "":
   mypath = QDir(path).path()
   self.cloud.localDirectory = mypath
   self.localProjDirModel.setRootPath(mypath)
   self.localProjTree.setRootIndex(self.localProjDirModel.index(mypath))



 def setRenderFile(self,file):
  fileText = str(self.selectRenderFile.currentText())
  fileText = file;
  #print("file text = %s" %fileText)
  #print(fileIndex)
  self.cloud.renderFile = str(fileText)
  #print(self.cloud.renderFile)


 def populateFileList(self):
  self.selectRenderFile.clear()
  self.selectRenderFile.addItems(self.cloud.projectFileList)

 def submitRenderJob(self):
  print "submit job"

  d=submitRenderJobWindow_v097.sjDialog(self,self.cloud.projectFileList,self.cloud.softwareList,self.stylesheet)
  d.setStyleSheet(self.stylesheet)
  result = d.exec_()
  if result == True:
   emptyCheck = d.checkFields()
   if len(emptyCheck)>0:
    for check in emptyCheck:
     print check + " field is empty. Please enter information in field."
    self.submitRenderJob()
   else:
    file = d.selectRenderFile.currentText().strip("/")
    frames = d.frames.text()
    #project = d.project.text()
    #id = d.id.text()
    output = d.output.text()
    layers = d.layersToggle.isChecked()
    depth = d.layerDepth.currentText()
    rdet = d.rdetToggle.isChecked()
    software = d.selectSoftware.currentText()
    passes = d.passesToggle.isChecked()
    passName = d.passName.text()

    print file
    print frames
    #print project
    #print id
    print output
    print layers
    print depth
    print rdet
    print software
    self.statusBar().showMessage('Creating render job.',3000)
    submitRenderJobThread = Thread(target=self.submitRenderJobThread,args=(file,frames,self.cloud.currentProject,output,layers,depth,rdet,software,passes,passName))
    submitRenderJobThread.daemon = True
    submitRenderJobThread.start();


 def submitRenderJobThread(self,file,frames,project,output,layers,depth,rdet,software,passes,passName):
  submitjob = submitRenderJob(self.cloud,file,frames,self.cloud.currentProject,output,layers,depth,rdet,software,passes,passName)
  submitjob.job.connect(self.populateQueue)
  submitjob.status.connect(self.setStatus)
  submitjob()


 def deleteRenderJob(self):
  cloud = self.cloud
  tree = self.renderQueueTree
  columns = tree.columnCount()
  selItems = tree.selectedItems()

  if len(selItems) > 0:
			message = "Are you sure you want to delete the selected files?\n"
			message += "Press 'Yes' to continue. Press 'No' to cancel the operation."
			flags = QMessageBox.StandardButton.Yes
			flags |= QMessageBox.StandardButton.No
			delete = QMessageBox()
			delete.setStyleSheet(self.stylesheet)
			reply = delete.question(self,"Delete Project?",message,flags)
			if reply==QMessageBox.Yes:
				print "proceed with delete"
				for item in selItems:
					print(item.text(0))
					id = item.text(0)
					index = tree.indexOfTopLevelItem(item)
					tree.takeTopLevelItem(index)
					deleteRenderJobThread = Thread(target=self.deleteRenderJobThread,args=(id,))
					deleteRenderJobThread.daemon = True
					deleteRenderJobThread.start();

			else:
				print "cancel delete"

  else:
   print("No Render Jobs Selected")


 def deleteRenderJobThread(self,id):
  self.cloud.cloudRunning = False;
  if self.checkInProgress is True:
   while self.checkInProgress is True:
    time.sleep(.1)
  print 'deleting'
  self.cloud.deleteRenderJob(id)


 def populateQueue(self,job):
   treeRow = QTreeWidgetItem()
   job.treeRow = treeRow
   tree = self.renderQueueTree
   items = []
   treeRow.setText(0,job.id)
   treeRow.setText(1,job.fileName)
   treeRow.setText(2,'Rendering')
   treeRow.setText(3,str(job.framesComplete))
   treeRow.setText(4,str(job.totalFrames))
   treeRow.setText(5,str(job.region))
   items.append(treeRow)
   tree.addTopLevelItems(items)
   tree.resizeColumnToContents(0)
   tree.resizeColumnToContents(1)
   tree.resizeColumnToContents(2)
   tree.resizeColumnToContents(3)
   tree.resizeColumnToContents(4)
   tree.resizeColumnToContents(5)

 def updateQueueGUI(self,totalFrames,framesComplete,lastFrame,lastFrameTime,jobID):
  print "total frames = %s" %totalFrames
  print "frames complete = %s" %framesComplete
  tree = self.renderQueueTree
  totalRows = tree.topLevelItemCount()-1
  i=0
  while i <= totalRows:
   row = tree.topLevelItem(i)
   if row.text(0) == jobID:
    row.setText(3,framesComplete)
    row.setText(4,totalFrames)
    if framesComplete == totalFrames:
     row.setText(2,"Complete")

   i+=1;
  self.statusBar().showMessage("Job %s : frame %s finshed rendering in %s seconds." %(jobID,lastFrame,lastFrameTime),3000)



 def updateQueueThread(self):
  getmessages = getMessagesObject(self.cloud)
  getmessages.complete.connect(self.updateQueueGUI)
  getmessages.status.connect(self.setStatus)
  getmessages.download.connect(self.autoDownloadFiles)
  getmessages()

 def updateQueue(self):
  updateQueueThread = Thread(target=self.updateQueueThread,args=())
  updateQueueThread.daemon = True
  updateQueueThread.start();


 def launchSpotInstances(self):
  d=launchSpotInstanceWindow_v097.lsiDialog(self.cloud,self.stylesheet)
  d.setStyleSheet(self.stylesheet)
  result = d.exec_()
  if result == True:
   badFields = d.checkFields()
   if len(badFields)>0:
    message = ""
    for field in badFields:
     message += field
    mBox = QMessageBox();
    mBox.setText(message);
    mBox.setStyleSheet(self.stylesheet)
    reply = mBox.exec_();
    if reply==QMessageBox.Ok:
     print "ok"
     self.launchSpotInstances()
    else:
     print "not ok"
     return

   else:
    comp = d.computerType.currentText()
    num = d.numInstances.text()
    size = d.vSize.text()
    #project = d.project.text()
    #id = d.id.text()
    bid = d.bid.text().strip("$")

    alarmtoggle = d.alarmToggle.isChecked()

    if alarmtoggle is True:
     alarm = {}
     alarm['Threshold'] = float(d.alarmThreshold.text())
     alarm['Period'] = int(d.alarmPeriod.text())
     alarm['PeriodCount'] = int(d.alarmPeriodCount.text())
    else:
     alarm = None

    print comp
    print num
    print bid

    cloud = self.cloud
    cost = bid
    count = num
    cpu = comp
    ami = "RenderNodeAMI"
    launchSpotInstancesThread = Thread(target=self.launchSpotInstancesThread,args=(cost,count,ami,cpu,size,alarm))
    launchSpotInstancesThread.daemon = True
    launchSpotInstancesThread.start();



 def launchSpotInstancesThread(self,cost,count,ami,cpu,size,alarm):
  self.cloud.spotRequests = False;
  if self.checkInProgress is True:
   while self.checkInProgress is True:
    time.sleep(1);

  launchSpotInst = launchSpotInstancesObject(self.cloud,cost,count,ami,cpu,size,alarm)
  launchSpotInst.updatetree.connect(self.spotInstanceUpdateTree)
  launchSpotInst()


 def spotInstanceUpdateTree(self,spotInfo):
  cloud = self.cloud
  tree = self.renderFarmTreemodel
  treeview = self.renderFarmTree
  tree.setHorizontalHeaderLabels(["Name","ID","Type","Region","State","Price"])

  instID = QStandardItem(spotInfo['spotid'])
  instType = QStandardItem(spotInfo['type'])
  instPrice = QStandardItem(spotInfo['price'])
  instName = QStandardItem(spotInfo['name'])
  instRegion = QStandardItem(spotInfo['region'])
  instState = QStandardItem(spotInfo['state'])
  i = tree.rowCount();
  tree.setItem(i,0,instName)
  tree.setItem(i,1,instID)
  tree.setItem(i,2,instType)
  tree.setItem(i,3,instRegion)
  tree.setItem(i,4,instState)
  tree.setItem(i,5,instPrice)
  self.updateFarmView();


 def launchInstances(self):
  d=launchInstanceWindow_v097.liDialog(self.cloud,self.stylesheet)
  d.setStyleSheet(self.stylesheet)
  result = d.exec_()
  if result == True:
   if d.numInstances.text() == "0":
    message = "The 'number of instances' field is zero.\n"
    message += "You must choose an amount greater than zero."
    mBox = QMessageBox();
    mBox.setText(message);
    mBox.setStyleSheet(self.stylesheet)
    reply = mBox.exec_();
    if reply==QMessageBox.Ok:
     print "ok"
     self.launchInstances()
    else:
     print "not ok"
     return

   else:
    comp = d.computerType.currentText()
    num = d.numInstances.text()
    size = d.vSize.text()
    alarmtoggle = d.alarmToggle.isChecked()

    if alarmtoggle is True:
     alarm = {}
     alarm['Threshold'] = float(d.alarmThreshold.text())
     alarm['Period'] = int(d.alarmPeriod.text())
     alarm['PeriodCount'] = int(d.alarmPeriodCount.text())
    else:
     alarm = None


    print comp
    print num
    cloud = self.cloud
    count = num
    cpu = comp
    ami = "RenderNodeAMI"
    launchInstancesThread = Thread(target=self.launchInstancesThread,args=(count,ami,cpu,size,alarm))
    launchInstancesThread.daemon = True
    launchInstancesThread.start();

 def launchInstancesThread(self,count,ami,cpu,size,alarm):
  launchInst = launchInstancesObject(self.cloud,count,ami,cpu,size,alarm)
  launchInst.updatetree.connect(self.appendTree)
  launchInst()



 def terminateInstances(self):
  cloud = self.cloud
  compList = []
  spotList = []
  tree = self.renderFarmTree
  model = self.renderFarmTreemodel

  if len(tree.selectedIndexes())>0:
			message = "Are you sure you want to delete the selected files?\n"
			message += "Press 'Yes' to continue. Press 'No' to cancel the operation."
			flags = QMessageBox.StandardButton.Yes
			flags |= QMessageBox.StandardButton.No
			reply = QMessageBox.question(self,"Delete Project?",message,flags)

			if reply==QMessageBox.Yes:
				print "proceed with delete"
				while tree.selectedIndexes():
				 idx = tree.selectedIndexes()[0]
				 nameText = model.item(idx.row(),0).text();
				 if nameText == 'Spot Request':
				  spotList.append(model.item(idx.row(),1).text())
				 else:
				  computer = {}
				  computer['name'] = model.item(idx.row(),0).text()
				  computer['id'] = model.item(idx.row(),1).text()
				  computer['type'] = model.item(idx.row(),2).text()
				  compList.append(computer)

				 model.removeRow(idx.row(),idx.parent());

				terminateInstancesThread = Thread(target=self.terminateInstancesThread,args=(compList,spotList))
				terminateInstancesThread.daemon = True
				terminateInstancesThread.start();

			else:
				print "cancel delete"

  else:
   print("No Computers Selected")


 def terminateInstancesThread(self,compList,spotList):
  self.cloud.spotRequests = False;
  if self.checkInProgress is True:
   while self.checkInProgress is True:
    time.sleep(1)

  terminateInst = terminateInstances(self.cloud,compList,spotList)
  terminateInst.complete.connect(self.updateFarmTree)
  terminateInst()


 def clearFilesThread(self):
  clearfiles = clearFilesObject(self.cloud)
  clearfiles.complete.connect(self.setStatus)
  clearfiles()


 def clearFiles(self):
  if len(self.cloud.renderFramesList)<0:
   print 'cannot send command'
   msgBox = QMessageBox()
   msgBox.setStyleSheet(self.stylesheet);
   msgBox.setText("Commands cannot be sent while render jobs are running.")
   msgBox.exec_()

  else:
   print 'send command'
   clearFilesThread = Thread(target=self.clearFilesThread,args=())
   clearFilesThread.daemon = True
   clearFilesThread.start();


 def clearProjectThread(self):
  clearproject = clearProjectObject(self.cloud)
  clearproject.complete.connect(self.setStatus)
  clearproject()

 def clearProject(self):
  if len(self.cloud.renderFramesList)>0:
   print 'cannot send command'
   msgBox = QMessageBox()
   msgBox.setText("Commands cannot be sent while render jobs are running.")
   msgBox.exec_()

  else:
   print 'send command'
   clearProjectThread = Thread(target=self.clearProjectThread,args=())
   clearProjectThread.daemon = True
   clearProjectThread.start();

 def updateFarmTree(self,spotsOnly):
  cloud = self.cloud
  instList = []
  spotList = []
  tree = self.renderFarmTree
  model = self.renderFarmTreemodel

  rowCount = model.rowCount()
  i = 0

  while i < rowCount:
   id = model.item(i,1).text()
   name = model.item(i,0).text()

   if name == "Spot Request":
    spotList.append(id)
   else:
    instList.append(id)

   i+=1;

  updateFarmTreeThread = Thread(target=self.updateFarmTreeThread,args=(instList,spotList,spotsOnly))
  updateFarmTreeThread.daemon = True
  updateFarmTreeThread.start();


 def updateFarmTreeThread(self,instList,spotList,spotsOnly):
  updateFarm = updateFarmTreeObject(self.cloud,instList,spotList,spotsOnly)
  updateFarm.add.connect(self.appendTree)
  updateFarm.remove.connect(self.removeTree)
  updateFarm.update.connect(self.updateTreeItem)
  updateFarm()

 def appendTree(self,instInfo):
  cloud = self.cloud
  tree = self.renderFarmTreemodel
  tree.setHorizontalHeaderLabels(["Name","ID","Type","Region","State","Price"])

  treeview = self.renderFarmTree
  instID = QStandardItem(instInfo['id'])
  instType = QStandardItem(instInfo['type'])
  instName = QStandardItem(instInfo['name'])
  instRegion = QStandardItem(instInfo['region'])
  instState = QStandardItem(instInfo['state'])
  instPrice = None

  if 'price' in instInfo.keys():
   instPrice = QStandardItem(instInfo['price'])

  i = tree.rowCount();

  tree.setItem(i,0,instName)
  tree.setItem(i,1,instID)
  tree.setItem(i,2,instType)
  tree.setItem(i,3,instRegion)
  tree.setItem(i,4,instState)

  if instPrice != None:
   tree.setItems(i,5,instPrice)

  self.updateFarmView();

 def removeTree(self,spotid):
  cloud = self.cloud
  tree = self.renderFarmTree
  model = self.renderFarmTreemodel
  parent = model.invisibleRootItem();

  rowCount = model.rowCount()
  i = 0

  while i < rowCount:
   uispotid = model.item(i,1).text()
   item = model.item(i,0)
   idx = model.indexFromItem(item)

   if uispotid == spotid:
    print 'row remove'
    model.removeRow(idx.row(),idx.parent());
    break
   i+=1;

 def updateTreeItem(self,instInfo):
  cloud = self.cloud
  tree = self.renderFarmTree
  model = self.renderFarmTreemodel
  parent = model.invisibleRootItem();

  rowCount = model.rowCount()
  i = 0

  while i < rowCount:
   ui_id = model.item(i,1).text()
   item = model.item(i,0)

   if ui_id == instInfo['id']:
    print 'update'

    model.item(i,0).setText(instInfo['name'])
    model.item(i,1).setText(instInfo['id'])
    model.item(i,2).setText(instInfo['type'])
    model.item(i,3).setText(instInfo['region'])
    model.item(i,4).setText(instInfo['state'])
    break
   i+=1;


 def initFarm(self):
  tree = self.renderFarmTreemodel
  tree.setHorizontalHeaderLabels(["Name","ID","Type","Region","Price","State"])
  tree.clear()

  initFarmThread = Thread(target=self.initFarmThread,args=())
  initFarmThread.daemon = True
  initFarmThread.start();

 def initFarmThread(self):
  initFarm = initFarmTreeObject(self.cloud)
  initFarm.add.connect(self.appendTree);
  initFarm();



 def updateFarmView(self):
  print 'update farm'
  tree = self.renderFarmTree
  treeModel = self.renderFarmTreemodel

  totalColumns = treeModel.columnCount()
  i=0
  while i <= totalColumns-1:
   tree.resizeColumnToContents(i)
   i+=1;

  tree.sortByColumn(0,Qt.AscendingOrder)



 def initRegions(self):
  initRegionsThread = Thread(target=self.initRegionsThread,args=())
  initRegionsThread.daemon = True
  initRegionsThread.start();


 def initRegionsThread(self):
  cloud = self.cloud
  initregionscan = initRegionsObject(cloud);
  initregionscan.activeregion.connect(self.initRegionsUpdate)
  initregionscan()

 def initRegionsUpdate(self,region):
  dropdown = self.regDropdown
  regionCount = dropdown.count()
  self.statusBar().showMessage("Region %s is Active" %region,2000)

  for i in range(regionCount):
   if dropdown.itemText(i) == region:
    oldtext = dropdown.itemText(i)
    newtext = '*%s' %oldtext
    dropdown.setItemText(i,newtext)


 def regionProgChanged(self,index):
  if len(self.previousRegion) > 1:
   self.previousRegion.pop(0)
  self.previousRegion.append(index);
  print 'region is %s' %self.previousRegion[-1]


 def regionChanged(self,index):
  dropdown = self.regDropdown
  regionCount = dropdown.count()

  if len(self.cloud.renderFramesList)>0:
   msgBox = QMessageBox()
   msgBox.setText("Region cannot be changed while render jobs are running.")
   msgBox.exec_()
   self.regDropdown.setCurrentIndex(self.previousRegion[0])


  else:
   ddtext = dropdown.currentText()
   self.activeRegionLayout.setCurrentIndex(0)

   if ddtext[0:1] == "*":
    region = ddtext[1:]
   else:
    region = ddtext
   print region;

   activeRegionsSet = set(self.cloud.activeRegions)

#   for i in range(regionCount):
#    if region in activeRegionsSet:
#     self.activeRegionLayout.setCurrentIndex(1)
#     break

   if region in activeRegionsSet:
    self.activeRegionLayout.setCurrentIndex(1)

   regionChangedThread = Thread(target=self.regionChangedThread,args=(region,))
   regionChangedThread.daemon = True
   regionChangedThread.start();
   self.statusBar().showMessage("Scanning Region...")


 def regionChangedThread(self,region):
  regionscan = ScanRegion(region,self.cloud,self.cloud.key,self.cloud.keyid,self.cloud.secretkey);
  #self.connect(regionscan, SIGNAL('regionstatus(QString,QString,QString,QString,QString'),self.regionCheck)
  regionscan.regionstatus.connect(self.regionCheck)

  regionscan()


 def regionCheck(self,imagestatus,image,keystatus,key,region,bucketstatus,bucket):
  print "checked"
  self.statusBar().showMessage("Region %s : Scan Complete" %region,2000)
  print imagestatus
  print image
  print keystatus
  print key
  print region


  message = "";

  if imagestatus is False:
   message += "The selected region does not have a RenderNodeAMI\n"
   self.tab2.setLayout(self.unavailableLayout)
  else:
   #self.cloud.rn_ami = image
   self.cloud.region = region
   self.cloud.connectCloud();
   self.initFarm() #repopulates farm tree


  if keystatus is False:
   message += "The selected region does not have a Key Pair.\n"
  else:
   self.cloud.key = key

  if bucketstatus is False:
   message += "The selected region does not have a storage bucket."
  else:
   self.cloud.bucketname = bucket
   self.cloud.connectCloud()
   self.dirDropdown.clear()
   self.cloud.populateProjectsList()
   projList = self.cloud.projects #gets cloud projects
   print 'project list is %s' %projList
   self.dirDropdown.addItems(projList) #adds them to dropdown list
   #self.populateCloudTree();

  if (imagestatus is False) or (keystatus is False) or (bucketstatus is False):
   message += "Press 'Yes' to create these items."
   flags = QMessageBox.StandardButton.Yes
   flags |= QMessageBox.StandardButton.No
   reply = QMessageBox.question(self,"Activate Region ?",message,flags)
   if reply==QMessageBox.Yes:
    print "proceed with creating items"
    if imagestatus is False:
     copyImageThread = Thread(target=self.copyImageThread,args=(region,))
     copyImageThread.daemon = True
     copyImageThread.start();

    if keystatus is False:
     createKeyThread = Thread(target=self.createKeyThread,args=(region,))
     createKeyThread.daemon = True
     createKeyThread.start();

    if bucketstatus is False:
     createBucketThread = Thread(target=self.createBucketThread,args=(region,bucket))
     createBucketThread.daemon = True
     createBucketThread.start();

   else:
    print 'keep region'
    print self.previousRegion
    self.regDropdown.setCurrentIndex(self.previousRegion[0])
    self.activeRegionLayout.setCurrentIndex(1)

  else:
   self.activeRegionLayout.setCurrentIndex(1)

   if region not in self.cloud.activeRegions:
    self.cloud.activeRegions.append(region)
    self.initRegionsUpdate(region);


 def copyImageThread(self,region):
  newAMI = self.cloud.copyImage(region);
  self.cloud.rn_ami = newAMI['ImageId']
  copymon = CopyImageStatus(region,self.cloud.keyid,self.cloud.secretkey,newAMI['ImageId']);
  self.connect(copymon, SIGNAL("status(QString)"),self.copyMonitor)

  while True:
   status = copymon()
   print status
   if status == "available":
    break
   time.sleep(15)

  self.cloud.region = region
  self.cloud.connectCloud();
  self.initFarm();
  if region not in self.cloud.activeRegions:
   self.cloud.activeRegions.append(region)
   self.initRegionsUpdate(region);
  self.activeRegionLayout.setCurrentIndex(1)

 def createKeyThread(self,region):
  newKey = self.cloud.createKey(region);
  self.cloud.key = newKey['KeyName']
  print self.cloud.key

 def createBucketThread(self,region,newbucketname):
  createbucket = createBucketObject(self.cloud,region,newbucketname);
  createbucket.bucketstatus.connect(self.createBucketResponse)
  createbucket()

 def createBucketResponse(self,bucketstatus,newbucketname,region):
  if bucketstatus is True:
   self.cloud.bucketname = newbucketname
   self.cloud.bucketList[region] = newbucketname
   self.cloud.connectCloud()
   self.dirDropdown.clear()
   self.cloud.populateProjectsList()
   projList = self.cloud.projects #gets cloud projects
   self.dirDropdown.addItems(projList) #adds them to dropdown list
  else:
   reply = QInputDialog.getText(self, "Create Root Folder","Enter Root Folder Name:")
   if reply[1]:
				newbucketname = "%s--%s" %(reply[0],region)
				print(newbucketname)
				createbucket = createBucketObject(self.cloud,region,newbucketname);
				createbucket.bucketstatus.connect(self.createBucketResponse)
				createbucket()


 def createBucketThreadOld(self,region,newbucketname):
  print 'create bucket %s' %newbucketname
  print region
  s3Resource = self.cloud.session.resource('s3',region);
  try:
   newbucket = s3Resource.Bucket(newbucketname)
   response = newbucket.create(newbucket,CreateBucketConfiguration={'LocationConstraint': region})
   print 'New Bucket Created'
  except botocore.exceptions.ClientError as e:
   print("Bucket cannot be created please try another name")
   reply = QInputDialog.getText(self, "Create Root Folder","Enter Root Folder Name:")
   if reply[1]:
				newbucketname = "%s--%s" %(reply[0],region)
				print(newbucketname)
				try:
				 bucket = s3Resource.Bucket(newbucketname)
				 response = bucket.create(bucket,CreateBucketConfiguration={'LocationConstraint':region})
				except botocore.exceptions.ClientError as e:
					print("Bucket cannot be created please try another name",5000)
					self.statusBar().showMessage("Bucket cannot be created please try another name.",5000)
					self.createBucketThread(region,newbucketname)
				else:
				 self.cloud.bucketname = newbucketname
				 self.cloud.bucketList[region] = newbucketname
				 self.cloud.connectCloud()

				 self.dirDropdown.clear()
				 self.cloud.populateProjectsList()

				 projList = self.cloud.projects #gets cloud projects
				 self.dirDropdown.addItems(projList) #adds them to dropdown list





 def populateRegions(self):
  self.cloud.getRegions();
  print self.cloud.regions;
  self.populateRegionsDropdown();

 def populateRegionsDropdown(self):
  dropdown = self.regDropdown
  dropdown.addItems(self.cloud.regions)
  regionCount = dropdown.count()

  for i in range(regionCount):
   if dropdown.itemText(i) == self.cloud.region:
    dropdown.setCurrentIndex(i)
    self.activeRegionLayout.setCurrentIndex(1)

  activeRegionsSet = set(self.cloud.activeRegions)

  for i in range(regionCount):
   ddtext = dropdown.itemText(i)
   if ddtext in activeRegionsSet:
    oldtext = ddtext
    newtext = "*%s" %ddtext
    dropdown.setItemText(i,newtext)



 def closeEvent(self,event):
  print("closing")
  self.backupJobs();
  self.cloud.updateConfig();


def run():
 app = QApplication(sys.argv)
 GUI = Window()
 sys.exit(app.exec_())

run()
