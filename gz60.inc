;*******************************************************************************
;*           MC9S08GB60 FRAMEWORK INCLUDE FILE FOR ASM8 ASSEMBLER              *
;*******************************************************************************
; FREEWARE, Copyright (c) Janos Bencsik  <hc08@butyi.hu>
;*******************************************************************************

;                   #Uses     macros.inc
                    #Message  **********************
                    #Message  * Target: HC908GZ60  *
                    #Message  **********************

                    #HcsOff
                    #NoMMU                        ;MMU not available

_GZ_                def       60
FLL_FACTOR          def       256                 ;dummy to silence generic warning

;*******************************************************************************
;* Author: Janos Bencsik  <hc08@butyi.hu>
;*
;* Description: Register and bit name definitions for HC908GZ60
;*
;* Documentation: HC908GZ60 family Data Sheet for register and bit explanations
;* See CPU08 Reference Manual for explanation of equate files
;*
;* Assembler:  ASM8 by Tony G. Papadimitriou <tonyp@acm.org>
;*******************************************************************************

; **** Input/Output (I/O) Ports ************************************************

PTA                 def       $00,1               ;I/O port A data register
DDRA                def       $03,1               ;I/O port A data direction register
PTAPUE              def       $0D,1               ;I/O port A pullup enable controls

PTB                 def       $01,1               ;I/O port B data register
DDRB                def       $05,1               ;I/O port B data direction register

PTC                 def       $02,1               ;I/O port C data register
DDRC                def       $06,1               ;I/O port C data direction register
PTCPUE              def       $0E,1               ;I/O port C pullup enable controls

PTDD                def       $03,1               ;I/O port D data register
DDRD                def       $07,1               ;I/O port D data direction register
PTDPUE              def       $0F,1               ;I/O port D pullup enable controls

PTE                 def       $08,1               ;I/O port E data register
DDRE                def       $0C,1               ;I/O port E data direction register

PTF                 def       $440,1              ;I/O port F data register
DDRF                def       $444,1              ;I/O port F data direction register

PTG                 def       $441,1              ;I/O port G data register
DDRG                def       $445,1              ;I/O port G data direction register

; **** Serial Communications Interface (ESCI) ***********************

SCPSC               def       $09,1               ;SCI Prescaler

PDS2.               def       7                   ;Prescaler Divisor Select Bits
PDS1.               def       6                   ; 0 = Bypass this prescaler
PDS0.               def       5                   ; 1 = 2, ... , 7 = 8
PSSB4.              def       4                   ;Clock Insertion Select Bits
PSSB3.              def       3                   ;
PSSB2.              def       2                   ;
PSSB1.              def       1                   ;
PSSB0.              def       0                   ;

