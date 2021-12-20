#!/usr/bin/env python3

#*-------------------------------------------*#
#  Title       : UART Tool v1.4.2             #
#  File        : uart.py                      #
#  Author      : Yigit Suoglu                 #
#  License     : EUPL-1.2                     #
#  Last Edit   : 02/09/2021                   #
#*-------------------------------------------*#
#  Description : Python3 script for serial    #
#                communication via UART       #
#*-------------------------------------------*#

import sys
import serial
import threading
import time
import signal
import os
import random

from serial import Serial
from datetime import datetime

global listener_alive
global block_listener
global log_listener_check
global program_log
global log_directory
global log
global log_lock


#Prompt coloring
def get_now():
  return '\033[35m' + str(datetime.now()).replace('.', ',') + ':\033[0m'


def get_time_stamp():
  return '\033[F' + get_now() + ' '


def print_time_stamp():
  print_raw(get_time_stamp())


def print_error(msg, write_log=True):
  global log_listener_check
  sys.stdout.write('\033[31m' + msg + '\033[0m')
  if write_log:
    log_thread = threading.Thread(target=log_write, args=[msg.strip('\n'), 'error'])
    log_thread.start()


def print_fatal(msg, write_log=True):
  global log_listener_check
  sys.stdout.write('\033[1;31m' + msg + '\033[0m')
  if write_log:
    log_thread = threading.Thread(target=log_write, args=[msg.strip('\n'), 'fatal error'])
    log_thread.start()


def print_success(msg, write_log=True):
  global log_listener_check
  sys.stdout.write('\033[32m' + msg + '\033[0m')
  if write_log:
    log_thread = threading.Thread(target=log_write, args=[msg.strip('\n'), 'success'])
    log_thread.start()


def print_info(msg, write_log=True):
  global log_listener_check
  sys.stdout.write('\033[2m' + msg + '\033[0m')
  if write_log:
    log_thread = threading.Thread(target=log_write, args=[msg.strip('\n'), 'info'])
    log_thread.start()


def print_warn(msg, write_log=True):
  global log_listener_check
  sys.stdout.write('\033[91m' + msg + '\033[0m')
  if write_log:
    log_thread = threading.Thread(target=log_write, args=[msg.strip('\n'), 'warning'])
    log_thread.start()


#Helper functions
def print_raw(msg):
  sys.stdout.write(msg)


def get_log_time(entry_time):
  return entry_time.strftime('%Y-%m-%d %H:%M:%S,%f ')


def get_cpu_time():
  return time.clock_gettime_ns(time.CLOCK_THREAD_CPUTIME_ID)


def usleep(us):
  time.sleep(us/1000000.0)


def log_write(entry, entry_type=''):
  global program_log
  global log_lock
  global log
  entry_time = datetime.now()
  if program_log is not None and not os.path.isfile(program_log):
    program_log = None
    print_raw(get_now() + ' ')
    print_warn('Log is missing!\n')
  if program_log is None:
    return
  attempts = 0
  while log_lock:
    if attempts == 100:
      print_error('Log lock timeout!\n')
      print_input_symbol()
      return
    attempts += 1
    usleep(10)
  log_lock = True
  try:
    if entry_type != '':
      entry_type += ': '
    log = open(str(program_log), 'a')
    log.write(get_log_time(entry_time))
    for num in range(100):
      entry = entry.replace(('\033[' + str(num) + 'm'), '')
    entry_list = str(entry).split('\n')
    log.write(entry_type + entry_list[-1].lower() + '\n')
    log.close()
  except Exception as log_err:
    program_log = None
    print_warn('Cannot keep log\n')
    print_error(str(log_err) + '\n')
    print_input_symbol()
  finally:
    log_lock = False


def serial_write(send_data):
  try:
    uart_conn.write(send_data)
  except Exception as serial_write_error:
    print_error('Cannot send!\n')
    print_error(str(serial_write_error) + '\n')


def print_input_symbol():
  sys.stdout.write('\033[32m> \033[0m')


class ListenerControl(Exception):
  pass


def check_listener(signum, frame):
  global log_listener_check
  if log_listener_check:  #so that log won't be spammed with it
    log_listener_check = False
    msg = 'debug: listener daemon check ' + str(signum) + ' ' + str(frame)
    log_thread = threading.Thread(target=log_write, args=[msg])
    log_thread.start()
  raise ListenerControl


def process_timeout(signum, frame):
  global log_listener_check
  print_fatal('Timeout!\n', False)
  msg = 'fatal error: process timeout ' + str(signum) + ' ' + str(frame)
  log_thread = threading.Thread(target=log_write, args=[msg, 'error'])
  log_thread.start()
  raise TimeoutError


