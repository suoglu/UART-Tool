# UART Tool

## Contents of Readme

1. About
2. Usage
   1. Description
   2. Arguments
   3. Software configurations
   4. Commands
3. Dependencies

[![Repo on GitLab](https://img.shields.io/badge/repo-GitLab-6C488A.svg)](https://gitlab.com/suoglu/uart-tool)
[![Repo on GitHub](https://img.shields.io/badge/repo-GitHub-3D76C2.svg)](https://github.com/suoglu/UART-Tool)

---

## About

This repository contains python3 script, [uart.py](Sources/uart.py), for basic serial communication via UART.

## Usage

### Description

When the [script](Sources/uart.py) run, it polls for a serial device. First it searches for a *ttyUSB* device, then for a *ttyACM* device and finally for a *ttyCOM* device. If nothing is found, it exits. If found software configurations are initialized and script waits for and user input. Anything that starts with a single `\` considered a command, everything else data. To send a `\`, `\\` should be entered. Data can be entered as a character or a number of different bases. When the connection is lost, script automatically exits. User can also exit via exit commands or by keyboard interrupt.

## Arguments

Default configurations for the UART is 8-bit data with no parity and 1 stop bit; and baud rate set to 115.2k. User can change these configurations via arguments when calling the tool. User can also specify a serial device path. Device name must start with *tty*. Tool automatically detects arguments. Supported arguments (Bold for default values):

* Data size: 5, 6, 7, **8**
* Baud rate: **115.2k**, 1.2k<
* Stop-bit size: **1**, 1.5, 2
* Parity: **no**, even, odd, mark, space (first letters also work)
* Device path: */dev/tty\**, ***/dev/ttyUSB\****, ***/dev/ttyACM\****, ***/dev/ttyCOM\****
* Poll range: **10**...20

Tool also provide some helper functionality via arguments. When one of these arguments passed, tool exits after it's done. When multiple arguments are passed, only argument is processed.

* Help: Print info about arguments
* Search: Search for available devices
* i: interactive start, tool asks for serial configurations

## Software configurations

Software configurations handle how to interpret data and adds some options. Currently, implemented options (Bold for default values):

* Data type: **character**, hexadecimal number, decimal number, binary number
* Safe transmit: **Disabled**; relevant to sending non-character, if current data is not a numeric value stop sending
* Prefix: **None**; Bytes to send before data
* Suffix: **None**; Bytes to send after data
* Mute: **Disabled**; Do not print received data to terminal
* Dumping: **Disabled**; Dump received bytes into a file

When in a numeric data mode; data must be entered as a numeric value with respect to current set data type or by specifying its base.

## Commands

Commands allow user to change software configurations and interact with the script. Each command start with a single `\`, anything else considered as data. To send a `\` as first byte, use `\\`. Table of available commands can be found below.

|Command|Shortened|Description|
|:---:|:---:|---|
|`bin`||Binary data mode|
|`binhex`||Binary data mode, also print hexadecimal equivalent|
|`char`|`c`|Character data mode|
|`dec`||Decimal data mode|
|`dechex`||Decimal data mode, also print hexadecimal equivalent|
|`dump [filename]`||Dump received bytes into a file, filename can be given as argument|
|`exit`||Exits the script same as `quit`|
|`getpath`||Prints working directory|
|`hex`|`h`|Hexadecimal data mode|
|`help`||Prints information about the script|
|`license`||Prints license information|
|`mute`||Do not show received data on terminal|
|`nodump`||Stop dumping received data|
|`pref [data]`||Add bytes to prefix, data should be given as hexadecimal|
|`quit`|`q`|Exits the script same as `exit`|
|`safe`||Enable safe transmit mode|
|`send`|`s`|Send files|
|`setpath`||set directory for file operations, full or relative path, empty for cwd |
|`suff [data]`||Add bytes to suffix, data should be given as hexadecimal|
|`unmute`||Show received data on terminal|
|`unsafe`||Disable safe transmit mode|

## Dependencies

Script [uart.py](Sources/uart.py) uses *sys*, *pyserial*, *threading*, *time*, *datetime*, *os* and *signal* modules, and tested with Python 3.8.6 on Pop!_OS 20.10
