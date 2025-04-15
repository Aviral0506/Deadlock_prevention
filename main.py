# Deadlock Prevention and Recovery Toolkit 
import streamlit as st
import time
from typing import List, Dict
import threading
import random
import graphviz
import pandas as pd

class DeadlockToolkit:
    def __init__(self):
        self.resources = {}
        self.processes = {}
        self.lock = threading.Lock()
        self.action_log = []
        self.safe_sequence = []

    def log_action(self, message: str):
        timestamp = time.strftime('%H:%M:%S')
        self.action_log.append(f"[{timestamp}] {message}")

    def initialize_system(self, num_resources: int, num_processes: int):
        with self.lock:
            self.resources = {f"R{i}": random.randint(1, 5) for i in range(num_resources)}
            self.processes = {
                f"P{i}": {
                    "allocated": {},
                    "max_needed": {},
                    "status": "Running"
                } for i in range(num_processes)
            }
            for pid in self.processes:
                for rid in self.resources:
                    self.processes[pid]["max_needed"][rid] = random.randint(0, self.resources[rid])
                    self.processes[pid]["allocated"][rid] = 0
            self.action_log.clear()
            self.log_action("System initialized.")

    def request_resource(self, process_id: str, resource_id: str, amount: int) -> bool:
        with self.lock:
            if resource_id not in self.resources or process_id not in self.processes:
                return False
            if amount > self.processes[process_id]["max_needed"][resource_id]:
                return False
            available = self.resources[resource_id] - sum(
                p["allocated"].get(resource_id, 0) for p in self.processes.values()
            )
            if available < amount:
                return False
            temp_allocated = self.processes[process_id]["allocated"].copy()
            temp_allocated[resource_id] += amount
            safe, sequence = self.is_safe_state(process_id, temp_allocated)
            if safe:
                self.processes[process_id]["allocated"][resource_id] = temp_allocated[resource_id]
                self.safe_sequence = sequence
                self.log_action(f"{process_id} safely allocated {amount} of {resource_id}.")
                return True
            self.log_action(f"{process_id}'s request for {resource_id} denied due to unsafe state.")
            return False

    def is_safe_state(self, process_id: str, temp_allocated: Dict) -> (bool, List[str]):
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
        sequence = []
        while True:
            found = False
            for pid in temp_processes:
                if not temp_processes[pid]["finished"]:
                    if all(
                        temp_processes[pid]["max_needed"][rid] - temp_processes[pid]["allocated"][rid] <= available[rid]
                        for rid in self.resources
                    ):
                        for rid in self.resources:
                            available[rid] += temp_processes[pid]["allocated"][rid]
                        temp_processes[pid]["finished"] = True
                        sequence.append(pid)
                        found = True
            if not found:
                return all(p["finished"] for p in temp_processes.values()), sequence
            if all(p["finished"] for p in temp_processes.values()):
                return True, sequence

    def detect_deadlock(self) -> List[str]:
        waiting = {}
        for pid in self.processes:
            for rid in self.resources:
                need = self.processes[pid]["max_needed"][rid] - self.processes[pid]["allocated"][rid]
                if need > 0:
                    waiting[pid] = waiting.get(pid, []) + [rid]
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
        if deadlocked:
            self.log_action(f"Deadlock detected among: {', '.join(deadlocked)}")
        return deadlocked

    def recover_deadlock(self):
        deadlocked = self.detect_deadlock()
        if deadlocked:
            with self.lock:
                for pid in deadlocked[:1]:
                    for rid in self.resources:
                        self.resources[rid] += self.processes[pid]["allocated"].get(rid, 0)
                        self.processes[pid]["allocated"][rid] = 0
                    self.processes[pid]["status"] = "Terminated"
                    self.log_action(f"Terminated {pid} to resolve deadlock.")
            return f"Terminated {pid} to recover from deadlock"
        return "No deadlock detected"

    def generate_rag(self) -> graphviz.Digraph:
        g = graphviz.Digraph()
        for rid in self.resources:
            g.node(rid, shape='box')
        for pid in self.processes:
            g.node(pid, shape='ellipse')
            for rid, amount in self.processes[pid]["allocated"].items():
                if amount > 0:
                    g.edge(rid, pid, label=str(amount))
            for rid in self.resources:
                need = self.processes[pid]["max_needed"][rid] - self.processes[pid]["allocated"][rid]
                if need > 0:
                    g.edge(pid, rid, style='dashed', label=str(need))
        return g

# Streamlit UI
st.set_page_config(layout="wide")
st.title("🛠️ Deadlock Prevention & Recovery Toolkit")
toolkit = DeadlockToolkit()

st.sidebar.header("⚙️ System Configuration")
num_resources = st.sidebar.slider("Number of Resources", 1, 10, 3)
num_processes = st.sidebar.slider("Number of Processes", 1, 10, 3)

if st.sidebar.button("Initialize System"):
    toolkit.initialize_system(num_resources, num_processes)
    st.session_state["toolkit"] = toolkit
    st.success("✅ System initialized successfully!")

if "toolkit" in st.session_state:
    toolkit = st.session_state["toolkit"]

    st.subheader("📊 System State")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Resources**")
        st.json(toolkit.resources)
    with col2:
        st.write("**Processes**")
        st.json({pid: {
            "allocated": p["allocated"],
            "max_needed": p["max_needed"],
            "status": p["status"]
        } for pid, p in toolkit.processes.items()})

    st.subheader("🧠 Resource Allocation Graph")
    st.graphviz_chart(toolkit.generate_rag())

    st.subheader("📥 Request Resource")
    process_id = st.selectbox("Select Process", list(toolkit.processes.keys()))
    resource_id = st.selectbox("Select Resource", list(toolkit.resources.keys()))
    amount = st.number_input("Amount", min_value=1, max_value=10, value=1)
    if st.button("Request Resource"):
        success = toolkit.request_resource(process_id, resource_id, amount)
        if success:
            st.success("✅ Request granted")
        else:
            st.error("❌ Request denied")
        if toolkit.safe_sequence:
            st.info(f"Safe sequence: {toolkit.safe_sequence}")

    st.subheader("🧯 Deadlock Management")
    if st.button("Detect Deadlock"):
        deadlocked = toolkit.detect_deadlock()
        st.warning(f"Deadlocked processes: {deadlocked}" if deadlocked else "✅ No deadlock detected")

    if st.button("Recover from Deadlock"):
        result = toolkit.recover_deadlock()
        st.info(result)

    st.subheader("📄 Action Log")
    if toolkit.action_log:
        st.code("\n".join(toolkit.action_log))

    st.subheader("📋 Matrices")
    st.write("**Allocation Matrix**")
    alloc_df = pd.DataFrame({pid: p["allocated"] for pid, p in toolkit.processes.items()}).T
    st.dataframe(alloc_df)
    st.write("**Max Needed Matrix**")
    max_df = pd.DataFrame({pid: p["max_needed"] for pid, p in toolkit.processes.items()}).T
    st.dataframe(max_df)

    st.sidebar.subheader("💡 Project Features")
    st.sidebar.markdown("""
    - ✅ Deadlock Prevention (Banker's Algorithm)
    - ✅ Deadlock Detection & Recovery
    - 📈 Resource Allocation Graph (RAG)
    - 📝 Real-time Action Log
    - ✅ Safe Sequence Visualization
    """)
