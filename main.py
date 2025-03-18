import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
import random

class DeadlockToolkit:
    def __init__(self, processes: int, resources: int):
        """Initialize the toolkit with number of processes and resources."""
        self.processes = processes
        self.resources = resources
        # Allocation matrix: what each process currently holds
        self.allocation = np.zeros((processes, resources), dtype=int)
        # Maximum demand matrix: what each process might need
        self.maximum = np.zeros((processes, resources), dtype=int)
        # Available resources vector
        self.available = np.zeros(resources, dtype=int)
        # Need matrix: maximum - allocation
        self.need = np.zeros((processes, resources), dtype=int)

    def initialize_system(self, available: List[int], max_matrix: List[List[int]]):
        """Set up initial system state."""
        self.available = np.array(available)
        self.maximum = np.array(max_matrix)
        self.need = self.maximum.copy()  # Initially, need = maximum

    def request_resources(self, process_id: int, request: List[int]) -> bool:
        """Simulate a resource request and check safety using Banker's Algorithm."""
        request = np.array(request)
        
        # Check if request exceeds need
        if not np.all(request <= self.need[process_id]):
            print(f"Process {process_id} request exceeds its maximum need.")
            return False
        
        # Check if enough resources are available
        if not np.all(request <= self.available):
            print(f"Process {process_id} must wait; insufficient resources.")
            return False
        
        # Temporarily allocate resources
        self.available -= request
        self.allocation[process_id] += request
        self.need[process_id] -= request
        
        # Check if system is safe
        if self.is_safe_state():
            print(f"Process {process_id} request granted.")
            return True
        else:
            # Roll back if unsafe
            self.available += request
            self.allocation[process_id] -= request
            self.need[process_id] += request
            print(f"Process {process_id} request denied; unsafe state.")
            return False

    def is_safe_state(self) -> bool:
        """Implement Banker's Algorithm to check if system is in a safe state."""
        work = self.available.copy()
        finish = [False] * self.processes
        safe_sequence = []

        while False in finish:
            found = False
            for i in range(self.processes):
                if not finish[i] and np.all(self.need[i] <= work):
                    work += self.allocation[i]
                    finish[i] = True
                    safe_sequence.append(i)
                    found = True
            if not found:
                return False
        print(f"Safe sequence: {safe_sequence}")
        return True

    def release_resources(self, process_id: int, release: List[int]):
        """Release resources from a process."""
        release = np.array(release)
        self.allocation[process_id] -= release
        self.available += release
        self.need[process_id] += release
        print(f"Process {process_id} released resources.")


    def plot_resource_allocation(self):
        """Visualize resource allocation graph."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot allocation and need for each process
        for i in range(self.processes):
            ax.bar([f"P{i}_Alloc", f"P{i}_Need"], 
                   [np.sum(self.allocation[i]), np.sum(self.need[i])], 
                   color=['blue', 'orange'])
        
        # Plot available resources
        ax.bar("Available", np.sum(self.available), color='green')
        
        ax.set_ylabel("Resource Units")
        ax.set_title("Resource Allocation and Need")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def simulate_deadlock(self):
        """Simulate a deadlock scenario with random requests."""
        print("Simulating deadlock scenario...")
        for _ in range(self.processes * 2):  # Arbitrary number of requests
            process_id = random.randint(0, self.processes - 1)
            request = [random.randint(0, 2) for _ in range(self.resources)]
            print(f"Process {process_id} requesting {request}")
            self.request_resources(process_id, request)
            self.plot_resource_allocation()

    def custom_simulation(self):
        """Allow user to input custom resource requests."""
        while True:
            try:
                process_id = int(input("Enter process ID (0 to {}), or -1 to exit: ".format(self.processes - 1)))
                if process_id == -1:
                    break
                if process_id < 0 or process_id >= self.processes:
                    print("Invalid process ID.")
                    continue
                request = input(f"Enter resource request for P{process_id} (e.g., '1 0 2'): ").split()
                request = [int(x) for x in request]
                if len(request) != self.resources:
                    print(f"Request must specify {self.resources} resources.")
                    continue
                self.request_resources(process_id, request)
                self.plot_resource_allocation()
            except ValueError:
                print("Invalid input. Please enter integers.")

def main():
    # Example: 3 processes, 3 resources
    toolkit = DeadlockToolkit(processes=3, resources=3)
    
    # Initial system state
    available = [3, 3, 2]  # Available resources
    max_matrix = [
        [7, 5, 3],  # P0 max need
        [3, 2, 2],  # P1 max need
        [9, 0, 2],  # P2 max need
    ]
    
    toolkit.initialize_system(available, max_matrix)
    
    # Test a request
    toolkit.request_resources(1, [1, 0, 2])
    toolkit.plot_resource_allocation()
    
    # Simulate deadlock
    print("\nStarting random simulation...")
    toolkit.simulate_deadlock()
    
    # Custom simulation
    print("\nStarting custom simulation...")
    toolkit.custom_simulation()

if __name__ == "__main__":
    main()