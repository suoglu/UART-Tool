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
global block_listener


#Prompt coloring
def get_now():
  return '\033[35m' + str(datetime.datetime.now()) + ':\033[0m'


def print_error(msg):
  sys.stdout.write('\033[31m' + msg + '\033[0m')


def print_success(msg):
  sys.stdout.write('\033[32m' + msg + '\033[0m')


def print_info(msg):
  sys.stdout.write('\033[2m' + msg + '\033[0m')


def print_warn(msg):
  sys.stdout.write('\033[91m' + msg + '\033[0m')


#Helper functions
def get_time_stamp():
  return time.clock_gettime_ns(time.CLOCK_THREAD_CPUTIME_ID)


def print_raw(msg):
  sys.stdout.write(msg)


def serial_write(send_data):
  try:
    uart_conn.write(send_data)
  except Exception as serial_write_error:
    print_error('Cannot send!\n')
    print_error(str(serial_write_error) + '\n')


def print_input_symbol():
  sys.stdout.write('\033[32m> \033[0m')


def check_listener(signum, frame):
  raise TimeoutError


def process_timeout(signum, frame):
  print_warn('Timeout!\n')
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
  print_raw('   ~ \\license : prints license information\n')
  print_raw('   ~ \\mute    : do not print received received to terminal\n')
  print_raw('   ~ \\nodump  : stop dumping received bytes in dumpfile\n')
  print_raw('   ~ \\pref    : add bytes to send before transmitted data, arguments should be given as hexadecimal\n')
  print_raw('   ~ \033[7m\\quit\033[0m    : exits the script\n')
  print_raw('   ~ \\safe    : in non char mode, stop sending if non number given\n')
  print_raw('   ~ \033[7m\\send\033[0m    : send files\n')
  print_raw('   ~ \\setpath : set directory for file operations, full or relative path, empty for cwd\n')
  print_raw('   ~ \\suff    : add bytes to send after transmitted data, arguments should be given as hexadecimal\n')
  print_raw('   ~ \\unmute  : print received received to terminal\n')
  print_raw('   ~ \\unsafe  : in non char mode, do not stop sending if non number given\n')
  print_raw('\n  Marked commands can be called with their first letter\n')


