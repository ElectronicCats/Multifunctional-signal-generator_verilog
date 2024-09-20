module wave_with_adsr (
    input wire clk,             // Reloj de entrada
    input wire reset,           // Señal de reinicio
    input wire [7:0] attack,    // Parámetro de ataque para ADSR
    input wire [7:0] decay,     // Parámetro de decaimiento para ADSR
    input wire [7:0] sustain,   // Parámetro de sostenimiento para ADSR
    input wire [7:0] rel,   // Parámetro de liberación para ADSR
    output wire [7:0] wave_out, // Onda triangular modulada por ADSR
    output wire [7:0] amplitude // Amplitud del ADSR para visualización
);

    // Salidas intermedias
    wire [7:0] tri_wave_out;    // Onda triangular original
    wire [7:0] adsr_amplitude;  // Amplitud generada por el ADSR

    // Instanciar el generador de onda triangular
    triangular_wave_generator triangle_gen (
        .clk(clk),
        .reset(reset),
        .wave_out(tri_wave_out)   // Onda triangular generada
    );

    // Instanciar el generador ADSR
    adsr_generator adsr_gen (
        .clk(clk),
        .rst_n(~reset),          // Reset activo en bajo
        .attack(attack),
        .decay(decay),
        .sustain(sustain),
        .rel(rel),
        .amplitude(adsr_amplitude)  // Amplitud modulada por ADSR
    );

    // Modulación de la onda triangular con la amplitud del ADSR
    assign wave_out = (adsr_amplitude > 0 && tri_wave_out > 0) ? (tri_wave_out * adsr_amplitude) >> 8 : 0;


    // Expose the ADSR amplitude for visualization
    assign amplitude = adsr_amplitude;

endmodule

module triangular_wave_generator (
    input wire clk,            // Reloj de entrada
    input wire reset,          // Señal de reinicio
    output reg [7:0] wave_out  // Salida de onda triangular de 8 bits
);

    reg [7:0] counter;  // Contador para la onda triangular
    reg direction;      // Dirección del contador (ascendente o descendente)

    // Lógica del generador de onda triangular
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            counter <= 8'd0;      // Reiniciar el contador a 0
            direction <= 1'b1;    // Iniciar en modo ascendente
        end else begin
            if (direction) begin
                if (counter < 8'd255) begin
                    counter <= counter + 1;  // Incrementar el contador
                end else begin
                    direction <= 1'b0;  // Cambiar a modo descendente
                end
            end else begin
                if (counter > 8'd0) begin
                    counter <= counter - 1;  // Decrementar el contador
                end else begin
                    direction <= 1'b1;  // Cambiar a modo ascendente
                end
            end
        end
    end

    // Asignar el valor del contador a la salida
    always @(posedge clk) begin
        wave_out <= counter;
    end

endmodule

module adsr_generator (
    input  wire       clk,       // Clock
    input  wire       rst_n,     // Reset, active low
    input  wire [7:0] attack,    // Attack value
    input  wire [7:0] decay,     // Decay value
    input  wire [7:0] sustain,   // Sustain value
    input  wire [7:0] rel,       // Release value
    output reg  [7:0] amplitude  // Generated amplitude signal
);

    reg [3:0] state;  // State of ADSR: 0=idle, 1=attack, 2=decay, 3=sustain, 4=release
    reg [7:0] counter;  // A counter to handle timing of each phase

    // Define states for better readability
    localparam STATE_IDLE     = 4'd0;
    localparam STATE_ATTACK   = 4'd1;
    localparam STATE_DECAY    = 4'd2;
    localparam STATE_SUSTAIN  = 4'd3;
    localparam STATE_RELEASE  = 4'd4;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // On reset, return to idle state and reset amplitude
            state <= STATE_IDLE;
            amplitude <= 8'd0;
            counter <= 8'd0;
        end else begin
            case (state)
                STATE_IDLE: begin
                    // Start the attack phase based on some external trigger condition
                    // Example trigger: counter reaches a certain value
                    if (counter == 8'd255) begin
                        state <= STATE_ATTACK;
                        counter <= 8'd0;  // Reset the counter for the next phase
                    end else begin
                        counter <= counter + 1;
                    end
                end
                STATE_ATTACK: begin
                    // Increase amplitude until it reaches the attack value
                    if (amplitude < attack) begin
                        amplitude <= amplitude + 1;
                    end else begin
                        state <= STATE_DECAY;
                    end
                end
                STATE_DECAY: begin
                    // Decrease amplitude until it reaches the sustain level
                    if (amplitude > sustain) begin
                        amplitude <= amplitude - 1;
                    end else begin
                        state <= STATE_SUSTAIN;
                    end
                end
                STATE_SUSTAIN: begin
                    // Maintain amplitude at sustain level until release condition is met
                    amplitude <= sustain;
                    
                    // Check for release condition (external trigger or timer)
                    if (counter == 8'd255) begin
                        state <= STATE_RELEASE;
                        counter <= 8'd0;  // Reset counter for the release phase
                    end else begin
                        counter <= counter + 1;
                    end
                end
                STATE_RELEASE: begin
                    // Gradually decrease amplitude to zero (release phase)
                    if (amplitude > 0) begin
                        amplitude <= amplitude - 1;
                    end else begin
                        state <= STATE_IDLE;  // Return to idle once the release phase ends
                    end
                end
                default: state <= STATE_IDLE;  // Fallback to idle state in case of an unknown state
            endcase
        end
    end
endmodule
