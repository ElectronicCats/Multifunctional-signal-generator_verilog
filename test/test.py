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
    """Check if first three bits of `signal_value` are resolvable for I2S verification."""
    for i in range(3):
        if str(signal_value[i]) in ('x', 'z'):
            cocotb.log.warning(f"Unresolved I2S bit: uo_out[{i}] = {signal_value[i]}")
            return False
    return True

@cocotb.test()
async def test_tt_um_waves(dut):
    """Test and debug I2S output and ADSR modulation."""
    # Initialize clock and reset
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # Test wave selection via UART
    # Test Triangle wave
    await send_uart_byte(dut, 0x54)  # ASCII 'T' for Triangle wave
    await ClockCycles(dut.clk, 500)
    selected_wave = (dut.uo_out[2].value << 2) | (dut.uo_out[1].value << 1) | dut.uo_out[0].value
    assert selected_wave == 0b000, "Triangle wave not selected as expected"

    # Test Sawtooth wave
    await send_uart_byte(dut, 0x53)  # ASCII 'S' for Sawtooth wave
    await ClockCycles(dut.clk, 500)
    selected_wave = (dut.uo_out[2].value << 2) | (dut.uo_out[1].value << 1) | dut.uo_out[0].value
    assert selected_wave == 0b001, "Sawtooth wave not selected as expected"

    # Test Square wave
    await send_uart_byte(dut, 0x51)  # ASCII 'Q' for Square wave
    await ClockCycles(dut.clk, 500)
    selected_wave = (dut.uo_out[2].value << 2) | (dut.uo_out[1].value << 1) | dut.uo_out[0].value
    assert selected_wave == 0b010, "Square wave not selected as expected"

    # Test Sine wave
    await send_uart_byte(dut, 0x4E)  # ASCII 'N' for Sine wave
    await ClockCycles(dut.clk, 500)
    selected_wave = (dut.uo_out[2].value << 2) | (dut.uo_out[1].value << 1) | dut.uo_out[0].value
    assert selected_wave == 0b011, "Sine wave not selected as expected"

    # Test ADSR modulation phases
    dut.uio_in[0].value = 1  # Attack
    dut.uio_in[1].value = 0
    await ClockCycles(dut.clk, 50)

    initial_attack = dut.debug_attack.value
    await ClockCycles(dut.clk, 100)
    assert dut.debug_attack.value != initial_attack, "Expected `debug_attack` to change during attack phase"

    dut.uio_in[2].value = 1  # Decay
    dut.uio_in[3].value = 0
    await ClockCycles(dut.clk, 50)

    initial_decay = dut.debug_decay.value
    await ClockCycles(dut.clk, 100)
    assert dut.debug_decay.value != initial_decay, "Expected `debug_decay` to change during decay phase"

    dut.uio_in[4].value = 1  # Sustain
    dut.uio_in[5].value = 0
    await ClockCycles(dut.clk, 50)

    initial_sustain = dut.debug_sustain.value
    await ClockCycles(dut.clk, 100)
    assert dut.debug_sustain.value == initial_sustain, "Expected `debug_sustain` to remain constant during sustain phase"

    dut.uio_in[6].value = 1  # Release
    dut.uio_in[7].value = 0
    await ClockCycles(dut.clk, 50)

    initial_rel = dut.debug_rel.value
    await ClockCycles(dut.clk, 100)
    assert dut.debug_rel.value != initial_rel, "Expected `debug_rel` to change during release phase"

    # Verify I2S output: sck, ws, and sd
    for _ in range(10):
        await ClockCycles(dut.clk, 200)
        if is_resolvable(dut.uo_out.value[0:3]):
            break

    assert is_resolvable(dut.uo_out.value[0:3]), "uo_out[0:3] contains unresolved states after retries."

    initial_sck = dut.uo_out[0].value  # sck
    await ClockCycles(dut.clk, 10)
    assert dut.uo_out[0].value != initial_sck, "Expected sck toggling in I2S output"

    initial_ws = dut.uo_out[1].value  # ws
    await ClockCycles(dut.clk, 16)
    assert dut.uo_out[1].value != initial_ws, "Expected ws toggling in I2S output"

    for _ in range(10):
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out[2].value in (0, 1), "Expected valid sd bit (0 or 1) in I2S output"