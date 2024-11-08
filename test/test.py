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

    # Track wave selection by observing UART changes
    initial_wave_selection = (dut.uo_out[0].value, dut.uo_out[1].value, dut.uo_out[2].value)
    await send_uart_byte(dut, 0x31)  # Send UART byte '1' to change frequency
    await ClockCycles(dut.clk, 500)
    new_wave_selection = (dut.uo_out[0].value, dut.uo_out[1].value, dut.uo_out[2].value)
    assert new_wave_selection != initial_wave_selection, "Expected change in wave selection after UART command"

    # Simulate ADSR modulation by setting attack, decay, sustain, release
    dut.uio_in[0].value = 1
    await ClockCycles(dut.clk, 50)
    assert dut.attack.value > 0, "Expected non-zero attack value"

    dut.uio_in[2].value = 1
    await ClockCycles(dut.clk, 50)
    assert dut.decay.value > 0, "Expected non-zero decay value"

    dut.uio_in[4].value = 1
    await ClockCycles(dut.clk, 50)
    assert dut.sustain.value > 0, "Expected non-zero sustain value"

    dut.uio_in[6].value = 1
    await ClockCycles(dut.clk, 50)
    assert dut.rel.value > 0, "Expected non-zero release value"

    # Verify ADSR modulation on amplitude
    initial_amplitude = dut.adsr_amplitude.value
    await ClockCycles(dut.clk, 500)
    assert dut.adsr_amplitude.value != initial_amplitude, "Expected ADSR amplitude modulation over time"

    # Test I2S Transmission: Check `sck`, `ws`, and `sd` in `uo_out`
    for _ in range(10):
        await ClockCycles(dut.clk, 200)
        if is_resolvable(dut.uo_out.value[0:3]):
            break

    # Ensure I2S signals in uo_out[0:3] are resolvable
    assert is_resolvable(dut.uo_out.value[0:3]), "uo_out[0:3] contains unresolvable states after retries"

    # Observe toggling of I2S signals in `uo_out[0:3]`
    initial_sck = dut.uo_out[0].value  # sck
    await ClockCycles(dut.clk, 10)
    assert dut.uo_out[0].value != initial_sck, "Expected sck toggling in I2S output"

    initial_ws = dut.uo_out[1].value  # ws
    await ClockCycles(dut.clk, 16)
    assert dut.uo_out[1].value != initial_ws, "Expected ws toggling in I2S output"

    for _ in range(10):
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out[2].value in (0, 1), "Expected valid sd bit (0 or 1) in I2S output"
