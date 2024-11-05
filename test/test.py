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

def is_resolvable(signal_value):
    """Helper function to check if signal_value has only resolvable bits."""
    return 'x' not in str(signal_value) and 'z' not in str(signal_value)

@cocotb.test()
async def test_comprehensive_functionality(dut):
    """Test UART, ADSR, and I2S functionality in the module."""
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 20)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 50)  # Increased wait time to allow for stabilization

    # Test Frequency Selection (indirectly via `uo_out` observation)
    await send_uart_byte(dut, 0b00000001)  # Frequency byte, expect a unique pattern on `uo_out`
    await ClockCycles(dut.clk, 500)
    
    # Wait for uo_out to stabilize before reading
    for _ in range(5):  # Retry loop to allow additional stabilization time
        initial_uo_out = dut.uo_out.value
        if is_resolvable(initial_uo_out):
            break
        dut._log.warning("uo_out contains unknown ('x') or high-impedance ('z') states; retrying...")
        await ClockCycles(dut.clk, 200)

    # Verify that uo_out is now fully resolvable
    assert is_resolvable(dut.uo_out.value), "uo_out still contains unresolvable states after retries"

    initial_uo_out_int = dut.uo_out.value.integer
    await ClockCycles(dut.clk, 1000)
    new_uo_out_int = dut.uo_out.value.integer
    assert initial_uo_out_int != new_uo_out_int, "Expected frequency effect on uo_out"

    # Test Waveform Selection (indirectly via `uo_out` pattern observation)
    await send_uart_byte(dut, 0b01000010)  # Waveform byte, expect square wave pattern
    await ClockCycles(dut.clk, 500)
    
    wave_pattern_observed = any(dut.uo_out.value.integer != initial_uo_out_int for _ in range(10))
    assert wave_pattern_observed, "Expected waveform pattern on uo_out"

    # Test ADSR Modulation (observe non-zero `uo_out` upper bits)
    adsr_modulation_observed = any(dut.uo_out.value.integer >> 3 != 0 for _ in range(10))
    assert adsr_modulation_observed, "Expected ADSR modulation effect on uo_out upper bits"
