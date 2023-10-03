#!/usr/bin/env python
#Updated for Python 3
#Updated 10/2/2024 for BMP devices
import serial
import rfsettings
from time import sleep
import time

def rf2serial():
  try:
    port = '/dev/serial0'
    baud = 9600
    ser = serial.Serial(port=port, baudrate=baud)
    llapMsg=""
    llapMsgb = bytearray()
    while (True):
        # wait for a moment before doing anything else
        while ser.inWaiting():
          rfsettings.rf_event.set()
          nextbyte = ser.read()
          llapMsgb +=nextbyte
          # check we have the start of a LLAP message
          t = -1
          if llapMsgb[0] == 97:
             t =0
          if (t>=0 and len(llapMsgb)-t>=12): # we have an llap message
              start_time = time.time()
              rfsettings.message_queue.insert(0,(llapMsgb[t+1:t+3], llapMsgb[t+3:t+12]))
              llapMsgb = bytearray()
              sleep(0.2)
          if nextbyte == b'\x00' and t == -1:
             llapMsgb = bytearray()   # purge end of line
             break
        if rfsettings.event.is_set():
          break
        rfsettings.rf_event.clear()
        sleep(0.2)

  except Exception as e:
      template = "An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message)
      print(e)
      rfsettings.event.set()
      exit()
