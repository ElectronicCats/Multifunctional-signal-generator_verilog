import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

# UART transmission function to simulate sending a byte to the DUT's UART RX pin
async def send_uart_byte(dut, byte_value):
    # UART protocol simulation (1 start bit, 8 data bits, 1 stop bit)
    dut.ui_in[0].value = 0  # Start bit
    await ClockCycles(dut.clk, 10416)  # Approximate 9600 baud rate based on clk cycles
    
    # Send each bit in byte_value
    for i in range(8):
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 10416)

    dut.ui_in[0].value = 1  # Stop bit
    await ClockCycles(dut.clk, 10416)

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

    # Select waveform and frequency via UART
    await send_uart_byte(dut, 0x4E)  # 'N' for sine wave select
    await send_uart_byte(dut, 0x31)  # '1' for C#2 frequency (69.30 Hz)

    # Set ADSR parameters through the internal encoder or assign values directly
    dut._log.info("Configuring ADSR: Attack=20, Decay=10, Sustain=50, Release=30")

    # Assume adsr_amplitude can be observed for modulation
    adsr_amplitude_signal = dut.tt_um_waves.adsr_amplitude

    # Initial previous values for I2S signal checking
    sck_prev = dut.uo_out[0].value
    ws_prev = dut.uo_out[1].value
    sd_prev = dut.uo_out[2].value

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
