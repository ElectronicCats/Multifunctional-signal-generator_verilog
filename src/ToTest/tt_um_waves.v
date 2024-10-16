`include "triangular_wave_generator.v"
`include "sawtooth_wave_generator.v"
`include "square_wave_generator.v"
`include "sine_wave_generator.v"
`include "adsr_generator.v"

module tt_um_waves (
    input wire clk,                    // Reloj del sistema (25 MHz)
    input wire reset,                  // Señal de reinicio
    input wire [5:0] freq_select,      // Selección de frecuencia (6 bits para 64 niveles)
    input wire [7:0] attack,    // Parámetro de ataque para ADSR
    input wire [7:0] decay,     // Parámetro de decaimiento para ADSR
    input wire [7:0] sustain,   // Parámetro de sostenimiento para ADSR
    input wire [7:0] rel,       // Parámetro de liberación para ADSR
    input wire  [1:0] wave_select,     // Selección de tipo de onda: 0=Triangular, 1=Cuadrada
    output wire [7:0] wave_out,         // Salida de onda cuadrada de 8 bits
    output wire [7:0] amplitude // Amplitud del ADSR para visualización
);

    wire [7:0] tri_wave_out;    // Onda triangular original
    wire [7:0] saw_wave_out;    // Onda diente de sierra original
    wire [7:0] sqr_wave_out;    // Onda cuadrada original
    wire [7:0] sine_wave_out;    // Onda cuadrada original
    wire [7:0] adsr_amplitude;  // Amplitud generada por el ADSR
    reg [7:0] selected_wave;    // Onda seleccionada (triangular o cuadrada)
    reg [31:0] clk_div;                // Contador para el divisor de reloj
    reg clk_divided;                   // Señal de reloj dividida
    reg [31:0] clk_div_threshold;      // Umbral del divisor de reloj

    // Lógica para seleccionar el umbral del divisor de reloj según la frecuencia deseada
    always @(*) begin
        case (freq_select)
            // Octave 2
            6'b000000: clk_div_threshold = 32'd1915712;  // C2 (65.41 Hz)
            6'b000001: clk_div_threshold = 32'd1803586;  // C#2/Db2 (69.30 Hz)
            6'b000010: clk_div_threshold = 32'd1702624;  // D2 (73.42 Hz)
            6'b000011: clk_div_threshold = 32'd1607142;  // D#2/Eb2 (77.78 Hz)
            6'b000100: clk_div_threshold = 32'd1515152;  // E2 (82.41 Hz)
            6'b000101: clk_div_threshold = 32'd1431731;  // F2 (87.31 Hz)
            6'b000110: clk_div_threshold = 32'd1351351;  // F#2/Gb2 (92.50 Hz)
            6'b000111: clk_div_threshold = 32'd1275510;  // G2 (98.00 Hz)
            6'b001000: clk_div_threshold = 32'd1204819;  // G#2/Ab2 (103.83 Hz)
            6'b001001: clk_div_threshold = 32'd1136364;  // A2 (110.00 Hz)
            6'b001010: clk_div_threshold = 32'd1075268;  // A#2/Bb2 (116.54 Hz)
            6'b001011: clk_div_threshold = 32'd1017340;  // B2 (123.47 Hz)

            // Octave 3
            6'b001100: clk_div_threshold = 32'd957869;   // C3 (130.81 Hz)
            6'b001101: clk_div_threshold = 32'd901803;   // C#3/Db3 (138.59 Hz)
            6'b001110: clk_div_threshold = 32'd851315;   // D3 (146.83 Hz)
            6'b001111: clk_div_threshold = 32'd803571;   // D#3/Eb3 (155.56 Hz)
            6'b010000: clk_div_threshold = 32'd757576;   // E3 (164.81 Hz)
            6'b010001: clk_div_threshold = 32'd715867;   // F3 (174.61 Hz)
            6'b010010: clk_div_threshold = 32'd675676;   // F#3/Gb3 (185.00 Hz)
            6'b010011: clk_div_threshold = 32'd637755;   // G3 (196.00 Hz)
            6'b010100: clk_div_threshold = 32'd602411;   // G#3/Ab3 (207.65 Hz)
            6'b010101: clk_div_threshold = 32'd568182;   // A3 (220.00 Hz)
            6'b010110: clk_div_threshold = 32'd537634;   // A#3/Bb3 (233.08 Hz)
            6'b010111: clk_div_threshold = 32'd508673;   // B3 (246.94 Hz)

            //Octave 4
            6'b011000: clk_div_threshold = 32'd478783;   // C4 (261.63 Hz)
            6'b011001: clk_div_threshold = 32'd450905;   // C#4/Db4 (277.18 Hz)
            6'b011010: clk_div_threshold = 32'd425662;   // D4 (293.66 Hz)
            6'b011011: clk_div_threshold = 32'd401785;   // D#4/Eb4 (311.13 Hz)
            6'b011100: clk_div_threshold = 32'd378788;   // E4 (329.63 Hz)
            6'b011101: clk_div_threshold = 32'd357931;   // F4 (349.23 Hz)
            6'b011110: clk_div_threshold = 32'd337837;   // F#4/Gb4 (369.99 Hz)
            6'b011111: clk_div_threshold = 32'd318878;   // G4 (392.00 Hz)
            6'b100000: clk_div_threshold = 32'd301204;   // G#4/Ab4 (415.30 Hz)
            6'b100001: clk_div_threshold = 32'd284091;   // A4 (440.00 Hz)
            6'b100010: clk_div_threshold = 32'd268819;   // A#4/Bb4 (466.16 Hz)
            6'b100011: clk_div_threshold = 32'd254344;   // B4 (493.88 Hz)
          
          // Octave 5
            6'b100100: clk_div_threshold = 32'd239758;   // C5 (523.25 Hz)
            6'b100101: clk_div_threshold = 32'd225451;   // C#5/Db5 (554.37 Hz)
            6'b100110: clk_div_threshold = 32'd212328;   // D5 (587.33 Hz)
            6'b100111: clk_div_threshold = 32'd200892;   // D#5/Eb5 (622.25 Hz)
            6'b101000: clk_div_threshold = 32'd189394;   // E5 (659.25 Hz)
            6'b101001: clk_div_threshold = 32'd178966;   // F5 (698.46 Hz)
            6'b101010: clk_div_threshold = 32'd168919;   // F#5/Gb5 (739.99 Hz)
            6'b101011: clk_div_threshold = 32'd159439;   // G5 (783.99 Hz)
            6'b101100: clk_div_threshold = 32'd150602;   // G#5/Ab5 (830.61 Hz)
            6'b101101: clk_div_threshold = 32'd142045;   // A5 (880.00 Hz)
            6'b101110: clk_div_threshold = 32'd134410;   // A#5/Bb5 (932.33 Hz)
            6'b101111: clk_div_threshold = 32'd127172;   // B5 (987.77 Hz)
          
            // Octave 6
            6'b110000: clk_div_threshold = 32'd11969;    // C6 (1046.50 Hz)
            6'b110001: clk_div_threshold = 32'd11273;    // C#6/Db6 (1108.73 Hz)
            6'b110010: clk_div_threshold = 32'd10643;    // D6 (1174.66 Hz)
            6'b110011: clk_div_threshold = 32'd10045;    // D#6/Eb6 (1244.51 Hz)
            6'b110100: clk_div_threshold = 32'd9467;     // E6 (1318.51 Hz)
            6'b110101: clk_div_threshold = 32'd8948;     // F6 (1396.91 Hz)
            6'b110110: clk_div_threshold = 32'd8445;     // F#6/Gb6 (1479.98 Hz)
            6'b110111: clk_div_threshold = 32'd7972;     // G6 (1567.98 Hz)
            6'b111000: clk_div_threshold = 32'd7518;     // G#6/Ab6 (1661.22 Hz)
            6'b111001: clk_div_threshold = 32'd7102;     // A6 (1760.00 Hz)
            6'b111010: clk_div_threshold = 32'd6719;     // A#6/Bb6 (1864.66 Hz)
            6'b111011: clk_div_threshold = 32'd6359;     // B6 (1975.53 Hz)


            default: clk_div_threshold = 32'd284091;     // Default to A4 (440 Hz)
        endcase
    end

    // Divisor de reloj para ajustar la frecuencia de salida
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            clk_div <= 32'd0;
            clk_divided <= 1'b0;
        end else begin
            if (clk_div >= clk_div_threshold) begin
                clk_div <= 32'd0;
                clk_divided <= ~clk_divided; // Alterna el estado del reloj dividido
            end else begin
                clk_div <= clk_div + 1;
            end
        end
    end

    // Instanciar el generador de onda triangular
    triangular_wave_generator triangle_gen (
      .clk(clk_divided),
        .reset(reset),
        .wave_out(tri_wave_out)   // Onda triangular generada
    );

    // Instanciar el generador de onda diente de sierra
    sawtooth_wave_generator saw_gen (
        .clk(clk_divided),
        .reset(reset),
        .wave_out(saw_wave_out)   // Onda diente de sierra generada
    );

    // Instanciar el generador de onda cuadrada
    square_wave_generator sqr_gen (
        .clk(clk_divided),
        .reset(reset),
        .wave_out(sqr_wave_out)   // Onda cuadrada generada
    );

    // Instanciar el generador de onda senoidal
    sine_wave_generator sine_gen (
        .clk(clk_divided),
        .reset(reset),
        .wave_out(sine_wave_out)   // Onda senoidal generada
    );

    // Instanciar el generador ADSR
    adsr_generator adsr_gen (
        .clk(clk_divided),
        .rst_n(~reset),           // Reset activo en bajo
        .attack(attack),
        .decay(decay),
        .sustain(sustain),
        .rel(rel),
        .amplitude(adsr_amplitude)  // Amplitud modulada por ADSR
    );

    // Seleccionar entre la onda triangular, diente de sierra, cuadrada y senoidal
    always @(*) begin
        case (wave_select)
            2'b00: selected_wave = tri_wave_out;   // Selección de onda triangular
            2'b01: selected_wave = saw_wave_out;   // Selección de onda diente de sierra
            2'b10: selected_wave = sqr_wave_out;   // Selección de onda cuadrada
            2'b11: selected_wave = sine_wave_out;  // Selección de onda senoidal
            default: selected_wave = 8'd0;         // En caso de valor inválido, salida en 0
        endcase
    end

    // Modulación de la onda seleccionada con la amplitud del ADSR
    assign wave_out = (adsr_amplitude > 0 && selected_wave > 0) ? (selected_wave * adsr_amplitude) >> 8 : 0;

    // Exponer la amplitud del ADSR para visualización
    assign amplitude = adsr_amplitude;

endmodule