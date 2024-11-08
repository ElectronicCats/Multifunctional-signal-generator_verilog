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
    # Inicialización del reloj y reset
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # Verificar que la selección de onda cambia después de 1000 ciclos
    prev_selected_wave = int("".join(str(dut.uo_out[i].value) for i in range(3)), 2)
    await ClockCycles(dut.clk, 1000)
    current_selected_wave = int("".join(str(dut.uo_out[i].value) for i in range(3)), 2)
    assert current_selected_wave != prev_selected_wave, "Expected `selected_wave` to change after 1000 cycles."

    # Simular la transmisión UART con byte '1'
    await send_uart_byte(dut, 0x31)  # ASCII '1'
    await ClockCycles(dut.clk, 500)

    # Simular la modulación ADSR cambiando los valores de entrada
    dut.uio_in[0].value = 1  # Attack
    dut.uio_in[1].value = 0
    await ClockCycles(dut.clk, 50)

    # Verificación del cambio en las señales de depuración durante la fase de Attack
    initial_attack = dut.debug_attack.value
    await ClockCycles(dut.clk, 100)
    assert dut.debug_attack.value != initial_attack, "Expected `debug_attack` to change during attack phase"

    dut.uio_in[2].value = 1  # Decay
    dut.uio_in[3].value = 0
    await ClockCycles(dut.clk, 50)

    # Verificación del cambio en las señales de depuración durante la fase de Decay
    initial_decay = dut.debug_decay.value
    await ClockCycles(dut.clk, 100)
    assert dut.debug_decay.value != initial_decay, "Expected `debug_decay` to change during decay phase"

    dut.uio_in[4].value = 1  # Sustain
    dut.uio_in[5].value = 0
    await ClockCycles(dut.clk, 50)

    # Verificación del valor constante de las señales de depuración durante la fase de Sustain
    initial_sustain = dut.debug_sustain.value
    await ClockCycles(dut.clk, 100)
    assert dut.debug_sustain.value == initial_sustain, "Expected `debug_sustain` to remain constant during sustain phase"

    dut.uio_in[6].value = 1  # Release
    dut.uio_in[7].value = 0
    await ClockCycles(dut.clk, 50)

    # Verificación del cambio en las señales de depuración durante la fase de Release
    initial_rel = dut.debug_rel.value
    await ClockCycles(dut.clk, 100)
    assert dut.debug_rel.value != initial_rel, "Expected `debug_rel` to change during release phase"

    # Verificar la transmisión I2S: sck, ws y sd en `uo_out`
    for _ in range(10):
        await ClockCycles(dut.clk, 200)
        if is_resolvable(dut.uo_out.value[0:3]):
            break

    assert is_resolvable(dut.uo_out.value[0:3]), "uo_out[0:3] contiene estados no resolubles después de reintentos."

    # Observamos el cambio en los valores I2S
    initial_sck = dut.uo_out[0].value  # sck
    await ClockCycles(dut.clk, 10)
    assert dut.uo_out[0].value != initial_sck, "Expected sck toggling in I2S output"

    initial_ws = dut.uo_out[1].value  # ws
    await ClockCycles(dut.clk, 16)  # ws típicamente cambia a la mitad de la frecuencia de sck
    assert dut.uo_out[1].value != initial_ws, "Expected ws toggling in I2S output"

    for _ in range(10):
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out[2].value in (0, 1), "Expected valid sd bit (0 or 1) in I2S output"
