#!/usr/bin/env python3

#*-------------------------------------------*#
#  Title       : UART Tool v1.1               #                        
#  File        : uart.py                      #
#  Author      : Yigit Suoglu                 #
#  License     : EUPL-1.2                     #
#  Last Edit   : 25/05/2021                   #
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


def print_raw(promt):
  sys.stdout.write(promt)


def serial_write(sendData):
  try:
    uart_conn.write(sendData)
  except:
    return None


def print_input_symbol():
  sys.stdout.write('\033[32m> \033[0m')


def check_listener(signum, frame):
  raise TimeoutError


def process_timeout(signum, frame):
  print_warn('Timeout!\n')
  raise TimeoutError


def print_help():
  print_raw('  Usage:\n')
  print_raw('   Enter a command or data to send. Commands start with \'\\\'. To send a \'\\\' as a first byte use \'\\\\\'\n')
  print_raw('\n')
  print_raw('  Available Commands:\n')
  print_raw('   ~ \\bin     : print received bytes as binary number\n')
  print_raw('   ~ \\binhex  : print received bytes as binary number and hexadecimal equivalent\n')
  print_raw('   ~ \\c       : print received bytes as character\n')
  print_raw('   ~ \\char    : print received bytes as character\n')
  print_raw('   ~ \\dec     : print received bytes as decimal number\n')
  print_raw('   ~ \\dechex  : print received bytes as decimal number and hexadecimal equivalent\n')
  print_raw('   ~ \\dump    : dump received bytes in dumpfile, if argument given use it as file name\n')
  print_raw('   ~ \\exit    : exits the script\n')
  print_raw('   ~ \\getpath : prints working directory\n')
  print_raw('   ~ \\h       : print received bytes as hexadecimal number\n')
  print_raw('   ~ \\help    : prints this message\n')
  print_raw('   ~ \\hex     : print received bytes as hexadecimal number\n')
  print_raw('   ~ \\license : prints license information\n')
  print_raw('   ~ \\mute    : do not print received received to terminal\n')
  print_raw('   ~ \\nodump  : stop dumping received bytes in dumpfile\n')
  print_raw('   ~ \\pref    : add bytes to send before transmitted data, arguments should be given as hexadecimal\n')
  print_raw('   ~ \\q       : exits the script\n')
  print_raw('   ~ \\quit    : exits the script\n')
  print_raw('   ~ \\safe    : in non char mode, stop sending if non number given\n')
  print_raw('   ~ \\s       : send files\n')
  print_raw('   ~ \\send    : send files\n')
  print_raw('   ~ \\setpath : set directory for file operations, full or relative path, empty for cwd\n')
  print_raw('   ~ \\suff    : add bytes to send after transmitted data, arguments should be given as hexadecimal\n')
  print_raw('   ~ \\unmute  : print received received to terminal\n')
  print_raw('   ~ \\unsafe  : in non char mode, do not stop sending if non number given\n')


#listener daemon
def uart_listener(): #? if possible, TODO: keep the prompt already written in terminal when new received
  print_raw(get_now())
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
          print_raw('\033[F\r')
          byte_counter+=1

        last_line+=buff
        print_raw(last_line+'\n')
        print_input_symbol()
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
      print_error('\033[F\nConnection to ' + serial_path + ' lost!\n')
      print_info('Exiting daemon...\n')
      listener_alive = False
      break
    except Exception as e:
      print_error(str(e) + '\n')
      print_info('Exiting Daemon...\n')
      listener_alive = False
      break


