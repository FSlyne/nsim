import redis
import time

def threaded(fn):
    import threading
    def wrapper(*args, **kwargs):
        t=threading.Thread(target=fn, args=args, kwargs=kwargs)
        t.daemon=True
        t.start()
    return wrapper


hostname = '127.0.0.1'
port = '6379'

#r = redis.Redis(
#    host=hostname,
#    port=port )

class scheduler(object):
   def __init__(self, tick=1,wait=0,debug=0,finish=0):
      self.finish = finish
      self.tick = tick 
      self.gap = tick*0.9
      self.wait = wait
      self.queue='schedule'
      self.simtime=0
      self.r = redis.Redis(host=hostname,port=port )
      self.r.flushall()
      self.r.set('simtime','0.000')
      self.setactive()
#      self.process()
      self.dbg=debug=1
      self.logreader()

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
         try:
           for result,score in self.r.zrangebyscore(self.queue, 0 ,str(self.simtime+self.gap),withscores=True):
             if self.r.zrem(self.queue, result) == 1:
                self.signal(result)
                self.debug("%s %s %s" % (str(self.simtime),str(score),str(result)))
             else:
                self.debug("%s *" % self.simtime)
           else:
                self.debug("%s +" % self.simtime)
         except:
           self.debug("%s !" %self.simtime)
         if not self.r.exists('timlock'):
            self.simtime+=self.tick
         if self.wait > 0:
            time.sleep(self.wait)
         self.r.set("simtime",str(self.simtime))
      self.setinactive()

   @threaded
   def logreader(self):
      while True:
         print self.r.blpop("Logger")[1]

class process(object):
  import string
  import random
  def __init__(self,now=0,lk=False):
    self.r= redis.Redis(host=hostname,port=port )
    self.now=now
    self.lk = lk
    self.begin()

  @threaded
  def begin(self):
    result,score=self.waituntil(self.now,self.lk)

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

  def release(self,key):
    self.r.delete(key)

  def waiton(self,key,n,lk):
    self.r.zadd('schedule',str(key),str(n))
    result,score=self.r.blpop(key)
    self.now=n
    self.release(key)
    return result,score

  def waituntil(self,n,lk=False):
    mylock=self.gettoken()
    result,score=self.waiton(mylock,n,lk)
    if lk:
       self.lock()
    return result,score

  def waitfor(self,n,lk=False):
    result,score=self.waituntil(self.now+n,lk)
    return result,score

  def lock(self):
    print "locking !!"
    self.timlock=self.gettoken()
    self.r.sadd('timlock',str(self.timlock))

  def unlock(self):
    print "unlocking !!"
    try:
       self.r.srem('timlock',str(self.timlock))
    except:
       pass

@threaded
class tally(process):
  def __init__(self,a):
    self.a = a
    self.t = 0
    process.__init__(self,5)

  def worker(self):
    while True:
       self.waitfor(3)
       self.t+=self.a
       print "Tally is %d %d" % (self.a,self.t)
      
sched=scheduler()
T=tally(2)
S=tally(4)
sched.process()
         


