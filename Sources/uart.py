#!/usr/bin/env python3

import sys
import serial
import threading
import time
import datetime

from serial import Serial

def get_time_stamp():
  return time.clock_gettime_ns(time.CLOCK_THREAD_CPUTIME_ID)

#Some text coloring 
def get_now():
  return  '\033[35m' + str(datetime.datetime.now()) + ':\033[0m'

def print_error(msg):
  print('\033[31m',msg,'\033[0m',sep='')

def print_success(msg):
  print('\033[32m',msg,'\033[0m',sep='')

def print_info(msg):
  print('\033[2m',msg,'\033[0m',sep='')

def print_warn(msg):
  print('\033[33m',msg,'\033[0m',sep='')

def write(promt):
  sys.stdout.write(promt)

#Threaded functions
def uart_transmit():
  incoming = input()
  

def uart_receive():
  write(get_now() + ' Listening...\n')
  timer_stamp = 0
  last_line = ''
  while True:
    buff = ''
    if char:
      buff = uart_conn.read().decode()
    else:
      buff = hex(int.from_bytes(uart_conn.read()))
      buff = ' ' + buff
    current_time_stamp = get_time_stamp()
    if timer_stamp < current_time_stamp:
      last_line = '\033[F' + '\n'+ get_now() + ' \033[36mGot:\033[0m '
    else:
      write('\033[F')
    last_line+=str(buff)
    write(last_line+'\n')
    sys.stdout.flush()
    timer_stamp = get_time_stamp() + 50000

#Main function
if __name__ == '__main__':
  baud = 115200
  serial_path = '/dev/ttyUSB'
  par = serial.PARITY_NONE
  par_str = 'no'
  search_range = 10
  global char
  char = True
  #check arguments for custom settings
  while len(sys.argv) > 1:
    current = sys.argv.pop(-1)  
    if current.isnumeric():
      current = int(current)
      if current < 50:
        search_range = current
      else:
        baud = current
    elif current == 'even' or current.casefold() == 'e':
      par = serial.PARITY_EVEN
      par_str = 'even'
    elif current == 'odd' or current.casefold() == 'o':
      par = serial.PARITY_ODD
      par_str = 'odd'
    elif current == 'mark' or current.casefold() == 'm':
      par = serial.PARITY_MARK
      par_str = 'mark'
    elif current == 'space' or current.casefold() == 's':
      par = serial.PARITY_SPACE
      par_str = 'space'
    elif current == 'no' or current.casefold() == 'n':
      continue
    elif current.endswith('help') :
      print('Usage: uart.py [options]')
      print_info('Options can be baud rate and/or serial path, order doesn\'t matter')
    elif current.startswith('tty'):
      serial_path = '/dev/' + current
      try:
        uart_conn = Serial(serial_path,baud,timeout=1)
        uart_conn.close()
      except:
        print_error('\nCannot open ' + serial_path)
        print_info('\nExiting...')
        exit(1)
    else:
      print_warn('\nUnvalid argument:'+current)
      print_info('Skipping...')

  if serial_path == '/dev/ttyUSB': #if no device is given, poll for it
    current = ''
    for i in range(search_range+1):
      current = serial_path + str(i)
      try:
        uart_conn = Serial(current,baud,timeout=1)
        uart_conn.close()
        serial_path = current
      except:
        continue
  if serial_path == '/dev/ttyUSB':
    print_warn('\nCannot find ttyUSB device, searching for ttyACM...')
    serial_path = '/dev/ttyACM'
    current = ''
    for i in range(search_range+1):
      current = serial_path + str(i)
      try:
        uart_conn = Serial(current,baud,timeout=1)
        uart_conn.close()
        serial_path = current
      except:
        continue
  if serial_path == '/dev/ttyACM':
    print_warn('\nCannot find ttyACM device, searching for ttyCOM...')
    serial_path = '/dev/ttyCOM'
    current = ''
    for i in range(search_range+1):
      current = serial_path + str(i)
      try:
        uart_conn = Serial(current,baud,timeout=1)
        uart_conn.close()
        serial_path = current
      except:
        continue
  if serial_path == '/dev/ttyCOM':
    print_error('\nCannot find any devices, exiting...')
    exit(1)

  print_success('\nConnected to '+ serial_path)
  print_info('Configurations: '+str(baud)+' '+par_str+' parity\n')
  uart_conn = Serial(serial_path,baud,parity=par)

  #Set up and run threads
  thread_tx = threading.Thread(target=uart_transmit)
  thread_rx = threading.Thread(target=uart_receive)
  thread_rx.setDaemon(True)

  thread_rx.start()
  thread_tx.start()

  thread_tx.join()
  uart_conn.close()
