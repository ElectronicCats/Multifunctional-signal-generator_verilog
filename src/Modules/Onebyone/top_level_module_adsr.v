/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`define default_netname none



module tt_um_adsr_encoders (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs (amplitude output)
    input  wire [7:0] uio_in,   // IOs: Input path for rotary encoders
    output wire [7:0] uio_out,  // IOs: Output path (unused)
    output wire [7:0] uio_oe,   // IOs: Enable path (unused)
    input  wire       ena,      // will go high when the design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  wire [7:0] attack, decay, sustain, rel;  // ADSR parameters from rotary encoders
  wire [7:0] amplitude;  // Amplitude shaped by ADSR
  reg  [7:0] adsr_signal;  // Internal signal for output
  
  // Rotary encoder values mapped to ADSR parameters
  rotary_encoder encoder_1(.clk(clk), .rst_n(rst_n), .encoder_a(uio_in[0]), .encoder_b(uio_in[1]), .value(attack));    // Attack
  rotary_encoder encoder_2(.clk(clk), .rst_n(rst_n), .encoder_a(uio_in[2]), .encoder_b(uio_in[3]), .value(decay));     // Decay
  rotary_encoder encoder_3(.clk(clk), .rst_n(rst_n), .encoder_a(uio_in[4]), .encoder_b(uio_in[5]), .value(sustain));   // Sustain
  rotary_encoder encoder_4(.clk(clk), .rst_n(rst_n), .encoder_a(uio_in[6]), .encoder_b(uio_in[7]), .value(release));   // Release

  // ADSR envelope generator
  adsr_generator adsr(.clk(clk), .rst_n(rst_n), .attack(attack), .decay(decay), .sustain(sustain), .release(release), .amplitude(amplitude));

  // Assign amplitude to output
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      adsr_signal <= 8'd0;
    else
      adsr_signal <= amplitude;  // Update with ADSR-shaped signal
  end

  assign uo_out = adsr_signal;   // Output the final amplitude
  assign uio_out = 8'd0;         // Unused bidirectional outputs
  assign uio_oe = 8'd0;          // Set all uio pins as inputs

endmodule
