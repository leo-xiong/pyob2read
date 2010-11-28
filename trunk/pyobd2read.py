#!/usr/bin/python
import curses
import obd_io
from powertrain_codes import pcodes
import threading
import Queue
import re
from optparse import OptionParser
from realtimeplot import RealTimeData,RealTimePlot
import wx

class OBDGui:
 def __init__(self,screen,options):
  self.screen = screen 
  curses.halfdelay(1)
  self.infolines=['no port open']
  self.mode='main'
  self.options=options
  self.currcur=-1

 def drawFrame(self):
  self.screen.clear()
  if self.mode=='main':self.infostr='q: quit, o: open port'
  elif self.mode=='open':self.infostr='q: quit, r: read code, c: clear code, s: read sensors'
  elif self.mode=='sensor':self.infostr='q: quit, b: back, w: up,s: down, p: plot, space: toggle'
  self.screen.addstr(0,0,self.infostr)
  i=0
  for ln in self.infolines:
   self.screen.addstr(2+i,0,ln)
   i+=1
  if self.mode=='sensor' and self.currcur>=0:
   self.screen.addstr(2+self.currcur,0,self.infolines[self.currcur],curses.A_UNDERLINE)
  self.screen.refresh()

 def showSensors(self):
  def cmpS(a,b):
   ai=int(re.findall('\d+',a)[0])
   bi=int(re.findall('\d+',b)[0])
   return cmp(ai,bi)
  if not self.sensorReader.queue_done.empty():
   sensor_names = self.port.sensor_names()
   while not self.sensorReader.queue_done.empty():
     sensor=self.sensorReader.queue_done.get()
     s = str(sensor.id)+'\t'+sensor.value[0]
     self.sensorresults[str(sensor.id)]=s+':'+str(sensor.value[1])+' '+sensor.value[2]
   self.infolines=[]
   for result in self.sensorresults:
     self.infolines.append(self.sensorresults[result]) 
   self.infolines.sort(cmpS)  #This needs to be fixed

 def openport(self):
  try:
   self.port=obd_io.OBDPort(self.options.port)
   self.port.obd_debug('Read available sensors')
   self.sensorStr=self.port.sensor(0)[1]
   self.sensorReader=obd_io.sensorReader(self.port,self.sensorStr)
   self.sensorReader.start()
   self.sensorReader.refresh()
   self.sensorresults={}
   self.infolines=['port opened']
  except Exception as e:
   raise(e) 
   self.infolines=['port open failed ...']

 def readDTC(self):
  adtc=self.port.get_dtc()
  codearr=obd_io.decrypt_dtc_code(adtc)
  if len(codearr)>0:
   self.infolines=[codearr[0]+' : '+pcodes[codearr[0]]]
  else:
   self.infolines=['no code to read']

 def clearDTC(self):
  self.port.clear_dtc()
  self.infolines=['DTC code erased']

 def realPlot(self):
  if self.currcur>=0:
   sId=int(re.findall('\d+',self.infolines[self.currcur])[0])
   aSR=obd_io.OBDsensor(self.port,sId)
   aData=RealTimeSensorData(aSR)
   app = wx.PySimpleApp()
   app.frame = RealTimePlot(aData)
   app.frame.Show()
   app.MainLoop()
  
 def selectSensor(self):
  if self.currcur>=0:
   astr=''
   sId=int(re.findall('\d+',self.infolines[self.currcur])[0])
   for i in range(len(self.sensorReader.supp)):
    if i==sId-1: 
     astr+=str(1-int(self.sensorReader.supp[i]))
    else: astr+=self.sensorReader.supp[i]
   self.sensorReader.supp=astr
   self.sensorReader.populate() 
   
 def run(self):
  i=0
  while True:
   self.drawFrame() 
   c=self.screen.getch()  
   if self.mode=='main':
    if c==ord('q'):break
    elif c==ord('o'): 
     self.openport()
     self.mode='open'
     continue
   elif self.mode=='open':
    if c==ord('r'):self.readDTC() 
    elif c==ord('c'):self.clearDTC()
    elif c==ord('s'):
     self.infolines=['reading sensors..']
     self.mode='sensor' 
     self.currcur=-1
     continue
    elif c==ord('q'):break
   elif self.mode=='sensor':    
    if c==ord('q'):
     self.sensorready=False
     break
    elif c==ord('b'):
     self.mode='open'
     self.infolines=[''] 
    elif c==ord('w'):self.currcur=max(0,self.currcur-1)
    elif c==ord('s'):self.currcur=min(len(self.infolines)-1,self.currcur+1)  
    elif c==ord('p'):self.realPlot()
    elif c==ord(' '):self.selectSensor()     
   if self.mode=='sensor':    
    self.showSensors()
    if self.sensorReader.queue.empty():self.sensorReader.refresh()

class RealTimeSensorData(RealTimeData):
 def __init__(self,sensor):
  RealTimeData.__init__(self)
  self.sensor=sensor
 def getY(self):
  self.sensor.read()
  res=-1.0 #Default value  
  try:  
   res=float(self.sensor.value[1])
  except:
   return res   
  return res

def main(screen):
    a=OBDGui(screen,options)
    a.run()
  
if __name__=='__main__':
    parser=OptionParser();
    parser.add_option("-p", "--port", dest="port", default="/dev/ttyACM0",help="port , such as /dev/ttyACM0")
    (options, args) = parser.parse_args()    
    curses.wrapper(main)
