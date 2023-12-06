from queue import Queue, Empty
from threading import Thread, Event

class VectorProcess:
    def __init__(self, process_id, num_processes):
        """
        Initialize a Vector clock process with a unique ID.

        Args:
            process_id (int): Unique identifier for the process.
            num_processes (int): Total number of processes in the system.
        """
        self.process_id = process_id
        self.vector_clock = [0] * num_processes
        self.active = Event()
        self.msg_queue = Queue()
        self.connected_processes = []
        self.process_thread = Thread(target=self.process_activities, daemon=True)

    def connect_processes(self, processes):
        """
        Connect this process to other processes in the system.

        Args:
            processes (list): List of other VectorProcess instances to connect to.
        """
        self.connected_processes = processes

    def start_process(self):
        """Start the process's main thread."""
        self.process_thread.start()

    def stop_process(self):
        """Stop the process and wait for the thread to finish."""
        self.active.set()
        self.process_thread.join()

    def process_activities(self):
        while not self.active.is_set():
            try:
                payload, sender_clock = self.msg_queue.get(timeout=0.1)
                self.process_message(payload, sender_clock)
            except Empty:
                continue

    def process_message(self, payload, sender_clock):
        """ Update vector clock by comparing with the sender's clock """
        for i in range(len(self.vector_clock)):
            self.vector_clock[i] = max(self.vector_clock[i], sender_clock[i])
        # Increment the process's own vector clock entry
        self.vector_clock[self.process_id] += 1
        self.log_event("Received", payload)

    def send_message(self, target_id, payload):
        if target_id < len(self.connected_processes):
            # Increment the sender's vector clock and send the message
            self.vector_clock[self.process_id] += 1
            self.connected_processes[target_id].enqueue_message(payload, self.vector_clock.copy())
            self.log_event("Sent", payload)

    def enqueue_message(self, payload, clock):
        """Enqueue a message to be processed by the process."""
        self.msg_queue.put((payload, clock))

    def log_event(self, event_type, payload):
        print(f"{event_type} event: [PROCESS_ID: {self.process_id}], [VECTOR_CLOCK: {self.vector_clock}], [PAYLOAD: {payload}]")

    def simulate_internal_event(self):
        """Simulate an internal event for the current process."""
        # Increment the process's own vector clock entry to simulate an internal event
        self.vector_clock[self.process_id] += 1
        self.log_event("Internal Event", "Internal event occurred")