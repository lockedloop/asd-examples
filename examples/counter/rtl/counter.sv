module counter #(
    parameter int WIDTH = 8,
    parameter int MAX_COUNT = 255
)(
    input  logic             clk,
    input  logic             rst,
    input  logic             enable,
    output logic [WIDTH-1:0] count,
    output logic             overflow
);

    always_ff @(posedge clk) begin
        if (rst) begin
            count <= '0;
            overflow <= 1'b0;
        end else if (enable) begin
            if (count >= MAX_COUNT[$bits(count)-1:0]) begin
                count <= '0;
                overflow <= 1'b1;
            end else begin
                count <= count + 1;
                overflow <= 1'b0;
            end
        end
    end

endmodule
