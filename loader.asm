;*******************************************************************************
; FLASH ERASE AND PROGRAM ROUTINES INTO RAM FOR MC68HC908GZ60
;*******************************************************************************
; Written by Janos Bencsik, https://github.com/butyi/, V0.00 2019.06.29.
;
; MassErase
; ---------
; Erases the whole Flash memory. It can erase both Flash 1 and Flash 2 by
; register parameters.
; NOTE! If security failed, security bytes can only be cleared if erase
; address is address of FL1BPR. This took 2 days of by life. [angry smile]
;
; WriteFlash
; ----------
; Writes 64 or fewer bytes from RAM buffer into selected Flash row.
; It can write both Flash 1 and Flash 2 by register parameters.
; It is assumed that memory was erased before by mass erase.
; When data byte is 0xFF, it is not written. This way forbidden
; address ranges can be skipped.
;
; Parameters: see below
; Designed for:
; - Linux side host software (gzml.c)
; - 5.2Mhz quarz => 2.6Mhz fbus (ideal would be 5.333Mhz for
; monitor baud rate 9600, but 5.2 is still acceptable).
; - HC908GZ60, but easy to modify to be sufficient also for whole
; HC908GZ family. (like HC908GZ8, HC908GZ16, HC908GZ32, HC908GZ48)
; - Free ASM8 Macro Assembler (www.aspisys.com/asm8.htm)
; History:
; - VXX.XX XXXX.XX.XX: ...
;*******************************************************************************

                    #Uses     gz60.inc

;*******************************************************************************
                    #RAM      $80                 ; Parameters:
;*******************************************************************************

data                rmb       64                  ; Data buffer to be filled up
                                                  ; with row data to be written
                                                  ; before call WriteFlash
                                                  ; First byte is the first in
                                                  ; the row always independently
                                                  ; from address parameter, this
                                                  ; means, if address is 1, data
                                                  ; for address 1 shall be in
                                                  ; second byte (*0x0081)
                                                  ; Used only by WriteFlash

p_flcr              rmb       2                   ; Address of flash control
                                                  ; register (address of once
                                                  ; FL1CR or FL2CR)
                                                  ; Used by both MassErase and
                                                  ; WriteFlash

p_flbpr             rmb       2                   ; Address of flash block
                                                  ; protection register (address
                                                  ; of once FL1BPR or FL2BPR)
                                                  ; Used by both MassErase and
                                                  ; WriteFlash

address             rmb       2                   ; Start address to be programmed
                                                  ; or erased from
                                                  ; Used by both MassErase and
                                                  ; WriteFlash

ret                 rmb       1                   ; Return value of routines.
                                                  ; Zero menas no error.
                                                  ; Used by both MassErase and
                                                  ; WriteFlash

len                 rmb       1                   ; Length (number of bytes) to
                                                  ; be programmed
                                                  ; Used only by WriteFlash

;*******************************************************************************
                    #ROM      $100                ; Subroutines:
;*******************************************************************************

MassErase           proc
          ;--------------------------------------
          ; !!!!!! BEGIN OF ERASE !!!!!!!
          ;--------------------------------------
                    ldhx      p_flcr
                    lda       #$06
                    sta       ,x
          ;-------------------------------------- ; read flbpr
                    ldhx      p_flbpr
                    lda       ,x
          ;-------------------------------------- ; write something into address
                    ldhx      address
                    sta       ,x
                    bsr       Delay2              ; wait t_NVS (10 us)
          ;-------------------------------------- ; set HVEN bit
                    ldhx      p_flcr
                    lda       #$0E                ; $08|$04|$02
                    sta       ,x
          ;-------------------------------------- ; wait t_ERASE (4 ms for mass erase = 4*200*5us)
                    lda       #4
_@@                 ldx       #200
                    bsr       Delay
                    dbnza     _@@
          ;--------------------------------------
                    ldhx      p_flcr
                    lda       #$08
                    sta       ,x
          ;-------------------------------------- ; wait t_NVH  (100us for mass erase)
                    ldx       #20
                    bsr       Delay
          ;-------------------------------------- ; clear HVEN bit
                    ldhx      p_flcr
                    clr       ,x
                    bsr       Delay1              ; wait t_RCV  (1 us)
          ;--------------------------------------
          ; !!!!!! END OF ERASE !!!!!
          ;--------------------------------------
                    clr       ret                 ; show no error occured, erase finished
                    swi                           ; Jump back from RAM into monitor

