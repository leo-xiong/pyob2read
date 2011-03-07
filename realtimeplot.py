import pylab as pl
import time
import random
import wx
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

class RealTimeData:
 def __init__(self,range=50):
  self.range=range
  self.xdata=list([])
  self.ydata=list([])
 def getY(self):
  return random.uniform(0,10)
 def next(self):
  if len(self.xdata)==0: self.xdata.append(0)
  else: self.xdata.append(self.xdata[-1]+0.1)
  self.ydata.append(self.getY())
 def get_curr(self):
  N=self.range
  return [self.xdata[-N:-1],self.ydata[-N:-1]]
  
class RealTimePlot(wx.Frame):
 
 def __init__(self,data):
  wx.Frame.__init__(self, None, -1, "Real time data plot")        
  self.redraw_timer = wx.Timer(self)
  self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
  self.redraw_timer.Start(100)
  self.data=data          
  self.init_plot()
   
 def init_plot(self): 
  self.data.next()
  self.panel = wx.Panel(self)
  self.fig = Figure((6.0, 3.0))
  self.canvas = FigureCanvasWxAgg(self.panel, -1, self.fig)  
  self.axes = self.fig.add_subplot(111)           
  self.plot_data, = self.axes.plot(self.data.get_curr()[0],self.data.get_curr()[1])
  self.vbox = wx.BoxSizer(wx.VERTICAL)
  self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)              
  self.panel.SetSizer(self.vbox)
  self.vbox.Fit(self)
    
            
 def draw_plot(self):
  x=self.data.get_curr()[0]
  y=self.data.get_curr()[1]
  self.plot_data.set_data(x,y)
  self.axes.set_xlim((x[0],x[-1]))
  self.axes.set_ylim((min(y),max(y)))
  self.canvas.draw()
   
 def on_redraw_timer(self,event):
  self.data.next()
  self.draw_plot()  

if __name__ == '__main__':
  app = wx.PySimpleApp()
  adata=RealTimeData()
  app.frame = RealTimePlot([adata])
  app.frame.Show()
  app.MainLoop()
