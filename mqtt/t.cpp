`timescale 1ns / 1ps

////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer:
//
// Create Date:   01:54:47 10/17/2025
// Design Name:   cnt
// Module Name:   /home/ise/KTCK/tb.v
// Project Name:  KTCK
// Target Device:  
// Tool versions:  
// Description: 
//
// Verilog Test Fixture created by ISE for module: cnt
//
// Dependencies:
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
////////////////////////////////////////////////////////////////////////////////

module tb;

	// Inputs
	reg clk;
	reg rst;

	// Outputs
	wire [1:0] led_chuc;
	wire [3:0] led_donvi;

	// Instantiate the Unit Under Test (UUT)
	/*cnt uut (
		.clk(clk), 
		.rst(rst), 
		.led_chuc(led_chuc), 
		.led_donvi(led_donvi)
	);*/
	bcd_counter_0_to_19 uut(clk,rst,led_chuc,led_donvi);
	initial begin
		// Initialize Inputs
		clk = 1;
		rst = 1;
		#10 rst = 0;

	end
	always #10 clk = ~clk;
      
endmodule

