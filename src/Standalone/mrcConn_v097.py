#!/usr/bin/env python

import boto3
import botocore
import ConfigParser
import base64
import os
from time import time
import time
import datetime
import sys
from sys import platform
import thread
import threading
from threading import Thread
from boto3.s3.transfer import S3Transfer

from PySide.QtCore import *
from PySide.QtCore import QThread

class mRenderCloudObj():

 def __init__(self,mainStatusBar):

  self.keyid = None
  self.secretkey = None
  self.region = None
  self.activeRegions = []
  self.softwareList = []
  self.credValidate = False
  self.cloudConnect = False
  self.rendering = False
  self.cloudRunning = False
  self.spotRequests = False
  self.instancesRunning = None
  self.renderManagerRunning = False
  self.instanceList = []
  self.spotRequestList = []
  self.spotCancelList = []
  self.spotCheckCount = 5;
  self.session = None
  self.sqs = None
  self.s3 = None
  self.s3Client = None
  self.ec2Resource = None
  self.ec2Client = None
  self.bucketname = None
  self.bucket = None
  self.bucketList = {}
  self.ccq = None
  self.rmq = None
  self.rcq = None
  self.renderName = None
  self.renderFile = None
  self.projects = []
  self.currentProject = None
  self.currentProjectItems = {}
  self.projectFileList = []
  self.renderQueue = {}
  self.renderFramesList = []
  self.newJob = None
  self.localDirectory = None
  self.rn_ami = None
  self.key = None
  self.securitygroup = None
  self.runexe = False;
  #self.runexe = True;
  self.mainStatusBar = mainStatusBar
  self.cwd = None
  self.regions = []


  self.initCreds()



 def initCreds(self):

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
   if self.runexe is True:
    os.chdir(cwd)
  elif platform == "win32":
   pass


  cwd = os.getcwd()
  self.cwd = cwd
  print cwd
  credfilepath = cwd+"/Data/creds.txt"

  if os.path.exists(credfilepath):
   print "File exists"
   file = open(credfilepath,'r+');
   filecontents = file.read();
   file.close()
   credLinesArray = filecontents.splitlines()

   for cred in credLinesArray:
    credArray = cred.split("=")
    if credArray[0] == "AWSAccessKeyId":
     self.keyid = credArray[1]
     print self.keyid
    if credArray[0] == "AWSSecretKey":
     self.secretkey = credArray[1]
     print self.secretkey
    if credArray[0] == "AWSKeyPair":
     self.key = credArray[1]
     print self.key
    if credArray[0] == "AWSSecurityGroup":
     self.securitygroup = credArray[1]
     print self.securitygroup

   self.initConfig()
  else:
   print "Credentials Not Found"



 def initConfig(self):
  cwd = self.cwd
  print cwd
  configfilepath = cwd+"/Data/config.txt"
  bucketSetup = False;

  if os.path.exists(configfilepath):
  	print "File exists"
  	file = open(configfilepath,'r+');
  	filecontents = file.read();
  	file.close()
  	configLinesArray = filecontents.splitlines()
  	config = {}

  	for configLine in configLinesArray:

  	 configArray = configLine.split("=")

  	 if configArray[0] == "Region" and configArray[1]:
  	  config['Region'] = configArray[1]
  	  self.region = configArray[1]
  	  print self.region

  	 if configArray[0] == "Buckets" and configArray[1]:
  	  print 'Bucket Setup Already Complete'
  	  bucketSetup = True
  	  bucketlist = configArray[1].split(",")
  	  for b in bucketlist:
  	   bArr = b.split(":")
  	   self.bucketList[bArr[0]] = bArr[1]

  	 if configArray[0] == "ActiveRegions" and configArray[1]:
  	  config['ActiveRegions'] = configArray[1].split(",")
  	  print self.activeRegions

  	 if configArray[0] == "Software" and configArray[1]:
  	  config['SoftwareList'] = configArray[1].split(",")
  	  print self.softwareList

  	 if configArray[0] == "KeyPair" and configArray[1]:
  	  config['Key'] = configArray[1]
  	  print self.key

  	self.region = config['Region']
  	self.activeRegions = config['ActiveRegions']
  	self.softwareList = config['SoftwareList']
  	self.key = config['Key']

  	self.bucketname = self.bucketList[self.region]

  	self.credValidate = True;

  if bucketSetup is False:
   print "Bucket Setup Not Complete"


 def updateConfig(self):
  cwd = self.cwd
  print cwd
  configfilepath = cwd+"/Data/config.txt"

  buckets_to_list = ["%s:%s"%(k,v) for k,v in self.bucketList.items()]
  bucketstring = ",".join(buckets_to_list)

  if os.path.exists(configfilepath):
			print "File exists"
			file = open(configfilepath,'r');
			lines = file.readlines();
			file.close()
			aregsExists = False
			regExists = False
			bucketExists = False
			i = 0
			for line in lines:
				print line;
				linearray = line.split("=")
				if linearray[0] == "ActiveRegions":
				 arstring = ",".join(self.activeRegions)
				 lines[i] = "ActiveRegions=%s\n" %arstring
				 aregsExists = True
				i+=1;

			i = 0
			for line in lines:
				print line;
				linearray = line.split("=")
				if linearray[0] == "Region":
				 lines[i] = "Region=%s\n" %self.region
				 regExists = True
				i+=1;

			i = 0
			for line in lines:
				print line;
				linearray = line.split("=")
				if linearray[0] == "Buckets":
				 lines[i] = "Buckets=%s\n" %bucketstring
				 bucketExists = True
				i+=1;

			if aregsExists is False:
			 lines.append("\nActiveRegions=%s\n" %self.activeRegions)

			if regExists is False:
			 lines.append("\nRegion=%s\n" %self.region)

			if bucketExists is False:
			 lines.append("\nBuckets=%s\n" %bucketstring)

			file = open(configfilepath,'w');
			file.writelines(lines);
			file.close()



 def connectCloud(self):
  self.session = boto3.Session(region_name=self.region,aws_access_key_id=self.keyid,aws_secret_access_key=self.secretkey)
  self.sqs = self.session.resource('sqs')
  self.s3 = self.session.resource('s3')
  self.s3Client = self.session.client('s3')
  self.ec2Resource = self.session.resource('ec2')
  self.ec2Client = self.session.client('ec2')

  imageList = self.getImages(self.region)

  if len(imageList)>0:
   self.rn_ami = imageList[0]['ImageId']
   print(self.rn_ami)
  else:
   print 'image not found'

  self.cloudConnect = True


 def backupJobs(self):
  cwd = self.cwd
  print cwd
  jobdir = cwd+"/Data/Jobs/"

  if not os.path.exists(jobdir):
   os.makedirs(jobdir)

  rq = self.renderQueue

  for job in rq:

   print 'Job rendering status is %s' %rq[job].rendering

   if rq[job].rendering is True:

    id = rq[job].id

    jobfilename = "job_"+id+".txt"
    jobfilepath = jobdir+jobfilename

    if not os.path.exists(jobfilepath):

     print rq[job].fileName
     print rq[job].project
     print rq[job].software
     print rq[job].renderName
     print rq[job].layers
     print rq[job].depth
     print rq[job].renderDetail
     print rq[job].passes
     print rq[job].passName
     print rq[job].region

     file = str(rq[job].fileName)
     project = str(rq[job].project)
     software = str(rq[job].software)
     renderName = str(rq[job].renderName)
     layers = str(int(rq[job].layers))
     depth = str(rq[job].depth)
     renderDetail = str(int(rq[job].renderDetail))
     passes = str(int(rq[job].passes))
     passName = str(rq[job].passName)
     region = rq[job].region
     if passName == '':
      passName = 'None';

     filecontents = ",".join([id,file,project,software,renderName,str(layers),depth,str(renderDetail),passes,passName,region])+'\n'

     fl = rq[job].frameList

     for frame in fl:
      frameNum = fl[frame].frameNum
      complete = int(fl[frame].complete)
      renderTime = fl[frame].renderTime
      percentComplete = fl[frame].percentComplete
      sent = int(fl[frame].sent)
      filecontents += ",".join([str(frameNum),str(complete),str(renderTime),str(percentComplete),str(sent)])+'\n'

     print filecontents

     file = open(jobfilepath, 'w')
     file.write(filecontents)
     file.close()



 def checkJobs(self):
  cwd = self.cwd
  print cwd
  jobdir = cwd+"/Data/Jobs/"

  if os.path.exists(jobdir):
   print 'jobs folder there'
   files=os.listdir(jobdir)
   joblist = None
   if len(files)>0:
    print 'files there'

    joblist = []
    for file in files:
     #print file

     filepath = jobdir+file
     print filepath
     fileobj = open(filepath,'r');
     lines = fileobj.readlines();
     fileobj.close()
     os.remove(jobdir+file)
     job = {}
     frames = {}
     frameString = ''
     i = 0
     for line in lines:
      if line != "\n":
       #print line.strip();
       if i == 0:
        jLineArray = line.split(",")
        job['id'] = jLineArray[0]
        job['filename'] = jLineArray[1]
        job['project'] = jLineArray[2]
        job['software'] = jLineArray[3]
        job['renderName'] = jLineArray[4]
        job['layers'] = bool(int(jLineArray[5]))
        job['depth'] = jLineArray[6]
        job['renderdetail'] = bool(int(jLineArray[7].strip()));
        job['passes'] = bool(int(jLineArray[8].strip()))
        job['passName'] = jLineArray[9].strip()
        job['region'] = jLineArray[10].strip()
        #print job
       else:
        frame = {}
        fLineArray = line.split(",")
        frame['frameNum'] = fLineArray[0]
        frame['complete'] = bool(int(fLineArray[1]))
        frame['renderTime'] = fLineArray[2].strip("s")
        frame['percentComplete'] = float(fLineArray[3].strip());
        frame['sent'] = bool(int(fLineArray[4].strip()));
        frames[int(fLineArray[0])]=frame
        frameString+=fLineArray[0]+","

       i+=1;
     #print frames
     #print frameString
     print job
     newjob = cloudRenderJob(job['filename'],job['project'],frameString,job['renderName'],job['layers'],job['depth'],job['renderdetail'],job['id'],self.s3,self.sqs,job['software'],True,job['passes'],job['passName'],job['region'])

					#build a new frame list with frame objects and then
					#assign/overwrite the one just created through cloudRenderJob
					#this is


     for frame in newjob.frameList:
      #print newjob.frameList[frame];
      #print frames[frame]
      newjob.frameList[frame].complete = frames[frame]['complete']
      newjob.frameList[frame].renderTime = frames[frame]['renderTime']
      newjob.frameList[frame].percentComplete = frames[frame]['percentComplete']
      newjob.frameList[frame].sent = frames[frame]['sent']

     newjob.updateStats();

     frameList = newjob.frameList
     for frame in frameList:
      if frameList[frame].sent is False:
       self.renderFramesList.append(frameList[frame])

     rq = self.renderQueue
     rq[newjob.id] = newjob
     newjob.rendering = True;
     self.cloudRunning = True;
     joblist.append(newjob)


    print 'job list = '+str(joblist)
    return joblist

   else:
    print 'files not there'
    return None

  else:
   print 'jobs folder not there'
   return None



 def getRegions(self):
		response = self.ec2Client.describe_regions()

		for region in response["Regions"]:
			self.regions.append(region['RegionName'])


 def createProject(self,projName):
  response = self.s3Client.put_object(
        Bucket=self.bucketname,
        Body='',
        Key=str(projName+'/')
        )

 def populateProjectsList(self):
  #populate 'projects' list
  del self.projects[:]
  client = self.s3Client
  print self.bucketname
  paginator = client.get_paginator('list_objects')
  try:
   for result in paginator.paginate(Bucket=self.bucketname, Delimiter='/'):
    print result;
  except botocore.exceptions.ClientError as e:
   self.mainStatusBar.showMessage("Unable to find storage bucket.")
   pass
  else:
   prefixes = result.get('CommonPrefixes')
   if prefixes != None:
    for prefix in prefixes:
     self.projects.append(str(prefix.get('Prefix')).strip("/"))
     #print(prefix);
   else:
    print  'No projects currently exist.'
    self.projects = []

 def getCurrentProjectItems(self,dir):

		bucket = self.s3.Bucket(self.bucketname)
		projectFiles = self.projectFileList
		del projectFiles[:] #clears list
		root = []
		allCloudObjs = self.currentProjectItems
		allCloudObjs.clear()

		for obj in bucket.objects.filter(Prefix=dir+"/",Delimiter=""):
			keyDict = {}
			if str(obj.key)[-1] != "/":
			 #print obj.key
			 pathArr = obj.key.split("/")
			 relPathArr = pathArr[1:-1]
			 #print relPathArr
			 relPath = "/".join(relPathArr)
			 keyDict['Path'] = relPath;
			 keyDict['Name'] = pathArr[-1];
			 file = keyDict['Path']+"/"+keyDict['Name'];
			 if file[-3:] == "lxo":
                             self.projectFileList.append(file.strip("/"))
			 #print keyDict;
			 allCloudObjs[keyDict['Path']+"/"+keyDict['Name']] = keyDict

		#print allCloudObjs


 def deleteProject(self):
  bucket = self.s3.Bucket(self.bucketname)
  client = self.s3Client
  dir = self.currentProject
  for obj in bucket.objects.filter(Prefix=dir+"/",Delimiter=""):
   obj.delete()
  pKey = str(dir+"/")
  object = self.s3.Object(self.bucketname,pKey)
  object.delete()


 def deleteCloudFiles(self,fileItems):
  print("delete cloud Files")
  dir = self.currentProject+"/"
  #client = self.s3Client
  bucket = self.s3.Bucket(self.bucketname)

  cloudFiles = bucket.objects.filter(Prefix=dir)

  self.mainStatusBar.showMessage("Deleting Files...");

  for file in fileItems:
   filename = file;
   for cFile in cloudFiles:
    keystring = str(cFile.key)
    tempArray = keystring.split("/")
    if tempArray[-1]==filename:
     #print("delete file named %s" %tempArray[-1])
     cFile.delete()
     #self.mainStatusBar.showMessage("File %s deleted." %filename);



 def uploadFiles(self,file,isDir):
  file = file
  proj = self.currentProject
  filePathArray = file.split("/");
  keyname = filePathArray[-1];
  key = proj+"/"+keyname;
  bucketname = self.bucketname

  #print("filearg = %s" %file)
  #print("keyarg = %s" %key)

  transfer = S3Transfer(self.s3Client)


  if isDir == 1:
	  for root,dirs,files in os.walk(file):
	   for file in files:
	    #print "root = %s" %root
	    #print "folderfile = %s" %file
	    progMonitor = ProgressPercentage(root+"/"+file,self.mainStatusBar)
	    transfer.upload_file(root+"/"+file, bucketname, key+"/"+file, callback=progMonitor)
  else:
   progMonitor = ProgressPercentage(file)
   transfer.upload_file(file, bucketname, key, callback=progMonitor)

  print(key)
  print("Upload Files")


 def getRenderFiles(self,key,filename,localPath):
  dir = self.currentProject+"/"
  bucket = self.s3.Bucket(self.bucketname)

  #Need a test here for local directory to make sure it has been set.
  newfile = self.localDirectory+"/"+localPath


  print newfile
  d = os.path.dirname(newfile)
  if not os.path.exists(d):
   os.makedirs(d)

  print key

  object = bucket.Object(key)
  keysize = object.content_length


  dlMonitor = DownloadPercentage(key,keysize)
  self.connect(dlMonitor, SIGNAL("progress(QString)"),self.showProgress)
  self.s3Client.download_file(self.bucketname,key,newfile,Callback=dlMonitor)



 def setRenderFile(self,file):
  self.renderFile = file;
  print self.renderFile

 def submitJob(self,file,frames,project,output,layers,depth,rdet,software,passes,passName):
  print "createRenderJob"
  id = str(hex(int(time.time()*10000000))[-6:])
  reload = False
  job = cloudRenderJob(file,project,frames,output,layers,depth,rdet,id,self.s3,self.sqs,software,reload,passes,passName,self.region)
  rq = self.renderQueue
  rq[job.id] = job
  frameList = job.frameList
  for frame in frameList:
   self.renderFramesList.append(frameList[frame])
  self.cloudRunning = True;
  return job


 def deleteRenderJob(self,id):
  print "deleteRenderJob"
  rq = self.renderQueue
  if id in rq.keys():
   #rq[id].deleteQueues()
   #if rq[id].rendering == True:
   # rq[id].deleteQueues()
   delFrameList = []
   for frame in self.renderFramesList:
    print 'Checking Frame: %s from Job: %s' %(frame.frameNum,frame.id)
    if frame.id == id:
     delFrameList.append(frame)
     print "Frame: %s from Job: %s marked" %(frame.frameNum,id)

   print '======='
   for frame in delFrameList:
    self.renderFramesList.remove(frame)
    print "Frame: %s from Job: %s deleted" %(frame.frameNum,id)

   del rq[id]
  print "job %s deleted" %id
