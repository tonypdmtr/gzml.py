#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Docstring
"""Command Line Monitor Loader for Motorola/Freescale/NXP MC68HC908GZ60"""

# Set built in COM port useable on Ubuntu:
#   'dmesg | grep tty' will list available ports. My one is '[    1.427419] 00:01: ttyS0 at I/O 0x3f8 (irq = 4, base_baud = 115200) is a 16550A'
#   Give access by 'sudo chmod o+rw /dev/ttyS0'

# Import statements
import os, sys, getopt, struct
import array
import serial # I use Python 2.7.17. For this I needed 'sudo apt install python-pip' and 'sudo python -m pip install pyserial'
import bincopy # 'pip install bincopy'
import re
import time
import ntpath

# Authorship information
__author__ = "Janos BENCSIK"
__copyright__ = "Copyright 2019, butyi.hu"
__credits__ = "https://gist.github.com/mgeeky , https://pypi.org/project/bincopy/"
__license__ = "GPL"
__version__ = "0.0.0"
__maintainer__ = "Janos BENCSIK"
__email__ = "gzml@butyi.hu"
__status__ = "Prototype"

# Code

# ---------------------------------------------------------------------------------------
# Global variables
# ---------------------------------------------------------------------------------------
version = "V0.01 2019.09.07.";

inputfile = ""
if sys.platform.startswith("linux") or sys.platform.startswith("cygwin") or sys.platform.startswith("darwin"): # linux or OS X
  port = "/dev/ttyS0"
elif sys.platform.startswith("win"): # Windows
  port = "COM1"
baud = 9600
comsleep_ms = 0 # 10ms is enough for some USB-Serial converters like ATEN. If not, try to increase to 20, 50, 100 for example.
fq = 5200000.
ptb4 = False # False is Low what causes faster baud rate
bra_offset_value = 0xFE # Zero nop
dumpstart = False
dumplength = 256
erase = False
mem_dump = False
mem = bytearray(65536)
connected = False
mass_erase_address = None
write_flash_address = None
branch_offset_address = None
FlashHandlerRoutinesAvailable = False
ram_routines = None # Will be read from file

# ---------------------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------------------

def p(str):  
  sys.stdout.write(str)
  sys.stdout.flush()

def err(s):
  p("\nERROR! "+s+"\n\n")
  for line in traceback.format_stack():
    p(line.strip())
  sys.exit(1)

# ---------------------------------------------------------------------------------------
def str_lh(bool_var):
  if bool_var:
    return "H"
  else:
    return "L"

# ---------------------------------------------------------------------------------------
def h(byte,f = "02X"):
  return("$"+format(byte,f))

# ---------------------------------------------------------------------------------------
def RecByte():
  if 0 < comsleep_ms:
    time.sleep(comsleep_ms / 1000.) # This delay is needed for USB-Serial devices
  bs = ser.read(1)
  if len(bs) == 0:
    err("There was no expected received byte during 1s timeout.")
  return ord(bs)

# ---------------------------------------------------------------------------------------
def SendByte(byte):
  my_bytes = bytearray()
  my_bytes.append(byte)
  byte=my_bytes
  if 0 < comsleep_ms:
    ser.flushInput()
  ser.write(byte)
  if 0 < comsleep_ms:
    ser.flushOutput()  
    time.sleep(comsleep_ms / 1000.) # This delay is needed for USB-Serial devices
  byte=ord(byte)
  echo = ser.read(1)
  if len(echo) == 0:
    err("There was no loopback during 1s timeout.")
  echo = ord(echo);
  if echo != byte:
    err("Loopback failed. Sent "+h(byte)+", received "+h(echo)+".")
  echo = ser.read(1)
  if len(echo) == 0:
    err("There was no target echo during 1s timeout.")
  echo = ord(echo);
  if echo != byte:
    err("Target echo failed. Sent "+h(byte)+", received "+h(echo)+".")
  #p("Sent byte "+h(byte))  

# ---------------------------------------------------------------------------------------
def Connection():
  global connected
  if connected:
    return
  
  p("Connect to device (Do a power reset and press Enter)\r")

  # Force power reset
  c = sys.stdin.read(1)
  if c == chr(27):
    sys.exit(0)
  
  # Send 8 security bytes
  for x in range(8):
    SendByte(0xFF)
  
  # Read break character
  if RecByte() == 0:
    p("Connection Done.\n")
    connected = True
  else:
    err("Connection failed.")