def print_help():
  print_raw('  \033[4mUsage\033[0m:\n')
  print_raw(
    '   Enter a command or data to send. Commands start with \'\\\'. To send a \'\\\' as a first byte use \'\\\\\'\n')
  print_raw('\n')
  print_raw('  \033[4mAvailable Commands\033[0m:\n')
  print_raw('   ~ \\bin     : print received bytes as binary number\n')
  print_raw('   ~ \\binhex  : print received bytes as binary number and hexadecimal equivalent\n')
  print_raw('   ~ \033[7m\\char\033[0m    : print received bytes as character\n')
  print_raw('   ~ \\dec     : print received bytes as decimal number\n')
  print_raw('   ~ \\dechex  : print received bytes as decimal number and hexadecimal equivalent\n')
  print_raw('   ~ \\dump    : dump received bytes in dumpfile, if argument given use it as file name\n')
  print_raw('   ~ \\exit    : exits the script\n')
  print_raw('   ~ \\getpath : prints working directory\n')
  print_raw('   ~ \\help    : prints this message\n')
  print_raw('   ~ \033[7m\\hex\033[0m     : print received bytes as hexadecimal number\n')
  print_raw('   ~ \\keeplog : do not delete programme log\n')
  print_raw('   ~ \\license : prints license information\n')
  print_raw('   ~ \\mute    : do not print received received to terminal\n')
  print_raw('   ~ \\nodump  : stop dumping received bytes in dumpfile\n')
  print_raw('   ~ \\pref    : add bytes to send before transmitted data, arguments should be given as hexadecimal\n')
  print_raw('   ~ \033[7m\\rand\033[0m    : send random bytes, argument determines how many\n')
  print_raw('   ~ \033[7m\\quit\033[0m    : exits the script\n')
  print_raw('   ~ \\safe    : in non char mode, stop sending if non number given\n')
  print_raw('   ~ \033[7m\\send\033[0m    : send files\n')
  print_raw('   ~ \\setpath : set directory for file operations, full or relative path, empty for cwd\n')
  print_raw('   ~ \\suff    : add bytes to send after transmitted data, arguments should be given as hexadecimal\n')
  print_raw('   ~ \\unmute  : print received received to terminal\n')
  print_raw('   ~ \\unsafe  : in non char mode, do not stop sending if non number given\n')
  print_raw('   ~ \\@       : print the path to the connected device\n')
  print_raw('\n  Marked commands can be called with their first letter\n')


#listener daemon
def uart_listener():  #? if possible, keep the prompt already written in terminal when new received
  print_raw(get_now())
  print_info(' Listening...\n')
  timer_stamp = 0
  last_line = ''
  last_timestamp = ''
  byte_counter = 0
  received_invalid = False
  global listener_alive
  global block_listener

  while True:  #main loop for listener
    try:
      read_byte = uart_conn.read()
      if not listener_mute:
        line_end = False
        buff = ''
        if char:
          try:
            buff = read_byte.decode()
            line_end = (buff == '\n')
            if line_end:
              buff = ''
          except UnicodeError:
            buff = '\033[2m[\033[0m\033[95m' + hex(int.from_bytes(read_byte, byteorder='little'))
            buff += '\033[0m\033[2m]\033[0m'
            received_invalid = True
          except Exception as decode_err:
            print_error(str(decode_err)+'\n')
            print_warn('Ignoring received byte\n')
        else:
          val = int.from_bytes(read_byte, byteorder='little')
          if dec_ow:
            buff = str(val)
          elif bin_ow:
            buff = bin(val)
          else:
            buff = hex(val)
          if hex_add:
            buff += (' (' + hex(val) + ')')
          buff += ' '
        byte_brake = ((not char or received_invalid) and (byte_counter == 15)) or (byte_counter == 63)
        if (timer_stamp < get_cpu_time()) or line_end or byte_brake or block_listener:
          received_invalid = False
          block_listener = False
          byte_counter = 0
          last_line = ''
          last_timestamp = '\033[F' + '\n' + get_now() + ' \033[36mGot:\033[0m '
        else:
          print_raw('\033[F\r')
          byte_counter += 1
        last_line += buff
        line = last_timestamp
        if char:
          line += ('\033[2m\'\033[0m'+last_line+'\033[2m\'\033[0m')
        else:
          line += last_line
        print_raw(line + '\n')
        print_input_symbol()
        sys.stdout.flush()
        timer_stamp = get_cpu_time() + 100000
      if dumpfile is not None:
        try:
          dump_path = working_directory + '/' + dumpfile
          dump = open(dump_path, 'ab')
          dump.write(read_byte)
          dump.close()
        except Exception as dump_error:
          print_error('Cannot dump to file \033[0m' + dumpfile + '\033[31m!\n')
          print_error(str(dump_error) + '\n')
    except serial.SerialException:
      print_fatal('\033[F\nConnection to ' + serial_path + ' lost!\n')
      print_warn('Killing daemon...\n')
      listener_alive = False
      break
    except Exception as listener_error:
      print_fatal(str(listener_error) + '\n')
      print_warn('Killing daemon...\n')
      listener_alive = False
      break


