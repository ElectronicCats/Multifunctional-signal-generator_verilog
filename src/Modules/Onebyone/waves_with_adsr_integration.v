module wave_with_adsr (
    input wire clk,             // Reloj de entrada
    input wire reset,           // Señal de reinicio
    input wire [7:0] attack,    // Parámetro de ataque para ADSR
    input wire [7:0] decay,     // Parámetro de decaimiento para ADSR
    input wire [7:0] sustain,   // Parámetro de sostenimiento para ADSR
    input wire [7:0] rel,       // Parámetro de liberación para ADSR
    input wire  [1:0] wave_select,     // Selección de tipo de onda: 0=Triangular, 1=Cuadrada
    output wire [7:0] wave_out, // Onda modulada por ADSR (triangular o cuadrada)
    output wire [7:0] amplitude // Amplitud del ADSR para visualización
);

    // Salidas intermedias
    wire [7:0] tri_wave_out;    // Onda triangular original
    wire [7:0] saw_wave_out;    // Onda diente de sierra original
    wire [7:0] sqr_wave_out;    // Onda cuadrada original
    wire [7:0] sine_wave_out;    // Onda cuadrada original
    wire [7:0] adsr_amplitude;  // Amplitud generada por el ADSR
    reg [7:0] selected_wave;    // Onda seleccionada (triangular o cuadrada)

    // Instanciar el generador de onda triangular
    triangular_wave_generator triangle_gen (
        .clk(clk),
        .reset(reset),
        .wave_out(tri_wave_out)   // Onda triangular generada
    );
  
    // Instanciar el generador de onda diente de sierra
    sawtooth_wave_generator saw_gen (
        .clk(clk),
        .reset(reset),
        .wave_out(saw_wave_out)   // Onda diente de sierra generada
    );
  
    // Instanciar el generador de onda cuadrada
    square_wave_generator sqr_gen (
        .clk(clk),
        .reset(reset),
        .wave_out(sqr_wave_out)   // Onda cuadrada generada
    );
  
    sine_wave_generator sine_gen (
        .clk(clk),
        .reset(reset),
      .wave_out(sine_wave_out)   // Onda cuadrada generada
    );

    // Instanciar el generador ADSR
    adsr_generator adsr_gen (
        .clk(clk),
        .rst_n(~reset),           // Reset activo en bajo
        .attack(attack),
        .decay(decay),
        .sustain(sustain),
        .rel(rel),
        .amplitude(adsr_amplitude)  // Amplitud modulada por ADSR
    );

    // Seleccionar entre la onda triangular, diente de sierra y la onda cuadrada
    always @(*) begin
        case (wave_select)
            2'b00: selected_wave = tri_wave_out;   // Selección de onda triangular
            2'b01: selected_wave = saw_wave_out;   // Selección de onda diente de sierra
            2'b10: selected_wave = sqr_wave_out;   // Selección de onda cuadrada
            2'b11: selected_wave = sine_wave_out;  //Selección de onda senoidal
            default: selected_wave = 8'd0;         // En caso de valor inválido, salida en 0
        endcase
    end

    // Modulación de la onda seleccionada con la amplitud del ADSR
    assign wave_out = (adsr_amplitude > 0 && selected_wave > 0) ? (selected_wave * adsr_amplitude) >> 8 : 0;

    // Exponer la amplitud del ADSR para visualización
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

module sawtooth_wave_generator (
    input wire clk,            // Reloj de entrada
    input wire reset,          // Señal de reinicio
    output reg [7:0] wave_out  // Salida de onda diente de sierra de 8 bits
);

    reg [7:0] counter;  // Contador para la onda diente de sierra

    // Lógica del generador de onda diente de sierra
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            counter <= 8'd0;  // Reiniciar el contador a 0
        end else begin
            counter <= counter + 1;  // Incrementar el contador
        end
    end

    // Asignar el valor del contador a la salida
    always @(posedge clk) begin
        wave_out <= counter;
    end

endmodule

