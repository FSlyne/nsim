from random import choice,randint
import string
import math

def packet_drop(n_bits,err):
   p_error = pow(10,err)
   prob_no_error = pow(1-p_error,n_bits)
   prob_error = 1- prob_no_error
   r=int(1/prob_error)
   v=randint(1,r+1)
   if v == r:
      return True
   else:
      return False


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


