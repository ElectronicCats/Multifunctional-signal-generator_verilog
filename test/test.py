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
    dut.ui_in.value = 0b10000000  # Select sine wave
    dut.uio_in.value = 0          # Initialize ADSR parameters

    # Configure ADSR envelope
    await set_adsr(dut, attack=20, decay=10, sustain=50, release=30)

    # Small delay for stabilization
    await ClockCycles(dut.clk, 50)

    # Verify ADSR impact on waveform
    await verify_adsr_waveform(dut, expected_wave="sine")


async def set_adsr(dut, attack, decay, sustain, release):
    """Configure the ADSR envelope parameters."""
    dut._log.info(f"Setting ADSR: Attack={attack}, Decay={decay}, Sustain={sustain}, Release={release}")

    # Set ADSR by modifying `uio_in` bits
    dut.uio_in.value = attack
    await ClockCycles(dut.clk, 10)
    dut.uio_in.value = decay
    await ClockCycles(dut.clk, 10)
    dut.uio_in.value = sustain
    await ClockCycles(dut.clk, 10)
    dut.uio_in.value = release
    await ClockCycles(dut.clk, 10)

    dut._log.info("ADSR parameters applied.")


async def verify_adsr_waveform(dut, expected_wave):
    """Verify ADSR-modulated waveform on `sd`."""
    dut._log.info(f"Checking for ADSR-modulated {expected_wave} waveform on `sd`.")

    prev_sd = dut.uo_out[2].value
    prev_amplitude = dut.adsr_amplitude.value  # Monitor amplitude from ADSR

    await ClockCycles(dut.clk, 5)

    for i in range(200):  # Extended cycle count for clearer observation
        await RisingEdge(dut.clk)
        current_sd = dut.uo_out[2].value
        current_amplitude = dut.adsr_amplitude.value

        # Logging to observe ADSR and sd behavior
        dut._log.info(f"Cycle {i}: `sd` = {current_sd}, `amplitude` = {current_amplitude}")

        # Check if amplitude modulation is applied
        if current_amplitude != prev_amplitude:
            dut._log.info("Detected ADSR amplitude modulation.")
            if current_sd != prev_sd:
                dut._log.info("Modulated waveform detected on `sd`.")
                return  # Success: Modulation observed on `sd`
            else:
                prev_sd = current_sd
        prev_amplitude = current_amplitude

    # Fail if modulation not observed
    assert False, "Expected ADSR modulation but saw no change in `sd`."
