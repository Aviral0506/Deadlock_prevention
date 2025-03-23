# deadlock_toolkit.py
import streamlit as st
import time
from typing import List, Dict
import threading
import random

class DeadlockToolkit:
    def __init__(self):
        self.resources = {}
        self.processes = {}
        self.lock = threading.Lock()

    def initialize_system(self, num_resources: int, num_processes: int):
        """Initialize system with resources and processes"""
        with self.lock:
            self.resources = {f"R{i}": random.randint(1, 5) for i in range(num_resources)}
            self.processes = {
                f"P{i}": {
                    "allocated": {},
                    "max_needed": {},
                    "status": "Running"
                } for i in range(num_processes)
            }
            # Initialize resource allocation
            for pid in self.processes:
                for rid in self.resources:
                    self.processes[pid]["max_needed"][rid] = random.randint(0, self.resources[rid])
                    self.processes[pid]["allocated"][rid] = 0

    def request_resource(self, process_id: str, resource_id: str, amount: int) -> bool:
        """Resource request with Banker's Algorithm for deadlock prevention"""
        with self.lock:
            if resource_id not in self.resources or process_id not in self.processes:
                return False

            # Check if request exceeds maximum needed
            if amount > self.processes[process_id]["max_needed"][resource_id]:
                return False

            # Check if enough resources are available
            available = self.resources[resource_id] - sum(
                p["allocated"].get(resource_id, 0) for p in self.processes.values()
            )

            if available < amount:
                return False

            # Simulate allocation for safety check
            temp_allocated = self.processes[process_id]["allocated"].copy()
            temp_allocated[resource_id] = temp_allocated.get(resource_id, 0) + amount
            
            if self.is_safe_state(process_id, temp_allocated):
                self.processes[process_id]["allocated"][resource_id] = temp_allocated[resource_id]
                return True
            return False

    def is_safe_state(self, process_id: str, temp_allocated: Dict) -> bool:
        """Check if system is in safe state using Banker's Algorithm"""
        available = {
            rid: self.resources[rid] - sum(
                p["allocated"].get(rid, 0) for p in self.processes.values()
            ) for rid in self.resources
        }
        
        temp_processes = {
            pid: {
                "allocated": p["allocated"].copy() if pid != process_id else temp_allocated,
                "max_needed": p["max_needed"].copy(),
                "finished": False
            } for pid, p in self.processes.items()
        }

        while True:
            found = False
            for pid in temp_processes:
                if not temp_processes[pid]["finished"]:
                    can_run = True
                    for rid in self.resources:
                        need = temp_processes[pid]["max_needed"][rid] - temp_processes[pid]["allocated"][rid]
                        if need > available[rid]:
                            can_run = False
                            break
                    if can_run:
                        for rid in self.resources:
                            available[rid] += temp_processes[pid]["allocated"][rid]
                        temp_processes[pid]["finished"] = True
                        found = True

            if not found:
                return all(p["finished"] for p in temp_processes.values())
            if all(p["finished"] for p in temp_processes.values()):
                return True

    def detect_deadlock(self) -> List[str]:
        """Detect deadlock using resource allocation graph"""
        waiting = {}
        for pid in self.processes:
            for rid in self.resources:
                need = self.processes[pid]["max_needed"][rid] - self.processes[pid]["allocated"][rid]
                if need > 0:
                    waiting[pid] = waiting.get(pid, []) + [rid]

        # Simple cycle detection
        visited = set()
        def has_cycle(pid, path):
            if pid in path:
                return True
            if pid in visited:
                return False
            visited.add(pid)
            for rid in waiting.get(pid, []):
                for next_pid in self.processes:
                    if self.processes[next_pid]["allocated"].get(rid, 0) > 0:
                        if has_cycle(next_pid, path + [pid]):
                            return True
            return False

        deadlocked = []
        for pid in self.processes:
            visited.clear()
            if has_cycle(pid, []):
                deadlocked.append(pid)
        return deadlocked

    def recover_deadlock(self):
        """Recover from deadlock by terminating processes"""
        deadlocked = self.detect_deadlock()
        if deadlocked:
            with self.lock:
                for pid in deadlocked[:1]:  # Terminate one process at a time
                    for rid in self.resources:
                        self.resources[rid] += self.processes[pid]["allocated"].get(rid, 0)
                        self.processes[pid]["allocated"][rid] = 0
                    self.processes[pid]["status"] = "Terminated"
            return f"Terminated process {pid} to recover from deadlock"
        return "No deadlock detected"

# Streamlit GUI
def main():
    st.title("Deadlock Prevention & Recovery Toolkit")
    toolkit = DeadlockToolkit()

    # Sidebar configuration
    st.sidebar.header("System Configuration")
    num_resources = st.sidebar.slider("Number of Resources", 1, 10, 3)
    num_processes = st.sidebar.slider("Number of Processes", 1, 10, 3)
    
    if st.sidebar.button("Initialize System"):
        toolkit.initialize_system(num_resources, num_processes)
        st.session_state["toolkit"] = toolkit
        st.success("System initialized successfully!")

    if "toolkit" in st.session_state:
        toolkit = st.session_state["toolkit"]

        # Display system state
        st.subheader("System State")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Resources:")
            st.json(toolkit.resources)
            
        with col2:
            st.write("Processes:")
            st.json({pid: {
                "allocated": p["allocated"],
                "max_needed": p["max_needed"],
                "status": p["status"]
            } for pid, p in toolkit.processes.items()})

        # Resource Request
        st.subheader("Resource Request")
        process_id = st.selectbox("Select Process", list(toolkit.processes.keys()))
        resource_id = st.selectbox("Select Resource", list(toolkit.resources.keys()))
        amount = st.number_input("Amount", min_value=1, max_value=10, value=1)
        
        if st.button("Request Resource"):
            success = toolkit.request_resource(process_id, resource_id, amount)
            st.success(f"Resource request {'succeeded' if success else 'failed'}")

        # Deadlock Detection and Recovery
        st.subheader("Deadlock Management")
        if st.button("Detect Deadlock"):
            deadlocked = toolkit.detect_deadlock()
            st.write(f"Deadlocked processes: {deadlocked if deadlocked else 'None'}")

        if st.button("Recover from Deadlock"):
            result = toolkit.recover_deadlock()
            st.write(result)

if __name__ == "__main__":
    main()