# ---------------------------------------------------------------------------------------
def hex_dump_memory(data, startaddress):
    # Thanks for this dump code for https://gist.github.com/mgeeky 
    s = ""
    n = 0
    lines = []
    if len(data) == 0:
        return "<empty>"
    for i in range(0, len(data), 16):
        line = ""
        line += "%04X | " % (i+startaddress)
        n += 16
        for j in range(n-16, n):
            if j >= len(data): break
            line += "%02X " % abs(data[j])
        line += " " * (3 * 16 + 7 - len(line)) + " | "
        for j in range(n-16, n):
            if j >= len(data): break
            c = data[j] if not (data[j] < 0x20 or data[j] > 0x7e) else "."
            line += "%c" % c
        lines.append(line)
    return "\n".join(lines)

# ---------------------------------------------------------------------------------------
# Calculates:
# - Baud rate for communication
# - Number of nop instructions in delay subroutine which gives timing of flash operations
#   Delay subroutine applies a relative branch back. This offset is overwritten by calculated value
def GetTiming(f = 4000000., ptb4 = False):
  baudrates = [50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 3600, 4800, 7200, 9600, 14400, 19200, 28800, 38400, 57600, 115200]
  fb = f
  if ptb4:
    fb = f / 2.
  baud_th = int(fb / 552.) # Theoretical 
  found = False
  for b in baudrates: # Search baud rate 
    if b*0.98 < baud_th and baud_th < b*1.02: # inside 2% tolerance
      found = True
      baud = b
      break
  if found == False: # No baud rate found
    err(str(f/1000000)+"MHz with PTB4="+str_lh(ptb4)+" needs baud rate "+str(baud_th)+". It cannot be covered with any standard baud rate.\nYou need to use different quartz (once 1, 1.3, 2, 2.65, 4, 5.3 or 8MHz ).")
  nop_cnt = int((fb / 400000) -3)
  bra_offset = int(254 - nop_cnt)
  p(str(f/1000000)+"MHz with PTB4="+str_lh(ptb4)+" needs "+str(nop_cnt)+" nop instructions in delay (branch offset "+h(bra_offset)+")\n")
  p("Best baud rate is "+str(baud)+" for "+str(baud_th)+" (tolerance is "+format((baud*100./baud_th)-100,".2f")+" %)\n")
  return {"baud_rate":baud, "bra_offset":bra_offset }

# ---------------------------------------------------------------------------------------
def ReadMemoryIntoList(start_address,length,verbose=False):
  data = [] # Crerate empty list
  l = 0
  if verbose: 
    p("Reading "+h(start_address+l,"04X"))

  # Read a byte
  SendByte(0x4A) # Monitor mode READ command
  SendByte((start_address >> 8) & 0xFF)
  SendByte(start_address & 0xFF)
  data.append(RecByte())
  l+=1

  while l < length:
    if verbose and (((l % 64) == 0) or ((l % 64) == 1)): 
      p("\rReading "+h((start_address+l)&0xFFFE,"04X"))
    SendByte(0x1A) # Monitor mode IREAD command
    data.append(RecByte())
    l+=1
    c = RecByte() # second read always needed, even if not needed for caller
    if l < length:
      data.append(c)
      l+=1
  
  if verbose: 
    p(", Done.\n")
    
  return (data)

# ---------------------------------------------------------------------------------------
def WriteMemoryFromList(data_list,start_address):
  l=0 
  SendByte(0x49) # Monitor mode WRITE command
  SendByte((start_address >> 8) & 0xFF)
  SendByte(start_address & 0xFF)
  SendByte(data_list[l])
  l += 1
  while l < len(data_list):
    #p(hex(data_list[l]))
    SendByte(0x19); # Monitor mode IWRITE command
    SendByte(data_list[l])
    l += 1

