from qiskit import QuantumCircuit, transpile
from qiskit.primitives import StatevectorSampler
from qiskit_aer import AerSimulator
import sys

# /d:/Repos/QiskitFallFest-Hackathon-2025/src/main.py
"""
Qiskit basics demo: create a Bell state, simulate statevector and measurement (QASM),
and print results. Requires qiskit (qiskit-aer).
Run: python src/main.py
"""

def make_bell_circuit():
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    # measure both qubits into both classical bits
    qc.measure([0, 1], [0, 1])
    return qc


def make_bell_statevector_circuit():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    return qc


def run_statevector(circuit):
    backend = AerSimulator(method='statevector')
    tcirc = transpile(circuit, backend)
    job = backend.run(tcirc)
    result = job.result()
    # get_statevector accepts the circuit or the job index
    try:
        sv = result.get_statevector(tcirc)
    except Exception:
        sv = result.get_statevector()
    return sv


def run_qasm(circuit, shots=1024):
    backend = AerSimulator(method='statevector')
    tcirc = transpile(circuit, backend)
    job = backend.run(tcirc, shots=shots)
    result = job.result()
    return result.get_counts()


def main():
    try:
        # build circuits
        qc_measure = make_bell_circuit()
        qc_sv = make_bell_statevector_circuit()

        # show circuit
        print("Circuit (with measurements):")
        print(qc_measure.draw(output='text'))

        # statevector before measurement
        sv = run_statevector(qc_sv)
        print("Statevector (Bell state):")
        print(sv)

        # sampling (measurement) results
        counts = run_qasm(qc_measure, shots=1024)
        print("Measurement counts (1024 shots):")
        print(counts)

    except Exception as e:
        print("Error running Qiskit demo:", file=sys.stderr)
        print("Make sure qiskit and qiskit-aer are installed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()