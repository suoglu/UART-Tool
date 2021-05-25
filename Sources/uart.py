#!/usr/bin/env python3

#*-------------------------------------------*#
#  Title       : UART Script v1.0             #                        
#  File        : uart.py                      #
#  Author      : Yigit Suoglu                 #
#  License     : EUPL-1.2                     #
#  Last Edit   : 24/05/2021                   #
#*-------------------------------------------*#
#  Description : Python3 script for serial    #
#                communication via UART       #
#*-------------------------------------------*#

import sys
import serial
import threading
import time
import datetime
import signal
import os


from serial import Serial

global listener_alive

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


def serial_write(sendData):
  try:
    uart_conn.write(sendData)
  except:
    return None


def check_listener(signum, frame):
  raise TimeoutError


def print_commands():
  write(' ~ \\bin    : print received bytes as binary number\n')
  write(' ~ \\binhex : print received bytes as binary number and hexadecimal equivalent\n')
  write(' ~ \\c      : print received bytes as character\n')
  write(' ~ \\char   : print received bytes as character\n')
  write(' ~ \\dec    : print received bytes as decimal number\n')
  write(' ~ \\dechex : print received bytes as decimal number and hexadecimal equivalent\n')
  write(' ~ \\dump   : dump received bytes in dumpfile, if argument given use it as file name\n')
  write(' ~ \\exit   : exits the script\n')
  write(' ~ \\h      : print received bytes as hexadecimal number\n')
  write(' ~ \\hex    : print received bytes as hexadecimal number\n')
  write(' ~ \\mute   : do not print received received to terminal\n')
  write(' ~ \\nodump : stop dumping received bytes in dumpfile\n')
  write(' ~ \\pref   : add bytes to send before transmitted data, arguments should be given as hexadecimal\n')
  write(' ~ \\q      : exits the script\n')
  write(' ~ \\quit   : exits the script\n')
  write(' ~ \\safe   : in non char mode, stop sending if non number given\n')
  write(' ~ \\send   : send the files in argument\n') #TODO
  write(' ~ \\setdir : set directory for file operations, full or relative path, empty for cwd\n') #TODO
  write(' ~ \\suff   : add bytes to send after transmitted data, arguments should be given as hexadecimal\n')
  write(' ~ \\unmute : print received received to terminal\n')
  write(' ~ \\unsafe : in non char mode, do not stop sending if non number given\n')
  write('\nTo send a \'\\\' as a first byte use \'\\\\\'\n')


#listener daemon
def uart_listener(): #? if possible, TODO: keep the prompt already written in terminal when new received
  write(get_now())
  print_info(' Listening...\n')
  timer_stamp = 0
  last_line = ''
  byte_counter = 0
  global listener_alive

  while True: #main loop for listener
    try:
      byte = uart_conn.read()
      if not listener_mute:
        if char:
          buff = byte.decode()
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
      if dumpfile != None:
        try:
          full_path = cwdir + '/' + dumpfile
          dump = open(full_path,'ab')
          dump.write(byte)
          dump.close()
        except:
          print_error('Cannot dump to file \033[0m' + dumpfile + '\033[31m!\n')
    except serial.SerialException:
      print_error('Connection to ' + serial_path + ' lost!\nExiting daemon...\n')
      listener_alive = False
      break
    except:
      print_error('Something unexpected happened!\nExiting daemon...\n')
      listener_alive = False
      break