PDS2_               def       %10000000           ;Prescaler Divisor Select Bits
PDS1_               def       %01000000           ; 0 = Bypass this prescaler
PDS0_               def       %00100000           ; 1 = 2, ... , 7 = 8
PSSB4_              def       %00010000           ;Clock Insertion Select Bits
PSSB3_              def       %00001000           ;
PSSB2_              def       %00000100           ;
PSSB1_              def       %00000010           ;
PSSB0_              def       %00000001           ;

  ; Prescaler Divisor (PDS)
  ;  0 = Bypass this prescaler
  ;  1 = 2
  ;  2 = 3
  ;  3 = 4
  ;  4 = 5
  ;  5 = 6
  ;  6 = 7
  ;  7 = 8

  ; PSSB[4:3:2:1:0] Prescaler Divisor Fine Adjust (PDFA)
  ;   0 0 0 0 0 0/32 = 0
  ;   0 0 0 0 1 1/32 = 0.03125
  ;   0 0 0 1 0 2/32 = 0.0625
  ;   0 0 0 1 1 3/32 = 0.09375
  ;   0 0 1 0 0 4/32 = 0.125
  ;   0 0 1 0 1 5/32 = 0.15625
  ;   0 0 1 1 0 6/32 = 0.1875
  ;   0 0 1 1 1 7/32 = 0.21875
  ;   0 1 0 0 0 8/32 = 0.25
  ;   0 1 0 0 1 9/32 = 0.28125
  ;   0 1 0 1 0 10/32 = 0.3125
  ;   0 1 0 1 1 11/32 = 0.34375
  ;   0 1 1 0 0 12/32 = 0.375
  ;   0 1 1 0 1 13/32 = 0.40625
  ;   0 1 1 1 0 14/32 = 0.4375
  ;   0 1 1 1 1 15/32 = 0.46875
  ;   1 0 0 0 0 16/32 = 0.5
  ;   1 0 0 0 1 17/32 = 0.53125
  ;   1 0 0 1 0 18/32 = 0.5625
  ;   1 0 0 1 1 19/32 = 0.59375
  ;   1 0 1 0 0 20/32 = 0.625
  ;   1 0 1 0 1 21/32 = 0.65625
  ;   1 0 1 1 0 22/32 = 0.6875
  ;   1 0 1 1 1 23/32 = 0.71875
  ;   1 1 0 0 0 24/32 = 0.75
  ;   1 1 0 0 1 25/32 = 0.78125
  ;   1 1 0 1 0 26/32 = 0.8125
  ;   1 1 0 1 1 27/32 = 0.84375
  ;   1 1 1 0 0 28/32 = 0.875
  ;   1 1 1 0 1 29/32 = 0.90625
  ;   1 1 1 1 0 30/32 = 0.9375
  ;   1 1 1 1 1 31/32 = 0.96875

SCIACTL             def       $0A,1               ;SCI A. Control

AM1.                def       7                   ;Loop mode select bit
ALOST.              def       6                   ;Enable SCI bit
AM0.                def       5                   ;Transmit invertion bit
ACLK.               def       4                   ;Mode (character length) bit (0=8, 1=9)
AFIN.               def       3                   ;Wake-up condition bit
ARUN.               def       2                   ;Idle line type bit
AROVFL.             def       1                   ;Parity enable bit
ARD8.               def       0                   ;Parity bit (0=even, 1=odd)

AM1_                def       %10000000           ;Loop mode select bit
ALOST_              def       %01000000           ;Enable SCI bit
AM0_                def       %00100000           ;Transmit invertion bit
ACLK_               def       %00010000           ;Mode (character length) bit (0=8, 1=9)
AFIN_               def       %00001000           ;Wake-up condition bit
ARUN_               def       %00000100           ;Idle line type bit
AROVFL_             def       %00000010           ;Parity enable bit
ARD8_               def       %00000001           ;Parity bit (0=even, 1=odd)

SCIADAT             def       $0B,1               ;SCI Arbiter Data

SPCR                def       $10,1               ;SPI Control R.

SPRIE.              def       7                   ;SPI Receiver interrupt enable
DMAS.               def       6                   ;DMA select
SPMSTR.             def       5                   ;SPI master
CPOL.               def       4                   ;Clock polarity
CPHA.               def       3                   ;Clock phase
SPWOM.              def       2                   ;SPI wired-OR mode
SPE.                def       1                   ;SPI enable
SPTIE.              def       0                   ;SPI transmit interrupt enable

SPRIE_              def       %10000000           ;SPI Receiver interrupt enable
DMAS_               def       %01000000           ;DMA select
SPMSTR_             def       %00100000           ;SPI master
CPOL_               def       %00010000           ;Clock polarity
CPHA_               def       %00001000           ;Clock phase
SPWOM_              def       %00000100           ;SPI wired-OR mode
SPE_                def       %00000010           ;SPI enable
SPTIE_              def       %00000001           ;SPI transmit interrupt enable

; **** Interrupt Request Module (IRQ) ******************************************

; **** Keyboard Interrupt Module (KBI) *****************************************

; **** Serial Peripheral Interface (SPI) ***************************************

; **** Analog-to-Digital Converter Module (ATD) ********************************

; **** Inter-Integrated Circuit Module (IIC) ***********************************

; **** Timer/PWM Module 1 (TPM1) ***** TPM1 has 3 channels *********************
; **** Timer/PWM Module 2 (TPM2) ***** TPM2 has 5 channels *********************

