import time

def threaded(fn):
    import threading
    def wrapper(*args, **kwargs):
        t=threading.Thread(target=fn, args=args, kwargs=kwargs)
        t.daemon=True
        t.start()
    return wrapper

class scheduler(object):
   def __init__(self):
      self.plist=[]
      self.process()

   @threaded
   def process(self):
      while True:
         for p in self.plist:
            p.fn()
            print p.a,p.b
         time.sleep(1)

   def addp(self,p,a,b):
      self.plist.append(self.func(p,a,b))

   class func(object):
      def __init__(self,fn,a,b):
         self.fn = fn
         self.a = a
         self.b = b

class extern(object):
   def __init__(self):
      sched=scheduler()
      sched.addp(self.say_hello,1,2)

   def say_hello(self):
      print "hello"

def say_hello():
   print "hello2"

#sched=scheduler()
e=extern()
#sched.addp(e.say_hello)

while True:
   time.sleep(1)

#scheduler().invoke(e.say_hello)

# sched=scheduler()
# sched.process()
