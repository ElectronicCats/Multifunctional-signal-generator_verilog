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

def is_resolvable(signal_values):
    """Check if signal values are resolvable for I2S verification."""
    for value in signal_values:
        if str(value) in ('x', 'z'):
            cocotb.log.warning(f"Unresolved I2S bit: {value}")
            return False
    return True

@cocotb.test()
async def test_tt_um_waves(dut):
    """Test and debug I2S output, waveform selection, white noise, and ADSR modulation."""
    # Initialize clock and reset
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # Test wave selection via UART
    waveforms = {
        0x54: "Triangle",  # ASCII 'T'
        0x53: "Sawtooth",  # ASCII 'S'
        0x51: "Square",    # ASCII 'Q'
        0x4E: "Sine",      # ASCII 'N'
        0x57: "White Noise" # ASCII 'W'
    }

    for byte, name in waveforms.items():
        await send_uart_byte(dut, byte)
        await ClockCycles(dut.clk, 500)
        selected_wave = (dut.uo_out[2].value << 2) | (dut.uo_out[1].value << 1) | dut.uo_out[0].value

        if name == "White Noise":
            assert selected_wave == 0b100, f"{name} not selected as expected"
        else:
            expected_value = list(waveforms.keys()).index(byte)
            assert selected_wave == expected_value, f"{name} not selected as expected"

    # Test ADSR modulation phases using encoder inputs
    adsr_phases = {
        "Attack": [0, 1],
        "Decay": [2, 3],
        "Sustain": [4, 5],
        "Release": [6, 7]
    }

    for phase, pins in adsr_phases.items():
        dut.uio_in[pins[0]].value = 1
        dut.uio_in[pins[1]].value = 0
        await ClockCycles(dut.clk, 50)

        debug_signal = getattr(dut, f"debug_{phase.lower()}")
        initial_value = debug_signal.value

        await ClockCycles(dut.clk, 100)

        if phase == "Sustain":
            assert debug_signal.value == initial_value, f"Expected `{phase}` to remain constant"
        else:
            assert debug_signal.value != initial_value, f"Expected `{phase}` to change"

    # Verify I2S output: sck, ws, and sd
    for _ in range(10):
        await ClockCycles(dut.clk, 200)
        if is_resolvable([dut.uo_out[i].value for i in range(3)]):
            break

    assert is_resolvable([dut.uo_out[i].value for i in range(3)]), "uo_out[0:3] contains unresolved states after retries."

    initial_sck = dut.uo_out[0].value  # sck
    await ClockCycles(dut.clk, 10)
    assert dut.uo_out[0].value != initial_sck, "Expected sck toggling in I2S output"

    initial_ws = dut.uo_out[1].value  # ws
    await ClockCycles(dut.clk, 16)
    assert dut.uo_out[1].value != initial_ws, "Expected ws toggling in I2S output"

    for _ in range(10):
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out[2].value in (0, 1), "Expected valid sd bit (0 or 1) in I2S output"
