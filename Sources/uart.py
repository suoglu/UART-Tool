#!/usr/bin/env python3

import sys
import serial
import threading
import time
import datetime
import os

from serial import Serial


#Prompt coloring 
def get_now():
  return  '\033[35m' + str(datetime.datetime.now()) + ':\033[0m'

def print_error(promt):
  sys.stdout.write('\033[31m'+promt+'\033[0m')

def print_success(promt):
  sys.stdout.write('\033[32m'+promt+'\033[0m')

def print_info(promt):
  sys.stdout.write('\033[2m'+promt+'\033[0m')

def print_warn(promt):
  sys.stdout.write('\033[91m'+promt+'\033[0m')


#Helper functions
def get_time_stamp():
  return time.clock_gettime_ns(time.CLOCK_THREAD_CPUTIME_ID)

def write(promt):
  sys.stdout.write(promt)

def print_commands():
  write(' ~ \\char: print received bytes as character\n')
  write(' ~ \\exit: exits the script\n')
  write(' ~ \\hex : print received bytes as hexadecimal number\n')
  write(' ~ \\quit: exits the script\n')
  write('\nTo send a \'\\\' as a first byte use \'\\\\\'\n')

#listener daemon
def uart_listener(): #TODO: keep the prompt already written in terminal when new received
  write(get_now())
  print_info(' Listening...\n')
  timer_stamp = 0
  last_line = ''
  byte_counter = 0
  while True: #main loop for receive
    buff = uart_conn.read()
    if char:
      buff = buff.decode()
    else:
      buff = hex(int.from_bytes(buff,byteorder='little'))
      buff+= ' '
    if (timer_stamp < get_time_stamp()) or ((buff == '\n') and char) or ((byte_counter == 15) and not char):
      byte_counter = 0
      last_line = '\033[F' + '\n'+ get_now() + ' \033[36mGot:\033[0m '
    else:
      write('\033[F\r')
      byte_counter+=1
    last_line+=buff
    write(last_line+'\n')
    sys.stdout.flush()
    timer_stamp = get_time_stamp() + 70000

#Main function
if __name__ == '__main__':
  baud = 115200
  serial_path = '/dev/ttyUSB'
  par = serial.PARITY_NONE
  par_str = 'no'
  search_range = 10
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
        print_info('\nExiting...\n')
        exit(1)
    else:
      print_warn('\nUnvalid argument:'+current)
      print_info('\nSkipping...\n')

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
    print_error('\nCannot find any devices, exiting...\n')
    exit(1)

  print_success('\nConnected to '+ serial_path)
  print_info('\nConfigurations: '+str(baud)+' '+par_str+' parity\n\n')
  char = True
  uart_conn = Serial(serial_path,baud,parity=par)
  
  #Set up listener daemon
  thread_rx = threading.Thread(target=uart_listener,daemon=True)
  thread_rx.start()
  
  incoming = ''
  while True: #main loop for send
    incoming = input()
    write('\033[F'+get_now()+' ')
    if incoming.startswith('\quit') or incoming.startswith('\exit'):
      break
    elif incoming.startswith('\help'):
      print_info('Help\n')
      write('Available Commands:\n')
      print_commands()
      continue
    elif incoming.startswith('\char'):
      #update_config(config_file_decoding,1)
      char = True
      print_info('Received bytes will be printed as character\n')
      continue
    elif incoming.startswith('\hex'):
      # update_config(config_file_decoding,0)
      print_info('Received bytes will be printed as hexadecimal number\n')
      char = False
      continue
    elif incoming.startswith('\\'):
      if incoming.startswith('\\\\'):
        incoming = incoming[1:]
      else:
        print_warn('Command \033[0m' + incoming + '\033[91m does not exist!\n')
        continue
    
    incoming+='\n'
    write('\033[33mSend:\033[0m '+incoming)
  print_info('Exiting...\n')

  uart_conn.close()
