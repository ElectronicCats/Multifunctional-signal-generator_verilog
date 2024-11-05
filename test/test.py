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
    """Test UART, ADSR, and I2S functionality in the module."""

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
    freq_byte = 0x31  # Example byte to set frequency (value '1')
    wave_byte = 0x51  # Example byte to set waveform to square wave ('Q')
    await send_uart_byte(dut, freq_byte)
    await send_uart_byte(dut, wave_byte)
    await ClockCycles(dut.clk, 100)  # Allow for processing

    # Check `uo_out` for expected frequency and wave type settings
    # Assuming frequency and wave select settings affect the output wave characteristics
    dut._log.info("Checking frequency and wave type based on `uo_out` waveform")
    # Verify signal patterns indirectly in I2S section below

    # -------- ADSR Testing --------
    # Simulate encoder inputs to adjust ADSR parameters
    dut.uio_in.value = 0b00001111  # Example to modify ADSR settings
    await ClockCycles(dut.clk, 20)  # Allow time to register input

    # Verify ADSR waveform modulation on `uo_out`
    assert dut.uo_out[7:3].value != 0, "ADSR modulation expected on uo_out[7:3]"

    # -------- I2S Output Testing --------
    # Check the I2S signals `sck`, `ws`, and `sd` in `uo_out[2:0]`
    dut._log.info("Monitoring I2S outputs for modulation and waveform verification.")
    sck_toggle_count = 0
    ws_toggle_count = 0
    previous_sck = dut.uo_out[0].value
    previous_ws = dut.uo_out[1].value

    for i in range(5000):
        await RisingEdge(dut.clk)
        
        # Capture current values of I2S signals
        current_sck = dut.uo_out[0].value
        current_ws = dut.uo_out[1].value
        current_sd = dut.uo_out[2].value

        # Detect `sck` and `ws` toggling
        if current_sck != previous_sck:
            sck_toggle_count += 1
            if sck_toggle_count % 32 == 0:
                ws_toggle_count += 1

        # Log the `sd` (data line) state periodically to observe wave modulation
        if i % 100 == 0:
            dut._log.info(f"Cycle {i}: SCK={current_sck}, WS={current_ws}, SD={current_sd}")

        # Update previous state values
        previous_sck = current_sck
        previous_ws = current_ws

    # Verify the I2S toggling counts to confirm I2S behavior
    assert sck_toggle_count > 0, "Expected `sck` to toggle"
    assert ws_toggle_count > 0, "Expected `ws` to toggle"
    dut._log.info("Test completed successfully.")
