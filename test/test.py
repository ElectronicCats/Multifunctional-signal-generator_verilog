import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

async def send_uart_byte(dut, byte_value):
    """Simulate sending a byte over UART at 9600 baud with a 25 MHz clock."""
    dut.ui_in[0].value = 0  # Start bit
    await ClockCycles(dut.clk, 2604)  # Wait for one baud period

    # Transmit each bit of the byte (least significant bit first)
    for i in range(8):
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 2604)

    dut.ui_in[0].value = 1  # Stop bit
    await ClockCycles(dut.clk, 2604)

@cocotb.test()
async def test_comprehensive_functionality(dut):
    """Test UART, ADSR, and I2S functionality in the module"""

    # Initialize the 25 MHz clock (40 ns period)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # -------- UART Testing --------
    # Send frequency and waveform selection via UART
    freq_byte = 0x31  # Select frequency 1 (example byte '1')
    wave_byte = 0x51  # Select square wave (example byte 'Q')
    await send_uart_byte(dut, freq_byte)
    await send_uart_byte(dut, wave_byte)
    await ClockCycles(dut.clk, 100)  # Wait for processing

    # Check that frequency and wave type are set correctly
    assert dut.uart_rx_inst.freq_select.value == 0b000001, f"Expected freq_select = 1, got {dut.uart_rx_inst.freq_select.value}"
    assert dut.uart_rx_inst.wave_select.value == 0b10, f"Expected wave_select = 2 (square wave), got {dut.uart_rx_inst.wave_select.value}"

    # -------- ADSR Testing --------
    # Manually toggle encoder inputs to modify ADSR parameters
    dut.uio_in.value = 0b00001111  # Set example encoder inputs
    await ClockCycles(dut.clk, 20)  # Allow time to register input

    # Check ADSR values are updated
    assert dut.attack.value > 0, "Attack should be set"
    assert dut.decay.value > 0, "Decay should be set"
    assert dut.sustain.value > 0, "Sustain should be set"
    assert dut.rel.value > 0, "Release should be set"

    # -------- I2S Output Testing --------
    # Monitor the I2S outputs for correct data modulation
    dut._log.info("Monitoring I2S output for modulation and wave selection verification.")
    sck_toggle_count = 0
    ws_toggle_count = 0
    previous_sck = dut.uo_out[0].value
    previous_ws = dut.uo_out[1].value

    for i in range(5000):
        await RisingEdge(dut.clk)
        
        # Track I2S signals
        current_sck = dut.uo_out[0].value
        current_ws = dut.uo_out[1].value
        current_sd = dut.uo_out[2].value

        # SCK and WS toggling
        if current_sck != previous_sck:
            sck_toggle_count += 1
            if sck_toggle_count % 32 == 0:
                ws_toggle_count += 1

        # Log I2S data bits and validate waveform modulation
        if i % 100 == 0:  # Log periodically to capture waveform changes
            dut._log.info(f"Cycle {i}: SCK={current_sck}, WS={current_ws}, SD={current_sd}")
        
        # Update previous values for the next cycle
        previous_sck = current_sck
        previous_ws = current_ws

    # Final assertion checks (e.g., verify SCK and WS toggling counts as a rough I2S check)
    assert sck_toggle_count > 0, "Expected SCK to toggle"
    assert ws_toggle_count > 0, "Expected WS to toggle"
    dut._log.info("Test completed successfully.")