#  if len(rq)>0:
#   self.cloudRunning = True;
  self.cloudRunning = True;



 def updateJobs(self):
  if len(self.instanceList)>0:
   messageList = self.getMessages()
   if len(messageList)>0:
    for messageInfo in messageList:
     if messageInfo['Type'] == "complete":
      inst = messageInfo['inst']
      inst['rendering'] = False;
      print ('Node:%s complete message' %inst['id'])

      self.processMessage(messageInfo)

     if messageInfo['Type'] == 'status':
      print messageInfo['Status']



 def getMessages(self):
  messageList = []
  for inst in self.instanceList:
   rq = inst['rqueue']
   messageInfo = {}
   messages = rq.receive_messages(MaxNumberOfMessages=10,WaitTimeSeconds=3);
   if len(messages) > 0:
    for message in messages:
     m = message.body
     lines = m.splitlines()
     for l in lines:
      data = l.split(":")
      messageInfo[data[0]] = data[1]

     message.delete();
     messageInfo['inst'] = inst
     messageInfo['instId'] = inst['id']
     messageList.append(messageInfo)
  return messageList;

 def processMessage(self,msg):
  if msg['Type'] == "complete":
   id = msg['id']
   print msg
   job = self.renderQueue[id]

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
   #job.frameList.remove(frame)
   print "%s frames out of %s frames complete." %(job.framesComplete,job.totalFrames)

  if msg['Type'] == 'status':
   #send progress message to local?
    print "Instance %s Status: %s)" %(msg['instId'],msg['Status'])
    return instId,msg['Status']


 def sendFrame(self,q,frame):

  jobid = frame.id
  job = self.renderQueue[jobid]

  message = "Type:render\n"
  message += "File:%s\n" %job.fileName
  message += "Project:%s\n" %job.project
  message += "Frame:%s\n" %frame.frameNum
  message += "Output:%s\n" %job.renderName
  message += "Layers:%s\n" %job.layers
  message += "Depth:%s\n" %job.depth
  message += "id:%s\n" %job.id
  message += "RenderDetail:%s\n" %job.renderDetail
  message += "Software:%s\n" %job.software
  message += "Passes:%s\n" %job.passes
  message += "PassName:%s\n" %job.passName
  message += "Bucket:%s" %self.bucketname
  q.send_message(MessageBody=message)

  frame.sent = True;




 def sendFrames(self):
  print "number of render frames is %s" %len(self.renderFramesList)
  print self.instanceList

  if len(self.instanceList)>0:
   for inst in self.instanceList:
    if len(self.renderFramesList)>0:
     if inst['rendering']==False:
      q = inst['squeue']

      frame = self.renderFramesList.pop();

      self.sendFrame(q,frame)

      inst['rendering'] = True;

      print 'Sending frame %s to node: %s' %(frame.frameNum,inst['id'])

    else:
     print 'frame list empty'


 def clearFiles(self,fileList):
  if len(fileList)>0:

   fileListString = ",".join(fileList);

   for inst in self.instanceList:
    if inst['rendering']==False:
     q = inst['squeue']

     message = "Type:cmd\n"
     message += "Cmd:clearFile\n"
     message += "Args:%s\n" %fileListString

     q.send_message(MessageBody=message)

     print 'sending clear frame cmd to node: %s' %inst['id']
     return True
    else:
     print 'Instance:%s is busy. Command not sent.' %inst['id']
     return False

 def clearProject(self,project):
  if project != None:

   for inst in self.instanceList:
    if inst['rendering']==False:
     q = inst['squeue']

     message = "Type:cmd\n"
     message += "Cmd:clearProject\n"
     message += "Args:%s\n" %project

     q.send_message(MessageBody=message)

     print 'sending clear project cmd to node: %s' %inst['id']
     return True
    else:
     print 'Instance:%s is busy. Command not sent.' %inst['id']
     return False


 def checkSpotRequests(self):
  nodeCount = 1;
  response = self.ec2Client.describe_instances(Filters=[{'Name':'tag:Type','Values':['RenderNode']},{'Name':'instance-state-name','Values':['running','pending']}])
  print response
  if len(response['Reservations'])>0:
   nodeList = response['Reservations'][0]['Instances']
   print nodeList
   nodeCount = len(nodeList)
   print nodeCount
  else:
   print 'No Nodes Active'


  i = nodeCount
  for instance in instances:
   namenum = str(i).zfill(3)
   name = 'RenderNode-'+namenum
   print(instance.id, instance.instance_type)
   waiter = client.get_waiter('instance_exists')
   waiter.wait(InstanceIds=[instance.id])
   response = ec2.create_tags(Resources=[instance.id],Tags=[{'Key':'Name','Value':name},{'Key':'Type','Value':'RenderNode'}])
   print response
   i+=1


 def launchSpotInstances(self,price,count,ami,cpu,size,alarm):
  print "launchSpotInstances"
  count = int(count)
  size = int(size)
  securitygroupDict = {}
  securitygroupDict['sg'] = self.securitygroup
  sg = [securitygroupDict['sg']]
  client = self.ec2Client
  keyname = self.key
  userdatastring = "#!/bin/sh \n sudo stdbuf -o0 python /opt/modoRenderCloud/renderNode.py > /opt/modoRenderCloud/startupLog.txt 2>&1"
  userdata=base64.b64encode(userdatastring)

  response = self.ec2Client.describe_images(Filters=[{'Name':'name','Values':['RenderNodeAMI']},{'Name':'state','Values':['available']}])
  imageList = response['Images']

  if len(imageList)>0:
   self.rn_ami = imageList[0]['ImageId']
   print(self.rn_ami)
   type = cpu
   response = client.request_spot_instances(
    DryRun=False,
    SpotPrice=price,
    InstanceCount=count,
    Type='one-time',
    LaunchSpecification={
        'ImageId': self.rn_ami,
        'KeyName': keyname,
        'InstanceType': type,
        'UserData':userdata,
        'IamInstanceProfile':{'Name': 'RenderNode'},
        'BlockDeviceMappings':[
         {
            'DeviceName': '/dev/sda1',
            'Ebs': {
                'VolumeSize': size,
             },
         },
        ]
     }
    )

   for spot in response['SpotInstanceRequests']:
    print spot['State'];
    spotInfo = {}
    spotInfo['spotid'] = spot['SpotInstanceRequestId']
    spotInfo['price'] = spot['SpotPrice']
    spotInfo['type'] = spot['LaunchSpecification']['InstanceType']
    spotInfo['name'] = 'Spot Request'
    spotInfo['region'] = spot['LaunchSpecification']['Placement']['AvailabilityZone']
    spotInfo['state'] = spot['State']
    spotInfo['alarm'] = alarm


    self.spotRequestList.append(spotInfo)

   self.spotCheckCount = 5;
   self.spotRequests = True
   return self.spotRequestList

  else:
   print 'image not found'



 def getImages(self,region):
  newSession = boto3.Session(region_name=region,aws_access_key_id=self.keyid,aws_secret_access_key=self.secretkey)
  newClient = newSession.client('ec2')
  response = newClient.describe_images(Filters=[{'Name':'name','Values':['RenderNodeAMI']},{'Name':'state','Values':['available']}])
  imageList = response['Images']
  return imageList

 def getCopyImages(self,region):
  newSession = boto3.Session(region_name=region,aws_access_key_id=self.keyid,aws_secret_access_key=self.secretkey)
  newClient = newSession.client('ec2')
  response = newClient.describe_images(Filters=[{'Name':'name','Values':['RenderNodeAMI']}])
  imageList = response['Images']
  return imageList

 def getKeyPairs(self,region):
  newSession = boto3.Session(region_name=region,aws_access_key_id=self.keyid,aws_secret_access_key=self.secretkey)
  newClient = newSession.client('ec2')
  response = newClient.describe_key_pairs(Filters=[{'Name':'key-name','Values':[self.key]}])
  keyList = response['KeyPairs']
  return keyList

 def copyImage(self,region):
  newSession = boto3.Session(region_name=region,aws_access_key_id=self.keyid,aws_secret_access_key=self.secretkey)
  newClient = newSession.client('ec2')
  response = newClient.copy_image(
    SourceRegion=self.region,
    SourceImageId=self.rn_ami,
    Name='RenderNodeAMI',
    )
  print response
  return response

 def createKey(self,region):
  newSession = boto3.Session(region_name=region,aws_access_key_id=self.keyid,aws_secret_access_key=self.secretkey)
  newClient = newSession.client('ec2')
  response = newClient.create_key_pair(KeyName=self.key)
  print response
  return response

 def createAlarm(self,instanceid,periodcount,period,threshold):
  cwclient = self.session.client('cloudwatch')
  alarmName = '%s_alarm' %instanceid
  alarmaction = 'arn:aws:automate:%s:ec2:terminate' %self.region
  response = cwclient.put_metric_alarm(
      AlarmName=alarmName,
      ActionsEnabled=True,
      AlarmActions=[
          alarmaction,
      ],
      MetricName='CPUUtilization',
      Namespace='AWS/EC2',
      Statistic='Average',
      Dimensions=[
          {
              'Name': 'InstanceId',
              'Value': instanceid
          },
      ],
      Period=period,
      EvaluationPeriods=periodcount,
      Threshold=threshold,
      ComparisonOperator='LessThanThreshold'
  )



 def launchInstances(self,count,ami,cpu,size,alarm):
  print "launchInstances"
  count = int(count)
  size = int(size)
  securitygroupDict = {}
  securitygroupDict['sg'] = self.securitygroup
  sg = [securitygroupDict['sg']]
  client = self.ec2Client
  ec2 = self.ec2Resource
  keyname = self.key
  userdatastring = "#!/bin/sh \n sudo stdbuf -o0 python /opt/modoRenderCloud/renderNode.py > /opt/modoRenderCloud/startupLog.txt 2>&1"
  userdata=userdatastring
  type = cpu

  response = self.ec2Client.describe_images(Filters=[{'Name':'name','Values':['RenderNodeAMI']},{'Name':'state','Values':['available']}])
  imageList = response['Images']

  if len(imageList)>0:
   self.rn_ami = imageList[0]['ImageId']
   print(self.rn_ami)
  else:
   print 'image not found'


  nodeCount = 1

  existinginstances = list(ec2.instances.filter(
   Filters=[{'Name': 'tag:Type', 'Values': ['RenderNode']},{'Name':'instance-state-name','Values':['running','pending']}]))

  nodeCount = len(existinginstances)+1


  instances = ec2.create_instances(
  	ImageId=self.rn_ami,
  	KeyName=keyname,
  	UserData=userdata,
  	InstanceType=type,
  	BlockDeviceMappings=[
        {
            'DeviceName': '/dev/sda1',
            'Ebs': {
                'VolumeSize': size,
            },
        },
   ],
   IamInstanceProfile={
  		'Name':'RenderNode'
  	},
  	MinCount=count,
  	MaxCount=count)

  i = nodeCount
  instList = [];

  for instance in instances:
   namenum = str(i).zfill(3)
   name = 'RenderNode-'+namenum
   print(instance.id, instance.instance_type)
   waiter = client.get_waiter('instance_exists')
   waiter.wait(InstanceIds=[instance.id])
   response = ec2.create_tags(Resources=[instance.id],Tags=[{'Key':'Name','Value':name},{'Key':'Type','Value':'RenderNode'}])
   print response

   #create node message queue
   sqName = '%s_SQueue' %instance.id
   rqName = '%s_RQueue' %instance.id
   sq = self.sqs.create_queue(QueueName=sqName, Attributes={'DelaySeconds': '0'})
   rq = self.sqs.create_queue(QueueName=rqName, Attributes={'DelaySeconds': '0'})

   instInfo = {}
   instInfo['id'] = instance.id
   instInfo['type'] = instance.instance_type
   instInfo['name'] = name
   instInfo['region'] = instance.placement['AvailabilityZone']
   instInfo['state'] = instance.state['Name']
   instInfo['squeue'] = sq
   instInfo['rqueue'] = rq
   instInfo['rendering'] = False;
   instInfo['active'] = True;
   instInfo['markedinactive'] = False;

   self.instanceList.append(instInfo)

   instList.append(instInfo)

   if alarm != None:
    self.createAlarm(instance.id,alarm['PeriodCount'],alarm['Period'],alarm['Threshold'])

   i+=1

  self.cloudRunning = True;
  return instList

 def updateInstancesInfo(self,ids):
  ec2 = self.ec2Resource
  instances = ec2.instances.filter(
    Filters=[{'Name': 'instance-id', 'Values': ids}])
  count = len(self.instanceList)+1
  for instance in instances:
   print(instance.id, instance.instance_type, instance.tags)
   for inst in self.instanceList:
    if inst['id'] == instance.id:
     inst['state'] = instance.state['Name']



 def initSpotInstance(self,newinstid,alarm):
  ec2 = self.ec2Resource
  instances = ec2.instances.filter(
    Filters=[{'Name': 'instance-id', 'Values': [newinstid]}])
  count = len(self.instanceList)+1
  for instance in instances:
   sqName = '%s_SQueue' %instance.id
   rqName = '%s_RQueue' %instance.id
   sq = self.sqs.create_queue(QueueName=sqName, Attributes={'DelaySeconds': '0'})
   rq = self.sqs.create_queue(QueueName=rqName, Attributes={'DelaySeconds': '0'})

   instInfo = {}
   print(instance.id, instance.instance_type, instance.tags)
   instInfo['id'] = instance.id
   instInfo['type'] = instance.instance_type
   instInfo['name'] = 'None'
   instInfo['region'] = instance.placement['AvailabilityZone']
   instInfo['state'] = instance.state['Name']
   instInfo['squeue'] = sq
   instInfo['rqueue'] = rq
   instInfo['rendering'] = False;
   instInfo['active'] = True;
   instInfo['markedinactive'] = False;

   if instance.tags is not None:
    if len(instance.tags) > 0:
     for tag in instance.tags:
      if 'Name' in tag.values():
       print tag['Value']
       instInfo['name'] = tag['Value']
   else:
    namenum = str(count).zfill(3)
    name = 'RenderNode-'+namenum
    response = ec2.create_tags(Resources=[instance.id],Tags=[{'Key':'Name','Value':name},{'Key':'Type','Value':'RenderNode'}])
    instInfo['name'] = name

   self.instanceList.append(instInfo)

   if alarm != None:
    self.createAlarm(instance.id,alarm['PeriodCount'],alarm['Period'],alarm['Threshold'])

   self.cloudRunning = True
   return instInfo



 def getSpotRequestInfo(self,spotid):
  ec2 = self.ec2Client
  ec2R = self.ec2Resource
  response = ec2.describe_spot_instance_requests(SpotInstanceRequestIds=[spotid])
  #print 'spot request qeury = %s' %response

  if len(response['SpotInstanceRequests'])>0:
   for spot in response['SpotInstanceRequests']:
    spotInfo = {}
    spotInfo['spotid'] = spot['SpotInstanceRequestId']
    spotInfo['price'] = spot['SpotPrice']
    spotInfo['type'] = spot['LaunchSpecification']['InstanceType']
    spotInfo['name'] = 'Spot Request'
    spotInfo['region'] = spot['LaunchSpecification']['Placement']['AvailabilityZone']
    spotInfo['state'] = spot['State']
    spotInfo['alarm'] = None

    if (spot['State'] == 'active'):
     spotInfo['id'] = spot['InstanceId']
     for spotListEntry in self.spotRequestList:
      if spotListEntry['spotid'] == spotid:
       spotInfo['alarm']=spotListEntry['alarm']
       self.spotRequestList.remove(spotListEntry)
   return spotInfo


 def getSpotRequests(self):
  del self.spotRequestList[:]
  ec2 = self.ec2Client
  ec2R = self.ec2Resource
  response = ec2.describe_spot_instance_requests(Filters=[{'Name':'state','Values':['open','active']}])
  print 'spot request qeury = %s' %response

  if len(response['SpotInstanceRequests'])>0:
   for spot in response['SpotInstanceRequests']:
    print spot['State'];
    spotInfo = {}
    spotInfo['id'] = spot['SpotInstanceRequestId']
    spotInfo['price'] = spot['SpotPrice']
    spotInfo['type'] = spot['LaunchSpecification']['InstanceType']
    spotInfo['name'] = 'Spot Request'
    spotInfo['region'] = spot['LaunchSpecification']['Placement']['AvailabilityZone']
    spotInfo['state'] = spot['State']
    if (spot['State'] != 'active') and (spot['SpotInstanceRequestId'] not in self.spotCancelList):
     self.spotRequestList.append(spotInfo)
   return self.spotRequestList




 def getInstances(self):
  del self.instanceList[:]
  ec2 = self.ec2Resource
  instances = list(ec2.instances.filter(
    Filters=[{'Name': 'tag:Type', 'Values': ['RenderNode']},{'Name':'instance-state-name','Values':['running','pending']}]))

  if len(instances)>0:
   del self.instanceList[:]
   for instance in instances:

    sqName = '%s_SQueue' %instance.id
    rqName = '%s_RQueue' %instance.id

    sq = self.sqs.get_queue_by_name(QueueName=sqName)
    rq = self.sqs.get_queue_by_name(QueueName=rqName)



