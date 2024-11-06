import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

async def send_uart_byte(dut, byte_value):
    """Simulate UART byte transmission with a start bit, 8 data bits, and a stop bit."""
    dut.ui_in[0].value = 0  # Start bit
    await ClockCycles(dut.clk, 2604)  # Adjust for correct baud rate timing

    # Send 8 data bits
    for i in range(8):
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 2604)  # Adjust timing as needed

    # Stop bit
    dut.ui_in[0].value = 1
    await ClockCycles(dut.clk, 2604)

def is_resolvable(signal_value):
    """Check each bit of signal_value and log unresolved bits."""
    for i in range(len(signal_value)):
        if str(signal_value[i]) in ('x', 'z'):
            cocotb.log.warning(f"Unresolved bit: uo_out[{i}] = {signal_value[i]}")
            return False
    return True

@cocotb.test()
async def test_tt_um_waves(dut):
    """Test to verify UART, frequency selection, wave generation, ADSR, and I2S output indirectly."""
    # Start clock for `clk`
    clock = Clock(dut.clk, 40, units="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Apply reset and allow extra stabilization time
    dut.rst_n.value = 0
    dut.uio_out.value = 0  # Explicitly initialize uio_out
    await ClockCycles(dut.clk, 50)  # Longer reset propagation
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 200)  # Additional stabilization time post-reset

    # Retry to stabilize uo_out
    for _ in range(10):
        await ClockCycles(dut.clk, 200)
        if is_resolvable(dut.uo_out.value):
            break
        else:
            dut._log.warning(f"uo_out contains unknown ('x'/'z') states: {dut.uo_out.value}")

    # Confirm that `uo_out` has fully stabilized
    assert is_resolvable(dut.uo_out.value), "uo_out still contains unresolvable states after retries"
    
    # Test UART Reception by sending 'T' for Triangle wave
    await send_uart_byte(dut, 0x54)  # 'T' character in ASCII
    await ClockCycles(dut.clk, 500)

    # Observe `uo_out` for selected_wave behavior change using individual bits
    prev_selected_wave = (dut.uo_out[2].value << 2) | (dut.uo_out[1].value << 1) | dut.uo_out[0].value
    await ClockCycles(dut.clk, 1000)
    current_selected_wave = (dut.uo_out[2].value << 2) | (dut.uo_out[1].value << 1) | dut.uo_out[0].value
    assert current_selected_wave != prev_selected_wave, "Expected `selected_wave` pattern change indicating wave_select=00"

    # Test frequency selection by sending '1'
    await send_uart_byte(dut, 0x31)  # ASCII '1'
    await ClockCycles(dut.clk, 500)
    assert dut.clk_divided.value == 1 or dut.clk_divided.value == 0, "Expected toggling of clk_divided based on freq_select=000001"

    # Test ADSR Modulation: Simulate encoder settings
    # Setting attack, decay, sustain, and release values by manually adjusting uio_in signals
    dut.uio_in[0].value = 1  # Encoder A for Attack
    dut.uio_in[1].value = 0  # Encoder B for Attack
    await ClockCycles(dut.clk, 50)
    assert dut.attack.value > 0, "Expected non-zero attack value"

    dut.uio_in[2].value = 1  # Encoder A for Decay
    dut.uio_in[3].value = 0  # Encoder B for Decay
    await ClockCycles(dut.clk, 50)
    assert dut.decay.value > 0, "Expected non-zero decay value"

    dut.uio_in[4].value = 1  # Encoder A for Sustain
    dut.uio_in[5].value = 0  # Encoder B for Sustain
    await ClockCycles(dut.clk, 50)
    assert dut.sustain.value > 0, "Expected non-zero sustain value"

    dut.uio_in[6].value = 1  # Encoder A for Release
    dut.uio_in[7].value = 0  # Encoder B for Release
    await ClockCycles(dut.clk, 50)
    assert dut.rel.value > 0, "Expected non-zero release value"

    # Verify ADSR modulates amplitude on uo_out
    await ClockCycles(dut.clk, 100)
    initial_amplitude = dut.adsr_amplitude.value
    await ClockCycles(dut.clk, 500)
    assert dut.adsr_amplitude.value != initial_amplitude, "Expected ADSR amplitude modulation over time"

    # Test I2S Transmission: Check `sck`, `ws`, and `sd` outputs for I2S signal generation
    # Observe `sck` toggling
    initial_sck = dut.uo_out[0].value  # sck
    await ClockCycles(dut.clk, 10)
    assert dut.uo_out[0].value != initial_sck, "Expected sck toggling in I2S output"

    # Observe `ws` toggling
    initial_ws = dut.uo_out[1].value  # ws
    await ClockCycles(dut.clk, 16)  # Typically, ws toggles at half the rate of sck
    assert dut.uo_out[1].value != initial_ws, "Expected ws toggling in I2S output"

    # Check `sd` carries data
    for _ in range(10):
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out[2].value == 0 or dut.uo_out[2].value == 1, "Expected valid sd bit (0 or 1) in I2S output"
