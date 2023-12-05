# test_lamport_process.py
import pytest
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lamport_Timestamps')))

from lamport_process import LamportProcess


def test_initial_clock_value():
    process = LamportProcess(1)
    assert process.logical_clock == 0, "Initial clock value should be zero"

def test_clock_increment_on_event():
    process = LamportProcess(1)
    process.process_event("TestEvent", process.process_id)
    assert process.logical_clock == 1, "Clock should increment on local event"

def test_clock_update_on_msg_receive():
    p1 = LamportProcess(1)
    p2 = LamportProcess(2)
    p1.connect_processes([p2])
    p2.connect_processes([p1])

    p1.send_msg(1, "TestMsg")
    assert p2.logical_clock > 0, "Clock should update on receiving a message"

def test_message_ordering():
    p1 = LamportProcess(1)
    p2 = LamportProcess(2)
    p1.connect_processes([p2])
    p2.connect_processes([p1])

    p1.send_msg(1, "Msg1")
    p2.send_msg(0, "Msg2")

    assert p1.logical_clock != p2.logical_clock, "Clocks should differ after message exchange"
    assert p2.logical_clock > p1.logical_clock, "P2's clock should be ahead of P1's clock"


def test_efficiency():
    start_time = time.time()
    # Perform a series of operations
    end_time = time.time()
    assert end_time - start_time < some_threshold, "Operations should complete within reasonable time"
