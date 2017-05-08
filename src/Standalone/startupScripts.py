# python


def renderNode():
 rendernode = """#!/usr/bin/python

import boto3
import botocore
import subprocess
from time import time
import time
import datetime
import sys
import os
import ast
import thread
from threading import Thread
import requests
import json
import shutil

class renderNode():

 def __init__(self):
 
  response = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document')
  rjson = json.loads(response.text)
  region = rjson['region'];
  print region
  
  self.instanceId = rjson['instanceId']
  self.rqName = "%s_RQueue" %self.instanceId;
  self.sqName = "%s_SQueue" %self.instanceId;
  
 
  self.rendering = False
  self.frameRenderTime = None
  
  self.region = region;
  
#  self.bucketname = "trevbucket"
  
#  self.bucketname = "%s--%s" %('*bucketnamepointer',self.region)

  self.bucketname = None 
  
  os.chdir("/opt/modoRenderCloud/")

  self.modocl = ""
  self.modosc = None
  self.modopipe = None
  
  self.software = None
  self.currentFile = None
  self.currentProject = None
  self.currentDir = None
  
  self.session = boto3.Session(region_name = self.region)


  self.sqs = self.session.resource('sqs')
  self.s3 = self.session.resource('s3')
  self.sqsClient = self.session.client('sqs')
  
  try:
   self.sq = self.sqs.get_queue_by_name(QueueName=self.sqName)
   self.rq = self.sqs.get_queue_by_name(QueueName=self.rqName)
  except botocore.exceptions.ClientError as e: #if there is an error pass through to continue for loop
   print "ERROR"
   self.rq = None
   self.sq = None



  t1 = Thread(target=self.startNode)
  t2 = Thread(target=self.sysCheckTimer,args=())
  t1.start()
  #t2.start()

  
 def sysCheckTimer(self):
  print "cc timer called"
  while True:
   self.sysCheck()
   time.sleep(5)

 
 def sysCheck(self):
  print 'sysCheck'
 
 def downloadFile(self,file):
  print "downloading file"
  bucket = self.s3.Bucket(self.bucketname)
  newfile = "%s/%s" %(self.currentDir,file)
  key = "%s/%s" %(self.currentProject,file)
  
  print "bucketname = %s" %self.bucketname
  print "key = %s" %key
  print "newfile = %s" %newfile
        
  bucket.download_file(key, newfile) #DOWNLOADS FILE


 def downloadProj(self,dir):
  dir = dir+"/"
  print dir
  bucket = self.s3.Bucket(self.bucketname)  
  for obj in bucket.objects.filter(Prefix=dir):
   if str(obj.key)[-1] != "/": #ONLY PROCESSES ITEMS THAT ARE NOT EMPTY FOLDERS
    temp = str(obj.key)
    #print temp
    tempArray = temp.split("/")
    #tempArray.pop(0);
    newfile = "";
    
    parentDir = tempArray[-2]
    parentDirArray = parentDir.split("_")
    
    if (parentDirArray[-1] != "renderframes") and (parentDirArray[-1] != "logfiles"): #KEEP FROM DOWNLOADING RENDERED FRAMES   
     if len(tempArray)>1: #IF FILE IS IN SUBFOLDER CHECKS TO SEE IF FOLDER EXISTS AND CREATES IT IF IT DOESN'T
      newfile = "/".join(tempArray)
      d = os.path.dirname(newfile)
      if not os.path.exists(d):
       os.makedirs(d)
     else:
      newfile = tempArray[0]
     print newfile
     print "downloading"
     bucket.download_file(obj.key, newfile) #DOWNLOADS FILE
     
 def checkProjExists(self,dir):
  dir = dir.replace('/', '')
  dir = dir.strip()
  print dir
  if not os.path.exists(dir):
   os.makedirs(dir)
   os.makedirs(dir+"/renderframes")
   #self.command("pathalias.path {%s}" %self.currentDir)
   #self.command("query platformservice alias ? {RenderCloud:}") 
   print "download project"
   print "does not exist"
   self.downloadProj(dir)
  else:
   print "exists"
   
 def openPipe(self):
		print "open pipe"
		pipe = subprocess.Popen(self.modocl, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
		header = pipe.stdout.readline();
		return pipe
   
 def command(self,commText):
  #print 'command called'
  retVal = ""
  p = self.modopipe;
  #print p
  #print commText
  p.stdin.write(commText+' \\n');
  output = "";
  outlog = "";
  while True:
   output = p.stdout.readline();
   #print "output = %s" %output
   if output.strip() != "+ ok" and output.strip() != "> + ok":
    #print "stdout =%s" %output, ;
    #put check here for if outlog[0:3] == "> !": to get rolling render log
    #and send to parser to send out rendering start and percent status
    outlog += output
   if output.strip() == "+ ok" or output.strip() == "> + ok" or output[0:1].strip() == "-":
    break;
    
  if outlog != "":
   #print "pipe out =%s" %outlog,;
   #print outlog[0:3];
   if outlog[0:3] == "> :":
    retVal = outlog.split(":")[-1].strip();
    return retVal
   if outlog[0:3] == "> !":
    #print "render =%s" %outlog;
    retVal = outlog
    return retVal
   if outlog[0:3] == "> #":
    retVal = outlog
    return retVal
   if outlog[0:3] == "-":
    retVal = outlog
    return retVal
  

 def closePipe(self):
  pipe = self.modopipe
  pipe.stdin.write("app.quit \\n")
  try:
   pipe.kill()
  except OSError:
   pass
   
 def openScene(self,scene):
  print "scene open"
  self.command("scene.open {%s}" %scene)
  self.currentFile = scene
  print "currentFile = %s" %self.currentFile
  
 def closeScene(self):
  self.command("!scene.close")
 
 def getRenderItem(self):
  itemQueryString = self.command("query sceneservice item.N ?");
  print "itemQueryString = %s" %itemQueryString;
  
  itemNum = int(itemQueryString)
  
  for i in range(itemNum):
   type = self.command("query sceneservice item.type ? %s" %i)
   
   if type == "polyRender":
    renderID = self.command("query sceneservice item.id ?")
    return renderID;
  
 def getRenderOutputs(self):
  itemNum = int(self.command("query sceneservice item.N ?"));
  renderOutputs = []
  
  for i in range(itemNum):
   type = self.command("query sceneservice item.type ? %s" %i)
   
   if type == "renderOutput":
    renderID = self.command("query sceneservice item.id ?")
    renderOutputs.append(renderID)
    
  return renderOutputs;
  
 def getRenderPasses(self,passName):
  itemNum = int(self.command("query sceneservice group.N ?"));
  renderPassesAll = []
  renderPasses = []

  renderPass = passName
    
  print passName
  for i in range(itemNum):
  	id = self.command("query sceneservice group.id ? %s" %i)
  	passtype = self.command("query sceneservice render.tags ? %s" %id)
  	if passtype == 'render':
  		name = self.command("query sceneservice group.name ? %s" %id)
  		renderPassesAll.append(name)
  
  if len(renderPassesAll)>0:
   if renderPass != None:
    for rpass in renderPassesAll:
     if rpass == renderPass:
      renderPasses.append(rpass);
    if len(renderPasses)==0:
     renderPasses=None
   else:
    renderPasses = None
  
  else:
   renderPasses = None
  
  return renderPasses 			

 def renderFrame(self,frame,savepath,layers,depth,passes,passName):
  print "render frame"
  print "savepath = %s" %savepath;
  renderItem = self.getRenderItem();

  self.command("select.subItem {%s} set" %renderItem)
  self.command("item.channel first %s" %frame)
  self.command("item.channel last %s" %frame)
  self.command("log.toConsoleRolling true")
  
  if layers is True:
   print 'render layers'
   if depth == "16-bit":
    print '16-bit'
    rendercmd = "render.animation {%s} %s" %(savepath,'openexrlayers')
   else:
    print '32-bit'
    rendercmd= "render.animation {%s} %s" %(savepath,'openexrlayers32')
   
  else:
   print 'render flat'
   rendercmd = "render.animation {%s} *" %(savepath)
 
  renderPasses = None
  
  if passName == '':
   passName = None;
  
  if passes is True and passName != None:
   renderPasses = self.getRenderPasses(passName)
  
  renderlog = ''
  
  print 'renderPasses = %s' %renderPasses
   
  if renderPasses != None:
   for rpass in renderPasses:
    passcmd = ' group:%s' %rpass
    renderlog += self.command(rendercmd+passcmd);
  else:
   renderlog = self.command(rendercmd);

  
  return renderlog
 
 def getMessages(self):
  response = self.sqsClient.list_queues(QueueNamePrefix='%s_SQueue'%self.instanceId)
  if len(response['QueueUrls'])>0:
   qUrl = response['QueueUrls'][0]
   print qUrl
   try:
    print self.sqName
    self.sq = self.sqs.get_queue_by_name(QueueName=self.sqName)
    print self.sq
   except botocore.exceptions.ClientError as e: #if there is an error pass through to continue for loop
    print "ERROR"
    self.rq = None
    return None
   else: # if there is not an error test to see if there are messages in the queue
    try:
     response = self.sqsClient.get_queue_attributes(QueueUrl=qUrl,AttributeNames=['ApproximateNumberOfMessages','ApproximateNumberOfMessagesNotVisible'])
    except botocore.exceptions.ClientError as e: #if there is an error pass back to the for loop
     print e
     return None
    else:
     visMsg = response['Attributes']['ApproximateNumberOfMessages']
     invisMsg = response['Attributes']['ApproximateNumberOfMessagesNotVisible']
     if visMsg+invisMsg != 0: #if there are messages try to recieve them
      try:
       messages = self.sq.receive_messages(MaxNumberOfMessages=10,WaitTimeSeconds=5);
      except botocore.exceptions.ClientError as e: #if there is an error pass back to the for loop
       print e
       messages = []
       return None
      else: #if there is not an error double check to make sure messages were received
       if len(messages) > 0:
        return messages #if messages were received return the message



 def processMessage(self,message):
  print "process messages"
  
  if message != None:
   messageInfo = {}
   m = message.body
   print("message there");
   lines = m.splitlines()
   for l in lines:
    data = l.split(":")
    messageInfo[data[0]] = data[1]
    
   message.delete();
  else:
   messageInfo = None
  
  return messageInfo
  
 def completeMessage(self,file,frame,id,fileList):
		print "Complete Message"
		fileListString = ",".join(fileList);
		message = "Type:complete\\n"
		message += "File:%s\\n" %file
		message += "Frame:%s\\n" %frame
		message += "Status:complete\\n"
		message += "FileList:%s\\n"%fileListString
		message += "Time:%s\\n" %self.frameRenderTime
		message += "id:%s" %id
		try:
		 self.rq = self.sqs.get_queue_by_name(QueueName=self.rqName)
		 self.rq.send_message(MessageBody=message)
		except botocore.exceptions.ClientError as e: #if there is an error pass through to continue for loop
		 print "ERROR"
		 pass

		print message

 def clearFileCompleteMessage(self,status):
		print "Clear File Complete Message"
		message = "Type:status\\n"
		message += "Status:%s" %status
		try:
		 self.rq = self.sqs.get_queue_by_name(QueueName=self.rqName)
		 self.rq.send_message(MessageBody=message)
		except botocore.exceptions.ClientError as e: #if there is an error pass through to continue for loop
		 print "ERROR"
		 pass
		print message
 
 def clearProjectCompleteMessage(self,status):
		print "Clear Project Complete Message"
		message = "Type:status\\n"
		message += "Status:%s" %status
		try:
		 self.rq = self.sqs.get_queue_by_name(QueueName=self.rqName)
		 self.rq.send_message(MessageBody=message)
		except botocore.exceptions.ClientError as e: #if there is an error pass through to continue for loop
		 print "ERROR"
		 pass
		print message
 
 def uploadRenderFile(self,localpath,bucketname,uploadpath):
  print "Upload Render File"
  file = localpath
  key = uploadpath
  try:
   self.s3.Object(bucketname, key).put(Body=open(file, 'rb'))
   os.remove(file)
  except botocore.exceptions.ClientError as e: #if there is an error pass through to continue for loop
   print "ERROR"
   pass


 def doRender(self,frameInfo):
 		 
		 if frameInfo != None: #IF INSTRUCTIONS ARE THERE
		  project = frameInfo['Project']
		  file = frameInfo['File']
		  frame = frameInfo['Frame'].strip()
		  name = frameInfo['Output']
		  id = frameInfo['id']
		  layers = ast.literal_eval(frameInfo['Layers'])
		  depth = frameInfo['Depth']
		  software = frameInfo['Software']
		  passes = ast.literal_eval(frameInfo['Passes'])
		  passName = frameInfo['PassName']
		  self.bucketname = frameInfo['Bucket']
		  
		  if software != self.software: #IF SOFTWARE FROM MESSAGE IS NOT THE CURRENTLY SELECTED SOFTWARE (RETURNS FALSE FIRST TIME)
		   self.software = software;
		   self.modocl = "/opt/modoRenderCloud/%s/modo_cl" %self.software #SET PATH TO SOFTWARE

		   if self.modopipe != None: #IF THERE IS ALREADY A PIPE THEN CLOSE IT AND OPEN IT WITH NEW SOFTWARE PATH
		    self.closePipe();
		    self.modopipe = self.openPipe();
		   else:
		    self.modopipe = self.openPipe(); #IF NOT PIPE CURRENTLY EXISTS, OPEN A PIPE
		  
		  if self.currentProject != project:
		   self.currentProject = project
		   self.checkProjExists(project)
		   
		   self.command("pathalias.create {%s} {/opt/modoRenderCloud/%s}" %(self.currentProject, self.currentProject))
		   
		   if self.modopipe != None:
		    self.closePipe();
		    self.modopipe = self.openPipe();

		  print "%s/%s" %(os.getcwd(),project)
		  self.currentDir = "%s/%s" %(os.getcwd(),project)

		  if self.currentFile != file: #CHECK TO SEE IF FILE IN NEW COMMAND IS THE SAME AS THE LAST COMMAND
		   print "new scene"
		   openfile = self.currentDir+"/"+file
		   print openfile
		   if self.currentFile != None:
		    self.closeScene() #IF FILE IS DIFFERENT CLOSE CURRENT SCENE AND OPEN NEW ONE
		    
		   if not os.path.exists(openfile):
		    self.downloadFile(file)
		     
		   self.openScene(openfile);
		  else:
		   print "same scene"
		   
		  outpath = self.currentDir+"/renderframes/"+name
		  
		  renderlog = self.renderFrame(frame,outpath,layers,depth,passes,passName); #RENDER THE FILE FROM THE SCENE
		  
		  renderArray = renderlog.splitlines();
		  
		  logpath = self.currentDir+"/renderframes/"+name+"_"+frame+"_log"+".txt"
		  logfile = open(logpath,"w") #opens file with name of "test.txt"
		  logfile.write(renderlog)
		  logfile.close()
		  
		  for line in renderArray:
		   #PARSE RENDER LOG
		    
		   if line[0:37] == "! (renderProgress)     Frame Complete":
		    renderString = line.replace(" ","").split("|")[1].split(":")[1].split("[")[1].strip("]");
		    self.frameRenderTime = renderString

		   if line[0:34] == "! (renderProgress) Render complete":
		    print "DONE!"
		    
		  #GET ALL FILES IN RENDERFRAMES DIRECTORY AND UPLOAD THEM TO CORRECT S3 LOCATION
		  filedir=self.currentDir+"/renderframes/"
		  files=os.listdir(filedir)
		  fileList = []
		  for file in files:
		   print file
		   filepath = filedir+file
		   if file[-3:] == "txt":
		    uploadpath = project+"/job-"+id+"_renderframes/logfiles/"+name+"_log"+"_"+frame+".txt"
		   else:
		    uploadpath = project+"/job-"+id+"_renderframes/"+file
		    fileList.append(str(file))
		   
		   self.uploadRenderFile(filepath,self.bucketname,uploadpath)
		  self.completeMessage(file,frame,id,fileList)
		 self.rendering = False;
 
 

 def doCommand(self,messageInfo):
  print 'do command'
  print messageInfo
  if messageInfo['Cmd'] == 'clearProject':
   project = messageInfo['Args'];
   self.clearProject(project)

  if messageInfo['Cmd'] == 'clearFile':
   fileList = messageInfo['Args'].split(",");
   self.clearFile(fileList)

 def clearProject(self,project):
  print 'clear project'
  if os.path.exists(project):
   shutil.rmtree(project);
   status = 'Project %s cleared on instance %s' %(project,self.instanceId)   
   self.clearProjectCompleteMessage(status)
   self.currentProject = None
  else:
   status = 'Clear Project Failed. Project folder did not exist.'
   self.clearProjectCompleteMessage(status)

   
 def clearFile(self,fileList):
  print 'clear file'
  if len(fileList)>0:
   for file in fileList:
    fullfilepath = ('%s/%s' %('/opt/modoRenderCloud/',file))
    if os.path.exists(fullfilepath):
     os.remove(fullfilepath)
     self.reloadFile(file)
     status = 'File %s successfully reloaded.' %file
     self.clearFileCompleteMessage(status)
    else:
     status = 'Clear File Failed. File did not exist.'
     self.clearFileCompleteMessage(status)
    
  
 def reloadFile(self,file):
  newfile = '/opt/modoRenderCloud/%s' %file
  key = file
  bucket = self.s3.Bucket(self.bucketname)    
  bucket.download_file(key, newfile) #DOWNLOADS FILE
  print 'file reloaded'

 
 def startNode(self):
  
  while True:
   #get messages
   messages = self.getMessages();
   
   #process messages
   if messages != None:
    for message in messages:
     messageInfo = self.processMessage(message)
     
     if messageInfo != None:
      #if render then render
      if messageInfo['Type']=='render':
       self.rendering = True;      
       self.doRender(messageInfo)
      
      #if command then command
      if messageInfo['Type']=='cmd':
       print 'message is command'
       print 'self.rendering = %s' %self.rendering
       while True:
        if self.rendering is False:
         break
         
       self.doCommand(messageInfo)
       
   else:
    print 'No Message Found'  
   

   time.sleep(10)
		  
renderNode()
"""

 return rendernode

