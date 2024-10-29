# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test project behavior")

    # Set the input values you want to test for the desired wave type and frequency
    # Example: Set a frequency selection and wave type
    dut.ui_in.value = 0b11000000 # Set freq_select and wave_select to known values
    await ClockCycles(dut.clk, 5)

    # Check if uo_out[2:0] is producing I2S signals (sck, ws, sd)
    # This test assumes that sck (bit 0) toggles, ws (bit 1) toggles slowly, and sd (bit 2) is serial data.
    
    # Check sck toggling
    prev_sck = dut.uo_out[0].value
    await ClockCycles(dut.clk, 2)
    assert dut.uo_out[0].value != prev_sck, "sck did not toggle as expected."

    # Check ws toggling (expect slower toggle rate than sck)
    prev_ws = dut.uo_out[1].value
    await ClockCycles(dut.clk, 16)
    assert dut.uo_out[1].value != prev_ws, "ws did not toggle as expected."

    dut._log.info("Initial I2S signal toggling test passed")

    # Additional tests can be added to check data patterns on `sd`, depending on the expected output pattern