#Main function
if __name__ == '__main__':
  start_time = datetime.now()
  log_directory = '.uart_tool'
  program_log = None
  log_lock = False
  print_info('Welcome to the UART tool v1.4.2!\n')
  baud = 115200
  serial_path = '/dev/ttyUSB'
  data_size = serial.EIGHTBITS
  stop_size = serial.STOPBITS_ONE
  par = serial.PARITY_NONE
  par_str = 'no'
  search_range = 10
  #check arguments for custom settings
  try:
    while len(sys.argv) > 1:
      current = sys.argv.pop(-1)
      current = current.strip()
      if current.isnumeric() or current == '1.5' or current == '1,5':
        if current == '1,5':
          current = 1.5
        else:
          current = float(current)
        if 20 > current > 10:
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
      elif current.casefold().strip('--') == 'help' or current.casefold() == '-h':
        print('\033[FUsage: uart.py [arg]                  ')
        print_info(' Arguments can be the uart configurations or one of the following commands:\n\n')
        print_info('  --interactive (-i): interactive start up, tool asks for uart configurations\n')
        print_info('  --help        (-h): Print this message\n')
        print_info('  --search      (-s): Search for connected devices\n')
        print_info('\n Uart configurations can be given in any order\n')
        sys.exit(0)
      elif current.casefold() == '-i' or current.casefold().strip('--') == 'interactive':
        print_info('\nInteractive configuration mode\nLeave empty for default values\n\n')
        while True:  #ask baud rate
          cin = str(input('Baud rate: '))
          cin = cin.strip()
          if cin == '':
            print_raw('\033[FBaud rate: ')
            print_info(str(baud) + '\n')
            break
          if not cin.isnumeric():
            print_warn('Baud rate must be an integer!\n')
            continue
          cin = int(cin)
          if cin > 1199:
            baud = cin
            break
          else:
            print_warn('Minimum baud rate should be 1.2k\n')
        while True:  #ask data size
          cin = str(input('Data size: '))
          cin = cin.strip()
          if cin == '':
            print_raw('\033[FData size: ')
            print_info(str(data_size) + '\n')
            break
          if not cin.isnumeric():
            print_warn('Data size must be an integer!\n')
            continue
          cin = int(cin)
          if 4 < cin < 9:
            data_size = cin
            break
          else:
            print_warn('Data size should be either 5, 6, 7 or 8\n')
        while True:  #ask parity
          cin = str(input('Parity: '))
          cin = cin.strip()
          if cin == '':
            print_raw('\033[FParity: ')
            print_info(par + '\n')
            break
          if cin.casefold() == 'odd' or cin.casefold() == 'o':
            par = serial.PARITY_ODD
            par_str = 'odd'
            break
          elif cin.casefold() == 'even' or cin.casefold() == 'e':
            par = serial.PARITY_EVEN
            par_str = 'even'
            break
          elif cin.casefold() == 'mark' or cin.casefold() == 'm':
            par = serial.PARITY_MARK
            par_str = 'mark'
            break
          elif cin.casefold() == 'space' or cin.casefold() == 's':
            par = serial.PARITY_SPACE
            par_str = 'space'
            break
          elif cin.casefold() == 'none' or cin.casefold() == 'n' or cin.casefold() == 'no':
            break
          else:
            print_warn('Parity should be odd, even, mark, space or none\n')
        while True:  #ask stop bit
          cin = str(input('Stop bit size: '))
          cin = cin.strip()
          if cin == '':
            print_raw('\033[FStop bit size: ')
            print_info(str(stop_size) + '\n')
            break
          try:
            cin = float(cin)
          except ValueError:
            print_warn('Stop bit size must be a float!\n')
            continue
          except Exception as config_error:
            print_error(str(config_error)+'\n')
            continue
          if cin == 1 or cin == 2:
            stop_size = cin
            break
          elif cin == 1.5:
            stop_size = serial.STOPBITS_ONE_POINT_FIVE
            break
          else:
            print_warn('Stop bit size should be either 1, 1.5 or 2\n')
        if serial_path == '/dev/ttyUSB':
          while True:  #ask serial path
            cin = str(input('Device: '))
            cin = cin.strip()
            if cin == '':
              print_raw('\033[FDevice: ')
              print_info('Search\n')
              break
            if not cin.startswith('tty'):
              print_warn('Device name should start with tty\n')
              continue
            try:
              try_path = '/dev/' + cin
              uart = Serial(try_path, timeout=1)
              uart.close()
              serial_path = try_path
              break
            except serial.SerialException:
              print_error('Cannot connect to device \033[0m' + cin + '\033[31m!\n')
            except Exception as conn_error:
              print_error(str(conn_error) + '\n')
      elif current.casefold().strip('--') == 'search' or current.casefold() == '-s':
        print_info('\nSearching for connected devices...\n')
        found_dev = 0
        non_res_dev = 0
        poll_path = '/dev/ttyUSB'
        for i in range(search_range + 1):
          current = poll_path + str(i)
          if os.path.exists(current):
            try:
              uart_conn = Serial(current, timeout=1)
              uart_conn.close()
              print_success('\nFound ttyUSB' + str(i))
              found_dev += 1
            except serial.SerialException:
              print_warn('\nFound ttyUSB' + str(i) + ', but cannot connect!')
              non_res_dev += 1
            except Exception as search_err:
              print_warn(str(search_err)+'\n')
              print_info('Ignoring...\n')
        poll_path = '/dev/ttyACM'
        for i in range(search_range + 1):
          current = poll_path + str(i)
          if os.path.exists(current):
            try:
              uart_conn = Serial(current, timeout=1)
              uart_conn.close()
              print_success('\nFound ttyACM' + str(i))
              found_dev += 1
            except serial.SerialException:
              print_warn('\nFound ttyACM' + str(i) + ', but cannot connect!')
              non_res_dev += 1
            except Exception as search_err:
              print_warn(str(search_err)+'\n')
              print_info('Ignoring...\n')
        poll_path = '/dev/ttyCOM'
        for i in range(search_range + 1):
          current = poll_path + str(i)
          if os.path.exists(current):
            try:
              uart_conn = Serial(current, timeout=1)
              uart_conn.close()
              print_success('\nFound ttyCOM' + str(i) + '\n')
              found_dev += 1
            except serial.SerialException:
              print_warn('\nFound ttyCOM' + str(i) + ', but cannot connect!')
              non_res_dev += 1
            except Exception as search_err:
              print_warn(str(search_err)+'\n')
              print_info('Ignoring...\n')
        print_raw('\n\n')
        if found_dev != 0:
          print_success('Found ')
          print_raw(str(found_dev))
          if found_dev == 1:
            print_success(' device!\n')
          else:
            print_success(' devices!\n')
        if non_res_dev != 0:
          print_warn('Found ')
          print_raw(str(non_res_dev))
          if non_res_dev == 1:
            print_success(' device, but cannot connect to it!\n!\n')
          else:
            print_success(' devices, but cannot connect to them!\n!\n')
        if non_res_dev == 0 and found_dev == 0:
          print_error('Cannot find any devices!\n')
        sys.exit(0)
      elif current.startswith('tty'):
        serial_path = '/dev/' + current
        try:
          uart_conn = Serial(serial_path, baud, timeout=1)
          uart_conn.close()
        except serial.SerialException:
          print_fatal('\nCannot open ' + serial_path)
          print_info('\nExiting...\n')
          sys.exit(1)
        except Exception as dev_err:
          print_fatal(str(dev_err) + '\n')
          print_info('\nExiting...\n')
          sys.exit(1)
      else:
        print_warn('\nInvalid argument:' + current)
        print_info('\nSkipping...\n')

    if serial_path == '/dev/ttyUSB':  #if no device is given, poll for it
      for i in range(search_range + 1):
        current = serial_path + str(i)
        try:
          uart_conn = Serial(current, baud, timeout=1)
          uart_conn.close()
          serial_path = current
        except serial.SerialException:
          continue
        except Exception as dev_err:
          print_fatal(str(dev_err) + '\n')
          print_info('\nExiting...\n')
          sys.exit(1)
    if serial_path == '/dev/ttyUSB':
      serial_path = '/dev/ttyACM'
      for i in range(search_range + 1):
        current = serial_path + str(i)
        try:
          uart_conn = Serial(current, baud, timeout=1)
          uart_conn.close()
          serial_path = current
        except serial.SerialException:
          continue
        except Exception as dev_err:
          print_fatal(str(dev_err) + '\n')
          print_info('\nExiting...\n')
          sys.exit(1)
    if serial_path == '/dev/ttyACM':
      serial_path = '/dev/ttyCOM'
      current = ''
      for i in range(search_range + 1):
        current = serial_path + str(i)
        try:
          uart_conn = Serial(current, baud, timeout=1)
          uart_conn.close()
          serial_path = current
        except serial.SerialException:
          continue
        except Exception as dev_err:
          print_fatal(str(dev_err) + '\n')
          print_info('\nExiting...\n')
          sys.exit(1)
    if serial_path == '/dev/ttyCOM':
      print_fatal('\nCannot find any devices, exiting...\n')
      sys.exit(1)
  except KeyboardInterrupt:
    print_warn('\nInterrupted by user\n')
    print_info('\nExiting...\n')
    sys.exit(1)
  except Exception as arg_err:
    print_fatal('\n' + str(arg_err) + '\n')
    print_info('\nExiting...\n')
    sys.exit(1)

  #Software Configurations
  global block_listener
  char = False
  dec_ow = False
  bin_ow = False
  hex_add = False
  safe_tx = False
  prefix = None
  suffix = None
  keep_log = False
  listener_mute = False
  working_directory = os.getcwd()
  dumpfile = None
  log_listener_check = True
  log_lock = False

  #Prepare program log
  try:
    if not os.path.isdir(log_directory):
      os.mkdir(log_directory)
    program_log = log_directory + 'uart_' + start_time.strftime('%Y-%m-%d_%Hh%Mm%Ss') + '.log'
    log = open(program_log, 'a')
    log.write(get_log_time(start_time))
    log.write('debug: program start\n')
    log.write(get_log_time(datetime.now()))
    log.write('debug: log start\n')
    log.close()
  except Exception as e:
    program_log = None
    print_error(str(e)+'\n')
    print_info('Running without a log\n')

  print_success('\nConnected to ' + serial_path)
  print_info('\nConfigurations: ' + str(baud) + ' ' + str(data_size) + ' bits with ' + par_str + ' parity and ' + str(
    stop_size) + ' stop bit(s)\n\n')

  try:
    uart_conn = Serial(serial_path, baud, data_size, par, stop_size)
  except Exception as e:
    print_fatal(str(e) + '\n')
    sys.exit(2)

  #Set up listener daemon
  try:
    listener_daemon = threading.Thread(target=uart_listener, daemon=True)
    listener_daemon.start()
  except Exception as e:
    print_fatal(str(e) + '\n')
    sys.exit(4)

  listener_alive = True
  block_listener = False
  cin = ''
  print_input_symbol()

  while True:  #main loop for send
    try:
      signal.signal(signal.SIGALRM, check_listener)
      signal.alarm(1)
      cin = input()  #Wait for input
      stamp = '\033[F' + get_now() + ' '
      signal.signal(signal.SIGALRM, process_timeout)
      signal.alarm(1800)  #Half an hour
      cin = cin.strip()
      if cin == '':
        print_time_stamp()  #print timestamp
        print_info('Nothing to do!\n', False)
        print_input_symbol()
        continue

      #command handling
      if cin == '\\quit' or cin == '\\exit' or cin == '\\q':
        print_time_stamp()  #print timestamp
        break
      elif cin == '\\help':
        print_time_stamp()  #print timestamp
        print_info('Help\n', False)
        print_help()
        block_listener = True
        print_input_symbol()
        continue
      elif cin == '\\license':
        print_time_stamp()  #print timestamp
        print_info('License\n', False)
        print_raw('EUPL-1.2\n')
        print_raw('Full text: https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin == '\\char' or cin == '\\c':
        char = True
        dec_ow = False
        bin_ow = False
        hex_add = False
        print_time_stamp()  #print timestamp
        print_info('Received bytes will be printed as character\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin == '\\hex' or cin == '\\h':
        print_time_stamp()  #print timestamp
        print_info('Received bytes will be printed as hexadecimal number\n')
        block_listener = True
        char = False
        dec_ow = False
        bin_ow = False
        hex_add = False
        print_input_symbol()
        continue
      elif cin == '\\dec':
        print_time_stamp()  #print timestamp
        print_info('Received bytes will be printed as decimal number\n')
        block_listener = True
        char = False
        dec_ow = True
        bin_ow = False
        hex_add = False
        print_input_symbol()
        continue
      elif cin == '\\bin':
        print_time_stamp()  #print timestamp
        print_info('Received bytes will be printed as binary number\n')
        block_listener = True
        char = False
        dec_ow = False
        bin_ow = True
        hex_add = False
        print_input_symbol()
        continue
      elif cin == '\\dechex':
        print_time_stamp()  #print timestamp
        print_info('Received bytes will be printed as decimal number and hexadecimal equivalent\n')
        block_listener = True
        char = False
        dec_ow = True
        bin_ow = False
        hex_add = True
        print_input_symbol()
        continue
      elif cin == '\\binhex':
        print_time_stamp()  #print timestamp
        print_info('Received bytes will be printed as binary number and hexadecimal equivalent\n')
        block_listener = True
        char = False
        dec_ow = False
        bin_ow = True
        hex_add = True
        print_input_symbol()
        continue
      elif cin == '\\@':
        print_time_stamp()  #print timestamp
        print_info('Connected to: \033[0m' + serial_path + '\n')
        print_input_symbol()
        continue
      elif cin == '\\keeplog':
        print_time_stamp()  #print timestamp
        if program_log is not None:
          keep_log = True
          print_info('Programme log will be kept\n')
        else:
          try:
            log_lock = True
            program_log = log_directory + 'uart_' + start_time.strftime('%Y%m%dh%Hm%Ms%S') + '.log'
            log = open(program_log, 'a')
            log.write(get_log_time(start_time))
            log.write('program start\n')
            log.write(get_log_time(datetime.now()))
            log.write('log start, tool run without a log!\n')
            log.close()
            print_info('New log generated\n')
            keep_log = True
          except Exception as e:
            print_error('Cannot keep log\n')
            print_error(str(e)+'\n')
          finally:
            log_lock = False
        print_input_symbol()
        continue
      elif cin == '\\safe':
        print_time_stamp()  #print timestamp
        print_info('Safe transmit mode enabled\n')
        block_listener = True
        safe_tx = True
        print_input_symbol()
        continue
      elif cin == '\\unsafe':
        print_time_stamp()  #print timestamp
        print_info('Safe transmit mode disabled\n')
        block_listener = True
        safe_tx = False
        print_input_symbol()
        continue
      elif cin == '\\unmute':
        print_time_stamp()  #print timestamp
        print_info('Listener unmuted\n')
        listener_mute = False
        print_input_symbol()
        continue
      elif cin == '\\mute':
        print_time_stamp()  #print timestamp
        print_info('Listener muted\n')
        listener_mute = True
        if dumpfile is None:
          print_warn('Dumping is disabled, received data will be discarded!\n')
        print_input_symbol()
        continue
      elif cin == '\\nodump':
        print_time_stamp()  #print timestamp
        print_info('Dumping disabled\n')
        dumpfile = None
        if listener_mute:
          print_warn('Listener is muted, received data will be discarded!\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin.startswith('\\dump'):
        cin = cin[5:]
        tmp_file = None
        cin = cin.split(' ')
        print_time_stamp()  #print timestamp
        if len(cin) == cin.count(''):
          tmp_file = 'uart_received.bin'
        else:
          for arg in cin:
            if arg != '':
              if tmp_file is None:
                tmp_file = arg
              else:
                print_warn('Ignoring extra arguments\n', False)
                break
        if not os.path.isfile(working_directory + '/' + tmp_file):
          try:
            tmp_dump = open(working_directory + '/' + tmp_file, 'x')
            tmp_dump.close()
          except Exception as e:
            print_error('Cannot find or create file \033[0m' + tmp_file + '\033[31m in current path!\n')
            print_error(str(e) + '\n')
            print_input_symbol()
            continue
        try:
          tmp_dump = open(working_directory + '/' + tmp_file, 'r')
          tmp_dump.close()
          dumpfile = tmp_file
          print_info('Received bytes will be dumped to \033[0m' + dumpfile + '\n')
        except Exception as open_error:
          print_error('Cannot open file \033[0m' + tmp_file + '\033[31m!\n')
          print_error(str(open_error)+'\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin.startswith('\\send') or cin.startswith('\\s ') or cin == '\\s':
        sendByte = 0
        sendFile = 0
        if cin.strip() == '\\send' or cin.strip() == '\\s':
          block_listener = True
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
              full_path = working_directory + '/' + filename
              file = open(full_path, 'rb')
              sendFile += 1
            except Exception as open_err:
              print_time_stamp()  #print timestamp
              print_error('Cannot open file \033[0m' + filename + '\033[31m!\n')
              print_error(str(open_err) + '\n')
              if safe_tx:
                print_info('Breaking\n')
                break
              else:
                print_info('Continuing\n')
                continue
            byte = file.read(1)
            while byte != b'':
              serial_write(byte)
              sendByte += 1
              byte = file.read(1)
            file.close()
        print_time_stamp()  #print timestamp
        if sendFile == 0:
          print_warn("Didn't write anything\n")
        else:
          print_info('Wrote ' + str(sendByte) + ' bytes from ' + str(sendFile) + ' file(s)\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin.startswith('\\rand') or cin.startswith('\\r ') or cin == '\\r':
        random_byte_count = 1
        print_time_stamp()  #print timestamp
        if cin.strip() != '\\rand' and cin.strip() != '\\r':
          if cin.startswith('\\rand'):
            cin = cin[5:].strip()
          else:
            cin = cin[2:].strip()
          arg = cin.split(' ')
          try:
            temp = int(arg[0])
          except ValueError:
            print_error('Argument should be a number!\n', False)
            print_input_symbol()
            continue
          except Exception as rand_err:
            print_error(str(rand_err)+'\n')
            print_input_symbol()
            continue
          if len(arg) != 1:
            print_warn('Ignoring extra arguments\n', False)
          random_byte_count = temp
        print_info('\033[2mSending \033[0m'+str(random_byte_count)+'\033[2m random byte(s)\n')
        block_listener = True
        random.seed()
        if random_byte_count > 100:
          print_info(('\n\033[F\033[0m' + get_now() + '\033[2m Too many bytes to show!\n'), False)
          block_listener = True
          for i in range(random_byte_count):
            random_byte = random.randint(0, 255)
            serial_write(random_byte.to_bytes(1, byteorder='little'))
        else:
          random_bytes = ''
          for i in range(random_byte_count):
            random_byte = random.randint(0, 255)
            serial_write(random_byte.to_bytes(1, byteorder='little'))
            random_bytes += (hex(random_byte)+' ')
          print_raw('\n\033[F' + get_now() + ' \033[33mSend: \033[0m\033[96m'+random_bytes+'\033[0m\n')
          block_listener = True
        block_listener = True
        print_input_symbol()
        continue
      elif cin == '\\getpath':
        print_time_stamp()  #print timestamp
        print_info('Current path: \033[0m' + working_directory + '\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin.startswith('\\setpath'):
        cin = cin.strip()
        if cin == '\\setpath':
          working_directory = os.getcwd()
        else:
          cin = cin[8:]
          cin = cin.split(' ')
          tmpdir = None
          print_time_stamp()  #print timestamp
          for arg in cin:
            if arg != '':
              if tmpdir is None:
                tmpdir = arg
              else:
                print_warn('Ignoring extra arguments\n', False)
                break
          if tmpdir.startswith('~/'):
            tmpdir = str(os.path.expanduser("~")) + tmpdir[1:]
          elif not tmpdir.startswith('/'):
            tmpdir = os.getcwd() + '/' + tmpdir
          if os.path.isdir(tmpdir):
            working_directory = tmpdir
          else:
            print_raw(tmpdir)
            print_error(' is not a valid directory path!\n')
            print_input_symbol()
            continue
        print_info('Working directory set to \033[0m' + working_directory + '\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin.startswith('\\pref'):
        cin = cin[5:]
        try:
          cin = cin.split(' ')
          hold_bytes = []
          print_time_stamp()  #print timestamp
          if len(cin) == cin.count(''):
            prefix = None
            print_info('Prefix removed\n')
            block_listener = True
          else:
            for item in cin:
              if item != '':
                byte_val = int(item, 16)
                hold_bytes.append(byte_val.to_bytes(1, 'little'))
            print_info('Prefix updated to ')
            for item in cin:
              if item != '':
                print_info(item + ' ')
            prefix = hold_bytes
            print_raw('\n')
        except ValueError:
          print_error('Arguments must be hexadecimal!\n', False)
        except Exception as err:
          print_error(str(err)+'\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin.startswith('\\suff'):
        cin = cin[5:]
        try:
          cin = cin.split(' ')
          hold_bytes = []
          print_time_stamp()  #print timestamp
          if len(cin) == cin.count(''):
            suffix = None
            print_info('Suffix removed\n')
          else:
            for item in cin:
              if item != '':
                byte_val = int(item, 16)
                hold_bytes.append(byte_val.to_bytes(1, 'little'))
            print_info('Suffix updated to ')
            for item in cin:
              if item != '':
                print_info(item + ' ')
            suffix = hold_bytes
            print_raw('\n')
        except ValueError:
          print_error('Arguments must be hexadecimal!\n', False)
        except Exception as err:
          print_error(str(err)+'\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin.startswith('\\'):
        if cin.startswith('\\\\'):
          cin = cin[1:]
        else:
          print_time_stamp()  #print timestamp
          print_warn(('Command \033[0m' + cin + '\033[91m does not exist!\n'), False)
          print_info('Use \033[0m\\help\033[2m to see the list of available commands\n', False)
          block_listener = True
          print_input_symbol()
          continue

      #Data handling
      send_str = ''
      toSend = 0
      cin_org = ''  #to silence a warning

      if prefix is not None:
        for byte in prefix:
          serial_write(byte)
      if not char:
        cin = cin.replace('_', '').replace('\'', '').strip()
        #if input is to large divide it into single transfers
        cin_temp = ''
        cin_org = cin
        for item in cin.split(' '):
          #negative = False
          base = None
          current_item = ''
          if item.startswith('-'):
            #negative = True
            #item = item[1:]
            print_time_stamp()  #print timestamp
            print_warn("Cannot send negative values!\n\n")
            print_time_stamp()  #print timestamp
            print_info("Skipping "+item+"\n\n")
            cin_org = cin_org.replace(item, '\b', 1)
            continue
          if item.startswith('0x'):
            base = 'x'
          elif item.startswith('0d'):
            base = 'd'
          elif item.startswith('0o'):
            base = 'o'
          elif item.startswith('0b'):
            base = 'b'
          if base is not None:
            item = item[2:]
          else:
            if bin_ow:
              base = 'b'
            elif dec_ow:
              base = 'd'
            else:
              base = 'x'
          #seperate according to base
          max_data = 0
          if data_size == serial.EIGHTBITS:
            max_data = 256
          elif data_size == serial.SEVENBITS:
            max_data = 128
          elif data_size == serial.SIXBITS:
            max_data = 64
          else:
            max_data = 32
          try:
            item_int = -1
            if base == 'x':
              item_int = int(item, 16)
              while item_int > (max_data - 1):
                current_item = ' ' + hex(int(item_int % max_data)) + current_item
                item_int = int(item_int / max_data)
              if item_int != -1:
                current_item = ' ' + hex(int(item_int % max_data)) + current_item
            elif base == 'd':
              item_int = int(item, 10)
              while item_int > (max_data-1):
                current_item = ' 0d' + str(int(item_int % max_data)) + current_item
                item_int = int(item_int / max_data)
              if item_int != -1:
                current_item = ' 0d' + str(int(item_int % max_data)) + current_item
            elif base == 'o':
              item_int = int(item, 8)
              while item_int > (max_data - 1):
                current_item = ' ' + oct(int(item_int % max_data)) + current_item
                item_int = int(item_int / max_data)
              if item_int != -1:
                current_item = ' ' + oct(int(item_int % max_data)) + current_item
            else:
              item_int = int(item, 2)
              while item_int > (max_data - 1):
                current_item = ' ' + bin(int(item_int % max_data)) + current_item
                item_int = int(item_int / max_data)
              if item_int != -1:
                current_item = ' ' + bin(int(item_int % max_data)) + current_item
            cin_temp += current_item
          except ValueError:
            print_time_stamp()  #print timestamp
            print_error('0' + base + item + ' is not a valid number with correct base!\n\n')
            block_listener = True
            if safe_tx:
              break
            else:
              continue
          except Exception as err:
            print_error('On ' + item + ': ' + str(err)+'\n')
            if safe_tx:
              break
            else:
              continue
        cin = cin_temp.strip()
        toSend = 0  #use as a buffer
        #this loop will send all buffered data
        for item in cin.split(' '):
          if item == '':
            continue
          try:
            if item.startswith('0x'):
              toSend = int(item[2:], 16)
            elif item.startswith('0d'):
              toSend = int(item[2:], 10)
            elif item.startswith('0o'):
              toSend = int(item[2:], 8)
            elif item.startswith('0b'):
              toSend = int(item[2:], 2)
            else:
              print_time_stamp()  #print timestamp
              print_fatal('No base found for '+item+'! This shouldn\'t happen!')
              break
          except ValueError:
            print_time_stamp()  #print timestamp
            print_fatal(item+' is not a valid number with correct base! This shouldn\'t happen!')
            break
          except Exception as err:
            print_time_stamp()  #print timestamp
            print_error('On '+item+': '+str(err))
            if safe_tx:
              break
            else:
              continue
          if toSend > 255 and data_size == serial.EIGHTBITS:
            print_time_stamp()  #print timestamp
            print_fatal(hex(toSend) + ' does not fit in a byte! This shouldn\'t happen!')
            break
          elif toSend > 127 and data_size == serial.SEVENBITS:
            print_time_stamp()  #print timestamp
            print_fatal(hex(toSend) + ' does not fit in 7 bits! This shouldn\'t happen!')
            break
          elif toSend > 63 and data_size == serial.SIXBITS:
            print_time_stamp()  #print timestamp
            print_fatal(hex(toSend) + ' does not fit in 6 bits! This shouldn\'t happen!')
            break
          elif toSend > 31 and data_size == serial.FIVEBITS:
            print_time_stamp()  #print timestamp
            print_fatal(hex(toSend) + ' does not fit in 5 bits! This shouldn\'t happen!')
            break
          serial_write(toSend.to_bytes(1, 'little'))
      else:
        serial_write(cin.encode())
      if suffix is not None:
        for byte in suffix:
          serial_write(byte)
      print_time_stamp()  #print timestamp
      if cin != '':
        print_raw('\033[33mSend:\033[0m ')
        if char:
          print_raw(cin)
        else:
          print_raw(cin_org + ' \033[2m(' + cin + ')\033[0m')
        print_raw('\n')
      else:
        print_warn('Nothing left to send!\n')
      block_listener = True
      print_input_symbol()

    except serial.SerialException:
      print_fatal('Connection to ' + serial_path + ' lost!\nExiting...\n')
      sys.exit(2)
    except KeyboardInterrupt:
      print_warn('Interrupted by user\n')
      break
    except ListenerControl:
      if listener_alive:
        continue
      else:
        print_error('Daemon is dead!\n')
        print_info('Exiting...\n')
        sys.exit(2)
    except TimeoutError:
        sys.exit(2)
    except Exception as e:
      print_fatal(str(e) + '\n')
      print_info('Exiting...\n')
      break

  print_info('Disconnecting...\n')
  uart_conn.close()

  if program_log is not None and not keep_log:
    if os.path.isfile(program_log):
      os.remove(program_log)
    else:
      print_warn(('Cannot delete program log, \033[0m'+program_log+'\033[91m!\n'), False)

  sys.exit(0)
