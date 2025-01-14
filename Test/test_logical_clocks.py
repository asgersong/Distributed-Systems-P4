# test_lamport_process.py
import pytest
import time
import sys
import os
from queue import Queue
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Lamport_Timestamps')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Vector_Clocks')))

from lamport_process import LamportProcess
from vector_process import VectorProcess


# LamportProcess tests
def test_Lamport_process_initialization():
    process = LamportProcess(0)
    assert process.process_id == 0, "Process ID should be set correctly"
    assert process.logical_clock == 0, "Logical clock should be initialized to zero"
    assert process.connected_processes == [], "Connected processes should be initialized to an empty list"

def test_clock_increment_on_event():
    process = LamportProcess(0)
    process.process_event("TestEvent", process.process_id)
    assert process.logical_clock == 1, "Clock should increment on local event"

def test_clock_update_on_msg_send():
    p0 = LamportProcess(0)
    p1 = LamportProcess(1)
    p0.connect_processes([p0, p1])
    p1.connect_processes([p0, p1])

    p0.start_process()
    p1.start_process()

    p0.send_msg(1, "TestMsg")
    time.sleep(0.1)  # Allow some time for message processing
    assert p0.logical_clock == 1, "Clock should update on sending a message"

    p0.stop_process()
    p1.stop_process()

def test_clock_update_on_msg_receive():
    p0 = LamportProcess(0)
    p1 = LamportProcess(1)
    p0.connect_processes([p0, p1])
    p1.connect_processes([p0, p1])

    p0.start_process()
    p1.start_process()

    p0.send_msg(1, "TestMsg")
    time.sleep(1)  # Allow some time for message processing
    assert p1.logical_clock == 2, "Clock should update on receiving a message"

    p0.stop_process()
    p1.stop_process()

def test_clocks_update_on_msg_send_and_receive():
    p0 = LamportProcess(0)
    p1 = LamportProcess(1)
    p0.connect_processes([p0, p1])
    p1.connect_processes([p0, p1])

    p0.start_process()
    p1.start_process()

    p0.send_msg(1, "TestMsg")
    time.sleep(0.1)  # Allow some time for message processing
    assert p1.logical_clock == 2, "p1's clock should be 2 after receiving a message"
    p0.process_event("LocalEvent", p0.process_id)  # Local event at p0 local clock should be incremented to 2
    p0.process_event("LocalEvent", p0.process_id)  # Local event at p0 local clock should be incremented to 3
    p1.process_event("LocalEvent", p1.process_id)  # Local event at p1 local clock should be incremented to 2
    p0.send_msg(1, "TestMsg") # p0 sends another message to p1 (p0's local clock should be incremented to 4)
    time.sleep(0.1)  # Allow some time for message processing
    assert p0.logical_clock == 4, "p0's clock should be 4 after sending 2 messages and 2 local events"
    assert p1.logical_clock == 5, "p1's clock should be 5 after receiving 2 messages and 1 local event"

    p0.stop_process()
    p1.stop_process()

def test_message_ordering():
    p0 = LamportProcess(0)
    p1 = LamportProcess(1)
    p0.connect_processes([p0, p1])
    p1.connect_processes([p0, p1])

    p0.start_process()
    p1.start_process()

    p0.send_msg(1, "Msg1")
    time.sleep(0.1)  # Allow some time for message processing
    p1.process_event("LocalEvent", p1.process_id)  # Local event at p1
    p1.send_msg(0, "Msg2")

    time.sleep(0.1)  # Allow some time for message processing

    # Check if both clocks are incremented and equal
    assert p0.logical_clock > 0 and p1.logical_clock > 0, "Clocks should be incremented"

    p0.stop_process()
    p1.stop_process()

def test_efficiency():
    start_time = time.time()
    
    num_processes = 5
    num_messages = 10

    processes = [LamportProcess(i) for i in range(num_processes)]
    for process in processes:
        process.connect_processes(processes)
        process.start_process()

    for _ in range(num_messages):
        sender = processes[_ % num_processes]
        receiver_id = (_ + 1) % num_processes
        sender.send_msg(receiver_id, f"Message {_}")

    time.sleep(0.5)  # Allow some time for message processing

    for process in processes:
        assert process.logical_clock > 0, "Logical clock didn't update correctly"
        process.stop_process()

    end_time = time.time()
    
    expected_threshold = 1.0  # Adjust based on your observations and requirements
    assert end_time - start_time < expected_threshold, "Operations should complete within a reasonable time"

def test_send_msg_invalid_process_id():
    p0 = LamportProcess(0)
    p1 = LamportProcess(1)

    # Connect p0 to p1 only
    p0.connect_processes([p1])  # Note that p1 is not connected to p0

    p0.start_process()
    p1.start_process()

    invalid_process_id = 2  # This ID does not exist in the connected processes
    p0.send_msg(invalid_process_id, "TestMsg")

    time.sleep(0.1)  # Allow some time for the process

    # Check if the error log is present
    error_log_present = any("Invalid target process ID" in log for log in p0.event_log)
    assert error_log_present, "Error log for invalid process ID should be present"

    p0.stop_process()
    p1.stop_process()

def test_send_msg_via_process_event():
    p0 = LamportProcess(0)
    p1 = LamportProcess(1)

    p0.start_process()
    p1.start_process()

    p0.connect_processes([p0, p1])

    p0.process_event("TestMsg", 1)

    time.sleep(0.1)  # Allow some time for the process

    # Check if the error log is present
    assert p0.logical_clock == 1, "Logical clock should be incremented on sending a message"

    p0.stop_process()
    p1.stop_process()

# VectorProcess tests

def test_vector_clock_initialization():
    num_processes = 3
    process = VectorProcess(0, num_processes)
    assert process.vector_clock == [0] * num_processes, "Initial vector clock should be all zeros"

def test_connect_processes():
    p0 = VectorProcess(0, 2)
    p1 = VectorProcess(1, 2)
    p0.connect_processes([p0, p1])
    p1.connect_processes([p0, p1])
    assert p0.connected_processes == [p0, p1], "p0 should be connected to p0 and p1"
    assert p1.connected_processes == [p0, p1], "p1 should be connected to p0 and p1"

def test_vector_clock_update_on_event():
    num_processes = 2
    p0 = VectorProcess(0, num_processes)
    p1 = VectorProcess(1, num_processes)

    # Connect processes and simulate events
    p0.connect_processes([p0, p1])
    p1.connect_processes([p0, p1])
    p0.start_process()
    p1.start_process()

    p0.send_message(1, "LocalEvent")  # Simulate an event by sending a message
    time.sleep(0.1)  # Allow some time for message processing
    assert p0.vector_clock[0] == 1, "p0's vector clock should be [1, 0] after sending a message"
    assert p1.vector_clock[1] == 1, "p1's vector clock should be [1, 1] after receiving a message"
    assert p1.vector_clock[0] == 1, "p0's vector clock should be [1, 1] after receiving a message"

    p0.stop_process()
    p1.stop_process()


def test_simulate_internal_event():
    num_processes = 2
    p0 = VectorProcess(0, num_processes)
    p1 = VectorProcess(1, num_processes)

    # Connect processes
    p0.connect_processes([p0, p1])
    p1.connect_processes([p0, p1])

    p0.start_process()
    p1.start_process()

    # Simulate an internal event in process 0
    p0.simulate_internal_event()
    
    time.sleep(0.1)  # Allow some time for event processing

    # Check if process 0's vector clock entry has been incremented
    assert p0.vector_clock[0] == 1, "Process 0's vector clock should be [1, 0] after simulating an internal event"

    p0.stop_process()
    p1.stop_process()
