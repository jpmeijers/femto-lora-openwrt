/* RAM-only MT7620 receiver. No flash access. MIPS o32 callable from U-Boot.
 * Install through uncached alias 0xa3000000, execute at 0x83000000.
 * Header is little endian: magic 0x314d5446, byte count, zlib CRC32.
 * Payload goes to uncached RAM 0xa2000000, bounded to 16 MiB.
 */
.set noreorder
.set noat
.option pic0
.text
.globl _start

.macro rxbyte dest
.Lrx\@:
 lw $t0, 0x1c($s0)
 andi $t0, $t0, 1
 beq $t0, $zero, .Lrx\@
 nop
 lw \dest, 0($s0)
 andi \dest, \dest, 255
.endm

_start:
 addiu $sp, $sp, -40
 sw $ra, 36($sp)
 sw $s0, 0($sp)
 sw $s1, 4($sp)
 sw $s2, 8($sp)
 sw $s3, 12($sp)
 sw $s4, 16($sp)
 sw $s5, 20($sp)
 sw $s6, 24($sp)
 li $s0, 0xb0000c00
 la $a0, ready
 jal puts
 nop
 jal word
 nop
 li $t4, 0x314d5446
 bne $v0, $t4, fail
 nop
 jal word
 nop
 move $s2, $v0
 beq $s2, $zero, fail
 nop
 li $t4, 0x01000001
 sltu $t4, $s2, $t4
 beq $t4, $zero, fail
 nop
 jal word
 nop
 move $s5, $v0
 li $s1, 0xa2000000
 li $s3, -1
 move $s4, $s2
 li $s6, 0xedb88320
payload:
 rxbyte $v0
 sb $v0, 0($s1)
 addiu $s1, $s1, 1
 xor $s3, $s3, $v0
 li $t1, 8
bit:
 andi $t2, $s3, 1
 subu $t2, $zero, $t2
 and $t2, $t2, $s6
 srl $s3, $s3, 1
 xor $s3, $s3, $t2
 addiu $t1, $t1, -1
 bne $t1, $zero, bit
 nop
 addiu $s4, $s4, -1
 bne $s4, $zero, payload
 nop
 nor $s3, $s3, $zero
 bne $s3, $s5, fail
 nop
 la $a0, okay
 jal puts
 nop
 move $v0, $zero
 b done
 nop
fail:
 la $a0, bad
 jal puts
 nop
 li $v0, 1
done:
 lw $ra, 36($sp)
 lw $s0, 0($sp)
 lw $s1, 4($sp)
 lw $s2, 8($sp)
 lw $s3, 12($sp)
 lw $s4, 16($sp)
 lw $s5, 20($sp)
 lw $s6, 24($sp)
 jr $ra
 addiu $sp, $sp, 40

/* Read one LE word; rxbyte only clobbers t0 and its destination. */
word:
 move $t1, $zero
 move $t2, $zero
 li $t3, 32
wordbyte:
 rxbyte $v0
 sllv $v0, $v0, $t2
 or $t1, $t1, $v0
 addiu $t2, $t2, 8
 bne $t2, $t3, wordbyte
 nop
 jr $ra
 move $v0, $t1

puts:
 move $t1, $a0
putnext:
 lbu $t2, 0($t1)
 beq $t2, $zero, putdone
 nop
putwait:
 lw $t0, 0x1c($s0)
 andi $t0, $t0, 0x20
 beq $t0, $zero, putwait
 nop
 sw $t2, 4($s0)
 b putnext
 addiu $t1, $t1, 1
putdone:
 jr $ra
 nop

.section .rodata
ready: .asciz "\r\nFEMTO-READY\r\n"
okay: .asciz "\r\nFEMTO-OK\r\n"
bad: .asciz "\r\nFEMTO-BAD\r\n"
