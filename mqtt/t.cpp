`timescale 1ns / 1ps
module top(
    input wire clk_50M,
    input wire reset,
    output wire clk,
    output wire stb,
    output wire dio
);

wire clk_khz;
wire enable_fast;
wire [7:0] led_pattern;

ClockAndEnableGenerator clock_gen (
        .clki(clk_50M), 
        .reset(reset),
        .clk_khz_out(clk_khz), 
        .enable_out(enable_fast)
);
LedSangDon effect_generator (
        .clk(clk_50M),
        .reset(reset), 
        .enable(enable_fast),
        .led_out(led_pattern)
);

    TM1638 tm_driver (
        .led(led_pattern), 
        .seg7(4'hF), .seg6(4'hF), .seg5(4'hF), .seg4(4'hF),
        .seg3(4'hF), .seg2(4'hF), .seg1(4'hF), .seg0(4'hF),
        .clkinput(clk_khz),
        .clk(clk),
        .stb(stb),
        .dio(dio)
    );

endmodule
module LedSangDon (
    input wire clk,
    input wire reset,
    input wire enable,
    output wire [7:0] led_out
);
reg [3:0] stop_position;
    reg [3:0] running_position;
    reg [7:0] background_leds;
    
    reg [7:0] led_out_reg;
    assign led_out = led_out_reg;
always @(posedge clk or posedge reset) begin
        if (reset) begin
            stop_position <= 3'd7;
            running_position <= 3'd0;
background_leds <= 8'b0;
        end else if (enable) begin 
            if (background_leds == 8'hFF) begin
                background_leds <= 8'b0;
                stop_position <= 3'd7;
                running_position <= 3'd0;
            end else begin
if (running_position == stop_position) begin
                    background_leds <= background_leds | (1 << running_position);
                    stop_position <= stop_position - 1;
                    running_position <= 3'd0;
                end else begin
                    running_position <= running_position + 1;
                end
            end
        end
    end
    always @(*) begin
        if (background_leds == 8'hFF) begin
            led_out_reg = 8'hFF;
        end else begin
            led_out_reg = background_leds | (1 << running_position);
        end
    end

endmodule


 
module ClockAndEnableGenerator(
    input wire clki,
    input wire reset,
    output wire clk_khz_out,
    output wire enable_out
);
    parameter MAX_COUNT = 12500000;
    
    reg [26:0] counter;
always @(posedge clki or posedge reset) begin
        if (reset) begin
            counter <= 0;
        end else if (counter == MAX_COUNT - 1) begin
            counter <= 0;
        end else begin
            counter <= counter + 1;
        end
    end
assign clk_khz_out = counter[5];
    assign enable_out = (counter == MAX_COUNT - 1);
endmodule

module TM1638(
    input wire [7:0] led,
    input wire [3:0] seg7,seg6,seg5,seg4,seg3,seg2,seg1,seg0,
    input clkinput,
    output reg clk,
    output reg stb,
    output reg dio
);
function [7:0] sseg;
        input [3:0] hex;
        begin
            case (hex)
                4'h0: sseg = 8'b0111111;
                4'h1: sseg = 8'b0000110;
                4'h2: sseg = 8'b1011011;
                4'h3: sseg = 8'b1001111;
                4'h4: sseg = 8'b1100110;
                4'h5: sseg = 8'b1101101;
                4'h6: sseg = 8'b1111101;
                4'h7: sseg = 8'b0000111;
				4'h8: sseg = 8'b1111111;
                4'h9: sseg = 8'b1101111;
                4'hA: sseg = 8'b1110111;
                4'hB: sseg = 8'b1111100;
                4'hC: sseg = 8'b1011000;
                4'hD: sseg = 8'b1011110;
                4'hE: sseg = 8'b1111001;
                default : sseg = 8'b0000000;
            endcase
        end
    endfunction

integer cs = 0;
reg [7:0] command1 = 8'h40, command2 = 8'hC0, command3 = 8'h8F;
wire [127:0] leddata;
reg [127:0] leddatahold;

	 assign leddata[0*8+7:0*8+0]   = sseg(seg0);
    assign leddata[1*8+7:1*8+0]   = led[0];
    assign leddata[2*8+7:2*8+0]   = sseg(seg1);
    assign leddata[3*8+7:3*8+0]   = led[1];
    assign leddata[4*8+7:4*8+0]   = sseg(seg2);
    assign leddata[5*8+7:5*8+0]   = led[2];
    assign leddata[6*8+7:6*8+0]   = sseg(seg3);
    assign leddata[7*8+7:7*8+0]   = led[3];
    assign leddata[8*8+7:8*8+0]   = sseg(seg4);
    assign leddata[9*8+7:9*8+0]   = led[4];
    assign leddata[10*8+7:10*8+0] = sseg(seg5);
    assign leddata[11*8+7:11*8+0] = led[5];
    assign leddata[12*8+7:12*8+0] = sseg(seg6);
    assign leddata[13*8+7:13*8+0] = led[6];
    assign leddata[14*8+7:14*8+0] = sseg(seg7);
    assign leddata[15*8+7:15*8+0] = led[7];
	 initial begin
        clk = 1;
        stb = 1;
        dio = 0;
    end
always @(posedge clkinput) begin
        cs = cs + 1;        
        if (cs == 0) begin
            stb = 0;
            command1 = 8'h40; command2 = 8'hC0; command3 = 8'h8F;
            leddatahold = leddata;
        end
        else if ((cs >= 1) && (cs <= 16)) begin
            dio = command1[0];
            clk = ~clk;
            if (clk) command1 = command1 >> 1;
        end
else if (cs == 17) stb = 1;
        else if (cs == 18) stb = 0;
        else if ((cs >= 19) && (cs <= 34)) begin
            dio = command2[0];
            clk = ~clk;
            if (clk) command2 = command2 >> 1;
        end
        else if ((cs >= 35) && (cs <= 290)) begin
            dio = leddatahold[0];
            clk = ~clk;
            if (clk) leddatahold = leddatahold >> 1;
        end
else if (cs == 291) stb = 1;
        else if (cs == 292) stb = 0;
        else if ((cs >= 293) && (cs <= 308)) begin
            dio = command3[0];
            clk = ~clk;
            if (clk) command3 = command3 >> 1;
        end
        else if (cs == 309) stb = 1;
        else if (cs == 310) cs = -1;
    end

endmodule





