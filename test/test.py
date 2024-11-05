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

    # Send frequency selection command
    freq_byte = 0b00000001  # Frequency selection value 1
    await send_uart_byte(dut, freq_byte)
    
    # Send waveform selection command
    wave_byte = 0b01000010  # Selecting waveform 2 (e.g., square wave)
    await send_uart_byte(dut, wave_byte)

    # Wait for the settings to propagate
    await ClockCycles(dut.clk, 100)

    # Check if ADSR parameters are affecting the amplitude modulation
    adsr_value = int(dut.uo_out.value) >> 3  # Extract bits [7:3] of uo_out
    assert adsr_value != 0, "Expected ADSR modulation on uo_out[7:3]"

    # Check I2S signals for activity
    sck_initial = int(dut.uo_out[0].value)
    ws_initial = int(dut.uo_out[1].value)
    sd_initial = int(dut.uo_out[2].value)
    
    # Wait for some clock cycles and check if I2S signals are toggling
    await ClockCycles(dut.clk, 10)
    assert int(dut.uo_out[0].value) != sck_initial, "Expected SCK to toggle"
    assert int(dut.uo_out[1].value) != ws_initial, "Expected WS to toggle"
    assert int(dut.uo_out[2].value) != sd_initial, "Expected SD to toggle"

    # Log results
    dut._log.info(f"Final ADSR amplitude bits: {adsr_value}")
    dut._log.info("I2S signals toggled as expected")