#     sq = self.sqs.create_queue(QueueName=sqName, Attributes={'DelaySeconds': '0'})
#     rq = self.sqs.create_queue(QueueName=rqName, Attributes={'DelaySeconds': '0'})




    instInfo = {}
    print(instance.id, instance.instance_type, instance.tags)
    instInfo['id'] = instance.id
    instInfo['type'] = instance.instance_type
    instInfo['name'] = 'None'
    instInfo['region'] = instance.placement['AvailabilityZone']
    instInfo['state'] = instance.state['Name']
    instInfo['squeue'] = sq
    instInfo['rqueue'] = rq
    instInfo['rendering'] = False;
    instInfo['active'] = True;
    instInfo['markedinactive'] = False;

    if len(instance.tags) > 0:
     for tag in instance.tags:
      if 'Name' in tag.values():
       print tag['Value']
       instInfo['name'] = tag['Value']

    self.instanceList.append(instInfo)
   else:
    pass
    #put alarm check/delete here

  return self.instanceList


 def monitorRender(self):
  print "Monitor Render"




 def cancelSpotRequests(self,spotList):
  print 'cancel spot request'
  ec2 = self.ec2Client
  if len(spotList)>0:
   response = ec2.cancel_spot_instance_requests(SpotInstanceRequestIds=spotList)
  for spot in spotList:
   for spotRequest in self.spotRequestList:
    if spot == spotRequest['spotid']:
     self.spotRequestList.remove(spotRequest);


 def terminateInstances(self,compList):
  #message = "MessageType:terminate\n"
  #self.ccq.send_message(MessageBody=message)
  #print message
  #print "Terminate Instances"
  idList = []
  for comp in compList:
   id = comp['id']
   idList.append(id)
   print(id)
   self.deleteAlarm(id)
   for inst in self.instanceList:
    if inst['id'] == id:
     self.instanceList.remove(inst)
     inst['squeue'].delete()
     inst['rqueue'].delete()

  self.ec2Resource.instances.filter(InstanceIds=idList).terminate()




 def deleteAlarm(self,instanceid):
  cwresource = self.session.resource('cloudwatch')

  alarms = cwresource.alarms.all()

  for alarm in alarms:
   print alarm.dimensions

   for dimension in alarm.dimensions:
    if dimension['Name'] == 'InstanceId':
     if dimension['Value'] == instanceid:
      print 'alarm match'
      alarm.delete()

 def cleanUpAlarms(self):
  ec2= self.ec2Resource

  instances = ec2.instances.filter(Filters=[{'Name': 'tag:Type', 'Values': ['RenderNode']},{'Name':'instance-state-name','Values':['terminated']}])
  for instance in instances:
   print(instance.id, instance.instance_type, instance.tags)
   self.deleteAlarm(instance.id)


 def getSpotPriceHistory(self,type):
  client = self.ec2Client;

  instanceTypes = [type]

  response = client.describe_spot_price_history(
   DryRun=False,
   StartTime=datetime.datetime.utcnow()-datetime.timedelta(minutes=30),
   EndTime=datetime.datetime.utcnow(),
   InstanceTypes=instanceTypes,
   ProductDescriptions=['Linux/UNIX'],
   MaxResults=123,
  )

  return response['SpotPriceHistory']

 def getAvailabilityZones(self):
  zoneList = []
  response = self.ec2Client.describe_availability_zones()

  for zone in response['AvailabilityZones']:
   print zone['ZoneName']
   zoneList.append(zone['ZoneName'])

  return zoneList


