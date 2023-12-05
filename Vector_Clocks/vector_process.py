from queue import Queue, Empty
from threading import Thread, Event
import time

class VectorProcess:
    def __init__(self, process_id, num_processes):
        """Initialize the Vector process with a unique ID and total number of processes."""
        self.process_id = process_id
        self.vector_clock = [0] * num_processes  # Vector clock for this process
        self.active = Event()  # Event flag to control the process's activity
        self.msg_queue = Queue()  # Queue for incoming msgs
        self.scheduled_events = Queue()  # Queue for scheduled events
        self.process_thread = Thread(target=self.process_activities, daemon=True)  # Thread for the process
        self.connected_processes = []  # List of connected processes for msg passing
        self.init_time = time.time()  # Record the start time of the process
        self.event_log = []  # Log for events

    def connect_processes(self, other_processes):
        """Connect this process to other processes in the system."""
        self.connected_processes = other_processes

    def process_activities(self):
        """Main loop to process events and msgs."""
        while not self.active.is_set():
            self.process_scheduled_events()
            self.process_incoming_msgs()

    def process_scheduled_events(self):
        """Process events based on their scheduled time."""
        if not self.scheduled_events.empty():
            scheduled_time, payload, target_proc_id = self.scheduled_events.queue[0]
            if self.current_time() >= scheduled_time:
                self.scheduled_events.get()  # Remove the event from the queue
                self.process_event(payload, target_proc_id)

    def process_incoming_msgs(self):
        """Process any incoming msgs from other processes."""
        try:
            msg_payload, sender_clock = self.msg_queue.get(timeout=0.1)
            self.process_msg(msg_payload, sender_clock)
        except Empty:
            pass

    def current_time(self):
        """Calculate and return the current time since process start."""
        return time.time() - self.init_time

    def process_msg(self, payload, sender_clock):
        """Process a received msg, updating the vector clock."""
        for i in range(len(self.vector_clock)):
            self.vector_clock[i] = max(self.vector_clock[i], sender_clock[i])
        self.vector_clock[self.process_id] += 1
        self.log_event("Received", payload)

    def queue_msg(self, payload, clock):
        """Queue a msg for sending to another process."""
        self.msg_queue.put((payload, clock))

    def send_msg(self, target_proc_id, payload):
        """Send a msg to a target process."""
        if 0 <= target_proc_id < len(self.connected_processes):
            self.vector_clock[self.process_id] += 1
            self.connected_processes[target_proc_id].queue_msg(payload, self.vector_clock.copy())
        else:
            raise IndexError(f"Invalid process ID: {target_proc_id}")

    def process_event(self, payload, target_proc_id):
        """Process an event, either local or sending a msg."""
        if payload == "STOP":
            self.active.set()
            return

        if target_proc_id == self.process_id:
            self.vector_clock[self.process_id] += 1
            self.log_event("Local", payload)
        else:
            self.send_msg(target_proc_id, payload)

    def log_event(self, event_type, event_payload):
        """Log an event with its details."""
        log_entry = f"{event_type} event [PROCESS_ID: {self.process_id}], [CLOCK: {self.vector_clock}], [PAYLOAD: {event_payload}], [TIME: {round(self.current_time(), 2)}]"
        self.event_log.append(log_entry)
        print(log_entry)

    def start_process(self):
        """Start the process's main thread."""
        self.process_thread.start()

    def stop_process(self):
        """Stop the process and wait for the thread to finish."""
        self.active.set()
        self.process_thread.join()

    def schedule_events(self, events):
        """Schedule events for the process."""
        self.scheduled_events = events
