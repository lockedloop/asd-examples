module counter #(
    parameter int WIDTH = 8
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
            count <= count + 1;
            overflow <= &count;
        end
    end

endmodule
