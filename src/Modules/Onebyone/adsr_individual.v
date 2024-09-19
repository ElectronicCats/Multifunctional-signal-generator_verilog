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

  wire [7:0] attack, decay, sustain, rel_phase;  // ADSR parameters
  wire [7:0] amplitude;  // Amplitude shaped by ADSR
  reg  [7:0] adsr_signal;  // Internal signal for output

  // Gate signal from ui_in[0] (controls the start of the ADSR)
  wire gate_signal = ui_in[0];

  // Rotary encoder values mapped to ADSR parameters
  rotary_encoder encoder_1(.clk(clk), .rst_n(rst_n), .encoder_a(ui_in[1]), .encoder_b(ui_in[2]), .value(attack));    // Attack
  rotary_encoder encoder_2(.clk(clk), .rst_n(rst_n), .encoder_a(ui_in[3]), .encoder_b(ui_in[4]), .value(decay));     // Decay
  rotary_encoder encoder_3(.clk(clk), .rst_n(rst_n), .encoder_a(ui_in[5]), .encoder_b(ui_in[6]), .value(sustain));   // Sustain
  rotary_encoder encoder_4(.clk(clk), .rst_n(rst_n), .encoder_a(ui_in[7]), .encoder_b(ui_in[7]), .value(rel_phase)); // Release

  // ADSR envelope generator
  adsr_generator adsr(
    .clk(clk), 
    .rst_n(rst_n), 
    .gate_signal(gate_signal), // Gate signal to control ADSR
    .attack(attack), 
    .decay(decay), 
    .sustain(sustain), 
    .rel_phase(rel_phase), 
    .amplitude(amplitude)
  );

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


// Rotary Encoder Module
module rotary_encoder (
    input  wire clk,       // Clock
    input  wire rst_n,     // Reset, active low
    input  wire encoder_a, // Encoder A signal
    input  wire encoder_b, // Encoder B signal
    output reg  [7:0] value // Value controlled by the encoder
);
    reg [1:0] prev_state;  // Previous state of encoder

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            value <= 8'd0;  // Reset the value to zero
            prev_state <= 2'b00;
        end else begin
            case ({encoder_a, encoder_b})
                2'b00: prev_state <= 2'b00;
                2'b01: if (prev_state == 2'b00) value <= value + 1; prev_state <= 2'b01;
                2'b10: if (prev_state == 2'b00) value <= value - 1; prev_state <= 2'b10;
                2'b11: prev_state <= 2'b11;
            endcase
        end
    end
endmodule


// ADSR Generator Module
module adsr_generator (
    input  wire       clk,       // Clock
    input  wire       rst_n,     // Reset, active low
    input  wire       gate_signal, // Gate signal (triggers the ADSR envelope)
    input  wire [7:0] attack,    // Attack value
    input  wire [7:0] decay,     // Decay value
    input  wire [7:0] sustain,   // Sustain value
    input  wire [7:0] rel_phase, // Release value
    output reg  [7:0] amplitude  // Generated amplitude signal
);

    reg [7:0] attack_counter, decay_counter, release_counter;  // Counters for timing ADSR phases
    reg [3:0] state;  // State of ADSR: 0=idle, 1=attack, 2=decay, 3=sustain, 4=release

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= 4'd0;
            amplitude <= 8'd0;
            attack_counter <= 8'd0;
            decay_counter <= 8'd0;
            release_counter <= 8'd0;
        end else begin
            case (state)
                4'd0: begin  // Idle state, waiting for a gate signal to start
                    if (gate_signal) begin
                        state <= 4'd1;
                        attack_counter <= 8'd0;
                    end
                end
                4'd1: begin  // Attack phase
                    if (attack_counter < attack) begin
                        amplitude <= amplitude + 1;  // Ramp up amplitude
                        attack_counter <= attack_counter + 1;
                    end else begin
                        state <= 4'd2;
                        decay_counter <= 8'd0;
                    end
                end
                4'd2: begin  // Decay phase
                    if (decay_counter < decay) begin
                        amplitude <= amplitude - 1;  // Ramp down amplitude
                        decay_counter <= decay_counter + 1;
                    end else begin
                        state <= 4'd3;  // Move to sustain
                    end
                end
                4'd3: begin  // Sustain phase
                    amplitude <= sustain;  // Hold the sustain level
                    if (!gate_signal) begin
                        state <= 4'd4;  // Move to release when gate signal goes low
                        release_counter <= 8'd0;
                    end
                end
                4'd4: begin  // Release phase
                    if (release_counter < rel_phase) begin
                        amplitude <= amplitude - 1;  // Ramp down amplitude
                        release_counter <= release_counter + 1;
                    end else begin
                        state <= 4'd0;  // Return to idle
                    end
                end
                default: state <= 4'd0;  // Default back to idle
            endcase
        end
    end
endmodule
