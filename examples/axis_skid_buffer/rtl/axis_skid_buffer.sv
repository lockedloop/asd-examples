// AXI-Stream Skid Buffer
//
// This module implements a skid buffer (also known as a pipeline register with
// elastic buffering) for AXI-Stream interfaces. The skid buffer breaks the
// combinatorial path from master ready to slave ready, improving timing closure
// while maintaining zero-bubble throughput.
//
// Architecture:
//   - Two-register design: output register + skid register
//   - Accepts one additional transfer when output is stalled
//   - Registered ready signal prevents combinatorial feedback
//
// Operation:
//   - Normal mode: Data passes through to output register in one cycle
//   - Buffered mode: When output stalls, incoming data goes to skid register
//   - Ready signal deasserts when both registers are full
//
// Parameters:
//   - DATA_WIDTH: Width of the data bus (1-4096 typical)
//   - TLAST_ENABLE: Include TLAST signal for packet boundaries

module axis_skid_buffer #(
    parameter int DATA_WIDTH = 8,
    parameter bit TLAST_ENABLE = 1
)(
    input  logic clk,
    input  logic rst,

    // Slave (input) AXI-Stream interface
    input  logic                  s_axis_tvalid,
    output logic                  s_axis_tready,
    input  logic [DATA_WIDTH-1:0] s_axis_tdata,
    input  logic                  s_axis_tlast,

    // Master (output) AXI-Stream interface
    output logic                  m_axis_tvalid,
    input  logic                  m_axis_tready,
    output logic [DATA_WIDTH-1:0] m_axis_tdata,
    output logic                  m_axis_tlast
);

    // Internal registers for the skid buffer
    logic [DATA_WIDTH-1:0] skid_data;
    logic                  skid_last;
    logic                  skid_valid;

    // Output registers
    logic [DATA_WIDTH-1:0] out_data;
    logic                  out_last;
    logic                  out_valid;

    // Ready when skid buffer is empty
    assign s_axis_tready = !skid_valid;

    // Output assignments
    assign m_axis_tvalid = out_valid;
    assign m_axis_tdata = out_data;

    generate
        if (TLAST_ENABLE) begin : gen_tlast
            assign m_axis_tlast = out_last;
        end else begin : gen_no_tlast
            assign m_axis_tlast = 1'b0;
        end
    endgenerate

    // Main skid buffer logic
    always_ff @(posedge clk) begin
        if (rst) begin
            skid_valid <= 1'b0;
            skid_data <= '0;
            skid_last <= 1'b0;
            out_valid <= 1'b0;
            out_data <= '0;
            out_last <= 1'b0;
        end else begin
            // Handle output stage
            if (m_axis_tready || !out_valid) begin
                // Output can advance
                if (skid_valid) begin
                    // Move skid data to output
                    out_data <= skid_data;
                    out_last <= skid_last;
                    out_valid <= 1'b1;
                    skid_valid <= 1'b0;
                end else if (s_axis_tvalid) begin
                    // Direct path from input to output
                    out_data <= s_axis_tdata;
                    out_last <= TLAST_ENABLE ? s_axis_tlast : 1'b0;
                    out_valid <= 1'b1;
                end else begin
                    // No new data available
                    out_valid <= 1'b0;
                end
            end else if (s_axis_tvalid && !skid_valid) begin
                // Output is stalled but we can accept data into skid buffer
                skid_data <= s_axis_tdata;
                skid_last <= TLAST_ENABLE ? s_axis_tlast : 1'b0;
                skid_valid <= 1'b1;
            end
            // If output stalled and skid full, do nothing (ready is low)
        end
    end

endmodule