# ---------------------------------------------------------------------------------------
def ReadFlashHandlerRoutinesConnectAndWriteToRAM():
  global ram_routines, mass_erase_address, write_flash_address, branch_offset_address
  global FlashHandlerRoutinesAvailable
  if FlashHandlerRoutinesAvailable == True:
    return
  # Read flash handler routines from S19 string what will be copied into RAM.
  p("Read flash handler routines")
  ram_routines = bincopy.BinFile("loader.s19")
  ram_routines = list(ram_routines.as_binary())
  p(", Done.\n")

  # Search start address of routines
  p("Search start address of routines")
  with open("loader.lst") as lf:
    for line in lf:
      match = re.search("\s+([\dABCDEFabcdef]{4})\s+write_flash\s+", line)
      match2 = re.search("\s+([\dABCDEFabcdef]{4})\s+mass_erase\s+", line)
      match3 = re.search("\s+([\dABCDEFabcdef]{4})\s+branch_offset\s+", line)
      if match:
        write_flash_address = int(match.group(1), 16)
      if match2:
        mass_erase_address = int(match2.group(1), 16)
      if match3:
        branch_offset_address = int(match3.group(1), 16)-1
  p(", Done.\n")
        
  #p(" - mass_erase_address="+hex(mass_erase_address)+"\n")
  #p(" - write_flash_address="+hex(write_flash_address)+"\n")
  #p(" - branch_offset_address="+hex(branch_offset_address)+"\n")
  
  # Set branch_offset to adjust delay subroutine to given timing (quarz) by jump back to calculated number of NOP instructions
  ram_routines[branch_offset_address-mass_erase_address] = bra_offset_value
  
  FlashHandlerRoutinesAvailable = True

  # Connect to device
  Connection()
  
  p("Write flash routines into RAM")
  WriteMemoryFromList(ram_routines,0x100)
  p(", Done.\n")

# ---------------------------------------------------------------------------------------
def RunFromAddress(start_address):
  SendByte(0x0C) # Monitor mode READSP command
  SP = (((RecByte() << 8) | (RecByte() & 0xFF)) - 1) & 0xFFFF
  buff = []
  buff.append(0) # H
  buff.append(0) # CC
  buff.append(0) # A
  buff.append(0) # X
  buff.append(start_address >> 8)
  buff.append(start_address & 0xFF)
  WriteMemoryFromList(buff,SP+1)
  SendByte(0x28) # Monitor mode RUN command

# ---------------------------------------------------------------------------------------
def WaitForJumpBack():
  # Read break character
  if RecByte() != 0:
    err("Jump back timeout happened.") # No brake character received

# ---------------------------------------------------------------------------------------
def SelectFlash(address,length):
  if 64 < length: # length shall not be larger than flash row size
    err("SelectFlash called with too high length.")
  buff = [] # Empty list
  if 0x8000 <= address:
    #   FL1CR FF88 
    #   FL1BPR FF80
    # p_flcr  (PGM 0x01, ERASE 0x02, MASS 0x04, HVEN 0x08)
    buff.append(0xFF) 
    buff.append(0x88) 
    # p_flbpr
    buff.append(0xFF) 
    buff.append(0x80) 
  else:
    #   FL2CR FE08 
    #   FL2BPR FF81
    # p_flcr  (PGM 0x01, ERASE 0x02, MASS 0x04, HVEN 0x08)
    buff.append(0xFE) 
    buff.append(0x08) 
    # p_flbpr
    buff.append(0xFF)
    buff.append(0x81) 
  # address
  buff.append((address>>8)&0xFF)
  buff.append(address&0xFF)
  # ret
  buff.append(0xEE) # default value: error
  # len
  buff.append(length);
  return buff  

# ---------------------------------------------------------------------------------------
def MassEraseFlash(address):
  WriteMemoryFromList(SelectFlash( address, 0 ), 0xC0 ) # Write parameters into RAM
  RunFromAddress(mass_erase_address)
  WaitForJumpBack()
  # Read return value 
  SendByte(0x4A) # Monitor mode READ command
  SendByte(0x00)
  SendByte(0xC6) # 0xC6 is because row data buffer is from 0x80 to 0xBF, parameters are from 0xC0  
  ret = RecByte()
  if ret != 0:
    err("Mass erase of address "+h(address,"04X")+" failed with error code "+str(ret))
  
