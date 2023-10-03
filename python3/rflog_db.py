#!/usr/bin/env python
#rflog_db.py Interface between RF Module serial interface and AdafruitIO
#---------------------------------------------------------------------------------
# Release from JemRF.com
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Revision History
# V1.00 - Release
# V2.00 - Updates to improve performance and added new sensor types
# V3.00 - Updated for Python 3
# V3.10 - Updated to fix issue with BME devices and add support for RSSI.
# -----------------------------------------------------------------------------------
#
import MySQLdb
import serial
import time
from time import sleep
import sys
from threading import Thread
from bme280 import process_bme_reading
from rf2serial import rf2serial
import rfsettings

DEBUG = True
Farenheit = False

def dprint(message):
  if (DEBUG):
    print(message)

def ProcessMessageThread(value, value2, DevId, type):
  try:
      thread.start_new_thread(ProcessMessage, (value, value2, DevId, type, ) )
  except:
      print("Error: unable to start thread")

def LogTelemetry(devid, type, value, uom):
  # log the temperature to the database
  # open database connection
  db = MySQLdb.connect(
  "localhost",
  "dblogger",
  "password",
  "sensor_logs" )


  # prepare a cursor object using cursor()
  # method
  cursor = db.cursor()

  # build the SQL statement
  sql = "INSERT INTO telemetry_log (device_id, type, value, date, unit_of_measure) VALUES ('%s', %d, '%s', NOW(), '%c')" % (devid, type, value, uom)

  dprint(sql);

  # Execute the SQL command
  cursor.execute(sql)

  # Commit your changes in the database
  db.commit()

  # disconnect from server
  db.close()

  dprint("Telemetry "+ str(devid) + ","+ str(type) + "," + str(value) + "," + uom + "," + "logged");

def ProcessMessage(value, DevId, type, uom):
# Notify the host that there is new data from a sensor (e.g. door open)
  try:
    dprint("Processing data : DevId="+str(DevId)+",Type="+str(type)+",Value="+str(value))
    LogTelemetry(DevId,type, value, uom)

  except Exception as e: dprint(e)
  return(0)

def remove_duplicates():
    x=0
    dprint("sorted deduplified queue:")

    #sort the queue by ID
    rfsettings.message_queue = sorted(rfsettings.message_queue, key = lambda x: (x[0]))

    x=0
    while x<len(rfsettings.message_queue)-1:
        if rfsettings.message_queue[x][0]==rfsettings.message_queue[x+1][0] and \
           rfsettings.message_queue[x][1]==rfsettings.message_queue[x+1][1]:
            rfsettings.message_queue.pop(x)
        else:
            x=x+1

    for x in range(0,len(rfsettings.message_queue)):
        print(rfsettings.message_queue[x][0]+rfsettings.message_queue[x][1])

def queue_processing():
  global measure
  try:
    sensordata=""
    bme_data=bytearray()
    bme_messages=0
    uom=""
    start_time = time.time()
    while (True):
        if len(rfsettings.message_queue)>0 and not rfsettings.rf_event.is_set():
            if bme_messages == 0:
               remove_duplicates()
            message = rfsettings.message_queue.pop()
            try:
               devID = message[0].decode()
               data = message[1].decode()
               dprint(time.strftime("%c")+ " " + devID + data)
            except Exception as e:
               data = "BMP"

            if data.startswith('BUTTONON'):
                sensordata=0
                db_type=1
                uom="B"

            if data.startswith('STATEON'):
                sensordata=0
                db_type=2
                uom="S"

            if data.startswith('STATEOFF'):
                sensordata=1
                db_type=2
                uom="S"

            if data.startswith('BUTTONOFF'):
                sensordata=1
                db_type=1
                uom="S"

            if data.startswith('TMPA'):
                sensordata=DoFahrenheitConversion(str(data[4:].rstrip("-")))
                db_type=3
                if Farenheit : uom="F"
                else : uom="C"

            if data.startswith('ANAA'):
                sensordata=str(data[4:].rstrip("-"))
                sensordata=(float(sensordata)-1470)/16 #convert it to a reading between 1(light) and 48 (dark)
                sensordata=str(sensordata)
                db_type=4
                measure='2'
                uom=""

            if data.startswith('ANAB'):
                sensordata=str(data[4:].rstrip("-"))
                sensordata=(float(sensordata)-1470)/16 #convert it to a reading between 1(light) and 48 (dark)
                sensordata=str(sensordata)
                measure='2'
                db_type=4
                uom=""

            if data.startswith('TMPC'):
                sensordata=DoFahrenheitConversion(str(data[4:].rstrip("-")))
                db_type=1
                if Farenheit : uom="F"
                else : uom="C"

            if data.startswith('TMPB'):
                sensordata=DoFahrenheitConversion(str(data[4:].rstrip("-")))
                db_type=1
                if Farenheit : uom="F"
                else : uom="C"

            if data.startswith('HUM'):
                sensordata=str(data[3:].rstrip("-"))
                db_type=5
                measure='2'
                uom="%"

            if data.startswith('BATT'):
                sensordata=data[4:].strip('-')
                db_type=6
                uom="V"
                
            if data.startswith('RSSI'):
                sensordata=data[4:]
                db_type=8
                uom="d"
         
            if data.startswith('BMP') or (bme_messages>0 and sensordata==''):
              data = message[1]
              start_time = time.time()
              if bme_messages==0:
                  bme_data[len(bme_data):]=data[5:9]
              else:
                  bme_data[len(bme_data):]=data[0:9]
              bme_messages=bme_messages+1


              if bme_messages==5:
                bme_messages=0
                bme280=process_bme_reading(bme_data, devID)
                if bme280.error != "":
                  dprint(bme280.error)
                else:
                  if bme280.temp_rt == 1:
                    if Farenheit : uom="F"
                    else : uom="C"
                    ProcessMessage(DoFahrenheitConversion(round(bme280.temp,1)), devID, 1, uom)
                  if bme280.hum_rt == 1:
                    measure='2'
                    ProcessMessage(round(bme280.hum,2), devID, 5, "%")
                  if bme280.hum_rt == 1:
                    measure='2'
                    ProcessMessage(round(bme280.press/100,1), devID, 7, "P")
                bme_messages=0
                bme_data=bytearray()
            if sensordata != "":
                ProcessMessage(sensordata, devID, db_type, uom)
        sensordata=""

        if rfsettings.event.is_set():
            break

        elapsed_time = time.time() - start_time
        if (elapsed_time > 5):
            start_time = time.time()-120
            bme_messages=0
            bme_data=bytearray()

  except Exception as e:
      template = "An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message)
      print(e)
      rfsettings.event.set()
      exit()


def DoFahrenheitConversion(value):
  if Farenheit:
    value = float(value)*1.8+32
    value = round(value,2)
  return(value)

def main():
    dprint("Data Logger Started.")
    rfsettings.init()

    a=Thread(target=rf2serial, args=())
    a.start()

    b=Thread(target=queue_processing, args=())
    b.start()

    while not rfsettings.event.is_set():
      try:
          sleep(1)
      except KeyboardInterrupt:
          rfsettings.event.set()
          break

if __name__ == "__main__":
    try:
      main()
    except Exception as e:
      template = "An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(e).__name__, e.args)
      print(message)
      print(e)
      rfsettings.event.set()
    finally:
      rfsettings.event.set()
      exit()






