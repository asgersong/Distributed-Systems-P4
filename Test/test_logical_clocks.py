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

def test_initial_clock_value():
    process = LamportProcess(0)
    assert process.logical_clock == 0, "Initial clock value should be zero"

def test_clock_increment_on_event():
    process = LamportProcess(0)
    process.process_event("TestEvent", process.process_id)
    assert process.logical_clock == 1, "Clock should increment on local event"

def test_clock_update_on_msg_receive():
    p0 = LamportProcess(0)
    p1 = LamportProcess(1)
    p0.connect_processes([p0, p1])
    p1.connect_processes([p0, p1])

    p0.start_process()
    p1.start_process()

    p0.send_msg(1, "TestMsg")
    time.sleep(0.5)  # Allow some time for message processing
    assert p1.logical_clock > 0, "Clock should update on receiving a message"

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
    assert p0.logical_clock == p1.logical_clock, "Clocks should be equal after the events"

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
    assert end_time - start_time < expected_threshold, "Operations should complete within reasonable time"


# VectorProcess tests
def test_vector_clock_initialization():
    num_processes = 3
    process = VectorProcess(0, num_processes)
    assert process.vector_clock == [0, 0, 0], "Initial vector clock should be all zeros"

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

    p0.process_event("LocalEvent", p0.process_id)
    assert p0.vector_clock == [1, 0], "p0's vector clock should be [1, 0] after local event"

    p0.stop_process()
    p1.stop_process()

def test_message_sending_and_receiving():
    p0 = VectorProcess(0, 2)
    p1 = VectorProcess(1, 2)
    p0.connect_processes([p0, p1])
    p1.connect_processes([p0, p1])
    
    p0.start_process()
    p1.start_process()

    p0.send_msg(1, "Hello from p0")
    time.sleep(0.1)
    assert p1.vector_clock[0] == 1, "p1's vector clock should be [1, 0] after receiving a message"

    p0.stop_process()
    p1.stop_process()

def test_scheduled_events_handling():
    process = VectorProcess(0, 1)
    process.start_process()
    process.schedule_events(Queue())
    process.scheduled_events.put((time.time() + 0.1, "Scheduled Event", 0))
    time.sleep(2)
    assert process.vector_clock[0] == 1, "p0's vector clock should be [1] after processing a scheduled event"
    process.stop_process()

def test_logging():
    process = VectorProcess(0, 1)
    process.start_process()
    process.process_event("Test Event", process.process_id)
    time.sleep(0.1)
    assert len(process.event_log) > 0, "Event log should contain at least one event"
    process.stop_process()

def test_error_handling():
    p0 = VectorProcess(0, 1)
    with pytest.raises(IndexError):
        p0.send_msg(1, "Message to non-existent process")
