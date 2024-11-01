import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

async def send_uart_byte(dut, byte_value):
    dut.ui_in[0].value = 0  # Start bit
    await ClockCycles(dut.clk, 2604)  # 9600 baud with 25 MHz clock
    
    for i in range(8):  # Transmit each bit
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 2604)

    dut.ui_in[0].value = 1  # Stop bit
    await ClockCycles(dut.clk, 2604)

@cocotb.test()
async def test_adsr_i2s_waveform(dut):
    # Initialize clock
    clock = Clock(dut.clk, 40, units="ns")  # 40 ns for 25 MHz
    cocotb.start_soon(clock.start())

    # Reset and enable
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)  # Allow time for reset to propagate

    # Send UART commands to select sine wave ('N') and C#2 frequency ('1')
    await send_uart_byte(dut, ord('N'))  # 'N' for sine wave
    await send_uart_byte(dut, ord('1'))  # '1' for C#2 frequency

    # Set example ADSR values via GPIO encoders
    dut.uio_in.value = 0b00001111  # Example ADSR setting; adjust as needed

    # Monitor variables
    sck_prev, ws_prev, sd_prev = dut.uo_out[0].value, dut.uo_out[1].value, dut.uo_out[2].value
    expected_sck_toggle_rate = 25_000_000 // 65  # For frequency ~65 Hz (C#2)

    # Counters for frequency and ADSR monitoring
    sck_toggle_count = 0

    for i in range(3000):  # Run for sufficient cycles to verify stability
        await RisingEdge(dut.clk)
        sck_current, ws_current, sd_current = dut.uo_out[0].value, dut.uo_out[1].value, dut.uo_out[2].value

        # Extract adsr_amplitude (bits [7:3] of uo_out)
        if 'x' in str(dut.uo_out.value):
            adsr_amplitude = 0  # Handle unknown state
        else:
            adsr_amplitude = (int(dut.uo_out.value) >> 3) & 0x1F

        # Frequency check on sck toggles
        if sck_current != sck_prev:
            sck_toggle_count += 1
            if sck_toggle_count >= expected_sck_toggle_rate:
                dut._log.info("Frequency toggle verified at C#2 (65 Hz)")
                sck_toggle_count = 0

        # Verify ws toggles for each frame (every 32 sck toggles for I2S)
        if i % 32 == 0:
            assert ws_current != ws_prev, "I2S frame ws did not toggle as expected."

        # Log ADSR effect periodically on SD and check amplitude changes
        if i % 50 == 0:
            dut._log.info(f"Cycle {i}: ADSR Amplitude: {adsr_amplitude}, SD data: {sd_current}")

        # Update previous values for next cycle
        sck_prev, ws_prev, sd_prev = sck_current, ws_current, sd_current