def cloudRenderNodeSetup():
 cloudRenderNodeSetup = """#!/bin/bash

sudo apt-get update

sudo apt-get --assume-yes install python-pip

sudo pip install boto3

sudo pip install awscli

sudo apt-get --assume-yes install libglu1-mesa libsm6 libxrender1 libfontconfig libxrandr2 libxcursor1 libxft2 libxi6 libxinerama1

export AWS_DEFAULT_REGION=*region

q=$(aws sqs get-queue-url --output text --queue-name 'mrc_cloud_commands')

echo $q

aws sqs send-message --queue-url "$q" --message-body "Initial OS setup complete."

sudo mkdir /opt/modoRenderCloud/

sudo chmod 777 /opt/modoRenderCloud/

aws sqs send-message --queue-url "$q" --message-body "Directory structure complete."

aws s3 cp s3://*bucketname/renderNode.py /opt/modoRenderCloud/

aws s3 rm s3://*bucketname/renderNode.py

*softwareinstall

rendernode=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=RenderNodeSetup" "Name=instance-state-name,Values=running" --output text --query 'Reservations[*].Instances[*].InstanceId')

aws sqs send-message --queue-url "$q" --message-body "AMI creation initialized."

newami=$(aws ec2 create-image --instance-id $rendernode --name "RenderNodeAMI" --description "An AMI for my server" --reboot --output text)

"""
 return cloudRenderNodeSetup

def cloudSetupSoftware():
 cloudSetupSoftware = """

aws s3 cp s3://*bucketname/*modoinstall /opt/modoRenderCloud/*modoinstall

aws s3 rm s3://*bucketname/*modoinstall

sudo mkdir /opt/modoRenderCloud/*modoname/

sudo chmod 777 /opt/modoRenderCloud/*modoname/

sudo chmod a+wx /opt/modoRenderCloud/*modoinstall

sudo yes | ./opt/modoRenderCloud/*modoinstall --target /opt/modoRenderCloud/*modoname/

sudo rm /opt/modoRenderCloud/*modoinstall

aws sqs send-message --queue-url "$q" --message-body "*modoname install complete."
"""
 return cloudSetupSoftware 