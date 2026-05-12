from lib.simulator import QuantumSimulator

sim = QuantumSimulator(n_qubits=2)
sim.x(0)
sim.cnot(1, 0)
sim.h(1)

measurements = sim.measure(shots=1000)
probabilities = sim.get_probabilities()
state_vector = sim.get_state()

print('Measurements:', measurements)
print('Probabilities:', probabilities)