class cloudRenderJob():
 def __init__(self,filename,project,frames,rendername,layers,depth,rdet,id,s3,sqs,software,reload,passes,passName,region):
  self.sqs = sqs
  self.s3 = s3
  self.fileName = filename
  self.project = project
  self.software = software
  self.frameList = None
  self.renderName = rendername
  self.layers = layers
  self.depth = depth
  self.passes = passes
  self.passName = passName
  self.renderDetail = rdet
  self.framesComplete = 0
  self.totalFrames = 0
  self.lastFrame = 0
  self.lastRenderFile = None
  self.lastFrameTime = 0.0
  self.rendering = True;
  self.id = id
  self.region = region
  self.bucket = None
  self.cq = None #command queue object
  self.mq = None #message queue object
  self.treeRow = None
  self.newFrame = False;
  self.makeFrameList(frames)
#  if reload is False:
#   self.createCommandQueue()
#   self.createMessageQueue()
#   self.sendCommands()

 def makeFrameList(self,frames):
  #print "make Frame List"
  #frameList = []
  frameList = {}
  frameRawArray = frames.split(",")
  frameRawArray = ' '.join(frameRawArray).split()

  for frame in frameRawArray:
   rangeCheck = frame.split("-");
   i = int(rangeCheck[0]);
   if len(rangeCheck)>1:
    while i <= int(rangeCheck[1]):
     frame = renderFrame(i,self.id);
     frameList[i]=frame;
     #frameList.append(str(i));
     i+=1;
   else:
    frame = renderFrame(i,self.id);
    frameList[i]=frame;
    #frameList.append(frame);
  self.totalFrames = len(frameList)
  self.frameList = frameList
  #print "job frameList =%s" %frameList

 def createCommandQueue(self):
  print "createCommandQueue"
  qName = "job_"+str(self.id)+"_commandQueue"
  q = self.sqs.create_queue(QueueName=qName, Attributes={'DelaySeconds': '0'})
  self.cq = q
  #self.sendCommands()

 def createMessageQueue(self):
  print "createMessageQueue"
  qName = "job_"+str(self.id)+"_messageQueue"
  q = self.sqs.create_queue(QueueName=qName, Attributes={'DelaySeconds': '0'})
  self.mq = q

 def startJob(self):
  print "start job"
  #self.sendCommands()

 def stopJob(self):
  print "stop job"
  #purge self.cq

 def sendCommands(self):
  print "sendCommands"
  frameList = self.frameList

  for frame in frameList:
   message = "Type:cmd\n"
   message += "File:%s\n" %self.fileName
   message += "Project:%s\n" %self.project
   message += "Frame:%s\n" %frameList[frame].frameNum
   message += "Output:%s\n" %self.renderName
   message += "Layers:%s\n" %self.layers
   message += "Depth:%s\n" %self.depth
   message += "id:%s\n" %self.id
   message += "RenderDetail:%s\n" %self.renderDetail
   message += "Software:%s\n" %self.software
   message += "Passes:%s\n" %self.passes
   message += "PassName:%s" %self.passName
   self.cq.send_message(MessageBody=message)
   print message


 def deleteQueues(self):
  print "deleteQueues"
  self.mq.delete()
  self.cq.delete()


 def getMessages(self):
  print "get job %s messages" %self.id
  messageInfo = {}
  messages = self.mq.receive_messages(MaxNumberOfMessages=10,WaitTimeSeconds=6);
  if len(messages) > 0:
   print len(messages)
   for message in messages:
    messageText = message.body
    print("message there");
    lines = messageText.splitlines()
    for l in lines:
     data = l.split(":")
     messageInfo[data[0]] = data[1]
    if messageInfo['Type']=='msg':
     message.delete();
     self.processMessage(messageInfo)
     #return message
  else:
   messageInfo = None

 def processMessage(self,msg):
  if msg['Status'] == 'begin':
   print msg['Message'];
   #self.rendering = True;

  if msg['Status'] == 'complete':
   self.newFrame = True;
   #update jobs frameList and frames complete
   frame = int(msg['Frame'])
   self.lastFrame = int(msg['Frame'])
   self.lastFrameTime = msg['Time']
   self.lastRenderFile = msg['FileList']
   print "Frame %s Complete!" %msg['Frame']
   print "Frame %s Render Time : %s" %(msg['Frame'],msg['Time'])
   self.framesComplete +=1
   self.frameList[frame].complete = True
   self.frameList[frame].renderTime = self.lastFrameTime;
   #self.frameList.remove(frame)
   if self.framesComplete == self.totalFrames:
    self.rendering = False
    self.deleteQueues();
  if msg['Status'] == 'rendering':
   #send progress message to local?
    print "Status: Frame %s is %s percent complete" %(msg['Frame'],msg['Percent'])

  print "%s frames out of %s frames complete." %(self.framesComplete,self.totalFrames)

 def updateStats(self):
  #print 'frames'
  for frame in self.frameList:
   #print self.frameList[frame].complete
   if self.frameList[frame].complete is True:
    #print 'completely true';
    self.framesComplete += 1;

 def update(self):
  print "job update"
  #updateMsg = self.getMessages()
  #self.getMessages()
  #return updateMsg

class renderFrame():
 def __init__(self,number,id):
  self.id = id
  self.frameNum = number;
  self.complete = False;
  self.renderTime = 0.0;
  self.percentComplete = 0.0;
  self.sent = False;
