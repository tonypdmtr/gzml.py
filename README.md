# gzml.py

Command Line Monitor Loader for Motorola/Freescale/NXP MC68HC908GZ60

## Why?

My motivation was, I still have working hardwares, but I couldn't update the sw because 
loaders developed for WinXP and motherboard built in COM port do not work on Win7, Win10 and on USB-RS232 devices.
Therefore I could not use PEMICRO prog08sz any longer, as I could 10 years before.
Additionally meantime I have switched from Windows to Linux. 
I have already written a [tool](https://github.com/butyi/gzml) for this purpose on Linux, 
but it has two disadvantages: 
- Does not work with non-standard baud rates. Therefore it does not work with usual quarz frequencies, like 8MHz, 4MHz.
- Does not work on Windows.

To get rid these drawbacks (and to have experience in Python), I have re-written the monitor loader in Python here.

## What are supported by gzml.py?

It supports only basic monitor features what are needed to erase flash and download
software into flash. Usually I just use monitor loader to download the bootloader into
an empty uC. After that system software can be downloaded easily through RS232 UART port. 
Therefore I just implemented those functions, which are needed to download my bootloader.

### Supported Operational Systems (OS)

- Linux
- Windows
- OS X (most likely, but I could not tested)

### Supported functions

- Mass erase entire flash memory
- Write S19 file content into flash memory
- Dump data from memory

### Does not support

- Erase range
- Debugging
- Write bytes or ranges
- Define security bytes for connect device
- ... (many other features supported by PEMICRO prog08sz and other tools) 

## How get use gzml.py?

- Install Python, PIP, pySerial (different on Linux and Windows)
- Open terminal
- Execute gzml.py

## How to execute gzml.py?

On Linux call script starting with `./`, and need to be executable (`chmod +x gzml.py`). E.g. `./gzml.py -h`.
On Windows script can be called simple alone if PATH environment contains path of python engine. E.g. `gzml.py -h`.

`gzml.py -h`

Print out usual help about version, command line options, usual usage.

## What are main functions of gzml.py?

Main functions are
- Erase
- Download
- Dump

### Erase

`gzml.py -e`

Erase the entire Flash memory. If the security failed during connection phrase,
the command will only mass erase Flash 1 (0x8000-0xFFFF) including security bytes.
In this case, to erase Flash 2 (0x0462 - 0x7FFF) too, you need to execute the same
command again. Since security bytes were erased, security will pass with default
full 0xFF bytes, and Flash 2 will also erased.

### Download

`gzml.py -f hmdl.s19`

Download software into Flash memory. This command does not erase Flash even if it
would be needed. If you download into not erased memory, you will have verify errors.
 
### Dump

`gzml.py -d 0xFF00`

Dump memory content from address 0xFF00 - 0xFFFF. Default length of dump is 256.
You can increase/decrease it by -l command line parameter. See help for more details.

### More functions in one call

Script supports to call function sequence by one call, 
but the execution order will always be the following independently of order of command line parameters. 
- Erase
- Download
- Dump

`gzml.py -e -f hmdl.s19 -d 0xFF00`

Erases the entire Flash memory, downloads hmdl.s19 software and sump last two pages.

![Example CLI output](https://github.com/butyi/gzml.py/raw/master/gzmlpy_example.png)

## Baudrate

Fortunately pySerial supports some non-standard baud rates like 7200 and 14400 both on Linux and Windows.
Since baudrate can be calculated as fQuarz / 556 if PTB4 = Low, and fQuarz / 1112 if PTB4 = High, the 
script parameters are fQuarz in Hz and PTB4 state.
For example 
- 8 MHz and PTB4=L: `gzml.py -d 0xFF00 -q 8000000`
- 8 MHz and PTB4=H: `gzml.py -d 0xFF00 -q 8000000 -1`
- 5.2 MHz and PTB4=L: `gzml.py -d 0xFF00 -q 5200000`

Using defined quarz frequency and PTB4 state the script calculates
- Serial baud rate
- Delay length in uC code to have same timing for flash handling even with different fQuarz

If there is no close baudrate with the defined quarz, script will warn you and stop.
The folowing quarz frequencies can be covered by some available baud rate.
1 MHz, 1.3 MHz, 2 MHz, 2.6-2.7 MHz, 3.9-4 MHz, 5.2-5.4 MHz, 7.8-8.1 MHz

## Sleep

Since USB-Serial converters are much slower that motherboard built in serial interface,
some delay is needed for them to read back the necessary response bytes.
By default, no delay is applied. This is suitable for motherboard built in serial interfaces.
If you have loopback related errors, remember to this sleep parameter and try to increase.
I propose, first use 10ms by parameter `-s 10`. This was enough for my ATEN USB-Serial converter.
If still have problem, increase more. 20ms was enough for my FT231XS device.
My experience was, that 10ms does not slow down the download procedure. 20-30ms can already be felt.

## Hardware

To be HW interface easy and cheap, buy TTL USB-Serial interface from China.
I use FT232RL FTDI USB to TTL Serial Adapter Module for communication. This is supported by both Linux and Windows 10.
The mini step up power supply board is used to generate Vtst for IRQ pin.
With this, you just need some cable and that's it.

![GZ monitor interface circuit](https://github.com/butyi/gzml/raw/master/FT232RL_FTDI_USB_to_TTL_Serial_Adapter_Module_for_monitor_download_into_CEM35_CPU_with_MC68HC908GZ60.jpg)

My first CPU card circuit diagram (schematic) is visible here. 

![GZ monitor interface circuit](https://github.com/butyi/gzml/raw/master/homemat_cem35_cpu_0_sch.jpg)

More info is [here](http://butyi.hu/cem35).

## How to develop it Further?

If you only improve script features, just edit gzml.py and enjoy it.

If you want to improve uC side code too, compile uC code first by `asm8 loader.asm`.

## Was it tested?

Only main features was tested with some values.
If you find any bug, or do not like how it works, feel free to fix or modify it.

I have tested the followings on Linux (Ubuntu 16.04 LTS)
- Mass erase
- Program into area Flash1 (0x8000 - 0xFFFF)
- Program into area Flash2 (0x0980 - 0x7FFF)
- Dump from memory
- Motherboard mounted ttyS0 with default zero sleep
- USB Serial interface ttyUSB0 
  both [FT231XS](https://www.ftdichip.com/Support/Documents/DataSheets/Cables/DS_Chipi-X.pdf) with 20ms sleep and
  [ATEN UC232A1](https://www.aten.com/global/en/products/usb-&-thunderbolt/usb-converters/uc232a1/) with 10ms sleep

I have tested the followings on Windows 10
- Mass erase
- Program into area Flash1 (0x8000 - 0xFFFF)
- Program into area Flash2 (0x0980 - 0x7FFF)
- Dump from memory
- USB Serial interface [FT231XS](https://www.ftdichip.com/Support/Documents/DataSheets/Cables/DS_Chipi-X.pdf) with 20ms sleep 
 
## Files

- `asm8` Assembly compiler.
- `gz60.inc` Target specific definitions, mainly register.
- `loader.asm` Source code of target specific flash handler routines.
- `loader.lst` List file of compiled loader.asm. This is used by script to know start address of routines.
- `loader.s19` Compiled binary of target specific flash handler routines. This will be read by script and copied into RAM for execution. 
- `README.md` Getting started, documentation, example calls.
- `mem.dump` Memory dump to check if S19 read was correct. It is written when `-m` option is set.
- `gzml.py` The script itself.

## License

This is free. You can do anything you want with it.
While I am using Linux, I got so many support from free projects, I am happy if I can help for the community.

## Thanks

Thanks for [predecessor](https://github.com/jaromir-sukuba/bl08) and [bincopy](https://pypi.org/project/bincopy/).

## Keywords

Motorola, Freescale, NXP, MC68HC908GZ60, 68HC908GZ60, HC908GZ60, MC908GZ60, 908GZ60, HC908GZ48, HC908GZ32, HC908GZ, 908GZ

###### 2019 Janos Bencsik

