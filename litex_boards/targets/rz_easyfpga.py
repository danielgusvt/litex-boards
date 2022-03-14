#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2021 Alain Lou <alainzlou@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

import os
import argparse

from migen import *

from litex.build.io import DDROutput

from litex_boards.platforms import easyfpga

from litex.soc.cores.clock import CycloneIVPLL
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser
from litex.soc.cores.gpio import GPIOOut
from litex.soc.cores.bitbang import I2CMaster

from litedram.modules import MT48LC4M16
from litedram.phy import GENSDRPHY, HalfRateGENSDRPHY

kB = 1024

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq, sdram_rate="1:1"):
        self.rst = Signal()
        self.clock_domains.cd_sys = ClockDomain()
        if sdram_rate == "1:2":
            self.clock_domains.cd_sys2x    = ClockDomain()
            self.clock_domains.cd_sys2x_ps = ClockDomain(reset_less=True)
        else:
            self.clock_domains.cd_sys_ps = ClockDomain(reset_less=True)

        # # #

        # Clk / Rst
        clk50 = platform.request("clk50")
        rst_n  = platform.request("rst_n")

        # PLL
        self.submodules.pll = pll = CycloneIVPLL(speedgrade="-8")
        self.comb += pll.reset.eq(self.rst | ~rst_n)
        pll.register_clkin(clk50, 50e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        if sdram_rate == "1:2":
            pll.create_clkout(self.cd_sys2x,    2*sys_clk_freq)
            pll.create_clkout(self.cd_sys2x_ps, 2*sys_clk_freq, phase=270)  # Ideally 90° but needs to be increased.
        else:
            pll.create_clkout(self.cd_sys_ps, sys_clk_freq, phase=180)  # Ideally 90° but needs to be increased.

        # SDRAM clock
        sdram_clk = ClockSignal("sys2x_ps" if sdram_rate == "1:2" else "sys_ps")
        self.specials += DDROutput(1, 0, platform.request("sdram_clock"), sdram_clk)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, bios_flash_offset, sys_clk_freq=int(50e6), with_led_chaser=True, with_lcd_gpio=False, sdram_rate="1:1", **kwargs):
        platform = easyfpga.Platform()

        # Use external ROM since too large for Cyclone IV EP4CE6
        kwargs["integrated_rom_size"]  = 0
        kwargs["integrated_sram_size"] = 0x1000

        # Set reset address
        #kwargs["cpu_reset_address"] = self.mem_map["spiflash"] + bios_flash_offset

        # Limit internal rom and sram size
 #       kwargs["integrated_rom_size"]  = 0x6200
#        kwargs["integrated_sram_size"] = 0x1000

        # Can only support minimal variant of vexriscv
        if kwargs.get("cpu_type", "vexriscv") == "vexriscv":
            kwargs["cpu_variant"] = "minimal"

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq,
            ident = "LiteX SoC on RZ-EasyFPGA",
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq, sdram_rate=sdram_rate)

        # SDR SDRAM --------------------------------------------------------------------------------
        if not self.integrated_main_ram_size:
            sdrphy_cls = HalfRateGENSDRPHY if sdram_rate == "1:2" else GENSDRPHY
            self.submodules.sdrphy = sdrphy_cls(platform.request("sdram"), sys_clk_freq)
            self.add_sdram("sdram",
                phy           = self.sdrphy,
                module        = MT48LC4M16(sys_clk_freq, sdram_rate), # Hynix HY57V641620FTP-7
                l2_cache_size = 0
            )

        # SPI Flash --------------------------------------------------------------------------------
        from litespi.modules import W25Q16JV
        from litespi.opcodes import SpiNorFlashOpCodes as Codes
        self.add_spi_flash(mode="1x", module=W25Q16JV(Codes.READ_1_1_1), with_master=False)

        # Add ROM linker region --------------------------------------------------------------------
        self.bus.add_region("rom", SoCRegion(
            origin = self.bus.regions["spiflash"].origin + bios_flash_offset,
            size   = 32*kB,
            linker = True)
        )

        # Leds -------------------------------------------------------------------------------------
        if with_led_chaser:
            self.submodules.leds = LedChaser(
                pads         = platform.request_all("user_led"),
                sys_clk_freq = sys_clk_freq)

        # GPIOOut for LCD --------------------------------------------------------------------------
        if with_lcd_gpio:
            self.submodules.gpio = GPIOOut(platform.request("lcd_display"))

#        self.submodules.i2c = I2CMaster(platform.request("temp_i2c"))


# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on RZ-EasyFPGA")
    parser.add_argument("--build",        action="store_true", help="Build bitstream.")
    parser.add_argument("--load",         action="store_true", help="Load bitstream.")
    parser.add_argument("--sys-clk-freq", default=50e6,        help="System clock frequency.")
    parser.add_argument("--sdram-rate",   default="1:1",       help="SDRAM Rate (1:1 Full Rate or 1:2 Half Rate).")
    parser.add_argument("--bios-flash-offset", default=0x20000,     help="BIOS offset in SPI Flash (default: 0x20000)")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(
        bios_flash_offset = args.bios_flash_offset,
        sys_clk_freq = int(float(args.sys_clk_freq)),
        sdram_rate   = args.sdram_rate,
        **soc_core_argdict(args)
    )
    builder = Builder(soc, **builder_argdict(args))
    builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".sof"))

if __name__ == "__main__":
    main()