def DownloadRow(data, address):
  WriteMemoryFromList( data, 0x80 + ( address & 0x3F )) # Write data into RAM
  WriteMemoryFromList( SelectFlash( address, len( data ) ), 0xC0 ) # Write parameters into RAM
  RunFromAddress(write_flash_address) # call burn
  WaitForJumpBack()
  # Read return value 
  SendByte(0x4A) # Monitor mode READ command
  SendByte(0x00)
  SendByte(0xC6) # 0xC6 is because row data buffer is from 0x80 to 0xBF, parameters are from 0xC0  
  ret = RecByte()
  if ret != 0:
    err("Write row of address "+h(address,"04X")+" failed with error code "+str(ret))

  
# ---------------------------------------------------------------------------------------
def PrintHelp(): 
  p("gzml.py - MC68HC908GZ60 Monitor Loader - " + version +"\n")
  p("Download software into flash memory from an S19 file using monitor mode\n")
  p("Options: \n")
  p("  -p port      Set serial com PORT used to communicate with target (e.g. COM1 or /dev/ttyS0)\n")
  p("  -s time_ms   Sleep time in ms before byte reception\n")
  p("  -q quarz     Frequency of applied quarz in board in Hz\n")
  p("  -1           Set if PTB4=1. Defaulst is PTB4=0\n")
  p("  -f s19file   S19 file path to be downloaded\n")
  p("  -d address   DUMP from memory address\n")
  p("  -l length    Dump LENGTH, default 0x80\n")
  p("  -e           ERASE only the target using mass erase, clearing security bytes\n")
  p("  -m           Memory dump into text file mem.dump\n")
  p("  -h           Print out this HELP text\n")
  p("Examples:\n")
  p("  gzml.py -e         Erase the whole flash memory to be uC empty\n")
  p("  gzml.py -f xy.s19  Download xy.s19 software into the empty uC\n")
  p("  gzml.py -d 0xFF00  Check if vectors were written properly\n")
  p("  gzml.py -e -f xy.s19 -q 8000000 Erase and Download xy.s19 software in one call (fQ=8MHz, PTB4=0)\n")
  sys.exit(0)

# ---------------------------------------------------------------------------------------
# MAIN()
# ---------------------------------------------------------------------------------------

#Parsing command line options
argv = sys.argv[1:]
try:
  opts, args = getopt.getopt(argv,"p:s:q:f:d:l:e1mh",["port=","sleep=","quarz=","file=","dump=","length=","erase","ptb4","memory","help"])
except getopt.GetoptError:
  p("Wrong option.\n")
  PrintHelp()
for opt, arg in opts:
  if opt in ("-h", "--help"):
    PrintHelp()
  elif opt in ("-p", "--port"):
    port = arg
  elif opt in ("-s", "--sleep"):
    comsleep_ms = int(arg, 0)
  elif opt in ("-q", "--quarz"):
    fq = int(arg)
  elif opt in ("-f", "--file"):
    inputfile = arg
  elif opt in ("-d", "--dump"):
    dumpstart = int(arg)
  elif opt in ("-l", "--length"):
    dumplength = int(arg)
  elif opt in ("-e", "--erase"):
    erase = True
  elif opt in ("-m", "--memory"):
    mem_dump = True
  elif opt in ("-1", "--ptb4"):
    ptb4 = True

# Inform user about parsed parameters
p("gzml.py - MC68HC908GZ60 Monitor Loader - " + version + "\n")
p("Port '" + port + "'\n")
p("Sleep is " + str(comsleep_ms) + "ms\n")
tinimg = GetTiming(fq,ptb4)
baud=tinimg["baud_rate"]
bra_offset_value = tinimg["bra_offset"]

# Open serial port
p("Open serial port")
try:
  ser = serial.Serial(port, baud, timeout=1)
except:
  err("Cannot open serial port " + port)
p(", Done.\n")

# ---------------------------------------------------------------------------------------
# Erase operation
if erase:
  # Read Flash Handler Routines and write into RAM
  ReadFlashHandlerRoutinesConnectAndWriteToRAM()

  p("Mass erase of Flash1")
  MassEraseFlash(0xFF80)
  p(", Done.\n")

  p("Mass erase of Flash2")
  MassEraseFlash(0x1000)
  p(", Done.\n")
  

