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
            value <= 8'd0;       // Reset the value to zero
            prev_state <= 2'b00; // Initialize previous state
        end else begin
            case ({encoder_a, encoder_b})
                2'b00: begin
                    prev_state <= 2'b00;
                end
                2'b01: begin
                    if (prev_state == 2'b00) begin
                        value <= value + 1;
                    end
                    prev_state <= 2'b01;
                end
                2'b10: begin
                    if (prev_state == 2'b00) begin
                        value <= value - 1;
                    end
                    prev_state <= 2'b10;
                end
                2'b11: begin
                    prev_state <= 2'b11;
                end
            endcase
        end
    end
endmodule
