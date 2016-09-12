import redis
import time
from utilities import *

def threaded(fn):
    import threading
    def wrapper(*args, **kwargs):
        t=threading.Thread(target=fn, args=args, kwargs=kwargs)
        t.daemon=True
        t.start()
    return wrapper


hostname = '127.0.0.1'
port = '6379'

pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
globalr = redis.Redis(connection_pool=pool )

#r = redis.Redis(
#    host=hostname,
#    port=port )

class scheduler(object):
   def __init__(self, tick=1,wait=0,debug=0,finish=0):
      self.finish = finish
      self.tick = tick 
      self.gap = tick*0.9
      self.wait = wait = 0.001
      self.waitqueue='schedule'
      self.tickqueue='ticks'
      self.sectickqueue='secticks'
      self.ms10tickqueue='10msticks'
      self.ms100tickqueue='100msticks'
      self.simtime=0.000
#      self.r = redis.Redis(host=hostname,port=port )
      self.r = globalr
      self.r.flushall()
      self.syncdb()
      self.setactive()
      self.dbg=debug
      self.logreader()
      self.plist=[] # functions to call back

   def setactive(self):
      self.r.set("simactive",1)

   def setinactive(self):
      self.r.set("simactive",0)

   def isactive(self):
     try:
       state=int(self.r.get('simactive'))
       if state > 0:
          return True
       else:
          return False
     except:
       return False

   def signal(self,key):
      ret=self.r.lpush(key,'release')

   def debug(self,line):
      if self.dbg:
         print line
  
   def process(self):
      while (self.simtime < self.finish or self.finish == 0):
         self.process_waits()
         if not self.r.exists('timlock'):
            self.simtime+=self.tick
            self.process_ticks()
            self.process_secticks()
            self.process_10msticks()
            self.process_100msticks()
            self.syncdb()
            self.scanp()
         if self.wait > 0:
            time.sleep(self.wait)
      self.setinactive()
      print "simtime",self.simtime,"finish",self.finish

   def process_waits(self):
      try:
        for result,score in self.r.zrangebyscore(self.waitqueue, 0 ,str(self.simtime+self.gap),withscores=True):
          if self.r.zrem(self.waitqueue, result) == 1:
             self.signal(result)
             self.debug("%s %s %s" % (str(self.simtime),str(score),str(result)))
          else:
             self.debug("%s *" % self.simtime)
        else:
             self.debug("%s +" % self.simtime)
      except:
        self.debug("%s !" %self.simtime)

   def process_ticks(self):
      try:
        for result,score in self.r.zrangebyscore(self.tickqueue, 0 ,str(self.simtime+self.gap),withscores=True):
          if self.r.zrem(self.tickqueue, result) == 1:
             self.signal(result)
             self.debug("%s %s %s" % (str(self.simtime),str(score),str(result)))
          else:
             self.debug("%s *" % self.simtime)
        else:
             self.debug("%s +" % self.simtime)
      except:
        self.debug("%s !" %self.simtime)

   def process_secticks(self):
      if not self.is_integer(float(self.simtime)):
          return
      try:
        for result,score in self.r.zrangebyscore(self.sectickqueue, 0 ,str(self.simtime+self.gap),withscores=True):
          if self.r.zrem(self.sectickqueue, result) == 1:
             self.signal(result)
             self.debug("%s %s %s" % (str(self.simtime),str(score),str(result)))
          else:
             self.debug("%s *" % self.simtime)
        else:
             self.debug("%s +" % self.simtime)
      except:
        self.debug("%s !" %self.simtime)

   def process_10msticks(self):
      if not self.is_integer(float(self.simtime)*100):
          return
      try:
        for result,score in self.r.zrangebyscore(self.ms10tickqueue, 0 ,str(self.simtime+self.gap),withscores=True):
          if self.r.zrem(self.ms10tickqueue, result) == 1:
             self.signal(result)
             self.debug("%s %s %s" % (str(self.simtime),str(score),str(result)))
          else:
             self.debug("%s *" % self.simtime)
        else:
             self.debug("%s +" % self.simtime)
      except:
        self.debug("%s !" %self.simtime)

   def process_100msticks(self):
      if not self.is_integer(float(self.simtime)*10):
          return
      try:
        for result,score in self.r.zrangebyscore(self.ms100tickqueue, 0 ,str(self.simtime+self.gap),withscores=True):
          if self.r.zrem(self.ms100tickqueue, result) == 1:
             self.signal(result)
             self.debug("%s %s %s" % (str(self.simtime),str(score),str(result)))
          else:
             self.debug("%s *" % self.simtime)
        else:
             self.debug("%s +" % self.simtime)
      except:
        self.debug("%s !" %self.simtime)


   def isclose(self,a, b, rel_tol=1e-09, abs_tol=0.0):
      return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

   def is_integer(self,fl):
      return self.isclose(fl, round(fl))

   def syncdb(self):
      self.r.set("simtime",str(self.simtime))
      self.r.set("simsec",str(int(self.simtime)))
      self.r.set("simbuck",str(round(self.simtime,1)))

   def scanp(self):
      for p in self.plist:
         self.invoke(p)

   def addp(self,p,a,b):
      self.plist.append(self.func(p,a,b))

   def invoke(self,p):
      if self.simtime < p.a:
           return
      if self.simtime > p.b:
           return
      p.fn(self.simtime) 

   class func(object):
      def __init__(self,fn,a,b):
         self.fn = fn
         self.a = a
         self.b = b

   @threaded
   def logreader(self):
      while True:
         print self.r.blpop("Logger")[1]

