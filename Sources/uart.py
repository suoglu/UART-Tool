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
  write(' ~ \\binhex : print received bytes as binary number\n')
  write(' ~ \\bin    : print received bytes as binary number and hexadecimal equivalent\n')
  write(' ~ \\c      : print received bytes as character\n')
  write(' ~ \\char   : print received bytes as character\n')
  write(' ~ \\dec    : print received bytes as decimal number\n')
  write(' ~ \\dechex : print received bytes as decimal number and hexadecimal equivalent\n')
  write(' ~ \\exit   : exits the script\n')
  write(' ~ \\h      : print received bytes as hexadecimal number\n')
  write(' ~ \\hex    : print received bytes as hexadecimal number\n')
  write(' ~ \\q      : exits the script\n')
  write(' ~ \\quit   : exits the script\n')
  write(' ~ \\safe   : in non char mode, stop sending if non number given\n')
  write(' ~ \\unsafe : in non char mode, do not stop sending if non number given\n')
  write('\nTo send a \'\\\' as a first byte use \'\\\\\'\n')

#listener daemon
def uart_listener(): #TODO: keep the prompt already written in terminal when new received
  write(get_now())
  print_info(' Listening...\n')
  timer_stamp = 0
  last_line = ''
  byte_counter = 0
  while True: #main loop for listener
    buff = uart_conn.read()
    if char:
      buff = buff.decode()
    else:
      val = int.from_bytes(buff,byteorder='little')
      if dec_ow:
        buff = str(val)
      elif bin_ow:
        buff = bin(val)
      else:
        buff = hex(val)
      if hex_add:
        buff+=(' ('+hex(val)+')')
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
  #Software Configurations
  char = True
  dec_ow = False
  bin_ow = False
  hex_add = False
  safe_tx = False
  uart_conn = Serial(serial_path,baud,parity=par)
  
  #Set up listener daemon
  thread_rx = threading.Thread(target=uart_listener,daemon=True)
  thread_rx.start()
  
  cin = ''
  while True: #main loop for send
    cin = input()
    write('\033[F'+get_now()+' ')
    if cin == '\quit' or cin =='\exit' or cin =='\q':
      break
    elif cin == '\help':
      print_info('Help\n')
      write('Available Commands:\n')
      print_commands()
      continue
    elif cin == '\char' or cin == '\c':
      char = True
      dec_ow = False
      bin_ow = False
      hex_add = False
      print_info('Received bytes will be printed as character\n')
      continue
    elif cin == '\hex' or cin == '\h':
      print_info('Received bytes will be printed as hexadecimal number\n')
      char = False
      dec_ow = False
      bin_ow = False
      hex_add = False
      continue
    elif cin == '\dec':
      print_info('Received bytes will be printed as decimal number\n')
      char = False
      dec_ow = True
      bin_ow = False
      hex_add = False
      continue
    elif cin == '\\bin':
      print_info('Received bytes will be printed as binary number\n')
      char = False
      dec_ow = False
      bin_ow = True
      hex_add = False
      continue
    elif cin == '\dechex':
      print_info('Received bytes will be printed as decimal number and hexadecimal equivalent\n')
      char = False
      dec_ow = True
      bin_ow = False
      hex_add = True
      continue
    elif cin == '\\binhex':
      print_info('Received bytes will be printed as binary number and hexadecimal equivalent\n')
      char = False
      dec_ow = False
      bin_ow = True
      hex_add = True
      continue
    elif cin == '\\safe':
      print_info('Safe transmit mode enabled\n')
      safe_tx = True
      continue
    elif cin == '\\unsafe':
      print_info('Safe transmit mode disabled\n')
      safe_tx = False
      continue
    elif cin.startswith('\\'):
      if cin.startswith('\\\\'):
        cin = cin[1:]
      else:
        print_warn('Command \033[0m' + cin + '\033[91m does not exist!\n')
        continue
    error_str = ''
    send_str = ''
    toSend = 0
    if not char:
      for item in cin.split(' '):
        try:
          if item.startswith('0x'):
            toSend = int(item, 16)
          elif item.startswith('0d'):
            toSend = int(item, 10) 
          elif item.startswith('0b') or bin_ow:
            toSend = int(cin, 2)
          elif dec_ow:
            toSend = int(item, 10) 
          else:
            toSend = int(item)
        except:
          error_str+=(item + ' is not a valid number!\n')
          if safe_tx:
            break
          else:
            continue
        send_str+=(item + ' ')
        uart_conn.write(toSend.to_bytes(1,'little'))
      cin = send_str
    else:
      uart_conn.write(cin.encode())
    cin+='\n'
    write('\033[33mSend:\033[0m '+cin)
    print_error(error_str)
  print_info('Exiting...\n')

  uart_conn.close()