#listener daemon
def uart_listener():  #? if possible, TODO: keep the prompt already written in terminal when new received
  print_raw(get_now())
  print_info(' Listening...\n')
  timer_stamp = 0
  last_line = ''
  byte_counter = 0
  global listener_alive
  global block_listener

  while True:  #main loop for listener
    try:
      read_byte = uart_conn.read()
      if not listener_mute:
        if char:
          buff = read_byte.decode()
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
        byte_brake = ((byte_counter == 15) and not char) or ((byte_counter == 80) and char)
        line_end = (buff == '\n') and char
        if (timer_stamp < get_time_stamp()) or line_end or byte_brake or block_listener:
          block_listener = False
          byte_counter = 0
          last_line = '\033[F' + '\n' + get_now() + ' \033[36mGot:\033[0m '
        else:
          print_raw('\033[F\r')
          byte_counter += 1

        last_line += buff
        print_raw(last_line + '\n')
        print_input_symbol()
        sys.stdout.flush()
        timer_stamp = get_time_stamp() + 100000
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
      print_error('\033[F\nConnection to ' + serial_path + ' lost!\n')
      print_info('Exiting daemon...\n')
      listener_alive = False
      break
    except Exception as listener_error:
      print_error(str(listener_error) + '\n')
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
    elif current.casefold() == 'help':
      print('\033[FUsage: uart.py [arg]                  ')
      print_info(' Arguments can be the uart configurations or one of the following commands:\n\n')
      print_info('   ~ i      : interactive start up, tool asks for uart configurations\n')
      print_info('   ~ help   : Print this message\n')
      print_info('   ~ search : Search for connected devices\n')
      print_info('\n Uart configurations can be given in any order\n')
      sys.exit(0)
    elif current.casefold() == 'i':
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
    elif current.casefold() == 'search':
      print_info('\nSearching for connected devices...\n')
      found_dev = 0
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
            print_warn('\nFound ttyUSB' + str(i) + ', but not responding')
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
            print_warn('\nFound ttyACM' + str(i) + ', but not responding')
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
          except serial.SerialException:
            print_warn('\nFound ttyCOM' + str(i) + ', but not responding')
          except Exception as search_err:
            print_warn(str(search_err)+'\n')
            print_info('Ignoring...\n')
      print_raw('\n')
      sys.exit(0)
    elif current.startswith('tty'):
      serial_path = '/dev/' + current
      try:
        uart_conn = Serial(serial_path, baud, timeout=1)
        uart_conn.close()
      except serial.SerialException:
        print_error('\nCannot open ' + serial_path)
        print_info('\nExiting...\n')
        sys.exit(1)
      except Exception as dev_err:
        print_error(str(dev_err) + '\n')
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
        print_error(str(dev_err) + '\n')
        print_info('\nExiting...\n')
        sys.exit(1)
  if serial_path == '/dev/ttyUSB':
    print_warn('\nCannot find a ttyUSB device, searching for a ttyACM device...')
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
        print_error(str(dev_err) + '\n')
        print_info('\nExiting...\n')
        sys.exit(1)
  if serial_path == '/dev/ttyACM':
    print_warn('\nCannot find a ttyACM device, searching for a ttyCOM device...')
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
        print_error(str(dev_err) + '\n')
        print_info('\nExiting...\n')
        sys.exit(1)
  if serial_path == '/dev/ttyCOM':
    print_error('\nCannot find any devices, exiting...\n')
    sys.exit(1)
  else:
    print_success('\nConnected to ' + serial_path)

  print_info('\nConfigurations: ' + str(baud) + ' ' + str(data_size) + ' bits with ' + par_str + ' parity and ' + str(
    stop_size) + ' stop bit(s)\n\n')

  #Software Configurations
  char = True
  dec_ow = False
  bin_ow = False
  hex_add = False
  safe_tx = False
  prefix = None
  suffix = None
  listener_mute = False
  working_directory = os.getcwd()
  dumpfile = None

  try:
    uart_conn = Serial(serial_path, baud, data_size, par, stop_size)
  except Exception as e:
    print_error(str(e) + '\n')
    sys.exit(2)

  #Set up listener daemon
  try:
    listener_daemon = threading.Thread(target=uart_listener, daemon=True)
    listener_daemon.start()
  except Exception as e:
    print_error(str(e) + '\n')
    sys.exit(4)

  listener_alive = True
  block_listener = False
  cin = ''
  print_input_symbol()

  while True:  #main loop for send
    try:
      # if not listener_alive:
      # raise ChildProcessError
      signal.signal(signal.SIGALRM, check_listener)
      signal.alarm(1)
      cin = input()  #Wait for input
      stamp = '\033[F' + get_now() + ' '
      signal.signal(signal.SIGALRM, process_timeout)
      signal.alarm(1800)  #Half an hour
      cin = cin.strip()
      if cin == '':
        continue

      #command handling
      if cin == '\\quit' or cin == '\\exit' or cin == '\\q':
        print_raw(stamp)  #print timestamp
        break
      elif cin == '\\help':
        print_raw(stamp)  #print timestamp
        print_info('Help\n')
        print_help()
        block_listener = True
        print_input_symbol()
        continue
      elif cin == '\\license':
        print_raw(stamp)  #print timestamp
        print_info('License\n')
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
        print_raw(stamp)  #print timestamp
        print_info('Received bytes will be printed as character\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin == '\\hex' or cin == '\\h':
        print_raw(stamp)  #print timestamp
        print_info('Received bytes will be printed as hexadecimal number\n')
        block_listener = True
        char = False
        dec_ow = False
        bin_ow = False
        hex_add = False
        print_input_symbol()
        continue
      elif cin == '\\dec':
        print_raw(stamp)  #print timestamp
        print_info('Received bytes will be printed as decimal number\n')
        block_listener = True
        char = False
        dec_ow = True
        bin_ow = False
        hex_add = False
        print_input_symbol()
        continue
      elif cin == '\\bin':
        print_raw(stamp)  #print timestamp
        print_info('Received bytes will be printed as binary number\n')
        block_listener = True
        char = False
        dec_ow = False
        bin_ow = True
        hex_add = False
        print_input_symbol()
        continue
      elif cin == '\\dechex':
        print_raw(stamp)  #print timestamp
        print_info('Received bytes will be printed as decimal number and hexadecimal equivalent\n')
        block_listener = True
        char = False
        dec_ow = True
        bin_ow = False
        hex_add = True
        print_input_symbol()
        continue
      elif cin == '\\binhex':
        print_raw(stamp)  #print timestamp
        print_info('Received bytes will be printed as binary number and hexadecimal equivalent\n')
        block_listener = True
        char = False
        dec_ow = False
        bin_ow = True
        hex_add = True
        print_input_symbol()
        continue
      elif cin == '\\safe':
        print_raw(stamp)  #print timestamp
        print_info('Safe transmit mode enabled\n')
        block_listener = True
        safe_tx = True
        print_input_symbol()
        continue
      elif cin == '\\unsafe':
        print_raw(stamp)  #print timestamp
        print_info('Safe transmit mode disabled\n')
        block_listener = True
        safe_tx = False
        print_input_symbol()
        continue
      elif cin == '\\unmute':
        print_raw(stamp)  #print timestamp
        print_info('Listener unmuted\n')
        listener_mute = False
        print_input_symbol()
        continue
      elif cin == '\\mute':
        print_raw(stamp)  #print timestamp
        print_info('Listener muted\n')
        listener_mute = True
        if dumpfile is None:
          print_warn('Dumping is disabled, received data will be discarded!\n')
        print_input_symbol()
        continue
      elif cin == '\\nodump':
        print_raw(stamp)  #print timestamp
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
        print_raw(stamp)  #print timestamp
        if len(cin) == cin.count(''):
          tmp_file = 'uart_received.bin'
        else:
          extra_arg = ''
          for arg in cin:
            if arg != '':
              if tmp_file is None:
                tmp_file = arg
              elif extra_arg == '':
                extra_arg = arg
              else:
                extra_arg += (', ' + arg)
          if extra_arg != '':
            print_warn('Ignoring following extra arguments:\033[0m ' + extra_arg + '\n')
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
              print_raw(stamp)  #print timestamp
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
        print_raw(stamp)  #print timestamp
        if sendFile == 0:
          print_warn("Didn't write anything\n")
        else:
          print_info('Wrote ' + str(sendByte) + ' bytes from ' + str(sendFile) + ' file(s)\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin == '\\getpath':
        print_raw(stamp)  #print timestamp
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
          print_raw(stamp)  #print timestamp
          for arg in cin:
            if arg != '':
              if tmpdir is None:
                tmpdir = arg
              else:
                print_warn('Ignoring extra arguments\n')
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
          print_raw(stamp)  #print timestamp
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
          print_error('Arguments must be hexadecimal!\n')
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
          print_raw(stamp)  #print timestamp
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
          print_error('Arguments must be hexadecimal!\n')
        except Exception as err:
          print_error(str(err)+'\n')
        block_listener = True
        print_input_symbol()
        continue
      elif cin.startswith('\\'):
        if cin.startswith('\\\\'):
          cin = cin[1:]
        else:
          print_raw(stamp)  #print timestamp
          print_warn('Command \033[0m' + cin + '\033[91m does not exist!\n')
          print_info('Use \033[0m\\help\033[2m to see the list of available commands\n')
          block_listener = True
          print_input_symbol()
          continue
      #Data handling
      error_str = ''
      send_str = ''
      toSend = 0

      if prefix is not None:
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
          except ValueError:
            error_str += (item + ' is not a valid number!\n')
            block_listener = True
            if safe_tx:
              break
          except Exception as err:
            print_error('On '+item+': '+str(err))
            if safe_tx:
              break
          send_str += (item + ' ')
          serial_write(toSend.to_bytes(1, 'little'))
        cin = send_str
      else:
        serial_write(cin.encode())

      if suffix is not None:
        for byte in suffix:
          serial_write(byte)

      cin += '\n'
      print_raw(stamp)  #print timestamp
      print_raw('\033[33mSend:\033[0m ' + cin)
      if error_str != '':
        print_error(error_str+'\n')
      block_listener = True
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
      print_error(str(e) + '\n')
      print_info('Exiting...\n')
      break

  print_info('Disconnecting...\n')
  uart_conn.close()
