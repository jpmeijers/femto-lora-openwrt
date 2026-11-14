ENTRY(_start)
SECTIONS {
 . = 0x83000000;
 .text : { *(.text*) *(.rodata*) }
 /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.gnu.attributes) *(.comment) *(.note*) }
}
