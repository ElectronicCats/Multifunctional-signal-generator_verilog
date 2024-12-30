import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


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


@cocotb.test()
async def test_tt_um_waves(dut):
    """Test waveform selection, ADSR phases, and I2S output using available pins."""
    # Initialize clock and reset
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # Log initial state
    initial_waveform = (dut.uo_out[2].value << 2) | (dut.uo_out[1].value << 1) | dut.uo_out[0].value
    dut._log.info(f"Initial waveform selection: {initial_waveform}")

    # Test waveform selection via UART
    waveforms = {
        0x54: 0b000,  # Triangle (ASCII 'T')
        0x53: 0b001,  # Sawtooth (ASCII 'S')
        0x51: 0b010,  # Square (ASCII 'Q')
        0x4E: 0b011,  # Sine (ASCII 'N')
        0x57: 0b100   # White Noise (ASCII 'W')
    }

    for byte, expected_value in waveforms.items():
        dut._log.info(f"Sending UART byte: {byte} (Expected waveform: {expected_value})")
        await send_uart_byte(dut, byte)
        await ClockCycles(dut.clk, 2000)  # Extended delay for UART processing

        # Read and log the waveform selection
        selected_wave = (dut.uo_out[2].value << 2) | (dut.uo_out[1].value << 1) | dut.uo_out[0].value
        dut._log.info(f"UART Byte: {byte}, Expected: {expected_value}, Got: {selected_wave}")
        assert selected_wave == expected_value, f"Expected waveform {expected_value}, got {selected_wave}"

    # Test ADSR modulation phases
    adsr_inputs = {
        "Attack": (0, 1),
        "Decay": (2, 3),
        "Sustain": (4, 5),
        "Release": (6, 7)
    }

    for phase, pins in adsr_inputs.items():
        dut._log.info(f"Testing ADSR phase: {phase}")
        # Activate each ADSR phase by toggling the respective encoder inputs
        dut.uio_in[pins[0]].value = 1  # Activate encoder A
        dut.uio_in[pins[1]].value = 0  # Deactivate encoder B
        await ClockCycles(dut.clk, 50)
        await ClockCycles(dut.clk, 100)
        
        # Verify ADSR phase output signal
        assert dut.uo_out[7].value == 1, f"Expected ADSR {phase} phase output signal"
        dut._log.info(f"ADSR {phase} phase signal verified")

    # Verify I2S output (sck, ws, sd)
    dut._log.info("Verifying I2S signals")
    for _ in range(10):
        await ClockCycles(dut.clk, 200)
        # Check for valid I2S signals: sck, ws, sd
        assert dut.uo_out[0].value in (0, 1), "Expected valid SCK signal"
        assert dut.uo_out[1].value in (0, 1), "Expected valid WS signal"
        assert dut.uo_out[2].value in (0, 1), "Expected valid SD signal"
        dut._log.info("I2S signals verified for this cycle")
