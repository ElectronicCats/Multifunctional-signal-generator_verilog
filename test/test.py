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
async def test_uart_receiver(dut):
    """Test the uart_receiver by sending commands to set frequency and waveform selection."""

    # Initialize the 25 MHz clock (40 ns period)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # Test 1: Send a frequency selection command
    freq_byte = 0b00000001  # Example: selecting frequency corresponding to value 1
    await send_uart_byte(dut, freq_byte)

    # Wait for the signal to be processed
    await ClockCycles(dut.clk, 100)

    # Verify freq_select has updated correctly
    assert dut.uart_rx_inst.freq_select.value == 0b000001, f"Expected freq_select = 1, got {dut.uart_rx_inst.freq_select.value}"

    # Test 2: Send a waveform selection command
    wave_byte = 0b01000010  # Example: selecting waveform 2 (e.g., square wave)
    await send_uart_byte(dut, wave_byte)

    # Wait for the signal to be processed
    await ClockCycles(dut.clk, 100)

    # Verify wave_select has updated correctly
    assert dut.uart_rx_inst.wave_select.value == 0b10, f"Expected wave_select = 2, got {dut.uart_rx_inst.wave_select.value}"

    # Logging final values
    dut._log.info(f"Final freq_select: {dut.uart_rx_inst.freq_select.value}")
    dut._log.info(f"Final wave_select: {dut.uart_rx_inst.wave_select.value}")