class process(object):
  import string
  import random
  def __init__(self,now=0,debug=False):
#    self.r= redis.Redis(host=hostname,port=port )
    self.r = globalr
    self.now=now
    self.mytick=0
    self.begin()
    self.debug=debug
    self.alert=open("alert.log","a+")

  @threaded
  def begin(self):
    result,score=self.waituntil(self.now)

  def isactive(self):
    try:
      state=int(self.r.get('simactive'))
      if state > 0:
         return True
      else:
         return False
    except:
      return False

  def randtoken(self,size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(self.random.choice(chars) for _ in range(size))

  def logwrite(self,line):
    self.r.rpush("Logger","%s %s" % (str(self.nw()),line))

  def nw(self):
#    return self.now
#    return "xyz"
    return self.r.get('simtime')

  def gettoken(self):
    key=self.randtoken()
    return(key)

  def getsimtime(self):
    return self.r.get("simtime")

  def release(self,key):
    self.r.delete(key)

  def waiton(self,key,n):
    self.r.zadd('schedule',str(key),str(n))
    result,score=self.r.blpop(key)
    self.now=n
    self.release(key)
    return result,score

  def waituntil(self,n):
    mylock=self.gettoken()
    result,score=self.waiton(mylock,n)
    return result,score

  def waitfor2(self,n):
    result,score=self.waituntil(self.now+n)
    return result,score

  def waitfor(self,n):
    if n <= 0:
       return
    for i in range(0,n):
       self.waittick()

  def waittick(self):
    key=self.gettoken()
    self.r.zadd('ticks',str(key),str(0))
    result,score=self.r.blpop(key)
    self.release(key)
    simtime=self.getsimtime()
    expect_tick = self.mytick+0.001
    act_tick=float(simtime)
    if self.debug and not isclose(act_tick, expect_tick):
      self.alert.write("%0.3f %s Missed Clock tick: %0.3f\n" % (act_tick,self.name,expect_tick))
    self.mytick =act_tick
    return simtime

  def waitsectick(self):
    key=self.gettoken()
    self.r.zadd('secticks',str(key),str(0))
    result,score=self.r.blpop(key)
    self.release(key)
    return str(int(float(self.getsimtime())))

  def wait10mstick(self):
    key=self.gettoken()
    self.r.zadd('10msticks',str(key),str(0))
    result,score=self.r.blpop(key)
    self.release(key)
    return str(int(float(self.getsimtime())))

  def wait100mstick(self):
    key=self.gettoken()
    self.r.zadd('100msticks',str(key),str(0))
    result,score=self.r.blpop(key)
    self.release(key)
    return str(int(float(self.getsimtime())))

  def lock(self):
    timlock=self.gettoken()
    self.r.sadd('timlock',str(timlock))
    now=self.getsimtime()
    return timlock,now

  def unlock(self,timlock):
    try:
       self.r.srem('timlock',str(timlock))
    except:
       pass

  def writedb(self,attr,value):
    self.r.set(attr,str(value))


  def updatebps(self,elem,bits): # bits
    val=float(self.r.get("simbuck"))
    fval = "%08.1f" % val
    cursec='bits:'+elem+':'+str(fval)
    try:
      curval=int(self.r.get(cursec))
      curval+=bits
      curval=int(curval)
    except:
      curval=int(bits)
    self.r.set(cursec,str(curval))
    self.r.expire(cursec,100)
    return curval

  def getbps(self,elem):
    bits=0
    pattern='bits:'+elem+':*'
#    l=list(self.r.scan_iter(match=pattern))
    l=self.r.keys(pattern)
    l.sort()
    l=l[-10:] # get the last 10 keys
    for e in l:
       try:
         b = self.r.get(e)
         bits+=int(b)    
       except:
         pass
    return bits


#@threaded
#class tally(process):
#  def __init__(self,a):
#    self.a = a
#    self.t = 0
#    process.__init__(self,5)
#
#  def worker(self):
#    while True:
#       self.waitfor(3)
#       self.t+=self.a
#       print "Tally is %d %d" % (self.a,self.t)
#      
#sched=scheduler()
#T=tally(2)
#S=tally(4)
#while True:
#  time.sleep(5)
         


