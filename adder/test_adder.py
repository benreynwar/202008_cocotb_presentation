import os
import random
import logging

import cocotb
from cocotb import triggers

logger = logging.getLogger(__name__)


@cocotb.test()
async def test_adder(dut):
    logger.setLevel(os.getenv('COCOTB_LOG_LEVEL', 'INFO'))
    n_checks = 100
    max_data = 7
    for check_index in range(n_checks):
        dut.a_data <= random.randint(0, max_data)
        dut.b_data <= random.randint(0, max_data)
        await triggers.ReadOnly()
        logger.info('{} + {} = {}'.format(
            int(dut.a_data), int(dut.b_data), int(dut.c_data)))
        if int(dut.c_data) != int(dut.a_data) + int(dut.b_data):
            logger.error('{} + {} = {}'.format(
                int(dut.a_data), int(dut.b_data), int(dut.c_data)))
            assert False
        await triggers.Timer(10, units='ns')
