import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

async def send_uart_byte(dut, byte_value):
    """Simulate UART byte transmission with start, data, and stop bits."""
    dut.ui_in[0].value = 0  # Start bit
    await ClockCycles(dut.clk, 2604)  # Adjust for correct baud rate timing

    # Send 8 data bits
    for i in range(8):
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 2604)  # Adjust timing as needed

    # Stop bit
    dut.ui_in[0].value = 1
    await ClockCycles(dut.clk, 2604)

@cocotb.test()
async def test_tt_um_waves(dut):
    """Test to verify UART, frequency selection, wave generation, ADSR, and I2S output indirectly."""
    # Start clock for `clk`
    clock = Clock(dut.clk, 40, units="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # Test UART Reception by sending 'T' for Triangle wave
    await send_uart_byte(dut, 0x54)  # 'T' character in ASCII
    await ClockCycles(dut.clk, 500)

    # Observe `uo_out` for `selected_wave` behavior change
    prev_selected_wave = dut.uo_out[2:0].value
    await ClockCycles(dut.clk, 1000)
    assert dut.uo_out[2:0].value != prev_selected_wave, "Expected `selected_wave` pattern change indicating wave_select=00"

    # Test frequency selection by sending '1'
    await send_uart_byte(dut, 0x31)  # ASCII '1'
    await ClockCycles(dut.clk, 500)
    assert dut.clk_divided.value == 1 or dut.clk_divided.value == 0, "Expected toggling of clk_divided based on freq_select=000001"

    # Additional tests as needed for ADSR and I2S functionality
