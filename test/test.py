# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


@cocotb.test()
async def test_wave_output(dut):
    # Set up a 100 KHz clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # Test parameters
    wave_types = {
        0b00: "triangular",
        0b01: "sawtooth",
        0b10: "square",
        0b11: "sine"
    }
    frequencies = [0b000000, 0b000001, 0b000010]  # Lower 3 frequency settings for brevity
    adsr_params = {
        "attack": 50,
        "decay": 30,
        "sustain": 100,
        "release": 40
    }

    # Set ADSR parameters
    dut.uio_in[0].value = 1  # Assume these set values incrementally; can be adjusted based on encoder behavior
    dut.uio_in[1].value = 1
    dut.uio_in[2].value = 1
    dut.uio_in[3].value = 1
    await ClockCycles(dut.clk, 10)

    # Go through each waveform type and frequency setting
    for wave_code, wave_name in wave_types.items():
        for freq in frequencies:
            dut.ui_in.value = (wave_code << 6) | freq

            dut._log.info(f"Testing wave: {wave_name}, freq: {freq}, ADSR: {adsr_params}")

            # Wait for 100 clock cycles to observe the output
            await ClockCycles(dut.clk, 100)

            # Capture the output
            output_values = []
            for _ in range(20):  # Collect samples
                await RisingEdge(dut.clk)
                output_values.append(dut.uo_out.value.integer)

            # Example checks (extend based on requirements):
            # 1. Check if output amplitude is modulated by ADSR.
            # 2. Confirm frequency of toggling matches expected frequency setting.
            # 3. Confirm waveform shape (can be done manually with visual inspection of `tb.vcd`).

            dut._log.info(f"Output values for {wave_name} at freq {freq}: {output_values}")

            # Simple example assertion for amplitude check:
            max_amplitude = max(output_values)
            assert max_amplitude > 0, f"Expected modulated output for {wave_name}, but got zero amplitude."

            # Further assertions can be added based on specific expected values per wave type and frequency.

    dut._log.info("Wave output test completed.")
