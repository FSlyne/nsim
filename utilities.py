from random import choice
import string

def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
   return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def is_integer(fl):
   return isclose(fl, round(fl))


def randPayload(size):
   return (''.join(choice(string.ascii_letters) for i in range(size)))


def chksum(string):
  checksum=0
  for c in string:
     checksum ^=ord(c)
  return "%02X" % checksum