#Main function
if __name__ == '__main__':
  print_info('Welcome to the UART tool v1.1!\n')
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
    elif current.casefold() == 'even' or current.casefold() == 'e':
      par = serial.PARITY_EVEN
      par_str = 'even'
    elif current.casefold() == 'odd' or current.casefold() == 'o':
      par = serial.PARITY_ODD
      par_str = 'odd'
    elif current.casefold() == 'mark' or current.casefold() == 'm':
      par = serial.PARITY_MARK
      par_str = 'mark'
    elif current.casefold() == 'space' or current.casefold() == 's':
      par = serial.PARITY_SPACE
      par_str = 'space'
    elif current.casefold() == 'no' or current.casefold() == 'n':
      continue
    elif current.endswith('help') :
      print('Usage: uart.py [options]')
      print_info('Options can be the uart configurations, order doesn\'t matter')
    elif current.startswith('tty'):
      serial_path = '/dev/' + current
      try:
        uart_conn = Serial(serial_path,baud,timeout=1)
        uart_conn.close()
      except:
        print_error('\nCannot open ' + serial_path)
        print_info('\nExiting...\n')
        sys.exit(1)
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
    sys.exit(1)
  else:
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
  
  try:
    uart_conn = Serial(serial_path,baud,data_size,par,stop_size)
  except Exception as e:
    print_error(str(e)+'\n')
    sys.exit(2)
  
  #Set up listener daemon
  try:
    listener_daemon = threading.Thread(target=uart_listener,daemon=True)
    listener_daemon.start()
  except Exception as e:
    print_error(str(e)+'\n')
    sys.exit(4)
  
  listener_alive = True
  cin = ''
  print_input_symbol()

  while True: #main loop for send
    try:
      # if not listener_alive:
       # raise ChildProcessError
      signal.signal(signal.SIGALRM, check_listener)
      signal.alarm(1)
      cin = input() #Wait for input
      signal.signal(signal.SIGALRM, process_timeout)
      signal.alarm(1800) #Half an hour
      cin = cin.strip()
      if cin == '':
        continue
      
      print_raw('\033[F'+get_now()+' ') #print timestamp
      #command handling
      if cin == '\quit' or cin =='\exit' or cin =='\q':
        break
      elif cin == '\help':
        print_info('Help\n')
        print_help()
        print_input_symbol()
        continue
      elif cin == '\license':
        print_info('License\n')
        print_raw('EUPL-1.2\n')
        print_raw('Full text: https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12\n')
        print_input_symbol()
        continue
      elif cin == '\char' or cin == '\c':
        char = True
        dec_ow = False
        bin_ow = False
        hex_add = False
        print_info('Received bytes will be printed as character\n')
        print_input_symbol()
        continue
      elif cin == '\hex' or cin == '\h':
        print_info('Received bytes will be printed as hexadecimal number\n')
        char = False
        dec_ow = False
        bin_ow = False
        hex_add = False
        print_input_symbol()
        continue
      elif cin == '\dec':
        print_info('Received bytes will be printed as decimal number\n')
        char = False
        dec_ow = True
        bin_ow = False
        hex_add = False
        print_input_symbol()
        continue
      elif cin == '\\bin':
        print_info('Received bytes will be printed as binary number\n')
        char = False
        dec_ow = False
        bin_ow = True
        hex_add = False
        print_input_symbol()
        continue
      elif cin == '\dechex':
        print_info('Received bytes will be printed as decimal number and hexadecimal equivalent\n')
        char = False
        dec_ow = True
        bin_ow = False
        hex_add = True
        print_input_symbol()
        continue
      elif cin == '\\binhex':
        print_info('Received bytes will be printed as binary number and hexadecimal equivalent\n')
        char = False
        dec_ow = False
        bin_ow = True
        hex_add = True
        print_input_symbol()
        continue
      elif cin == '\\safe':
        print_info('Safe transmit mode enabled\n')
        safe_tx = True
        print_input_symbol()
        continue
      elif cin == '\\unsafe':
        print_info('Safe transmit mode disabled\n')
        safe_tx = False
        print_input_symbol()
        continue
      elif cin == '\\unmute':
        print_info('Listener unmuted\n')
        listener_mute = False
        print_input_symbol()
        continue
      elif cin == '\\mute':
        print_info('Listener muted\n')
        listener_mute = True
        if dumpfile == None:
          print_warn('Dumping is disabled, received data will be discarded!\n')
        print_input_symbol()
        continue
      elif cin == '\\nodump':
        print_info('Dumping disabled\n')
        dumpfile = None
        if listener_mute:
          print_warn('Listener is muted, received data will be discarded!\n')
        print_input_symbol()
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
                extra_arg+=(', '+arg)
          if extra_arg != '':
            print_warn('Ignoring following extra arguments:\033[0m '+extra_arg+'\n')
        if not os.path.isfile(cwdir + '/' + tmpfile):
          try:
            tmpdump = open(cwdir + '/' + tmpfile,'x')
            tmpdump.close()
          except:
            print_error('Cannot find or create file \033[0m'+tmpfile+'\033[31m in current path!\n')
            print_input_symbol()
            continue
        try:
          tmpdump = open(cwdir + '/' + tmpfile,'r')
          tmpdump.close()
          dumpfile = tmpfile
          print_info('Received bytes will be dumped to \033[0m'+dumpfile+'\n')
        except:
          print_error('Cannot open file \033[0m'+tmpfile+'\033[31m!\n')
        finally:
          print_input_symbol()
          continue
      elif cin.startswith('\\send') or cin.startswith('\\s ') or cin == '\\s':
        sendByte = 0
        sendFile = 0
        if cin.strip() == '\\send' or cin.strip() == '\\s':
          files = input('Please provide the name of the file(s): ')
        else:
          if cin.strip() == '\\send':
            cin = cin[5:]
          else:
            cin = cin[2:]
          files = cin.strip()
        files = files.split(' ')
        for filename in files:
          if filename != '':
            file = None
            try:
              full_path = cwdir + '/' + filename
              file = open(full_path,'rb')
              sendFile+=1
            except:
              print_error('Cannot open file \033[0m'+filename+'\033[31m!\n')
              if safe_tx:
                print_info('Breaking\n')
                break
              else:
                print_info('Continuing\n')
                continue
            byte = file.read(1)
            while byte != b'':
              serial_write(byte)
              sendByte+=1
              byte = file.read(1)
        if sendFile == 0:
          print_warn('Didn\'t write anything\n')
        else:
          print_info('Wrote '+str(sendByte)+' bytes from '+str(sendFile)+' file(s)\n')
        print_input_symbol()
        continue
      elif cin == '\\getpath':
        print_info('Current path: \033[0m'+cwdir+'\n')
        if listener_mute:
          print_warn('Listener is muted, received data will be discarded!\n')
        print_input_symbol()
        continue
      elif cin.startswith('\\setpath'):
        cin = cin.strip()
        if cin == '\\setpath':
          cwdir = os.getcwd()
        else:
          cin = cin[8:]
          cin = cin.split(' ')
          tmpdir = None
          extra_arg =''
          for arg in cin:
            if arg != '':
              if tmpdir == None:
                tmpdir = arg
              elif extra_arg == '':
                extra_arg = arg
              else:
                extra_arg+=(', '+arg)
          if extra_arg != '':
            print_warn('Ignoring following extra arguments:\033[0m '+extra_arg+'\n')
          if tmpdir.startswith('~/'):
            tmpdir = str(os.path.expanduser("~")) + tmpdir[1:]
          elif not tmpdir.startswith('/'):
            tmpdir = os.getcwd() + '/' + tmpdir
          if os.path.isdir(tmpdir):
            cwdir = tmpdir
          else:
            print_raw(tmpdir)
            print_error(' is not a valid directory path!\n')
            print_input_symbol()
            continue
        print_info('Working directory set to \033[0m'+cwdir+'\n')
        print_input_symbol()
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
            print_raw('\n')
        except:
          print_error('Arguments must be hexadecimal!\n')
        finally:
          print_input_symbol()
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
            print_raw('\n')
        except:
          print_error('Arguments must be hexadecimal!\n')
        finally:
          print_input_symbol()
          continue
      elif cin.startswith('\\'):
        if cin.startswith('\\\\'):
          cin = cin[1:]
        else:
          print_warn('Command \033[0m' + cin + '\033[91m does not exist!\n')
          print_info('Use \033[0m\\help\033[2m to see the list of available commands\n')
          print_input_symbol()
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
      print_raw('\033[33mSend:\033[0m '+cin)
      print_error(error_str)
      print_input_symbol()
    
    except serial.SerialException:
      print_error('Connection to ' + serial_path + ' lost!\nExiting...\n')
      sys.exit(2)
    except KeyboardInterrupt:
      print_warn('\nUser Interrupt\n')
      break
    except TimeoutError:
      if listener_alive:
        continue
      else:
        print_warn('Daemon is killed!\n')
        print_info('Exiting...\n')
        sys.exit(2)
    except Exception as e: 
      print_error(str(e)+'\n')
      print_info('Exiting...\n')
      break

  print_info('Disconnecting...\n')
  uart_conn.close()
  