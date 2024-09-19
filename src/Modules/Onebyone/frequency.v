module frequency_selector (
    input wire [5:0] freq_select,    // Selección de frecuencia (6 bits para 64 niveles)
    output reg [31:0] clk_div_threshold // Umbral para el divisor de reloj
);

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
            6'b001100: clk_div_threshold = 32'd95786;    // C3 (130.81 Hz)
            6'b001101: clk_div_threshold = 32'd90180;    // C#3/Db3 (138.59 Hz)
            6'b001110: clk_div_threshold = 32'd85131;    // D3 (146.83 Hz)
            6'b001111: clk_div_threshold = 32'd80357;    // D#3/Eb3 (155.56 Hz)
            6'b010000: clk_div_threshold = 32'd75758;    // E3 (164.81 Hz)
            6'b010001: clk_div_threshold = 32'd71586;    // F3 (174.61 Hz)
            6'b010010: clk_div_threshold = 32'd67567;    // F#3/Gb3 (185.00 Hz)
            6'b010011: clk_div_threshold = 32'd63775;    // G3 (196.00 Hz)
            6'b010100: clk_div_threshold = 32'd60241;    // G#3/Ab3 (207.65 Hz)
            6'b010101: clk_div_threshold = 32'd56818;    // A3 (220.00 Hz)
            6'b010110: clk_div_threshold = 32'd53763;    // A#3/Bb3 (233.08 Hz)
            6'b010111: clk_div_threshold = 32'd50867;    // B3 (246.94 Hz)

            // Octave 4
            6'b011000: clk_div_threshold = 32'd47878;    // C4 (261.63 Hz)
            6'b011001: clk_div_threshold = 32'd45090;    // C#4/Db4 (277.18 Hz)
            6'b011010: clk_div_threshold = 32'd42566;    // D4 (293.66 Hz)
            6'b011011: clk_div_threshold = 32'd40178;    // D#4/Eb4 (311.13 Hz)
            6'b011100: clk_div_threshold = 32'd37878;    // E4 (329.63 Hz)
            6'b011101: clk_div_threshold = 32'd35793;    // F4 (349.23 Hz)
            6'b011110: clk_div_threshold = 32'd33783;    // F#4/Gb4 (369.99 Hz)
            6'b011111: clk_div_threshold = 32'd31888;    // G4 (392.00 Hz)
            6'b100000: clk_div_threshold = 32'd30120;    // G#4/Ab4 (415.30 Hz)
            6'b100001: clk_div_threshold = 32'd28409;    // A4 (440.00 Hz)
            6'b100010: clk_div_threshold = 32'd26881;    // A#4/Bb4 (466.16 Hz)
            6'b100011: clk_div_threshold = 32'd25434;    // B4 (493.88 Hz)

            // Octave 5
            6'b100100: clk_div_threshold = 32'd23939;    // C5 (523.25 Hz)
            6'b100101: clk_div_threshold = 32'd22545;    // C#5/Db5 (554.37 Hz)
            6'b100110: clk_div_threshold = 32'd21283;    // D5 (587.33 Hz)
            6'b100111: clk_div_threshold = 32'd20089;    // D#5/Eb5 (622.25 Hz)
            6'b101000: clk_div_threshold = 32'd18938;    // E5 (659.25 Hz)
            6'b101001: clk_div_threshold = 32'd17896;    // F5 (698.46 Hz)
            6'b101010: clk_div_threshold = 32'd16891;    // F#5/Gb5 (739.99 Hz)
            6'b101011: clk_div_threshold = 32'd15944;    // G5 (783.99 Hz)
            6'b101100: clk_div_threshold = 32'd15060;    // G#5/Ab5 (830.61 Hz)
            6'b101101: clk_div_threshold = 32'd14204;    // A5 (880.00 Hz)
            6'b101110: clk_div_threshold = 32'd13441;    // A#5/Bb5 (932.33 Hz)
            6'b101111: clk_div_threshold = 32'd12717;    // B5 (987.77 Hz)

            // Octave 6
            6'b110000: clk_div_threshold = 32'd11969;    // C6 (1046.50 Hz)
            6'b110001: clk_div_threshold = 32'd11272;    // C#6/Db6 (1108.73 Hz)
            6'b110010: clk_div_threshold = 32'd10642;    // D6 (1174.66 Hz)
            6'b110011: clk_div_threshold = 32'd10044;    // D#6/Eb6 (1244.51 Hz)
            6'b110100: clk_div_threshold = 32'd9470;     // E6 (1318.51 Hz)
            6'b110101: clk_div_threshold = 32'd8948;     // F6 (1396.91 Hz)
            6'b110110: clk_div_threshold = 32'd8445;     // F#6/Gb6 (1479.98 Hz)
            6'b110111: clk_div_threshold = 32'd7972;     // G6 (1567.98 Hz)
            6'b111000: clk_div_threshold = 32'd7518;     // G#6/Ab6 (1661.22 Hz)
            6'b111001: clk_div_threshold = 32'd7090;     // A6 (1760.00 Hz)
            6'b111010: clk_div_threshold = 32'd6719;     // A#6/Bb6 (1864.66 Hz)
            6'b111011: clk_div_threshold = 32'd6358;     // B6 (1975.53 Hz)

            default: clk_div_threshold = 32'd28409;      // Default to A4 (440 Hz)
        endcase
    end

endmodule
