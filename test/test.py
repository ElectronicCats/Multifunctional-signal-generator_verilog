import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

async def send_uart_byte(dut, byte_value):
    """Send a byte over UART with 9600 baud rate, assuming 25 MHz clock."""
    dut.ui_in[0].value = 0  # Start bit
    await ClockCycles(dut.clk, 2604)  # 9600 baud with 25 MHz clock
    
    for i in range(8):  # Transmit each bit
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 2604)

    dut.ui_in[0].value = 1  # Stop bit
    await ClockCycles(dut.clk, 2604)

@cocotb.test()
async def test_adsr_i2s_waveform(dut):
    """Test ADSR-modulated waveform generation with I2S output."""
    
    # Initialize clock at 25 MHz (40 ns period)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset and enable
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)  # Allow time for reset to propagate

    # Select sine wave and set frequency to C#2 via UART commands
    await send_uart_byte(dut, ord('N'))  # Select sine wave
    await send_uart_byte(dut, ord('1'))  # Select C#2 frequency
    dut._log.info(f"Selected Waveform: {dut.wave_select.value}, Frequency: {dut.freq_select.value}")

    # Set example ADSR values via GPIO encoders (adjust these as needed for test)
    dut.uio_in.value = 0b00001111  # Example ADSR settings for testing

    # Initialize variables for I2S and ADSR monitoring
    sck_prev, ws_prev, sd_prev = dut.uo_out[0].value, dut.uo_out[1].value, dut.uo_out[2].value
    expected_sck_toggle_rate = 25_000_000 // 65  # Calculate for C#2 frequency (approximately 65 Hz)
    sck_toggle_count = 0
    ws_toggle_count = 0

    # Buffer to store SD values for analysis of the ADSR envelope
    sd_samples = []
    capture_cycles = 4096  # Adjust based on desired analysis length

    # Run test for enough cycles to capture ADSR-modulated waveform
    for i in range(capture_cycles):
        await RisingEdge(dut.clk)
        sck_current, ws_current, sd_current = dut.uo_out[0].value, dut.uo_out[1].value, dut.uo_out[2].value

        # Capture SD values for analysis if WS (Word Select) is low (left channel)
        if ws_current == 0:
            sd_samples.append(int(sd_current))

        # Log I2S signals at intervals to observe changes
        if i % 32 == 0:
            dut._log.info(f"Cycle {i}: SCK: {sck_current}, WS: {ws_current}, SD: {sd_current}")

        # Check SCK toggle rate
        if sck_current != sck_prev:
            sck_toggle_count += 1
            if sck_toggle_count == expected_sck_toggle_rate:
                dut._log.info("SCK toggle rate matches expected frequency")
                sck_toggle_count = 0

        # Check WS toggling every 32 SCK cycles
        if sck_toggle_count % 32 == 0 and sck_toggle_count != 0:
            assert ws_current != ws_prev, "WS (Word Select) signal did not toggle as expected."

        # Update previous values for the next cycle
        sck_prev, ws_prev, sd_prev = sck_current, ws_current, sd_current

    # Post-processing: Analyze SD samples for ADSR envelope
    dut._log.info(f"Captured {len(sd_samples)} SD samples for ADSR analysis.")
    
    # ADSR Phase Analysis
    attack_phase = sd_samples[:int(len(sd_samples) * 0.1)]
    decay_phase = sd_samples[int(len(sd_samples) * 0.1):int(len(sd_samples) * 0.3)]
    sustain_phase = sd_samples[int(len(sd_samples) * 0.3):int(len(sd_samples) * 0.8)]
    release_phase = sd_samples[int(len(sd_samples) * 0.8):]

    # Attack phase check: SD should increase from 0
    assert max(attack_phase) > min(attack_phase), "Attack phase failed: SD should increase in amplitude."

    # Decay phase check: SD should peak and then decrease
    assert max(decay_phase) > min(decay_phase), "Decay phase failed: SD should decrease after peak."

    # Sustain phase check: SD should hold relatively steady amplitude
    sustain_variation = max(sustain_phase) - min(sustain_phase)
    assert sustain_variation < (0.1 * max(sustain_phase)), "Sustain phase failed: SD should maintain steady amplitude."

    # Release phase check: SD should decrease towards zero
    assert max(release_phase) > min(release_phase) and min(release_phase) == 0, "Release phase failed: SD should fade to zero."

    dut._log.info("ADSR phases verified successfully.")