module square_wave_generator (
    input wire clk,                  // Reloj del sistema
    input wire reset,                // Señal de reinicio
    output reg [7:0] wave_out        // Salida de onda cuadrada de 8 bits
);

    reg [7:0] counter;               // Contador para controlar la frecuencia de la onda cuadrada
    reg wave_state;                  // Estado actual de la onda cuadrada

    parameter MAX_COUNT = 8'd127;    // Valor máximo del contador para una frecuencia ajustada

    // Inicialización
    initial begin
        wave_state = 1'b0;
        wave_out = 8'd0;
        counter = 8'd0;
    end

    // Generación de la onda cuadrada
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            counter <= 8'd0;         // Reiniciar el contador
            wave_state <= 1'b0;      // Reiniciar el estado de la onda
            wave_out <= 8'd0;        // Reiniciar la salida de la onda
        end else begin
            if (counter == MAX_COUNT) begin
                wave_state <= ~wave_state;  // Cambiar el estado de la onda cuadrada
                wave_out <= (wave_state) ? 8'd255 : 8'd0; // Establecer la salida de la onda cuadrada
                counter <= 8'd0;       // Reiniciar el contador después de un ciclo completo
            end else begin
                counter <= counter + 1;  // Incrementar el contador
            end
        end
    end

endmodule

