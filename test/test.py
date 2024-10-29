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

    # Set the test wave and frequency (e.g., sine wave, frequency C4)
    dut.ui_in.value = 0b10000000  # Select sine wave (bits 7:6) and frequency C4 (bits 5:0)
    dut.uio_in.value = 0          # Clear ADSR encoder inputs
    dut._log.info("Reset completed and test parameters set.")

    # Configure ADSR values via uio_in inputs (e.g., set attack, decay, sustain, release)
    # Adjust as needed based on ADSR encoder inputs
    await set_adsr(dut, attack=20, decay=10, sustain=50, release=30)

    # Allow some time for the waveform to stabilize with ADSR modulation
    await ClockCycles(dut.clk, 100)

    # Observe the I2S output and check modulation
    prev_amplitude = dut.uo_out[2].value  # Start monitoring from sd (I2S serial data)
    await verify_adsr_waveform(dut, expected_wave="sine")


async def set_adsr(dut, attack, decay, sustain, release):
    """Configure ADSR parameters by simulating encoder inputs."""
    # Set the values in sequence for testing purposes; adjust if necessary
    dut._log.info(f"Setting ADSR parameters: Attack={attack}, Decay={decay}, Sustain={sustain}, Release={release}")
    # Encode these values directly or toggle inputs if using rotary encoders in design
    # For simplicity, we'll assume direct assignment is possible
    dut.uio_in.value = attack & 0xFF  # For example, setting attack value
    await ClockCycles(dut.clk, 10)
    dut.uio_in.value = decay & 0xFF
    await ClockCycles(dut.clk, 10)
    dut.uio_in.value = sustain & 0xFF
    await ClockCycles(dut.clk, 10)
    dut.uio_in.value = release & 0xFF
    await ClockCycles(dut.clk, 10)


async def verify_adsr_waveform(dut, expected_wave):
    """Monitor the I2S serial data (sd) for ADSR-modulated waveform."""
    dut._log.info(f"Verifying {expected_wave} waveform with ADSR modulation")

    # Initial previous amplitude to detect changes
    prev_sd = dut.uo_out[2].value  # Monitor I2S serial data pin

    # Check amplitude modulation in phases
    for _ in range(100):  # Adjust range based on modulation times
        await RisingEdge(dut.clk)
        current_sd = dut.uo_out[2].value
        dut._log.info(f"I2S sd output (modulated): {current_sd}")

        # You can add assertions or comparisons to validate the waveform pattern
        assert current_sd != prev_sd, "Expected ADSR modulation but saw no change in `sd`."
        prev_sd = current_sd  # Update for the next comparison
