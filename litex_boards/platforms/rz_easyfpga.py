#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2021 Alain Lou <alainzlou@gmail.com>
# Copyright (c) 2022 Daniel Vásquez <danielgusvt@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

from litex.build.generic_platform import *
from litex.build.altera import AlteraPlatform
from litex.build.altera.programmer import USBBlaster

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst
    ("clk50", 0, Pins("23"), IOStandard("3.3-V LVTTL")),
    ("rst_n",  0, Pins("25"), IOStandard("3.3-V LVTTL")),

    # Leds
    ("user_led", 0, Pins("84"), IOStandard("3.3-V LVTTL")),
    ("user_led", 1, Pins("85"), IOStandard("3.3-V LVTTL")),
    ("user_led", 2, Pins("86"), IOStandard("3.3-V LVTTL")),
    ("user_led", 3, Pins("87"), IOStandard("3.3-V LVTTL")),

    # DIP switches shared with buttons
    ("key", 0, Pins("88"),  IOStandard("3.3-V LVTTL")),
    ("key", 1, Pins("89"),  IOStandard("3.3-V LVTTL")),
    ("key", 2, Pins("90"),  IOStandard("3.3-V LVTTL")),
    ("key", 3, Pins("91"),  IOStandard("3.3-V LVTTL")),

    # Passive buzzer
    ("buzzer", 0, Pins("110"), IOStandard("3.3-V LVTTL")),

    # LM75A temperature sensor (I2C)
    ("temp_i2c", 0,
        Subsignal("scl", Pins("112")),
        Subsignal("sda", Pins("113")),
        IOStandard("3.3-V LVTTL")
    ),

    # AT24C08 EEPROM (I2C)
    ("eeprom_i2c", 0,
        Subsignal("scl", Pins("99")),
        Subsignal("sda", Pins("98")),
        IOStandard("3.3-V LVTTL")
    ),

    # W25Q16JV SPI Flash, IO2 and IO3 pins are hardwired to 3v3 so we cannot use QSPI mode.
    ("spiflash", 0,
        Subsignal("cs_n", Pins("8")),
        Subsignal("clk", Pins("12")),
        Subsignal("mosi", Pins("6")),
        Subsignal("miso", Pins("13")),
        IOStandard("3.3-V LVTTL"),
    ),

    # Serial - using DB9 connector through SP3232EEN
    ("serial", 0,
        Subsignal("tx", Pins("114")),
        Subsignal("rx", Pins("119")),
        IOStandard("3.3-V LVTTL")
    ),

    # VGA
    ("vga", 0,
        Subsignal("hsync", Pins("101")),
        Subsignal("vsync", Pins("103")),
        Subsignal("r", Pins("106")),
        Subsignal("g", Pins("105")),
        Subsignal("b", Pins("104")),
        IOStandard("3.3-V LVTTL"),
    ),

    # LCD display (HD44780 compatible)
    ("lcd_display", 0,
        Subsignal("data", Pins("142 1 144 3 2 10 7 11")),
        Subsignal("rs",   Pins("141")),
        Subsignal("rw",   Pins("138")),
        Subsignal("e",    Pins("143")),
        # Board provides 5V to display power pins, but it works fine with 3V3 on logic pins.
        IOStandard("3.3-V LVTTL")
    ),

    # 7 segment display
    ("segled", 0,
        Subsignal("ca",     Pins("128")),
        Subsignal("cb",     Pins("121")),
        Subsignal("cc",     Pins("125")),
        Subsignal("cd",     Pins("129")),
        Subsignal("ce",     Pins("132")),
        Subsignal("cf",     Pins("126")),
        Subsignal("cg",     Pins("124")),
        Subsignal("dp",     Pins("127")),
        Subsignal("digits", Pins("133 135 136 137")),
        IOStandard("3.3-V LVTTL")
    ),

    # PS/2
    ("ps2", 0,
        Subsignal("clk", Pins("119")),
        Subsignal("data", Pins("120")),
        IOStandard("3.3-V LVTTL")
    ),

    # IrDA receiver
    ("irda", 0,
        Subsignal("rxd", Pins("100")),
        IOStandard("3.3-V LVTTL")
    ),

    # GPIO
    # There are only 2 free gpio pins, the rest of the pins in the headers
    # are shared with the other peripherals
    ("gpio", 0, Pins(
        "24 111"),
        IOStandard("3.3-V LVTTL")
    ),

    # Hynix HY57V641620FTP-7 SDRAM
    ("sdram_clock", 0, Pins("43"), IOStandard("3.3-V LVTTL")),
    ("sdram", 0,
        Subsignal("a", Pins(
            "76 77 80 83 68 67 66 65",
            "64 60 75 59")),
        Subsignal("ba",    Pins("73 74")),
        Subsignal("cs_n",  Pins("72")),
        Subsignal("cke",   Pins("58")),
        Subsignal("ras_n", Pins("71")),
        Subsignal("cas_n", Pins("70")),
        Subsignal("we_n",  Pins("69")),
        Subsignal("dq", Pins(
            "28 30 31 32 33 34 38 39",
            "54 53 52 51 50 49 46 44")),
        Subsignal("dm", Pins("42 55")),
        IOStandard("3.3-V LVTTL")
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(AlteraPlatform):
    default_clk_name   = "clk50"
    default_clk_period = 1e9/50e6

    def __init__(self, toolchain="quartus"):
        AlteraPlatform.__init__(self, "EP4CE6E22C8", _io, toolchain=toolchain)
        self.add_platform_command("set_global_assignment -name FAMILY \"Cyclone IV E\"")
        self.add_platform_command("set_global_assignment -name RESERVE_DATA0_AFTER_CONFIGURATION \"USE AS REGULAR IO\"")
        self.add_platform_command("set_global_assignment -name RESERVE_DATA1_AFTER_CONFIGURATION \"USE AS REGULAR IO\"")
        self.add_platform_command("set_global_assignment -name RESERVE_DCLK_AFTER_CONFIGURATION \"USE AS REGULAR IO\"")
        self.add_platform_command("set_global_assignment -name CYCLONEII_RESERVE_NCEO_AFTER_CONFIGURATION \"USE AS REGULAR IO\"")
        self.add_platform_command("set_global_assignment -name RESERVE_FLASH_NCE_AFTER_CONFIGURATION \"USE AS REGULAR IO\"")
        self.add_platform_command("set_global_assignment -name ENABLE_BOOT_SEL_PIN ON")
        self.add_platform_command("set_global_assignment -name ENABLE_CONFIGURATION_PINS ON")

    def create_programmer(self):
        return USBBlaster()

    def do_finalize(self, fragment):
        AlteraPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk50", loose=True), 1e9/50e6)