;*******************************************************************************

Delay2              proc
                    bsr       Delay1
;                   bra       Delay1

;*******************************************************************************

Delay1              proc
                    pshx
                    ldx       #1
                    bsr       Delay
                    pulx
                    rts

;*******************************************************************************
; Wait defined time (number of applied nop instructions are adjusted dynamically by changing branch offset of dbnzx)
                              #Cycles 4           ;(4 for BSR)
Delay               proc
Loop@@              nop:20
                    dbnzx     Loop@@
                    rts

                    #Hint     Delay cycles: {:cycles}

;*******************************************************************************

WriteFlash          proc
          ;-------------------------------------- ; check length
                    lda       len
                    beq       Fail@@              ; jump to end in case of zero len
                    cmpa      #$40
                    bhi       Fail@@              ; jump to end in case of len greater than row size ($40 = 64)
          ;-------------------------------------- ; check address range if it is inside a row
                    lda       address+1           ; low byte of address
                    and       #$3F                ; use only position in row
                    add       len
                    deca                          ; -1
                    and       #$C0
                    bne       Fail@@              ; jump to end in case of row overflow
          ;-------------------------------------- ; Block protection turn off  (*p_flbpr=$FF)
;                   ldhx      p_flbpr
;                   lda       #255
;                   sta       ,x
          ;--------------------------------------
          ; !!!!!! BEGIN OF WRITE !!!!!
          ;-------------------------------------- ; Set the PGM bit in the FLASH control register (FLxCR)
                    ldhx      p_flcr
                    lda       #$01
                    sta       ,x
          ;-------------------------------------- ; Read the FLASH block protect register.
                    ldhx      p_flbpr
                    lda       ,x
          ;--------------------------------------
          ; Write to any FLASH address within the row address
          ; range desired with any data.
          ;--------------------------------------
                    ldhx      address
                    sta       ,x
                    bsr       Delay2              ; Wait for a time, t_NVS (10 us)
          ;-------------------------------------- ; Set the HVEN bit.
                    ldhx      p_flcr
                    lda       #$09
                    sta       ,x
                    bsr       Delay1              ; Wait for a time, t_PGS. (5 us)
          ;--------------------------------------
          ; Write one data byte to a FLASH address to be programmed.
          ;--------------------------------------
Loop@@              lda       address+1
                    and       #$3F
                    tax
                    clrh
                    lda       data,x              ; load byte from RAM buffer (data[address&0x3F])
                    cbeqa     #$FF,Cont@@         ; Since was erase before $FF can be skipped
                    ldhx      address
                    sta       ,x                  ; write data byte into memory pointed to by address
          ;-------------------------------------- ; Wait for a time, t_PROG (40 us)
                    ldx       #8
                    bsr       Delay
          ;--------------------------------------
Cont@@              inc       address+1           ; increase only low byte
                    dbnz      len,Loop@@          ; while 0<len, do loop again
          ;-------------------------------------- ; Clear the PGM bit.
                    ldhx      p_flcr
                    lda       #$08
                    sta       ,x
                    bsr       Delay1              ; Wait for a time, t_NVH (5us)
          ;-------------------------------------- ; Clear the HVEN bit
                    ldhx      p_flcr
                    clr       ,x
                    bsr       Delay1              ; Wait for a time, t_RCV (1us)
          ;--------------------------------------
          ; !!!!!! END OF WRITE !!!!!
          ;-------------------------------------- ; Block protection turn on  (*p_flbpr#$00)
;                   ldhx      p_flbpr
;                   clr       ,x
          ;-------------------------------------- ; Jump back from RAM into monitor
                    clr       ret                 ; show no error
                    swi
          ;-------------------------------------- ; Jump back from RAM into monitor
Fail@@              mov       #$01,ret            ; show error
                    swi
