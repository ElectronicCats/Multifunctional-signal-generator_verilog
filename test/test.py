import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

# UART transmission function to simulate sending a byte to the DUT's UART RX pin
async def send_uart_byte(dut, byte_value):
    # UART protocol simulation (1 start bit, 8 data bits, 1 stop bit)
    dut.ui_in[0].value = 0  # Start bit
    await ClockCycles(dut.clk, 2604)  # 9600 baud with 25 MHz clock
    
    # Send each bit in byte_value
    for i in range(8):
        dut.ui_in[0].value = (byte_value >> i) & 1
        await ClockCycles(dut.clk, 2604)

    dut.ui_in[0].value = 1  # Stop bit
    await ClockCycles(dut.clk, 2604)

@cocotb.test()
async def test_adsr_i2s_waveform(dut):
    # Initialize clock
    clock = Clock(dut.clk, 40, units="ns")  # Set clock period to 40 ns for 25 MHz
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # Send UART commands for sine wave and C#2 frequency
    await send_uart_byte(dut, 0x4E)  # 'N' for sine wave
    await send_uart_byte(dut, 0x31)  # '1' for C#2 frequency

    # ADSR and I2S signal monitoring
    sck_prev, ws_prev, sd_prev = dut.uo_out[0].value, dut.uo_out[1].value, dut.uo_out[2].value
    adsr_amplitude_signal = dut.tt_um_waves.adsr_amplitude

    for i in range(2000):
        await RisingEdge(dut.clk)
        sck_current, ws_current, sd_current = dut.uo_out[0].value, dut.uo_out[1].value, dut.uo_out[2].value
        adsr_amplitude = adsr_amplitude_signal.value

        # Check `sck` and `ws` toggling
        assert sck_current != sck_prev, "sck did not toggle as expected."
        if i % 32 == 0:
            assert ws_current != ws_prev, "ws did not toggle as expected for I2S frame."

        if i % 50 == 0:
            dut._log.info(f"ADSR Amplitude: {adsr_amplitude}, SD data: {sd_current}")

        sck_prev, ws_prev, sd_prev = sck_current, ws_current, sd_current
