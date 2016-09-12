import threading
import time
import random
import sys
import inspect
import redis
from scheduler import *
from utilities import *
from scapy.all import *

debug=True

hostname = '127.0.0.1'
port = '6379'

r = redis.Redis(
    host=hostname,
    port=port )

class LatencyQueue(process):
  import string
  import random
  def __init__(self,name='queue',ival=0.001,MaxSize=0,ratio=1,latency=0):
    self.latency=latency 
    self.size=0
    self.ival=ival
    self.MaxSize = MaxSize
    self.name=name
    self.ratio = ratio
    self.queuename="queue:"+self.randtoken()+":("+self.name+")"
    self.latencyqueue="latqueue:"+self.randtoken()+":("+self.name+")"
#    self.r=redis.Redis(host=hostname,port=port )
    self.counter=1
#    self.lat_manager()
    process.__init__(self,0)
    if latency>0:
       self.lat_manager()

  def randtoken(self,size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(self.random.choice(chars) for _ in range(size))

  @threaded
  def lat_manager(self):
    while True:
      t=self.waittick()
      lock,now=self.lock()
      ulimit=float(t)*1000+1
      for item,score in r.zrangebyscore(self.latencyqueue, 0 ,ulimit ,withscores=True):
#        if self.name == 'link1:a' or self.name == 'link1:b' :
#           print "LQ:",self.name,ulimit,score,str(Ether(item.decode('HEX'))[UDP].payload).split(':')[1]
        if r.zrem(self.latencyqueue, item) == 1:
           self.size+=len(item)
           r.rpush(self.queuename, item)
      self.unlock(lock)

  def put(self,item):
    if self.MaxSize > 0:
       if self.qsize() > self.MaxSize:
          return False
    if self.latency > 0:
       futuretime=(float(self.getsimtime())*1000+self.latency)/1000
       timestamp="%0.4f%06d" % (futuretime,self.counter); self.counter+=1
       timestamp=float(timestamp)*1000
       r.zadd(self.latencyqueue,item,timestamp)
    else:
       self.size+=len(item)
       r.rpush(self.queuename, item)
    return True

  def get(self, block=True, timeout=None):
    if block:
       item = r.blpop(self.queuename, timeout=timeout)
    else:
       item = r.lpop(self.queuename)
    if item:
       item = item[1]
    self.size=self.size-len(item)
    return item

  def qsize(self):
    # ratio is ratio of actual bytes to application bytes
    return int(self.size/self.ratio)

  def empty(self):
    return self.qsize() == 0


class Queue():
  import string
  import random

  def __init__(self,name='queue',ival=0.001,MaxSize=0,ratio=1):
    self.ival=ival
    self.MaxSize = MaxSize
    self.name=name
    self.ratio = ratio
    self.size=0
    self.queuename="queue:"+self.randtoken()+":("+self.name+")"

  def randtoken(self,size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(self.random.choice(chars) for _ in range(size))    

  def put(self,item):
    if self.MaxSize > 0:
       if self.qsize() > self.MaxSize:
          return False
    r.rpush(self.queuename, item)
    self.size+=len(item)
    return True

  def get(self, block=True, timeout=None):
    if block:
       item = r.blpop(self.queuename, timeout=timeout)
    else:
       item = r.lpop(self.queuename)
    if item:
       item = item[1]
    self.size=self.size=len(item)
    return item

  def qsize(self):
    # ratio is ratio of actual bytes to application bytes
    return int(self.size/self.ratio)

  def empty(self):
    return self.qsize() == 0

def threaded(fn):
    def wrapper(*args, **kwargs):
        t=threading.Thread(target=fn, args=args, kwargs=kwargs)
        t.daemon=True
        t.start()
    return wrapper

def debug(line):
   if debug:
      print line

class connector(process):
   def __init__(self,name,a,b,inspect,ratelimit=0,ratio=1):
      self.a = a
      self.b = b
      self.name = name
      self.ratio = ratio
      self.inspect=inspect
      self.ratelimit=ratelimit
      self.qsize=0
      process.__init__(self,0)
      self.worker()
      self.statscollector()

   @threaded
   def statscollector(self):
      while True:
         simtime=self.waitsectick()
         timlock,now=self.lock()
         root=self.name+':'+simtime+':'
         self.writedb(root+'bps',self.getstats(self.name,'bits'))
         self.writedb(root+'qsize',self.qsize); self.qsize=0
         self.unlock(timlock)

   @threaded
   def worker(self):
      while self.isactive:
         timlock,now=self.lock()
#         bps=self.getbps(self.name)
         try:
            self.qsize=max(self.a.qsize(),self.qsize)
         except:
            self.qsize=self.a.qsize()
         self.updatestats(self.name,0,'bits')
         self.unlock(timlock)
#         print self.name,self.getsimtime(),bps,self.qsize
         if self.b.MaxSize > 0 and self.b.qsize() >= self.b.MaxSize: # Back Pressure
            time.sleep(0.01)
            print "Back Pressure", self.b.qsize(), self.b.MaxSize
            continue
         if self.ratelimit > 0 and self.getstats(self.name,'bits') > self.ratelimit: # Rate Limit
            time.sleep(0.01)
            continue
#         timlock,now=self.lock()
         item=self.a.get()
         item=self.inspect(item,self.name) # Careful about putting the inspect within the lock

         self.updatestats(self.name,len(item)*8/self.ratio,'bits') # 2 chars = 8 bits

         if not self.b.put(item):
            self.updatestats(self.name,1,'pktdrp')

         self.unlock(timlock)

class xhub(object):
   def __init__(self,name,L):
      for n in L:
         P=[]
         for m in L:
            if n != m:
               P.append(m)
         self.worker(n,P)

   @threaded
   def worker(self,n,P):
      while True:
         item=n.get()
         for m in P:
            r.set("Debug","putting %s" % item)
            m.put(item)

class rrhub(object):
   def __init__(self,name,t,L):
      w=0
      self.worker1(w,t,L)
      w=0
      for n in L:
         self.worker2(w,n,t)
         w=w+1

   @threaded
   def worker1(self,w,t,L):
      while True:
         item=t.get()
         c = random.choice(L) 
         r.set("Logger","putting %s" % item)
         c.put(item)

   @threaded
   def worker2(self,w,n,t):
      while True:
         item=n.get()
         r.set("Logger","putting %s" % item)
         t.put(item)

class hub(object):
   def __init__(self,name,t,L):
      w=0
      self.worker1(w,t,L)
      w=0
      for n in L:
         self.worker2(w,n,t)
         w=w+1

   @threaded
   def worker1(self,w,t,L):
      while True:
         item=t.get()
         for n in L:
            r.set("Logger","putting %s" % item)
            n.put(item)

   @threaded
   def worker2(self,w,n,t):
      while True:
         item=n.get()
         r.set("Logger","putting %s" % item)
         t.put(item)
      
class connect(object):
   def __init__(self,name,X,Y,ratelimit=0):
      connector(name+':connect1',X.outq,Y.inq,self.inspect,ratelimit=ratelimit)
      connector(name+':connect2',Y.outq,X.inq,self.inspect,ratelimit=ratelimit)

   def inspect(self,item,name):
       return item

class loopback(object):
   def __init__(self,name,X):
      connector(name+':connect1',X.outq,X.inq,self.inspect)

   def inspect(self,item,name):
       return item

class layer(object):
   def __init__(self,name):
      self.up=duplex('up')
      self.down=duplex('down')
      self.A=self.up.A
      self.B=self.down.B
      self.C=self.up.B
      self.D=self.down.A

class stack1(object):
   def __init__(self,name):
      self.layer1=layer('layer1')
      self.layer2=layer('layer2')
      self.layer3=layer('layer3')
      self.layer4=layer('layer4')
      self.A=self.layer1.A
      self.B=self.layer1.B
      connect('J1',self.layer1.C,self.layer2.A)
      connect('J2',self.layer1.D,self.layer2.B)

      connect('J3',self.layer2.C,self.layer3.A)
      connect('J4',self.layer2.D,self.layer3.B)

      connect('J5',self.layer3.C,self.layer4.A)
      connect('J6',self.layer3.D,self.layer4.B)

      connect('top',self.layer4.C,self.layer4.D)

class stack(object):
   def __init__(self,name,n=1):
     if n<1:
        print "Number of stacks must be 1 or greater"
        return
     self.layer = []
     self.layer.append('a')
     for i in range(1,n+1):
        self.layer.append(layer('layer'+str(i)))

     for i in range(1,n):
        connect('J'+str(2*i-1),self.layer[i].C,self.layer[i+1].A)
        connect('J'+str(2*i-1),self.layer[i].D,self.layer[i+1].B)

     self.A=self.layer[1].A
     self.B=self.layer[1].B

     connect('top',self.layer[n].C,self.layer[n].D)



class duplex(process):
   def __init__(self, name,ival=0.001,start=0,stop=0,ratelimit=0,MaxSize=0,ratio=1,latency=0,debug=False):
      self.name = name
      self.ival = ival
      self.start = start
      self.stop = stop
      self.ratelimit = ratelimit
      self.latency = latency
      if latency > 0:
         self.a = LatencyQueue(name=self.name+':a',MaxSize=MaxSize,ratio=ratio,latency=latency/2) # ratio of stored bytes to application bytes
         self.b = LatencyQueue(name=self.name+':b',MaxSize=MaxSize,ratio=ratio,latency=latency/2)
         self.c = LatencyQueue(name=self.name+':c',MaxSize=MaxSize,ratio=ratio,latency=latency/2)
         self.d = LatencyQueue(name=self.name+':d',MaxSize=MaxSize,ratio=ratio,latency=latency/2)
      else:
         self.a = Queue(name=self.name+':a',MaxSize=MaxSize,ratio=ratio) # ratio of stored bytes to application bytes
         self.b = Queue(name=self.name+':b',MaxSize=MaxSize,ratio=ratio)
         self.c = Queue(name=self.name+':c',MaxSize=MaxSize,ratio=ratio)
         self.d = Queue(name=self.name+':d',MaxSize=MaxSize,ratio=ratio)

      connector(name+':link1',self.a,self.b,self.inspectA,self.ratelimit,ratio=ratio) # a -> b, forward from interface A to interface B
      connector(name+':link2',self.d,self.c,self.inspectB,self.ratelimit,ratio=ratio) # c -> d, reverse from interface B to interface A

      self.A=self.interface(name+':A',self.a,self.c,self) # a,c
      self.B=self.interface(name+':B',self.d,self.b,self) # d,b

      process.__init__(self,self.start,debug=debug)

   def inspectA(self,item,name):
      return item

   def inspectB(self,item,name):
      return item

   class interface:
      def __init__(self,name,inq,outq,outer):
         self.inq = inq
         self.outq = outq
         self.outer = outer
         self.name = name

      def put(self,item):
         if self.outer.debug:
            self.outer.logwrite("%s putting %s" % (self.name,item))
         self.inq.put(item)
         return

      def get(self):
         if self.outer.debug:
            self.outer.logwrite("%s getting %s" % (self.name,item))
         item=self.outq.get()
         return item

      def raw_put(self,stream):
         self.put(stream.encode("HEX"))

      def raw_get(self):
         stream=self.get()
         return stream.decode("HEX")

      def qsize(self):
         return self.outq.qsize()

class trafgen(duplex):
   def __init__(self, *args, **kwargs):
      self.Mbps=kwargs.get('speed',1) # Mbps
      if 'speed' in kwargs:
         del kwargs['speed']
      self.once=kwargs.get('once',0) # Mbps
      if 'once' in kwargs:
         del kwargs['once']
      self.ms1=kwargs.get('ms1',0) # Mbps
      if 'ms1' in kwargs:
         del kwargs['ms1']
      super(trafgen, self).__init__(*args, **kwargs)

      self.bpms = self.Mbps*1000
      self.size = size = 500

      process.__init__(self,0)

      if self.once > 0:
        self.worker3()
      elif self.ms1 > 0:
        self.worker4()
      else:
        self.worker1()
      self.worker2()

   @threaded
   def worker1(self):
     print "worker 1 starting"
     count=1
     self.payload=randPayload(self.size)
     while True:
       stime=self.waittick()
       bits=0
       timlock,now=self.lock()
       while True:
          load='%d:%s:%s'%(count,now,self.payload)
          loadbits=len(load)*8
          if bits+loadbits <= self.bpms:
             bits+=loadbits
             self.A.put(load); count+=1
          else:
             break 
       self.unlock(timlock)

   @threaded
   def worker2(self):
      print "worker 2 starting"
      while True:
         item=self.A.get()
         timlock,now=self.lock()
         self.logwrite("%s %s" % (self.name,item))
         self.unlock(timlock)
         
   @threaded
   def worker3(self):
     print "worker 3 starting"
     count=1
     self.payload=randPayload(self.size)
     stime=self.waittick()
     bits=0
     timlock,now=self.lock()
     load='%d:%s:%s'%(count,now,self.payload)
     self.A.put(load)
     self.unlock(timlock)
     
   @threaded
   def worker4(self):
     count=0
     print "worker 4 starting"
     payload="Message !!"
     while True:
       stime=self.waittick()
       timlock,now=self.lock()
       load='%d:%s:%s'%(count,now,payload)
       self.A.put(load)
       count+=1
       self.unlock(timlock)

class terminal(duplex):
   def __init__(self, *args, **kwargs):
      super(terminal, self).__init__(*args, **kwargs)
      process.__init__(self,0)
      self.worker()

   @threaded
   def worker(self):
      while True:
         item=self.B.get()
         timlock,now=self.lock()
         count,sendnow,payload=item.split(':') 
         item="Traffic Return: '%s:%s:%s'" % (str(count),str(sendnow),str(now))
         self.B.put(item)
         self.unlock(timlock)

