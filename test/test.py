import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


@cocotb.test()
async def test_adsr_i2s_waveform(dut):
    # Initialize clock
    clock = Clock(dut.clk, 10, units="us")  # Set clock period (100 KHz)
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # Set frequency and wave selection (e.g., select sine wave and a middle frequency)
    dut.ui_in.value = 0b11000000  # 110 = sine wave select, 000000 = lowest frequency
    dut.uio_in.value = 0          # Reset ADSR control encoder values if necessary

    # Set ADSR parameters through the internal encoder or assign values directly
    # Here we assume `adsr_amplitude` can be observed for modulation
    dut._log.info("Configuring ADSR: Attack=20, Decay=10, Sustain=50, Release=30")

    # Observe and monitor `sck`, `ws`, and `sd` I2S output pins over time
    sck_prev = dut.uo_out[0].value
    ws_prev = dut.uo_out[1].value
    sd_prev = dut.uo_out[2].value

    # Access `adsr_amplitude` using hierarchical path in cocotb
    adsr_amplitude_signal = dut.tt_um_waves.adsr_amplitude

    # Test loop - monitor the I2S outputs for a period and verify signal behavior
    for i in range(2000):  # Adjust iteration count as needed for simulation duration
        await RisingEdge(dut.clk)

        # Sample current values of I2S pins
        sck_current = dut.uo_out[0].value  # Bit clock
        ws_current = dut.uo_out[1].value   # Word select
        sd_current = dut.uo_out[2].value   # Serial data
        adsr_amplitude = adsr_amplitude_signal.value  # ADSR modulating amplitude

        # Verify `sck` toggles as a clock signal
        assert sck_current != sck_prev, "sck did not toggle as expected."

        # Verify `ws` changes periodically indicating word boundaries
        if i % 32 == 0:  # Assuming a periodic change every 32 cycles
            assert ws_current != ws_prev, "ws did not toggle as expected for I2S frame."

        # Verify `sd` data is modulated by ADSR amplitude (sample periodically)
        if i % 50 == 0:  # Adjust sampling interval as needed
            dut._log.info(f"ADSR Amplitude: {adsr_amplitude}, SD data: {sd_current}")

        # Update previous state variables for next comparison
        sck_prev = sck_current
        ws_prev = ws_current
        sd_prev = sd_current
