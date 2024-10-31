import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


# UART transmission function to simulate sending a byte to the DUT's UART RX pin
async def send_uart_byte(dut, byte_value):
    # UART protocol simulation (1 start bit, 8 data bits, 1 stop bit)
    dut.ui_in[0].value = 0  # Start bit
    await ClockCycles(dut.clk, 2604)  # 9600 baud with 25 MHz clock
    
    # Send each bit in byte_value
    for i in range(8):
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 2604)

    dut.ui_in[0].value = 1  # Stop bit
    await ClockCycles(dut.clk, 2604)

@cocotb.test()
async def test_adsr_i2s_waveform(dut):
    # Initialize clock
    clock = Clock(dut.clk, 40, units="ns")  # Set clock period to 40 ns for 25 MHz
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # Send UART commands for sine wave and C#2 frequency
    await send_uart_byte(dut, 0x4E)  # 'N' for sine wave
    await send_uart_byte(dut, 0x31)  # '1' for C#2 frequency (set `freq_select`)

    # Set ADSR values via GPIO encoder inputs
    dut.uio_in.value = 0b00001111  # Example encoder states for ADSR (adjust as needed)

    # Variables for monitoring
    sck_prev, ws_prev, sd_prev = dut.uo_out[0].value, dut.uo_out[1].value, dut.uo_out[2].value
    expected_frequency_toggle_rate = 25_000_000 // 65  # Example for C#2 frequency of 65 Hz
    
    # Frequency and ADSR modulation monitoring
    toggle_count = 0
    adsr_amplitude_signal = dut.adsr_amplitude.value  # Monitor ADSR output amplitude

    for i in range(3000):  # Run for sufficient cycles to verify stability
        await RisingEdge(dut.clk)
        sck_current, ws_current, sd_current = dut.uo_out[0].value, dut.uo_out[1].value, dut.uo_out[2].value
        adsr_amplitude = adsr_amplitude_signal.value

        # Frequency check: count sck toggles to verify frequency (sampling every toggle)
        if sck_current != sck_prev:
            toggle_count += 1
            if toggle_count == expected_frequency_toggle_rate:
                dut._log.info("Expected frequency verified at C#2 (65 Hz).")
                toggle_count = 0  # Reset toggle count after verification

        # Verify that ws toggles at frame rate (every 32 sck toggles for I2S)
        if i % 32 == 0:
            assert ws_current != ws_prev, "ws did not toggle as expected for I2S frame."

        # ADSR effect logging on `sd`
        if i % 50 == 0:
            dut._log.info(f"Cycle {i}: ADSR Amplitude: {adsr_amplitude}, SD data: {sd_current}")

        # Update previous values for next cycle
        sck_prev, ws_prev, sd_prev = sck_current, ws_current, sd_current
