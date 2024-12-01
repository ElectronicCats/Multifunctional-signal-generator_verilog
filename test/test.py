import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

async def send_uart_byte(dut, byte_value):
    """Simulate UART byte transmission with a start bit, 8 data bits, and a stop bit."""
    dut.ui_in[0].value = 0  # Start bit
    await ClockCycles(dut.clk, 2604)

    # Send 8 data bits
    for i in range(8):
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 2604)

    # Stop bit
    dut.ui_in[0].value = 1
    await ClockCycles(dut.clk, 2604)

def is_resolvable(signal_value):
    """Check if the signal is resolvable (no 'x' or 'z' states)."""
    for i in range(3):
        if str(signal_value[i]) in ('x', 'z'):
            cocotb.log.warning(f"Unresolved I2S bit: uo_out[{i}] = {signal_value[i]}")
            return False
    return True

@cocotb.test()
async def test_tt_um_waves(dut):
    """Test tt_um_waves module functionality, including UART, ADSR, and I2S."""
    # Initialize clock and reset
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # Test UART transmission for wave selection
    await send_uart_byte(dut, 0x54)  # ASCII 'T' for Triangle wave
    await ClockCycles(dut.clk, 500)
    assert dut.uo_out[2:0] == 0b000, "Triangle wave not selected as expected"

    await send_uart_byte(dut, 0x53)  # ASCII 'S' for Sawtooth wave
    await ClockCycles(dut.clk, 500)
    assert dut.uo_out[2:0] == 0b001, "Sawtooth wave not selected as expected"

    await send_uart_byte(dut, 0x51)  # ASCII 'Q' for Square wave
    await ClockCycles(dut.clk, 500)
    assert dut.uo_out[2:0] == 0b010, "Square wave not selected as expected"

    await send_uart_byte(dut, 0x4E)  # ASCII 'N' for Sine wave
    await ClockCycles(dut.clk, 500)
    assert dut.uo_out[2:0] == 0b011, "Sine wave not selected as expected"

    # Test white noise enable and disable
    await send_uart_byte(dut, 0x57)  # ASCII 'W' to enable white noise
    await ClockCycles(dut.clk, 500)
    assert dut.uo_out[2:0] == 0b100, "White noise not enabled as expected"

    await send_uart_byte(dut, 0x4F)  # ASCII 'O' to disable white noise
    await ClockCycles(dut.clk, 500)
    assert dut.uo_out[2:0] != 0b100, "White noise not disabled as expected"

    # Test ADSR envelope generation
    dut.uio_in.value = 0b00000001  # Simulate attack encoder movement
    await ClockCycles(dut.clk, 100)
    attack_value = int(dut.debug_attack.value)
    assert attack_value > 0, "Attack value not incremented as expected"

    dut.uio_in.value = 0b00000100  # Simulate sustain encoder movement
    await ClockCycles(dut.clk, 100)
    sustain_value = int(dut.debug_sustain.value)
    assert sustain_value > 0, "Sustain value not incremented as expected"

    # Test I2S output
    for _ in range(10):
        await ClockCycles(dut.clk, 200)
        if is_resolvable(dut.uo_out.value):
            break

    assert is_resolvable(dut.uo_out.value), "I2S output contains unresolved states"
    cocotb.log.info("I2S output verified successfully")
