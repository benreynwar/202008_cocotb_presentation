SIM=verilator

VERILOG_SOURCES=$(PWD)/myip_v1_0_S00_AXI.v

TOPLEVEL=myip_v1_0_S00_AXI

MODULE=test_axilite

EXTRA_ARGS += --trace --trace-structs

include $(shell cocotb-config --makefiles)/Makefile.sim
