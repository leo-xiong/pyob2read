#!/usr/bin/env python
import serial
import string
import time
import obd_sensors
from powertrain_codes import pcodes
from network_codes    import ucodes
import threading
import Queue
import random

GET_DTC_COMMAND   = "03"
CLEAR_DTC_COMMAND = "04"
#__________________________________________________________________________
def decrypt_dtc_code(code):
    """Returns the 5-digit DTC code from hex encoding"""
    dtc = []
    if code.strip()!='NO DATA':
     current = code[3:]
     for i in range(0,3):
         if len(current)<4:
             raise "Tried to decode bad DTC: %s" % code     
         tc = int(current[0],16) #typecode
         tc = tc >> 2
         if   tc == 0:
             type = "P"
         elif tc == 1:
             type = "C"
         elif tc == 2:
             type = "B"
         elif tc == 3:
             type = "U"
         else:
             raise tc
         dig1 = str(int(current[0],16) & 3)
         dig2 = str(int(current[1],16))
         dig3 = str(int(current[3],16))
         dig4 = str(int(current[4],16))
         if dig1+dig2+dig3+dig4=='0000':
             break        
         dtc.append(type+dig1+dig2+dig3+dig4)
         current = current[6:]
    return dtc
#__________________________________________________________________________

class debugPort(object):
 
 def __init__(self):
  self.dfile=open('obd.log','w')
  
 def debug(self,s):
  print >> self.dfile,"debug:",str(s)
 
class fakeSerialDevice(): 
 msg=''
 ci=0
 def flushOutput(self):
  pass
 def flushInput(self):
  pass
 def write(self,msg):
  if msg=='\r': return
  self.msg+=msg
 def read(self,N=1):
  dict={'03':'43 01 33 00 00 00 00>'
        }
  if self.msg in dict.keys():
   res=dict[self.msg.strip()][self.ci]
   self.ci+=1
   if res=='>': 
    self.msg=''
    self.ci=0
  else:
   res='>'
   self.msg=''
   self.ci=0
  return res
  
class OBDPort(debugPort):
     """ OBDPort abstracts all communication with OBD-II device."""
     def __init__(self,device):
         debugPort.__init__(self)
         """Initializes port by resetting device and gettings supported PIDs. """
         # These should really be set by the user.
         baud     = 9600 #10400 #38400  #9600
         databits = 8
         par      = serial.PARITY_NONE  # parity
         sb       = 1                   # stop bits
         to       = 2
         
         try:
             self.port = serial.Serial(device,baud, \
             parity = par, stopbits = sb, bytesize = databits,timeout = to)
         except "FIXME": #serial.serialutil.SerialException:
             raise "PortFailed"

         self.debug(self.port.portstr)
         ready = "ERROR"
	 #self.send_command("01 00")
	 #debug(self.get_result())
         while ready == "ERROR":
             self.send_command("atz")   # initialize
             self.debug(self.get_result())
             self.send_command("ate0")  # echo off
             self.debug(self.get_result())
             self.send_command("01 00") #check available commands for Mode 01
             astr=self.get_result()
             if astr.strip()=='UNABLE TO CONNECT':
              self.debug('retrying ..')
              continue
             ready = astr[-6:-1]
             self.debug(astr)
         self.debug("Port initilized")
     
     
     def close(self):
         """ Resets device and closes all associated filehandles"""
         self.port.send_command("atz")
         self.port.close()
         self.port = None

     def send_command(self, cmd):
         """Internal use only: not a public interface"""
#	 print "envoking ",cmd
         if self.port:
	     
             self.port.flushOutput()
             self.port.flushInput()
             for c in cmd:
                 self.port.write(c)
             self.port.write("\r")
#	 print "done writing"

     def interpret_result(self,code):
         """Internal use only: not a public interface"""
         # Code will be the string returned from the device.
         # It should look something like this:
         # '41 11 0 0\r\r'
         
         # 9 seems to be the length of the shortest valid response
         self.debug('interpreting code '+str(code))
         if len(code) < 7:
             raise "BogusCode"
          
         # get the first thing returned, echo should be off
         code = string.split(code, "\r")
         code = code[0]
         
         #remove whitespace
         code = string.split(code)
         code = string.join(code, "")
          

         if code[:6] == "NODATA": # there is no such sensor
             return "NODATA"
         # first 4 characters are code from ELM
         code = code[4:]
         return code
    
     def get_result(self):
         """Internal use only: not a public interface"""
#	 print "start reading"
         if self.port:
             buffer = ""
             while 1:
                 c = self.port.read(1)
                 if c == '>' and len(buffer) > 0:
                     break
                 else:
                     buffer = buffer + c
             return buffer