;TPM1CNT             def       $31,2               ;TPM1 counter
;TPM1CNTH            def       $31,1               ;TPM1 counter (high half)
;TPM1CNTL            def       $32,1               ;TPM1 counter (low half)

; **** Internal Clock Generator Module (ICG) ***********************************

; **** System Integration Module (SIM) *****************************************
SRSR                def       $FE01,1               ;Reset Status Register (SRSR)
COPCTL              def       $FFFF,1               ;Computer Operates Properly Control

; **** Power Management and Control Module (PMC) *******************************

; **** Debug Module (DBG) ******************************************************

; **** Flash Module (FLASH) ****************************************************

; **** Flash non-volatile register images **************************************

; **** END OF ORIGINAL DEFINITIONS *********************************************

_HC908GZ60_         def       *                   ;Tells us this INCLUDE has been used

FLASH_PAGE_SIZE     def       128                 ;minimum that must be erased at once

          #if FLASH_PAGE_SIZE <> 128
                    #Error    FLASH_PAGE_SIZE should be fixed at 128
          #endif

FLASH_DATA_SIZE     def       0                   ;default: no runtime flash storage

VECTORS             def       $FFCC               ;start of fixed vectors
          #ifdef RVECTORS
VECTORS             set       RVECTORS
          #endif
          ;-------------------------------------- ;Vectors
                    #temp     VECTORS
Vtpm2ch5            next      :temp,2             ;TPM2 channel 5 vector
Vtpm2ch4            next      :temp,2             ;TPM2 channel 4 vector
Vtpm2ch3            next      :temp,2             ;TPM2 channel 3 vector
Vtpm2ch2            next      :temp,2             ;TPM2 channel 2 vector
Vcantx              next      :temp,2             ;CAN transmit vector
Vcanrx              next      :temp,2             ;CAN receive vector
Vcanerr             next      :temp,2             ;CAN error vector
Vcanwu              next      :temp,2             ;CAN wake up vector
Vtim                next      :temp,2             ;time base vector
Vadc                next      :temp,2             ;analog to digital conversion vector
Vkeyboard           next      :temp,2             ;keyboard vector
Vescitx             next      :temp,2             ;SCI transmit vector
Vescirx             next      :temp,2             ;SCI receive vector
Vescierr            next      :temp,2             ;SCI error vector
Vspitx              next      :temp,2             ;SPI transmit vector
Vspirx              next      :temp,2             ;SPI receive vector
Vtpm2ovf            next      :temp,2             ;TPM2 overflow vector
Vtpm2ch1            next      :temp,2             ;TPM2 channel 1 vector
Vtpm2ch0            next      :temp,2             ;TPM2 channel 0 vector
Vtpm1ovf            next      :temp,2             ;TPM1 overflow vector
Vtpm1ch1            next      :temp,2             ;TPM1 channel 1 vector
Vtpm1ch0            next      :temp,2             ;TPM1 channel 0 vector
Vpll                next      :temp,2             ;PLL vector
Virq                next      :temp,2             ;IRQ vector
Vswi                next      :temp,2             ;SWI vector
Vreset              next      :temp,2             ;reset vector

ROM                 def       $8000
ROM_END             def       $FDFF               ;end of all flash (before NV register and fixed vectors)

RAM                 def       $0040
RAM_END             def       $043F

XRAM                def       $0580
XRAM_END            def       $097F

FLASH_START         def       ROM
FLASH_END           def       ROM_END

SERIAL_NUMBER       def       $FFA0               ;start of optional S/N (FFA0-FFAD)

#ifndef MHZ||KHZ
HZ                  def       8000000
#endif
;*******************************************************************************
                    #VECTORS  VECTORS
                    #RAM      RAM
                    #XRAM     XRAM
                    #ROM      ROM

                    #MEMORY   ROM       ROM_END
                    #MEMORY   RAM       RAM_END
                    #MEMORY   XRAM      XRAM_END
                    #MEMORY   VECTORS   VECTORS|$00FF
