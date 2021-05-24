#!/usr/bin/env python3

import sys
import serial
import threading
import time
import datetime

from serial import Serial

def get_time_stamp():
  return time.clock_gettime_ns(time.CLOCK_THREAD_CPUTIME_ID)

def get_now():
  return str(datetime.datetime.now())

def write(promt):
  sys.stdout.write(promt)


def uart_transmit():
  incoming = input()
  

def uart_receive():
  write(get_now() + ': Listening...\n')
  timer_stamp = 0
  while True:
    buff = ''
    if char:
      buff = uart_conn.read().decode()
    else:
      buff = hex(int.from_bytes(uart_conn.read()))
      buff = ' ' + buff
    current_time_stamp = get_time_stamp()
    if timer_stamp < current_time_stamp:
      write('\033[F')
      write('\n'+ get_now() + ': Got: ')
    else:
      write('\033[F')
    write(str(buff)+'\n')
    sys.stdout.flush()
    timer_stamp = get_time_stamp() + 50000


if __name__ == '__main__':
  baud = 115200
  serial_path = '/dev/ttyUSB'
  par = serial.PARITY_NONE
  par_str = 'no'
  search_range = 10
  global char
  char = True
  #check for arguments
  while len(sys.argv) > 1:
    current = sys.argv.pop(-1)  
    if current.isnumeric():
      current = int(current)
      if current < 50:
        search_range = current
      else:
        baud = current
    elif current == 'even':
      par = serial.PARITY_EVEN
      par_str = current
    elif current == 'odd':
      par = serial.PARITY_ODD
      par_str = current
    elif current == 'mark':
      par = serial.PARITY_MARK
      par_str = current
    elif current == 'space':
      par = serial.PARITY_SPACE
      par_str = current
    elif current.endswith('help') :
      print('Usage: uart.py [options]')
      print('Options can be baud rate and/or serial path, order doesn\'t matter')
    elif current.startswith('tty'):
      serial_path = '/dev/' + current
      try:
        uart_conn = Serial(serial_path,baud,timeout=1)
        uart_conn.close()
        print('\nConnected to', serial_path)
      except:
        print('\nCannot open', serial_path)
        print('\nExiting...')
        exit(1)
    else:
      print('\nUnvalid argument:', current,'\nSkipping...')
  if serial_path == '/dev/ttyUSB':
    current = ''
    for i in range(search_range+1):
      current = serial_path + str(i)
      try:
        uart_conn = Serial(current,baud,timeout=1)
        uart_conn.close()
        serial_path = current
        print('\nConnected to', serial_path)
      except:
        continue
  if serial_path == '/dev/ttyUSB':
    print('\nCannot find ttyUSB device, searching for ttyACM...')
    serial_path = '/dev/ttyACM'
    current = ''
    for i in range(search_range+1):
      current = serial_path + str(i)
      try:
        uart_conn = Serial(current,baud,timeout=1)
        uart_conn.close()
        serial_path = current
        print('\nConnected to', serial_path)
      except:
        continue
  if serial_path == '/dev/ttyACM':
    print('\nCannot find ttyACM device, searching for ttyCOM...')
    serial_path = '/dev/ttyCOM'
    current = ''
    for i in range(search_range+1):
      current = serial_path + str(i)
      try:
        uart_conn = Serial(current,baud,timeout=1)
        uart_conn.close()
        serial_path = current
        print('\nConnected to', serial_path)
      except:
        continue
  if serial_path == '/dev/ttyCOM':
    print('\nCannot find ttyCOM device, exiting...')
    exit(1)
  
  print('Configurations:',baud,par_str,'parity\n')
  uart_conn = Serial(serial_path,baud,parity=par)

  thread_tx = threading.Thread(target=uart_transmit)
  thread_rx = threading.Thread(target=uart_receive)
  thread_rx.setDaemon(True)

  thread_rx.start()
  thread_tx.start()
  thread_tx.join()
  uart_conn.close()
