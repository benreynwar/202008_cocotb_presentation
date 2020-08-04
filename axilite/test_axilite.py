import os
import logging
import collections
import random

import cocotb
from cocotb import triggers

logger = logging.getLogger(__name__)

async def clock(clock_signal, period, units):
    while True:
        clock_signal <= 0
        await triggers.Timer(period/2, units=units)
        clock_signal <= 1
        await triggers.Timer(period/2, units=units)


class ValidReadyForward:

    def __init__(self, clk, valid, ready, data, seed, p_valid=1):
        self.clk = clk
        self.valid_s = valid
        self.ready_s = ready
        self.data_s = data
        self.queue = collections.deque()
        self.rnd = random.Random(seed)
        self.p_valid = p_valid

    def add(self, data):
        self.queue.append(data)

    async def run(self):
        while True:
            if self.queue and (self.rnd.random() < self.p_valid):
                self.data_s <= self.queue.popleft()
                self.valid_s <= 1
                while True:
                    await triggers.ReadOnly()
                    if int(self.ready_s) == 1:
                        break
                    else:
                        await triggers.RisingEdge(self.clk)
            else:
                self.valid_s <= 0
            await triggers.RisingEdge(self.clk)


class ValidReadyBackwards:

    def __init__(self, clk, valid, ready, data, seed, p_ready=1):
        self.clk = clk
        self.valid_s = valid
        self.ready_s = ready
        self.data_s = data
        self.queue = collections.deque()
        self.rnd = random.Random(seed)
        self.p_ready = p_ready
        self.ready_s <= 0

    async def read(self):
        while True:
            self.ready_s <= (1 if self.rnd.random() < self.p_ready else 0)
            await triggers.ReadOnly()
            if (int(self.valid_s) == 1) and (int(self.ready_s) == 1):
                data = int(self.data_s)
                await triggers.RisingEdge(self.clk)
                self.ready_s <= 0
                return data
            await triggers.RisingEdge(self.clk)


@cocotb.test()
async def test_axilite(dut):
    seed = 1
    max_seed = pow(2, 16)-1
    rnd = random.Random(seed)
    logger.setLevel(os.getenv('COCOTB_LOG_LEVEL', 'INFO'))
    logger.info('Starting Test!')

    clk = dut.S_AXI_ACLK

    cocotb.fork(clock(clock_signal=clk, period=10, units='ns'))

    dut.S_AXI_ARESETN <= 0
    for i in range(10):
        await triggers.RisingEdge(clk)
    dut.S_AXI_ARESETN <= 1
    dut.S_AXI_WSTRB <= 15

    ar_interface = ValidReadyForward(
        clk=clk,
        valid=dut.S_AXI_ARVALID,
        ready=dut.S_AXI_ARREADY,
        data=dut.S_AXI_ARADDR,
        seed=rnd.randint(0, max_seed),
        p_valid=0.5,
        )
    r_interface = ValidReadyBackwards(
        clk=clk,
        valid=dut.S_AXI_RVALID,
        ready=dut.S_AXI_RREADY,
        data=dut.S_AXI_RDATA,
        seed=rnd.randint(0, max_seed),
        p_ready=0.5,
        )

    aw_interface = ValidReadyForward(
        clk=clk,
        valid=dut.S_AXI_AWVALID,
        ready=dut.S_AXI_AWREADY,
        data=dut.S_AXI_AWADDR,
        seed=rnd.randint(0, max_seed),
        p_valid=0.5,
        )
    w_interface = ValidReadyForward(
        clk=clk,
        valid=dut.S_AXI_WVALID,
        ready=dut.S_AXI_WREADY,
        data=dut.S_AXI_WDATA,
        seed=rnd.randint(0, max_seed),
        p_valid=0.5,
        )
    b_interface = ValidReadyBackwards(
        clk=clk,
        valid=dut.S_AXI_BVALID,
        ready=dut.S_AXI_BREADY,
        data=dut.S_AXI_BRESP,
        seed=rnd.randint(0, max_seed),
        p_ready=0.5,
        )

    cocotb.fork(ar_interface.run())
    cocotb.fork(w_interface.run())
    cocotb.fork(aw_interface.run())

    await triggers.RisingEdge(clk)

    for i in range(100):
        # Write into each register
        for address in range(4):
            w_interface.add(address+1)
            aw_interface.add(address*4)
            logger.info('Write {} to address {}'.format(address+1, address*4))
        for address in range(4):
            write_response = await b_interface.read()
            assert write_response == 0

        # Read from each register
        for address in range(4):
            ar_interface.add(address*4)
        for address in range(4):
            read_data = await r_interface.read()
            logger.info('Read {} from address {}'.format(read_data, address*4))
            assert read_data == address+1

        logger.info('Receive data {}'.format(read_data))

        
    