# ---------------------------------------------------------------------------------------
# Download operation
if 0 < len(inputfile):
  # Read Flash Handler Routines and write into RAM
  ReadFlashHandlerRoutinesConnectAndWriteToRAM()

  p("Build up memory model")
  # Build memory map of MC68HC908GZ60 in rows. This is a list of dictionary (c struct array)
  #  Property row and rowlen depends on hardware, start and length depends on used range in row.
  rows =        [{"row":0x462, "start":0x462, "rowlen":30, "used":False, "data":[] }]
  for r in range(0x480,0x500,64):
    rows.append({"row":r, "start":r, "rowlen":64, "used":False, "data":[] })
  for r in range(0x980,0x1B80,64):
    rows.append({"row":r, "start":r, "rowlen":64, "used":False, "data":[] })
  rows.append({"row":0x1E20, "start":0x1E20, "rowlen":0x60, "used":False, "data":[] })
  for r in range(0x1E80,0xFE00,64):
    rows.append({"row":r, "start":r, "rowlen":64, "used":False, "data":[] })
  rows.append({"row":0xFFCC, "start":0xFFCC, "rowlen":0x34, "used":False, "data":[] })
  p(", Done.\n")

  # Read S19 into data array. Not used bytes are 0xFF.
  p("Read S19 file "+ntpath.basename(inputfile))
  f = bincopy.BinFile(inputfile)
  p(", Done.\n")

  p("Collect data")
  mem = [0xFF] * 65536
  for segment in f.segments:
    i = 0
    for x in range(segment.address,segment.address+len(segment.data)):
      mem[x] = segment.data[i]
      i += 1
  p(", Done.\n")

  # Save memory content
  if mem_dump:
    p("Create or update file mem.dump")
    f1 = open("./mem.dump", "w+")
    f1.write(hex_dump_memory(mem, 0))
    f1.close()
    p(", Done.\n")

  # Fill memory map data from S19
  p("Fill memory rows with data")
  for r in rows:
    for a in range(r["row"], r["row"] + r["rowlen"]): # Go forward on row addresses
      if mem[a] != 0xFF and r["used"] == False: # If this is the first data byte
        r["start"] = a # Save start address
        r["used"] = True # Mark as row is used
      if r["used"] == True: # If row used
        r["data"].append(mem[a]) # Add further data bytes 
    if r["used"] == False: # If there is no data in row,
      continue # There is no more task
    # Delete 0xFF bytes from end of row
    for a in range(r["row"] + r["rowlen"]-1, r["row"]-1, -1): # Go backward on row addresses
      if mem[a] == 0xFF: # If data byte is empty
        r["data"].pop() # Drop it from data list
      else: # At first not empty data byte 
        break # leave the loop

  # Delete not used rows from list
  rows[:] = [r for r in rows if r.get("used") != False]
  #p(rows)
  
  p(", Done.\n")

  # Download rows
  for r in rows:
    p("Write row "+h(r["row"],"04X")+"("+h(r["rowlen"])+"): "+h(len(r["data"]))+" bytes from "+h(r["start"],"04X"))
    DownloadRow(r["data"],r["start"])
    p(", Verify")
    readback = ReadMemoryIntoList(r["start"],len(r["data"]))
    written = r["data"]
    for x in range(len(r["data"])):    
      if written[x] != readback[x]:
        err("Verify error. Address "+h((r["start"]+x),"04X")+", written "+h(written[x])+", readback "+h(readback[x]))
    p(", Done.\n")


# ---------------------------------------------------------------------------------------
# Dump operation
if int == type(dumpstart):
  p("Dump start address " + h(dumpstart,"04X") + " length " + h(dumplength) + "\n")
  
  # Connect to device
  Connection()
  
  if 0xFFFF < (dumpstart+dumplength): # limit dump at 0xFFFF
    dumplength = 0x10000 - dumpstart
  p(hex_dump_memory(ReadMemoryIntoList(dumpstart,dumplength,True), dumpstart))
  p("\n")
  


# ---------------------------------------------------------------------------------------
p("Done.\n")
ser.close()
sys.exit(0)
