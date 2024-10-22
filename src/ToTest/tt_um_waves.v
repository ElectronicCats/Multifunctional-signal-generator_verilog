/*
 * Copyright (c) 2024
 * SPDX-License-Identifier: Apache-2.0
 */

`define default_netname none

module tt_um_waves (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // Will go high when the design is enabled
    input  wire       clk,      // Clock
    input  wire       rst_n     // Reset_n - low to reset
);

    // Internal signals
    wire [5:0] freq_select = ui_in[5:0];    // Frequency selection from the first 6 bits of ui_in
    wire [1:0] wave_select = ui_in[7:6];    // Wave type selection from the last 2 bits of ui_in

    // Encoder input signals
    wire encoder_a_attack = uio_in[0]; // Encoder A for attack
    wire encoder_b_attack = uio_in[1]; // Encoder B for attack
    wire encoder_a_decay = uio_in[2];  // Encoder A for decay
    wire encoder_b_decay = uio_in[3];  // Encoder B for decay
    wire encoder_a_sustain = uio_in[4];// Encoder A for sustain
    wire encoder_b_sustain = uio_in[5];// Encoder B for sustain
  wire encoder_a_release = uio_in[6];// Enc oder A for release
    wire encoder_b_release = uio_in[7];// Encoder B for release

    // ADSR parameter values controlled by encoders
    wire [7:0] attack;
    wire [7:0] decay;
    wire [7:0] sustain;
    wire [7:0] rel;

    // Clock divider signals
    reg [31:0] clk_div, clk_div_threshold;
    reg clk_divided;
    wire [7:0] tri_wave_out, saw_wave_out, sqr_wave_out, sine_wave_out, adsr_amplitude;
    reg [7:0] selected_wave;

    // Clock divider logic with synchronous reset
    always @(posedge clk) begin
        if (!rst_n) begin
            clk_div <= 32'd0;
            clk_divided <= 1'b0;
        end else begin
            if (clk_div >= clk_div_threshold) begin
                clk_div <= 32'd0;
                clk_divided <= ~clk_divided;
            end else begin
                clk_div <= clk_div + 1;
            end
        end
    end

    // Clock divider threshold selection
    always @(*) begin
        case (freq_select)
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
            default: clk_div_threshold = 32'd284091; // Default to A4 (440 Hz)
        endcase
    end

    // Instantiate encoder modules for ADSR parameters
    encoder #(.WIDTH(8), .INCREMENT(1)) attack_encoder (
        .clk(clk),
        .rst_n(rst_n),
        .a(encoder_a_attack),
        .b(encoder_b_attack),
        .value(attack)
    );

    encoder #(.WIDTH(8), .INCREMENT(1)) decay_encoder (
        .clk(clk),
        .rst_n(rst_n),
        .a(encoder_a_decay),
        .b(encoder_b_decay),
        .value(decay)
    );

    encoder #(.WIDTH(8), .INCREMENT(1)) sustain_encoder (
        .clk(clk),
        .rst_n(rst_n),
        .a(encoder_a_sustain),
        .b(encoder_b_sustain),
        .value(sustain)
    );

    encoder #(.WIDTH(8), .INCREMENT(1)) release_encoder (
        .clk(clk),
        .rst_n(rst_n),
        .a(encoder_a_release),
        .b(encoder_b_release),
        .value(rel)
    );

    // Instantiate wave generators and ADSR generator
    triangular_wave_generator triangle_gen (.clk(clk_divided), .rst_n(rst_n), .wave_out(tri_wave_out));
    sawtooth_wave_generator saw_gen (.clk(clk_divided), .rst_n(rst_n), .wave_out(saw_wave_out));
    square_wave_generator sqr_gen (.clk(clk_divided), .rst_n(rst_n), .wave_out(sqr_wave_out));
    sine_wave_generator sine_gen (.clk(clk_divided), .rst_n(rst_n), .wave_out(sine_wave_out));
    adsr_generator adsr_gen (.clk(clk_divided), .rst_n(rst_n), .attack(attack), .decay(decay), .sustain(sustain), .rel(rel), .amplitude(adsr_amplitude));

    // Wave selection logic
    always @(*) begin
        case (wave_select)
            2'b00: selected_wave = tri_wave_out;
            2'b01: selected_wave = saw_wave_out;
            2'b10: selected_wave = sqr_wave_out;
            2'b11: selected_wave = sine_wave_out;
            default: selected_wave = 8'd0;
        endcase
    end

    // Modulate wave with ADSR
    assign uo_out = (adsr_amplitude > 0 && selected_wave > 0) ? (selected_wave * adsr_amplitude) >> 8 : 0;

    // Unused output assignments
    assign uio_out = 8'b0;
    assign uio_oe = 8'b0;

endmodule


module sine_wave_generator (
    input wire clk,                  // Clock
    input wire rst_n,                // Active-low reset
    output reg [7:0] wave_out        // 8-bit sine wave output
);

    reg [7:0] counter;               // Counter for indexing the sine table
    reg [7:0] sine_table [0:255];    // Sine table (256 values of 8 bits)

    // Initialization of the sine wave table
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

    // Sine wave generation logic with synchronous reset
    always @(posedge clk) begin
        if (!rst_n) begin
            counter <= 8'd0;
            wave_out <= 8'd0;
        end else begin
            counter <= counter + 8'd1;
            wave_out <= sine_table[counter];
        end
    end
endmodule

module square_wave_generator (
    input wire clk,                  // Clock
    input wire rst_n,                // Active-low reset
    output reg [7:0] wave_out        // 8-bit square wave output
);

    reg wave_state;                  // State of the square wave

    always @(posedge clk) begin
        if (!rst_n) begin
            wave_state <= 1'b0;
            wave_out <= 8'd0;
        end else begin
            wave_state <= ~wave_state;
            wave_out <= wave_state ? 8'd255 : 8'd0;
        end
    end
endmodule



module sawtooth_wave_generator (
    input wire clk,                  // Clock
    input wire rst_n,                // Active-low reset
    output reg [7:0] wave_out        // 8-bit sawtooth wave output
);

    reg [7:0] counter;

    always @(posedge clk) begin
        if (!rst_n) begin
            counter <= 8'd0;
        end else begin
            counter <= counter + 1;
        end
    end

    always @(posedge clk) begin
        wave_out <= counter;
    end
endmodule


module adsr_generator (
    input  wire       clk,       // Clock
    input  wire       rst_n,     // Active-low reset
    input  wire [7:0] attack,    // Attack value
    input  wire [7:0] decay,     // Decay value
    input  wire [7:0] sustain,   // Sustain value
    input  wire [7:0] rel,       // Release value
    output reg  [7:0] amplitude  // Generated amplitude signal
);

    reg [3:0] state;
    reg [7:0] counter;

    localparam STATE_IDLE     = 4'd0;
    localparam STATE_ATTACK   = 4'd1;
    localparam STATE_DECAY    = 4'd2;
    localparam STATE_SUSTAIN  = 4'd3;
    localparam STATE_RELEASE  = 4'd4;

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= STATE_IDLE;
            amplitude <= 8'd0;
            counter <= 8'd0;
        end else begin
            case (state)
                STATE_IDLE: begin
                    if (counter == 8'd255) begin
                        state <= STATE_ATTACK;
                        counter <= 8'd0;
                    end else begin
                        counter <= counter + 1;
                    end
                end
                STATE_ATTACK: begin
                    if (amplitude < attack) begin
                        amplitude <= amplitude + 1;
                    end else begin
                        state <= STATE_DECAY;
                    end
                end
                STATE_DECAY: begin
                    if (amplitude > sustain) begin
                        amplitude <= amplitude - 1;
                    end else begin
                        state <= STATE_SUSTAIN;
                    end
                end
                STATE_SUSTAIN: begin
                    amplitude <= sustain;
                    if (counter == 8'd255) begin
                        state <= STATE_RELEASE;
                        counter <= 8'd0;
                    end else begin
                        counter <= counter + 1;
                    end
                end
                STATE_RELEASE: begin
                    if (amplitude > 0) begin
                        amplitude <= amplitude - 1;
                    end else begin
                        state <= STATE_IDLE;
                    end
                end
                default: state <= STATE_IDLE;
            endcase
        end
    end
endmodule


module triangular_wave_generator (
    input wire clk,                  // Clock
    input wire rst_n,                // Active-low reset
    output reg [7:0] wave_out        // 8-bit triangular wave output
);

    reg [7:0] counter;
    reg direction;

    always @(posedge clk) begin
        if (!rst_n) begin
            counter <= 8'd0;
            direction <= 1'b1;
        end else begin
            if (direction) begin
                if (counter < 8'd255) begin
                    counter <= counter + 1;
                end else begin
                    direction <= 1'b0;
                end
            end else begin
                if (counter > 8'd0) begin
                    counter <= counter - 1;
                end else begin
                    direction <= 1'b1;
                end
            end
        end
    end

    always @(posedge clk) begin
        wave_out <= counter;
    end
endmodule


module encoder #(
    parameter WIDTH = 8,        // Width of the output value
    parameter INCREMENT = 1'b1  // Amount to increment or decrement
)(
    input clk,                  // System clock
    input rst_n,                // Active-low reset
    input a,                    // Encoder input A
    input b,                    // Encoder input B
    output reg [WIDTH-1:0] value // Output value
);

    // Internal signals for previous states of encoder inputs
    reg old_a, old_b;
    reg [1:0] state;  // State of encoder inputs

    // Encoder state transition table based on Gray code
    always @(posedge clk) begin
        if (!rst_n) begin
            old_a <= 0;
            old_b <= 0;
            value <= 0;
            state <= 2'b00;
        end else begin
            old_a <= a;
            old_b <= b;
            state <= {a, b};

            // Update value based on encoder state transitions
            case ({a, old_a, b, old_b})
                4'b1000, 4'b0111: value <= value + INCREMENT; // Clockwise rotation
                4'b0010, 4'b1101: value <= value - INCREMENT; // Counter-clockwise rotation
                default: value <= value; // No change for invalid or noise states
            endcase
        end
    end

endmodule
