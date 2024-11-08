import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

async def send_uart_byte(dut, byte_value):
    """Simulate UART byte transmission with start and stop bits."""
    dut.ui_in[0].value = 0  # Start bit
    await ClockCycles(dut.clk, 2604)  # Adjust for baud rate timing

    for i in range(8):
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 2604)

    dut.ui_in[0].value = 1  # Stop bit
    await ClockCycles(dut.clk, 2604)

@cocotb.test()
async def test_tt_um_waves(dut):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # Test UART frequency selection for ASCII '1' (which should map to freq_select = 1)
    await send_uart_byte(dut, ord('1'))
    await ClockCycles(dut.clk, 100)
    assert dut.freq_select.value == 1, "Expected freq_select to be 1 for input '1'"

    # Test wave selection - ASCII 'S' should select the sawtooth wave (wave_select = 01)
    await send_uart_byte(dut, ord('S'))
    await ClockCycles(dut.clk, 100)
    assert dut.wave_select.value == 1, "Expected wave_select to be 01 for input 'S' (Sawtooth wave)"

    # Test attack encoder by setting encoder signals
    dut.uio_in[0].value = 1  # encoder_a_attack
    dut.uio_in[1].value = 0  # encoder_b_attack
    await ClockCycles(dut.clk, 50)
    assert dut.attack.value > 0, "Expected non-zero attack value"

    # Check I2S signal behavior as indirect verification of clk_divided functionality
    initial_sck = dut.uo_out[0].value  # sck
    await ClockCycles(dut.clk, 10)
    assert dut.uo_out[0].value != initial_sck, "Expected sck toggling in I2S output"

    # Check word select toggling in I2S output
    initial_ws = dut.uo_out[1].value  # ws
    await ClockCycles(dut.clk, 16)
    assert dut.uo_out[1].value != initial_ws, "Expected ws toggling in I2S output"

    # Verify `sd` outputs valid bits from the modulated wave
    for _ in range(16):
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out[2].value in (0, 1), "Expected valid bit in `sd` (0 or 1) during I2S transmission"
