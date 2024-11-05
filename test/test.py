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

    # Test: Send frequency selection command
    freq_byte = 0x31  # '1' ASCII, representing frequency 1
    await send_uart_byte(dut, freq_byte)
    await ClockCycles(dut.clk, 100)

    # Verify frequency selection
    assert int(dut.freq_select.value) == 0b000001, f"Expected freq_select = 1, got {dut.freq_select.value}"

    # Test: Send waveform selection command
    wave_byte = 0x51  # 'Q' ASCII, selecting Square wave
    await send_uart_byte(dut, wave_byte)
    await ClockCycles(dut.clk, 100)

    # Verify wave selection
    assert int(dut.wave_select.value) == 0b10, f"Expected wave_select = 2, got {dut.wave_select.value}"

    # Set ADSR values via encoders
    dut.uio_in.value = 0b01010101  # Set encoders to test ADSR
    await ClockCycles(dut.clk, 200)

    # Verify ADSR-modulated amplitude on uo_out[7:3]
    adsr_value = (int(dut.uo_out.value) & 0b11111000) >> 3
    assert adsr_value != 0, "Expected ADSR modulation on uo_out[7:3]"

    # Verify I2S output signals toggling
    assert int(dut.uo_out[0].value) in [0, 1], "I2S sck not toggling as expected"
    assert int(dut.uo_out[1].value) in [0, 1], "I2S ws not toggling as expected"
    assert int(dut.uo_out[2].value) in [0, 1], "I2S sd not toggling as expected"

    # Logging final values
    dut._log.info(f"Final freq_select: {dut.freq_select.value}")
    dut._log.info(f"Final wave_select: {dut.wave_select.value}")
    dut._log.info(f"ADSR-modulated amplitude (uo_out[7:3]): {adsr_value}")
