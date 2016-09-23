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

# pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
#pool = redis.ConnectionPool(unix_socket_path='/var/run/redis/redis.sock')
#globalr = redis.Redis(connection_pool=pool )
globalr=redis.Redis(unix_socket_path='/var/run/redis/redis.sock')

#r = redis.Redis(
#    host=hostname,
#    port=port )

class scheduler(object):
   import random
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
      self.calcstats()
      self.calcbitrate()
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
      ret=self.r.lpush(key,self.simtime)

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
#         else:
#            time.sleep(0.1)
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

   def gettoken(self):
     key=self.randtoken()
     return(key)

   def release(self,key):
     self.r.delete(key)

   def waittick(self):
     key=self.gettoken()
     self.r.zadd('ticks',str(key),str(0))
     result,score=self.r.blpop(key)
     self.release(key)
     simtime=self.simtime
     return simtime

   def waitsectick(self):
     key=self.gettoken()
     self.r.zadd('secticks',str(key),str(0))
     result,score=self.r.blpop(key)
     self.release(key)
     return str(int(float(self.simtime)))

   def wait10mstick(self):
     key=self.gettoken()
     self.r.zadd('10msticks',str(key),str(0))
     result,score=self.r.blpop(key)
     self.release(key)
     return str(int(float(self.simtime)))

   def wait100mstick(self):
     key=self.gettoken()
     self.r.zadd('100msticks',str(key),str(0))
     result,score=self.r.blpop(key)
     self.release(key)
     return str(int(float(self.simtime)))

   def randtoken(self,size=6, chars=string.ascii_uppercase + string.digits):
     return ''.join(self.random.choice(chars) for _ in range(size))

   def lock(self):
     timlock=self.gettoken()
     self.r.sadd('timlock',str(timlock))
     now=self.simtime
     return timlock,now

   def unlock(self,timlock):
     try:
        self.r.srem('timlock',str(timlock))
     except:
        pass


   @threaded
   def calcstats(self):
      while True:
         simtime=self.waitsectick()
         timlock,now=self.lock()
         l = self.r.keys(pattern='stats:*')
         m=[]
         for e in l:
            w=e.split(':')[:-1]
            w=":".join(w)
            m.append(w)
         for e in m:
            tally=0
            pattern=e+":*"
            l=self.r.keys(pattern)
            l.sort()
            l=l[-10:] # get the last 10 keys
            for f in l:
               try:
                  b = self.r.get(f)
                  tally+=int(b)
               except:
                  pass
            f=e.split(':')
            unit=f[0]+'ps:'+f[1]+'ps:'+":".join(f[2:])+':'+simtime
            self.r.set(unit,tally)
         self.unlock(timlock)
      return

   @threaded
   def calcbitrate(self):
      while True:
         simtime=self.wait100mstick()
         timlock,now=self.lock()
         l = self.r.keys(pattern='stats:*')
         m=[]
         for e in l:
            w=e.split(':')[:-1]
            w=":".join(w)
            m.append(w)
         for e in m:
            tally=0
            pattern=e+":*"
            l=self.r.keys(pattern)
            l.sort()
            try:
               f=l[-1:][0] #
               b = int(self.r.get(f))*10 # 100th second * 10
               f=e.split(':')
               unit=f[0]+'ps:'+f[1]+'ps:'+":".join(f[2:])+':now'
               self.r.set(unit,b)
            except:
               print "Calcbitrate Exception"
         self.unlock(timlock)
      return



class process(object):
  import string
  import random
  def __init__(self,now=0,debug=False):
#    self.r= redis.Redis(host=hostname,port=port )
    self.r = globalr
    self.now=now
    self.mytick=0
    self.simtime=0
    self.begin()
    self.debug=debug
    self.alert=open("alert.log","a+")
    self.proctime=0
    self.ticktock()

  @threaded
  def begin(self):
    stime=self.waituntil(self.now)

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
    return self.simtime

  def gettoken(self):
    key=self.randtoken()
    return(key)

  def getsimtime(self):
    return self.simtime
#    return self.r.get("simtime")

  def release(self,key):
    self.r.delete(key)

  @threaded
  def ticktock(self):
    while True:
      self.simtime=self.waittick()

# wait until 0.001 seconds
  def waiton(self,key,n):
    self.r.zadd('schedule',str(key),str(n))
    result,score=self.r.blpop(key)
#    self.now=n
    self.release(key)
    return str(float(score))
  
# wait until 0.001 seconds
  def waituntil(self,n):
    mylock=self.gettoken()
    stime=self.waiton(mylock,n)
    return stime

  def waitfor2(self,n):
    stime=self.waituntil(self.now+n)
    return stime

  # wait n ticks
  def waitfor(self,n):
    if n <= 0:
       return self.simtime
    for i in range(0,n):
       stime = self.waittick()
    return stime

  def waittick(self):
     s=float(self.simtime); p=float(self.proctime)
     if s >= p+0.001:
         self.proctime=self.simtime
         if self.debug:
            self.alert.write("%0.3f %s Missed Clock tick: %0.3f\n" % (s,self.name,p))
         return self.simtime
     key=self.gettoken()
     self.r.zadd('ticks',str(key),str(0))
     result,score=self.r.blpop(key)
     self.proctime=str(float(score))
     self.release(key)
# ?? self.simtime = self.proctime
     return self.proctime

#    key=self.gettoken()
#    self.r.zadd('ticks',str(key),str(0))
#    result,score=self.r.blpop(key)
#    simtime=str(float(score))
#    self.release(key)
#    expect_tick = float(self.simtime)+0.001
#    act_tick=score
#    if self.debug and not isclose(act_tick, expect_tick):
#      self.alert.write("%0.3f %s Missed Clock tick: %0.3f\n" % (act_tick,self.name,expect_tick))
#    return simtime

  def waitsectick(self):
    key=self.gettoken()
    self.r.zadd('secticks',str(key),str(0))
    result,score=self.r.blpop(key)
    self.release(key)
    return str(int(float(self.simtime)))

  def wait10mstick(self):
    key=self.gettoken()
    self.r.zadd('10msticks',str(key),str(0))
    result,score=self.r.blpop(key)
    self.release(key)
    return str(int(float(self.simtime)))

  def wait100mstick(self):
    key=self.gettoken()
    self.r.zadd('100msticks',str(key),str(0))
    result,score=self.r.blpop(key)
    self.release(key)
    return str(int(float(self.simtime)))

  def lock(self):
    timlock=self.gettoken()
    self.r.sadd('timlock',str(timlock))
    return timlock,self.simtime

  def unlock(self,timlock):
    try:
       self.r.srem('timlock',str(timlock))
    except:
       pass
    return self.simtime

  def writedb(self,attr,value):
    self.r.set(attr,str(value))

  def getval(self,attr):
    try:
      v = self.r.get(attr)
    except:
      v=0
    return v


  def updatestats(self,elem,bits,units): # bits
    val=float(self.r.get("simbuck"))
    fval = "%08.1f" % val
    cursec="stats:"+units+':'+elem+':'+str(fval)
    try:
      self.r.incrby(cursec,str(bits))
      self.r.expire(cursec,100)
      cursec="stats:"+units+':tally'
      self.r.incrby(cursec,str(bits))
    except:
       print "update stats error"
    return 

  def getstats(self,elem,units):
    bits=0
    try:
       pattern="stats:"+units+':'+elem+':*'
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
       if len(l) > 0:
          bits=bits*10/len(l) # scale up
#    self.r.set("statsps:"+units+"ps:"+elem,bits)
    except:
       bits=0
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
         


