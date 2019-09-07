; -----------------------------------------------------------------------------
;           FLASH ERASE AND PROGRAM ROUTINES INTO RAM FOR MC68HC908GZ60
; -----------------------------------------------------------------------------
; Written by Janos Bencsik, https://github.com/butyi/, V0.00 2019.06.29.
; mass_erase
;   Erases the whole Flash memory. It can erase both Flash 1 and Flash 2 by
;   register parameters.
;   NOTE! if security failed security bytes can only be cleared if erase
;   address is address of FL1BPR. This took 2 days of by life. [angry smile]
; write_flash
;   Writes 64 or less bytes from RAM buffer into selected Flash row.
;   It can write both Flash 1 and Flash 2 by register parameters. 
;   It is assumed that memory was erased before by mass erase. 
;   When data byte is 0xFF, it is not written. By this way forbidden 
;   address ranges can be skipped. 
;
; Parameters: see below
; Designed for: 
; - Linux side host software (gzml.c)
; - 5.2Mhz quarz => 2.6Mhz fbus (ideal would be 5.333Mhz for 
;   monitor baud rate 9600, but 5.2 is still acceptable).
; - HC908GZ60, but easy to modify to be sufficient also for
;   HC908GZ family. (like HC908GZ8, HC908GZ16, HC908GZ32, HC908GZ48)
; - Free ASM8 Macro Assembler (www.aspisys.com/asm8man.htm)
; History:
; - VXX.XX XXXX.XX.XX: ...
; -----------------------------------------------------------------------------

#Uses gz60.inc

; Parameters:
        org     $80
;Data buffer to be filled up with row data to be written before call write_flash
;First byte is the first in the row always independently from address parameter,
;  this means, if address is 1, data for address 1 shall be in second byte (*0x0081)
;Used only by write_flash
data    rmb     64

;Address of flash control register (address of once FL1CR or FL2CR)
;Used by both mass_erase and write_flash
p_flcr  rmb     2

;Address of flash block protection register (address of once FL1BPR or FL2BPR)
;Used by both mass_erase and write_flash
p_flbpr rmb     2

;Start address to be programmed or erased from
;Used by both mass_erase and write_flash
address rmb     2

;Return value of routines. Zero menas no error.
;Used by both mass_erase and write_flash
ret     rmb     1

;Length (number of bytes) to be programmed
;Used only by write_flash
len     rmb     1

; Subroutines:
        org     $100
mass_erase

        ;!!!!!! BEGIN OF ERASE !!!!!!!

        ;set MASS and ERASE bits
        ldhx    p_flcr
        lda     #$06
        sta     ,x

        ;read flbpr
        ldhx    p_flbpr
        lda     ,x

        ;write something into address
        ldhx    address
        sta     ,x

        ;wait t_NVS (10 us)
        ldx     #2
        bsr     wait

        ;set HVEN bit
        ldhx    p_flcr
        lda     #$0E  ;$08|$04|$02
        sta     ,x

        ;wait t_ERASE (4 ms for mass erase = 4*200*5us)
        lda     #4
e_wait        
        ldx     #200
        bsr     wait
        dbnza   e_wait

        ;clear ERASE and MASS bit
        ldhx    p_flcr
        lda     #$08
        sta     ,x

        ;wait t_NVH  (100us for mass erase)
        ldx     #20
        bsr     wait

        ;clear HVEN bit
        ldhx    p_flcr
        clra
        sta     ,x

        ;wait t_RCV  (1 us)
        ldx     #1
        bsr     wait
        
        ; !!!!!! END OF ERASE !!!!!

        ;show no error occured, erase finished
        clr     ret
           
        ;Jump back from RAM into monitor
        swi


        ;Wait defined time (number of applied nop instructions are adjusted dinamically by changing branch offset of dbnzx)
wait
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        nop                     ;1 cyc
        dbnzx   wait            ;3 cyc
branch_offset
        rts


write_flash
        ;check length 
        lda     len
        beq     write_error     ;jump to end in case of len is zero
        cmp     #$40
        bhi     write_error     ;jump to end in case of len is greather than row size ($40 = 64)

        ;check address range if it is inside a row
        lda     address+1       ;low byte of address
        and     #$3F            ;use only position in row 
        add     len
        deca                    ;-1
        and     #$C0
        bne     write_error     ;jump to end in case of row overflow
        
        ;Block protection turn off  (*p_flbpr=$FF)
        ;ldhx    p_flbpr
        ;lda     #255
        ;sta     ,x

        ; !!!!!! BEGIN OF WRITE !!!!!

        ;Set the PGM bit in the FLASH control register (FLxCR).
        ldhx    p_flcr
        lda     #$01
        sta     ,x

        ;Read the FLASH block protect register.
        ldhx    p_flbpr
        lda     ,x

        ;Write to any FLASH address within the row address range desired with any data.
        ldhx    address
        sta     ,x

        ;Wait for a time, t_NVS (10 us)
        ldx     #2
        bsr     wait

        ;Set the HVEN bit.
        ldhx    p_flcr
        lda     #$09
        sta     ,x

        ;Wait for a time, t_PGS. (5 us)
        ldx     #1
        bsr     wait

datacycle
        ;Write one data byte to a FLASH address to be programmed.
        lda     address+1
        and     #$3F
        tax
        clrh
        lda     data,x          ;load byte from RAM buffer (data[address&0x3F])
        cmp     #$FF
        beq     nextdata        ;Since was erase before $FF can be skipped
        ldhx    address
        sta     ,x              ;write data byte into memory pointed by address

        ;Wait for a time, t_PROG. (40 us)
        ldx     #8
        bsr     wait
nextdata
        inc     address+1       ;increase only low byte
        dec     len
        lda     len
        bne     datacycle       ;while 0<len, do loop again

        ;Clear the PGM bit.
        ldhx    p_flcr
        lda     #$08
        sta     ,x

        ;Wait for a time, t_NVH. (5us)
        ldx     #1
        bsr     wait

        ;Clear the HVEN bit.
        ldhx    p_flcr
        clra
        sta     ,x

        ;Wait for a time, t_RCV. (1us)
        ldx     #1
        bsr     wait

        ; !!!!!! END OF WRITE !!!!!

        ;Block protection turn on  (*p_flbpr#$00)
        ;ldhx    p_flbpr
        ;clra
        ;sta     ,x
        
        ;Jump back from RAM into monitor
        clr     ret   ;show no error
        swi     

write_error        
        mov     #$01,ret   ;show error
        ;Jump back from RAM into monitor
        swi     