module sine_wave_generator (
    input wire clk,                  // Reloj de entrada
    input wire reset,                // Señal de reinicio
    output reg [7:0] wave_out        // Salida de onda senoidal de 8 bits
);

    reg [7:0] counter;               // Contador para indexar la tabla
    reg [7:0] sine_table [0:255];    // Tabla de valores senoidales (256 valores de 8 bits)

    // Inicialización de la tabla de valores senoidales
    initial begin
        sine_table[0] = 8'd128;
        sine_table[1] = 8'd131;
        sine_table[2] = 8'd134;
        sine_table[3] = 8'd137;
        sine_table[4] = 8'd140;
        sine_table[5] = 8'd143;
        sine_table[6] = 8'd146;
        sine_table[7] = 8'd149;
        sine_table[8] = 8'd152;
        sine_table[9] = 8'd155;
        sine_table[10] = 8'd158;
        sine_table[11] = 8'd161;
        sine_table[12] = 8'd164;
        sine_table[13] = 8'd167;
        sine_table[14] = 8'd170;
        sine_table[15] = 8'd173;
        sine_table[16] = 8'd176;
        sine_table[17] = 8'd179;
        sine_table[18] = 8'd182;
        sine_table[19] = 8'd185;
        sine_table[20] = 8'd187;
        sine_table[21] = 8'd190;
        sine_table[22] = 8'd193;
        sine_table[23] = 8'd195;
        sine_table[24] = 8'd198;
        sine_table[25] = 8'd201;
        sine_table[26] = 8'd203;
        sine_table[27] = 8'd206;
        sine_table[28] = 8'd208;
        sine_table[29] = 8'd210;
        sine_table[30] = 8'd213;
        sine_table[31] = 8'd215;
        sine_table[32] = 8'd217;
        sine_table[33] = 8'd219;
        sine_table[34] = 8'd222;
        sine_table[35] = 8'd224;
        sine_table[36] = 8'd226;
        sine_table[37] = 8'd228;
        sine_table[38] = 8'd230;
        sine_table[39] = 8'd231;
        sine_table[40] = 8'd233;
        sine_table[41] = 8'd235;
        sine_table[42] = 8'd236;
        sine_table[43] = 8'd238;
        sine_table[44] = 8'd240;
        sine_table[45] = 8'd241;
        sine_table[46] = 8'd242;
        sine_table[47] = 8'd244;
        sine_table[48] = 8'd245;
        sine_table[49] = 8'd246;
        sine_table[50] = 8'd247;
        sine_table[51] = 8'd248;
        sine_table[52] = 8'd249;
        sine_table[53] = 8'd250;
        sine_table[54] = 8'd251;
        sine_table[55] = 8'd251;
        sine_table[56] = 8'd252;
        sine_table[57] = 8'd253;
        sine_table[58] = 8'd253;
        sine_table[59] = 8'd254;
        sine_table[60] = 8'd254;
        sine_table[61] = 8'd254;
        sine_table[62] = 8'd254;
        sine_table[63] = 8'd254;
        sine_table[64] = 8'd255;
        sine_table[65] = 8'd254;
        sine_table[66] = 8'd254;
        sine_table[67] = 8'd254;
        sine_table[68] = 8'd254;
        sine_table[69] = 8'd254;
        sine_table[70] = 8'd253;
        sine_table[71] = 8'd253;
        sine_table[72] = 8'd252;
        sine_table[73] = 8'd251;
        sine_table[74] = 8'd251;
        sine_table[75] = 8'd250;
        sine_table[76] = 8'd249;
        sine_table[77] = 8'd248;
        sine_table[78] = 8'd247;
        sine_table[79] = 8'd246;
        sine_table[80] = 8'd245;
        sine_table[81] = 8'd244;
        sine_table[82] = 8'd242;
        sine_table[83] = 8'd241;
        sine_table[84] = 8'd240;
        sine_table[85] = 8'd238;
        sine_table[86] = 8'd236;
        sine_table[87] = 8'd235;
        sine_table[88] = 8'd233;
        sine_table[89] = 8'd231;
        sine_table[90] = 8'd230;
        sine_table[91] = 8'd228;
        sine_table[92] = 8'd226;
        sine_table[93] = 8'd224;
        sine_table[94] = 8'd222;
        sine_table[95] = 8'd219;
        sine_table[96] = 8'd217;
        sine_table[97] = 8'd215;
        sine_table[98] = 8'd213;
        sine_table[99] = 8'd210;
        sine_table[100] = 8'd208;
        sine_table[101] = 8'd206;
        sine_table[102] = 8'd203;
        sine_table[103] = 8'd201;
        sine_table[104] = 8'd198;
        sine_table[105] = 8'd195;
        sine_table[106] = 8'd193;
        sine_table[107] = 8'd190;
        sine_table[108] = 8'd187;
        sine_table[109] = 8'd185;
        sine_table[110] = 8'd182;
        sine_table[111] = 8'd179;
        sine_table[112] = 8'd176;
        sine_table[113] = 8'd173;
        sine_table[114] = 8'd170;
        sine_table[115] = 8'd167;
        sine_table[116] = 8'd164;
        sine_table[117] = 8'd161;
        sine_table[118] = 8'd158;
        sine_table[119] = 8'd155;
        sine_table[120] = 8'd152;
        sine_table[121] = 8'd149;
        sine_table[122] = 8'd146;
        sine_table[123] = 8'd143;
        sine_table[124] = 8'd140;
        sine_table[125] = 8'd137;
        sine_table[126] = 8'd134;
        sine_table[127] = 8'd131;
        sine_table[128] = 8'd128;
        sine_table[129] = 8'd124;
        sine_table[130] = 8'd121;
        sine_table[131] = 8'd118;
        sine_table[132] = 8'd115;
        sine_table[133] = 8'd112;
        sine_table[134] = 8'd109;
        sine_table[135] = 8'd106;
        sine_table[136] = 8'd103;
        sine_table[137] = 8'd100;
        sine_table[138] = 8'd97;
        sine_table[139] = 8'd94;
        sine_table[140] = 8'd91;
        sine_table[141] = 8'd88;
        sine_table[142] = 8'd85;
        sine_table[143] = 8'd82;
        sine_table[144] = 8'd79;
        sine_table[145] = 8'd76;
        sine_table[146] = 8'd73;
        sine_table[147] = 8'd70;
        sine_table[148] = 8'd68;
        sine_table[149] = 8'd65;
        sine_table[150] = 8'd62;
        sine_table[151] = 8'd60;
        sine_table[152] = 8'd57;
        sine_table[153] = 8'd54;
        sine_table[154] = 8'd52;
        sine_table[155] = 8'd49;
        sine_table[156] = 8'd47;
        sine_table[157] = 8'd45;
        sine_table[158] = 8'd42;
        sine_table[159] = 8'd40;
        sine_table[160] = 8'd38;
        sine_table[161] = 8'd36;
        sine_table[162] = 8'd33;
        sine_table[163] = 8'd31;
        sine_table[164] = 8'd29;
        sine_table[165] = 8'd27;
        sine_table[166] = 8'd25;
        sine_table[167] = 8'd24;
        sine_table[168] = 8'd22;
        sine_table[169] = 8'd20;
        sine_table[170] = 8'd19;
        sine_table[171] = 8'd17;
        sine_table[172] = 8'd15;
        sine_table[173] = 8'd14;
        sine_table[174] = 8'd13;
        sine_table[175] = 8'd11;
        sine_table[176] = 8'd10;
        sine_table[177] = 8'd9;
        sine_table[178] = 8'd8;
        sine_table[179] = 8'd7;
        sine_table[180] = 8'd6;
        sine_table[181] = 8'd5;
        sine_table[182] = 8'd4;
        sine_table[183] = 8'd4;
        sine_table[184] = 8'd3;
        sine_table[185] = 8'd2;
        sine_table[186] = 8'd2;
        sine_table[187] = 8'd1;
        sine_table[188] = 8'd1;
        sine_table[189] = 8'd1;
        sine_table[190] = 8'd1;
        sine_table[191] = 8'd1;
        sine_table[192] = 8'd1;
        sine_table[193] = 8'd1;
        sine_table[194] = 8'd1;
        sine_table[195] = 8'd1;
        sine_table[196] = 8'd1;
        sine_table[197] = 8'd1;
        sine_table[198] = 8'd2;
        sine_table[199] = 8'd2;
        sine_table[200] = 8'd3;
        sine_table[201] = 8'd4;
        sine_table[202] = 8'd4;
        sine_table[203] = 8'd5;
        sine_table[204] = 8'd6;
        sine_table[205] = 8'd7;
        sine_table[206] = 8'd8;
        sine_table[207] = 8'd9;
        sine_table[208] = 8'd10;
        sine_table[209] = 8'd11;
        sine_table[210] = 8'd13;
        sine_table[211] = 8'd14;
        sine_table[212] = 8'd15;
        sine_table[213] = 8'd17;
        sine_table[214] = 8'd19;
        sine_table[215] = 8'd20;
        sine_table[216] = 8'd22;
        sine_table[217] = 8'd24;
        sine_table[218] = 8'd25;
        sine_table[219] = 8'd27;
        sine_table[220] = 8'd29;
        sine_table[221] = 8'd31;
        sine_table[222] = 8'd33;
        sine_table[223] = 8'd36;
        sine_table[224] = 8'd38;
        sine_table[225] = 8'd40;
        sine_table[226] = 8'd42;
        sine_table[227] = 8'd45;
        sine_table[228] = 8'd47;
        sine_table[229] = 8'd49;
        sine_table[230] = 8'd52;
        sine_table[231] = 8'd54;
        sine_table[232] = 8'd57;
        sine_table[233] = 8'd60;
        sine_table[234] = 8'd62;
        sine_table[235] = 8'd65;
        sine_table[236] = 8'd68;
        sine_table[237] = 8'd70;
        sine_table[238] = 8'd73;
        sine_table[239] = 8'd76;
        sine_table[240] = 8'd79;
        sine_table[241] = 8'd82;
        sine_table[242] = 8'd85;
        sine_table[243] = 8'd88;
        sine_table[244] = 8'd91;
        sine_table[245] = 8'd94;
        sine_table[246] = 8'd97;
        sine_table[247] = 8'd100;
        sine_table[248] = 8'd103;
        sine_table[249] = 8'd106;
        sine_table[250] = 8'd109;
        sine_table[251] = 8'd112;
        sine_table[252] = 8'd115;
        sine_table[253] = 8'd118;
        sine_table[254] = 8'd121;
        sine_table[255] = 8'd124;
    end

    // Lógica de generación de onda senoidal
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            counter <= 8'd0;
            wave_out <= 8'd0;
        end else begin
            counter <= counter + 8'd1;
            wave_out <= sine_table[counter];  // Salida de la onda senoidal
        end
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
