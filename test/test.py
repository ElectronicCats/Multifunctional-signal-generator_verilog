import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


@cocotb.test()
async def test_project(dut):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # Set up sine wave with C4 frequency
    dut.ui_in.value = 0b10000000  # Wave select bits (7:6) for sine; bits (5:0) for frequency
    dut.uio_in.value = 0          # Clear ADSR inputs initially

    # Configure ADSR with enhanced settings
    await set_adsr(dut, attack=20, decay=10, sustain=50, release=30)

    # Allow stabilization time
    await ClockCycles(dut.clk, 50)

    # Verify waveform with ADSR modulation on `sd`
    await verify_adsr_waveform(dut, expected_wave="sine")


async def set_adsr(dut, attack, decay, sustain, release):
    """Set ADSR envelope parameters."""
    dut._log.info(f"Setting ADSR: Attack={attack}, Decay={decay}, Sustain={sustain}, Release={release}")

    # Adjust ADSR configuration here by setting `uio_in`
    dut.uio_in.value = attack & 0xFF
    await ClockCycles(dut.clk, 10)
    dut.uio_in.value = decay & 0xFF
    await ClockCycles(dut.clk, 10)
    dut.uio_in.value = sustain & 0xFF
    await ClockCycles(dut.clk, 10)
    dut.uio_in.value = release & 0xFF
    await ClockCycles(dut.clk, 10)

    dut._log.info("ADSR parameters set.")


async def verify_adsr_waveform(dut, expected_wave):
    """Check for ADSR-modulated waveform output on `sd`."""
    dut._log.info(f"Verifying {expected_wave} waveform with ADSR modulation on `sd`.")

    prev_sd = dut.uo_out[2].value  # Start monitoring `sd`
    await ClockCycles(dut.clk, 5)  # Small delay to allow ADSR to take effect

    for i in range(100):
        await RisingEdge(dut.clk)
        current_sd = dut.uo_out[2].value
        dut._log.info(f"Cycle {i}: `sd` = {current_sd}")

        # Check for change indicating modulation
        if current_sd != prev_sd:
            dut._log.info("ADSR modulation detected on `sd`.")
            return  # Success if modulation detected

        prev_sd = current_sd

    # If no modulation is detected, assert failure
    assert False, "Expected ADSR modulation but saw no change in `sd`."