#	     print "done"
         return None

     # get sensor value from command
     def get_sensor_value(self,sensor):
         """Internal use only: not a public interface"""
         cmd = sensor.cmd
         self.send_command(cmd)
         data = self.get_result()
         if data:
             data = self.interpret_result(data)
             if data != "NODATA":
                 data = sensor.value(data)
         else:
             raise Exception("NORESPONSE")
         return data

     # return string of sensor name and value from sensor index
     def sensor(self , sensor_index):
         """Returns 3-tuple of given sensors. 3-tuple consists of
         (Sensor Name (string), Sensor Value (string), Sensor Unit (string) ) """
         self.debug('reading sensor '+str(sensor_index))
         sensor = obd_sensors.SENSORS[int(sensor_index)]
         try:
             r = self.get_sensor_value(sensor)
         except "NORESPONSE":
             r = "NORESPONSE"
         return (sensor.name,r, sensor.unit)

     def sensor_names(self):
         """Internal use only: not a public interface"""
         names = []
         for s in obd_sensors.SENSORS:
             names.append(s.name)
         return names


     #
     # fixme: j1979 specifies that the program should poll until the number
     # of returned DTCs matches the number indicated by a call to PID 01
     #
     def get_dtc(self):
          """Returns a list of all pending DTC codes. Each element consists of
          a 2-tuple: (DTC code (string), Code description (string) )"""
          r = self.sensor(1)
          num = r[0]
          # get all DTC, 3 per mesg response
          self.send_command(GET_DTC_COMMAND)
          res = self.get_result() 
          return res
              
     def clear_dtc(self):
         """Clears all DTCs and freeze frame data"""
         self.send_command(CLEAR_DTC_COMMAND)     
         r = self.get_result()
         return r
     
     def log(self, sensor_index, filename): 
          file = open(filename, "w")
          start_time = time.time() 
          if file:
               data = self.sensor(sensor_index)
               file.write("%s     \t%s(%s)\n" % \
                         ("Time", string.strip(data[0]), data[2])) 
               while 1:
                    now = time.time()
                    data = self.sensor(sensor_index)
                    line = "%.6f,\t%s\n" % (now - start_time, data[1])
                    file.write(line)
                    file.flush()
         
class OBDPortTest(OBDPort):
 '''
 Class for testing gui functionality
 '''
 def __init__(self,device):
  self.port=fakeSerialDevice()
  
 def close(self):
  pass
 def sensor(self , sensor_index):
    sensor = obd_sensors.SENSORS[sensor_index]
    time.sleep(0.1)
    result=str(random.uniform(0,1))  
    if sensor_index==0:
     result='0011111000'  
    return (sensor.name,result, sensor.unit)
 def clear_dtc(self):
  pass
          
class sensorThread(threading.Thread):
 """
    This class is to submit jobs in parallel
 """
 def __init__(self,queue,queue_out):
  self.queue = queue
  self.queue_out = queue_out
  threading.Thread.__init__(self)

 def run(self):    
  while 1: 
   job=self.queue.get()
   if job == None:
    break
   try:    
    job.read()
    self.queue_out.put(job)
   except:
    print 'Failed to read sensor',job.id
    pass

class OBDsensor:
    def __init__(self,p,id):
        self.port=p
        self.id=id
        self.value=0.0
    def read(self):     
        self.value = self.port.sensor(self.id)
             
class sensorReader:
        def __init__(self,p,sensors):
            '''
            p - OBD port 
            sensor - binary string that describes which sensors to display
            '''
            self.port= p
            self.supp = sensors #p.sensor(0)[1]
            self.populate()
            
        def populate(self):             
            self.sensors=[]
            for i in range(2, len(self.supp)):
                if self.supp[i] == "1":
                    self.sensors.append(OBDsensor(self.port,i+1))         
            
        def start(self):          
            self.queue=Queue.Queue(0)         
            self.queue_done=Queue.Queue(0)   
            t=sensorThread(self.queue,self.queue_done)
            t.setDaemon(True)
            t.start()
            
        def refresh(self):
            for sensor in self.sensors:
                self.queue.put(sensor)                

        def terminate(self):
            #Put end marker to signal thread stop and wait
            for i in range(threads):
                self.sensor_queue.put(None)      
            while not self.sensor_queue.empty(): 
                time.sleep(1)
        def loopread(self):
            while 1:
                time.sleep(1)
                self.refresh()
                if not self.queue_done.empty():
                    sensor=self.queue_done.get()
                    print sensor.id,sensor.value
                    self.queue.put(sensor)                
        
# __________________________________________________________    
def test():
    p = OBDPortTest('/dev/ttyACM0')
    codes=decrypt_dtc_code(p.get_dtc())
    for code in codes:
        print code,pcodes[code]
#    areader=sensorReader(p)
#    areader.start()
#    areader.loopread()
           

if __name__ == "__main__":
     test()