#Main function
if __name__ == '__main__':
  print_info('Welcome to the UART Script!\n')
  baud = 115200
  serial_path = '/dev/ttyUSB'
  data_size = serial.EIGHTBITS
  stop_size = serial.STOPBITS_ONE
  par = serial.PARITY_NONE
  par_str = 'no'
  search_range = 10
  #check arguments for custom settings
  while len(sys.argv) > 1:
    current = sys.argv.pop(-1)  
    if current.isnumeric() or current == '1.5' or current == '1,5':
      if(current == '1,5'):
        current = 1.5
      else:
        current = float(current)
      if current < 20 and current > 10:
        search_range = int(current)
      elif current == 8:
        data_size = serial.EIGHTBITS
      elif current == 7:
        data_size = serial.SEVENBITS
      elif current == 6:
        data_size = serial.SIXBITS
      elif current == 5:
        data_size = serial.FIVEBITS
      elif current == 2:
        stop_size = serial.STOPBITS_TWO
      elif current == 1.5:
        stop_size = serial.STOPBITS_ONE_POINT_FIVE
      elif current == 1:
        stop_size = serial.STOPBITS_ONE
      elif current > 1999:
        baud = int(current)
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
    print_warn('\nCannot find a ttyUSB device, searching for a ttyACM device...')
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
    print_warn('\nCannot find a ttyACM device, searching for a ttyCOM device...')
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
  print_info('\nConfigurations: '+str(baud)+' '+str(data_size)+' bits with '+par_str+' parity and '+str(stop_size)+' stop bit(s)\n\n')

  #Software Configurations
  char = True
  dec_ow = False
  bin_ow = False
  hex_add = False
  safe_tx = False
  prefix=None
  suffix=None
  listener_mute = False
  cwdir = os.getcwd()
  dumpfile = None
  
  uart_conn = Serial(serial_path,baud,data_size,par,stop_size)
  
  #Set up listener daemon
  listener_daemon = threading.Thread(target=uart_listener,daemon=True)
  listener_daemon.start()
  listener_alive = True
  cin = ''

  while True: #main loop for send
    try:
      # if not listener_alive:
       # raise ChildProcessError
      signal.signal(signal.SIGALRM, check_listener)
      signal.alarm(1)
      cin = input() #Wait for input 
      write('\033[F'+get_now()+' ') #print timestamp
      #command handling
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
      elif cin == '\\unmute':
        print_info('Listner unmuted\n')
        listener_mute = False
        continue
      elif cin == '\\mute':
        print_info('Listner muted\n')
        listener_mute = True
        if dumpfile == None:
          print_warn('Dumping is disabled, received data will be discarded!\n')
        continue
      elif cin == '\\nodump':
        print_info('Dumping disabled\n')
        dumpfile = None
        if listener_mute:
          print_warn('Listener is muted, received data will be discarded!\n')
        continue
      elif cin.startswith('\\dump'):
        cin = cin[5:]
        tmpfile = None
        cin = cin.split(' ')
        if len(cin) == cin.count(''):
          tmpfile = 'uartrx.bin'
        else:
          extra_arg =''
          for arg in cin:
            if arg != '':
              if tmpfile == None:
                tmpfile = arg
              elif extra_arg == '':
                extra_arg = arg
              else:
                extra_arg+=(', '+extra_arg)
          if extra_arg != '':
            print_warn('Ignoring following extra arguments:\033[0m '+extra_arg+'\n')
        if not os.path.isfile(cwdir + '/' + tmpfile):
          try:
            tmpdump = open(cwdir + '/' + tmpfile,'x')
            tmpdump.close()
          except:
            print_error('Cannot find or create file \033[0m'+tmpfile+'\033[31m in current path!\n')
            continue
        try:
          tmpdump = open(cwdir + '/' + tmpfile,'r')
          tmpdump.close()
          dumpfile = tmpfile
          print_info('Received bytes will be dumped to \033[0m'+dumpfile+'\n')
        except:
          print_error('Cannot open file \033[0m'+tmpfile+'\033[31m!\n')
        finally:
          continue
      elif cin.startswith('\\send'): #TODO
        print_error('Not Implemented!\n')
        continue
      elif cin.startswith('\\setdir'): #TODO
        print_error('Not Implemented!\n')
        continue
      elif cin.startswith('\\pref'):
        cin = cin[5:]
        try:
          cin = cin.split(' ')
          hold_bytes = []
          if len(cin) == cin.count(''):
            prefix=None
            print_info('Prefix removed\n')
          else:
            for item in cin:
              if item != '':
                byte_val = int(item,16)
                hold_bytes.append(byte_val.to_bytes(1,'little'))
            print_info('Prefix updated to ')
            for item in cin:
              if item != '':
                print_info(item+' ')
            prefix=hold_bytes
            write('\n')
        except:
          print_error('Arguments must be hexadecimal!\n')
        finally:
          continue
      elif cin.startswith('\\suff'):
        cin = cin[5:]
        try:
          cin = cin.split(' ')
          hold_bytes = []
          if len(cin) == cin.count(''):
            suffix=None
            print_info('Suffix removed\n')
          else:
            for item in cin:
              if item != '':
                byte_val = int(item,16)
                hold_bytes.append(byte_val.to_bytes(1,'little'))
            print_info('Suffix updated to ')
            for item in cin:
              if item != '':
                print_info(item+' ')
            suffix=hold_bytes
            write('\n')
        except:
          print_error('Arguments must be hexadecimal!\n')
        finally:
          continue
      elif cin.startswith('\\'):
        if cin.startswith('\\\\'):
          cin = cin[1:]
        else:
          print_warn('Command \033[0m' + cin + '\033[91m does not exist!\n')
          continue
      #Data handling
      error_str = ''
      send_str = ''
      toSend = 0

      if prefix != None:
        for byte in prefix:
          serial_write(byte)

      if not char:
        for item in cin.split(' '):
          try:
            if item.startswith('0x'):
              toSend = int(item, 16)
            elif item.startswith('0d'):
              toSend = int(item, 10)
            elif item.startswith('0o'):
              toSend = int(item, 8) 
            elif item.startswith('0b') or bin_ow:
              toSend = int(cin, 2)
            elif dec_ow:
              toSend = int(item, 10) 
            else:
              toSend = int(item, 16)
          except:
            error_str+=(item + ' is not a valid number!\n')
            if safe_tx:
              break
            else:
              continue
          send_str+=(item + ' ')
          serial_write(toSend.to_bytes(1,'little'))
        cin = send_str
      else:
        serial_write(cin.encode())

      if suffix != None:
        for byte in suffix:
          serial_write(byte)

      cin+='\n'
      write('\033[33mSend:\033[0m '+cin)
      print_error(error_str)
    
    except serial.SerialException:
      print_error('Connection to ' + serial_path + ' lost!\nExiting...\n')
      quit(2)
    except KeyboardInterrupt:
      print_warn('\nUser Interrupt\n')
      break
    except TimeoutError:
      if listener_alive:
        continue
      else:
        print_warn('Daemon is killed!\n')
        print_info('Exiting...\n')
        quit(2)
    except Exception as e: 
      print_error(str(e)+'\nExiting...\n')
      break

  print_info('Disconnecting...\n')
  uart_conn.close()
  
