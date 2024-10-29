# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


@cocotb.test()
async def test_project(dut):
    # Set up a 100 KHz clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # Initial test setup
    dut.ui_in.value = 0b11110000  # Example: selecting a specific waveform and frequency
    dut.uio_in.value = 0
    dut._log.info("Reset completed and test parameters set.")

    # Wait for a few cycles to let outputs stabilize
    await ClockCycles(dut.clk, 100)

    # Monitor the I2S output signals
    prev_sck = dut.uo_out[0].value
    for _ in range(50):
        await RisingEdge(dut.clk)
        sck = dut.uo_out[0].value
        ws = dut.uo_out[1].value
        sd = dut.uo_out[2].value

        dut._log.info(f"sck: {sck}, ws: {ws}, sd: {sd}")

        # Check if the `sck` signal toggles
        assert sck != prev_sck, "sck did not toggle as expected."
        prev_sck = sck
