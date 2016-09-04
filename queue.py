import threading
import time
import random
import sys
import inspect
import redis
from scheduler import *

debug=True

hostname = '127.0.0.1'
port = '6379'

r = redis.Redis(
    host=hostname,
    port=port )

class Queue():
  import string
  import random

  def __init__(self,name='queue',ival=0.001,MaxSize=0):
    self.ival=ival
    self.MaxSize = MaxSize
    self.name=name
    self.queuename="queue:"+self.randtoken()+":("+self.name+")"

  def randtoken(self,size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(self.random.choice(chars) for _ in range(size))    

  def put(self,item):
    if self.MaxSize > 0:
       if self.qsize() > self.MaxSize:
          return False
    r.rpush(self.queuename, item)
    return True

  def get(self, block=True, timeout=None):
    if block:
       item = r.blpop(self.queuename, timeout=timeout)
    else:
       item = r.lpop(self.queuename)
    if item:
       item = item[1]
    return item

  def qsize(self):
    return r.llen(self.queuename)

  def empty(self):
    return r.qsize() == 0

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
   def __init__(self,name,a,b,inspect,ratelimit=0):
      self.a = a
      self.b = b
      self.name = name
      self.inspect=inspect
      self.ratelimit=ratelimit
      process.__init__(self,0)
      self.worker()
      self.qsize=0
      self.statscollector()

   @threaded
   def statscollector(self):
      while True:
         simtime=self.waitsectick()
         timlock=self.lock()
         root=self.name+':'+simtime+':'
         self.writedb(root+'bps',self.getbps(self.name))
         self.writedb(root+'qsize',self.qsize); self.qsize=0
         self.unlock(timlock)

   @threaded
   def worker(self):
      while self.isactive():
         timlock=self.lock()
#         bps=self.getbps(self.name)
         self.qsize=max(self.a.qsize(),self.qsize)
         self.updatebps(self.name,0)
         self.unlock(timlock)
#         print self.name,self.getsimtime(),bps,self.qsize
         if self.b.MaxSize > 0 and self.b.qsize() >= self.b.MaxSize: # Back Pressure
            time.sleep(0.01)
            print "Back Pressure", self.b.qsize(), self.b.MaxSize
            continue
         if self.ratelimit > 0 and self.getbps(self.name) > self.ratelimit: # Rate Limit
            time.sleep(0.01)
            continue
         item=self.a.get()
         item=self.inspect(item,self.name)
         timlock=self.lock()
         self.updatebps(self.name,len(item)*8)
         if not self.b.put(item):
            print "Dropping Packets"
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
   def __init__(self, name,ival=0.001,start=0,stop=0,ratelimit=0,MaxSize=0):
      self.name = name
      self.ival = ival
      self.start = start
      self.stop = stop
      self.ratelimit = ratelimit
      self.a = Queue(name=self.name+':a',MaxSize=MaxSize)
      self.b = Queue(name=self.name+':b',MaxSize=MaxSize)
      self.c = Queue(name=self.name+':c',MaxSize=MaxSize)
      self.d = Queue(name=self.name+':d',MaxSize=MaxSize)
      connector(name+':link1',self.a,self.b,self.inspect,self.ratelimit) # a -> b, forward from interface A to interface B
      connector(name+':link2',self.d,self.c,self.inspect,self.ratelimit) # c -> d, reverse from interface B to interface A

      self.A=self.interface(name+':A',self.a,self.c,self) # a,c
      self.B=self.interface(name+':B',self.d,self.b,self) # d,b

      process.__init__(self,self.start)

   def inspect(self,item,name):
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

      def qsize(self):
         return self.outq.qsize()

class trafgen(duplex):
   def __init__(self, *args, **kwargs):
      super(trafgen, self).__init__(*args, **kwargs)

      self.worker1()
      self.worker2()

   @threaded
   def worker1(self):
     while True:
       stime=self.waittick()
       timlock=self.lock()
       self.A.put(b'N')
       self.unlock(timlock)

   @threaded
   def worker2(self):
      while True:
         item=self.A.get()
         timlock=self.lock()
         self.logwrite("%s %s" % (self.name,item))
         self.unlock(timlock)

class terminal(duplex):
   def __init__(self, *args, **kwargs):
      super(terminal, self).__init__(*args, **kwargs)
      self.worker()

   @threaded
   def worker(self):
      while True:
         item=self.B.get()
         timlock=self.lock()
#         time.sleep(0.1)
         item="Bounce '%s'" % (str(item))
         self.B.put(item)
         self.unlock(timlock)

#sched=scheduler(tick=0.001,finish=10)

# node1=duplex('node1')
#stack1 = stack('stack1')
#stack2 = stack('stack2')


#traf=trafgen('traf')
#sched.addp(traf.worker1,0.000,0.100)
#term2=terminal('term2')

#connect('linkA',traf.B,stack1.A)
#connect('linkB',stack1.B,stack2.A)
#connect('linkC',stack2.B,term2.A)

#sched.process()

