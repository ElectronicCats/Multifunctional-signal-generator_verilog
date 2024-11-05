import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

# Helper function to send UART byte
async def send_uart_byte(dut, byte_value):
    """Simulate UART byte transmission with a start bit, 8 data bits, and a stop bit."""
    # Start bit (low)
    dut.ui_in[0].value = 0
    await ClockCycles(dut.clk, 2604)  # Adjust for correct baud rate timing

    # Send 8 data bits
    for i in range(8):
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 2604)  # Adjust timing as needed

    # Stop bit (high)
    dut.ui_in[0].value = 1
    await ClockCycles(dut.clk, 2604)

@cocotb.test()
async def test_tt_um_waves(dut):
    """Top-level test to verify UART, frequency selection, wave generation, ADSR, and I2S output."""
    # Start a clock for `clk` input
    clock = Clock(dut.clk, 40, units="ns")  # 25 MHz clock
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # 1. Test UART Reception for Wave Selection and Frequency Setting
    await send_uart_byte(dut, 0x54)  # 'T' for Triangle wave selection
    await ClockCycles(dut.clk, 500)
    assert dut.wave_select.value == 0b00, "Expected wave_select to be 00 (Triangle)"

    await send_uart_byte(dut, 0x31)  # '1' for frequency select 1
    await ClockCycles(dut.clk, 500)
    assert dut.freq_select.value == 0b000001, "Expected freq_select to be 000001"

    # 2. Test Clock Divider (Confirming clk_divided toggling with freq_select setting)
    prev_clk_divided = dut.clk_divided.value
    await ClockCycles(dut.clk, dut.clk_div_threshold.value * 2)
    assert dut.clk_divided.value != prev_clk_divided, "Expected clk_divided to toggle based on clk_div_threshold"

    # 3. Test Wave Generation (Confirm wave pattern change)
    await send_uart_byte(dut, 0x53)  # 'S' for Sawtooth wave
    await ClockCycles(dut.clk, 500)
    assert dut.wave_select.value == 0b01, "Expected wave_select to be 01 (Sawtooth)"
    saw_wave_observed = any(dut.selected_wave.value != 0 for _ in range(100))
    assert saw_wave_observed, "Expected non-zero sawtooth waveform output"

    # 4. Test ADSR Modulation (Observe modulation of selected waveform)
    attack_initial = dut.attack.value
    await ClockCycles(dut.clk, 500)
    assert dut.adsr_amplitude.value > 0, "Expected ADSR to modulate amplitude (non-zero)"

    # 5. Test I2S Transmission (Validate the I2S output signals)
    await ClockCycles(dut.clk, 500)
    assert dut.sck.value == 1 or dut.sck.value == 0, "Expected valid sck signal (0 or 1)"
    assert dut.ws.value == 1 or dut.ws.value == 0, "Expected valid ws signal (0 or 1)"
    assert dut.sd.value == 1 or dut.sd.value == 0, "Expected valid sd signal (0 or 1)"
