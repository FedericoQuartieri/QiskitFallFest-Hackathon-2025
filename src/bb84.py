"""
The BB84 QKD protocol

1: Alice chooses (4 + delta) * n random data bits.
2: Alice chooses a random (4 + delta) * n-bit string b. She encodes each data bit as
   {|0>, |1>} if the corresponding bit of b is 0 or {|+>, |->} if b is 1.
3: Alice sends the resulting state to Bob.
4: Bob receives the (4 + delta) * n qubits, announces this fact, and measures each
   qubit in the X or Z basis at random.
5: Alice announces b.
6: Alice and Bob discard any bits where Bob measured a different basis than
   Alice prepared. With high probability, there are at least 2n bits left (if not,
   abort the protocol). They keep 2n bits.
7: Alice selects a subset of n bits that will serve as a check on Eve's
   interference, and tells Bob which bits she selected.
8: Alice and Bob announce and compare the values of the n check bits. If more
   than an acceptable number disagree, they abort the protocol.
9: Alice and Bob perform information reconciliation and privacy amplification on
   the remaining n bits to obtain m shared key bits.
"""

# Basic BB84 simulation using Qiskit
# Functions:
# - run_bb84(n, delta, tolerance): run one instance returning status and keys/stats
# - main CLI example

import math
import random
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

def prepare_alice_circuit(data_bits, alice_bases):
    L = len(data_bits)
    qc = QuantumCircuit(L, L, name=f"BB84-{L}q") # All qubits start from |0>
    for i in range(L):
        b = alice_bases[i]
        bit = data_bits[i]
        if b == 0:
            if bit == 1:
                qc.x(i) # Flip ones
        else:
            if bit == 0:
                qc.h(i)
            else:
                qc.x(i)
                qc.h(i)
    return qc


def measure_bob_in_bases(qc, bob_bases):
    L = len(bob_bases)
    for i in range(L):
        if bob_bases[i] == 1:
            # measure X == apply H + measure Z
            qc.h(i)
        qc.measure(i, i)
    return qc


def run_bb84(n, delta, tolerance, backend):
    """Run a single BB84 simulation.
    n: target final sifted-key length after check (we follow the description that keeps 2n then uses n for check and n for raw key)
    delta: security margin used in (4+delta)*n total qubits
    tolerance: maximum acceptable QBER on check bits before abort

    Returns a dict with status and details.
    """
    # Generate random bit strings ###########################################
    total = math.ceil((4.0 + float(delta)) * n)
    # Alice
    data_bits = [random.randint(0, 1) for _ in range(total)]
    alice_bases = [random.randint(0, 1) for _ in range(total)]
    # Bob
    bob_bases = [random.randint(0, 1) for _ in range(total)]

    #### Build circuit (Alice + Bob) ######################################## 
    qc = prepare_alice_circuit(data_bits, alice_bases)
    # TODO: add random channel errors
    qc = measure_bob_in_bases(qc, bob_bases)

    # Run circuit (single-shot simulation) ##################################
    tcirc = transpile(qc, backend)
    job = backend.run(tcirc, shots=1)
    result = job.result()
    counts = result.get_counts()
    # counts keys are bitstrings with qubit 0 as left-most by default; Qiskit returns in order of classical bits
    measured_str = next(iter(counts))
    # Qiskit returns bitstring with highest index left; reverse to match index order
    measured_bits = [int(bit) for bit in measured_str[::-1]]

    # Sifting: keep positions where bases matched
    sifted_positions = [i for i in range(total) if alice_bases[i] == bob_bases[i]]
    if len(sifted_positions) < 2*n:
        return {
            "status": "abort",
            "reason": f"Not enough sifted bits: got {len(sifted_positions)}, need >= {2*n}",
            "sifted_len": len(sifted_positions)
        }

    # Keep first 2n sifted bits
    kept_pos = sifted_positions[: 2*n]
    alice_kept = [data_bits[i] for i in kept_pos]
    bob_kept = [measured_bits[i] for i in kept_pos]

    # Alice selects n check indices among the 2n
    indices = list(range(2 * n))
    check_indices = random.sample(indices, n)
    key_indices = [i for i in indices if i not in check_indices]

    # Compare check bits
    check_mismatches = 0
    for ci in check_indices:
        if alice_kept[ci] != bob_kept[ci]:
            check_mismatches += 1
    qber = check_mismatches / float(n)

    if qber > tolerance:
        return {
            "status": "abort",
            "reason": f"QBER too high on check bits: {qber:.3f} > {tolerance}",
            "qber": qber,
            "check_mismatches": check_mismatches,
            "n": n,
        }

    # Remaining n bits form the raw key (before reconciliation / privacy amplification)
    raw_key_alice = [alice_kept[i] for i in key_indices]
    raw_key_bob = [bob_kept[i] for i in key_indices]

    # For this basic demo, we assume perfect information reconciliation if QBER <= tolerance
    # and return the raw key (in practice, apply error correction and privacy amplification).
    shared_key = raw_key_alice  # TODO: improve selection?

    return {
        "status": "success",
        "qber" : qber,
        "sifted_len": len(sifted_positions),
        "total_qubits": total,
        "shared_key_bits": shared_key,
    }
if __name__ == "__main__":
    # Simple CLI demo: run with n=4, delta=0.2
    import argparse

    parser = argparse.ArgumentParser(description="Run a basic BB84 simulation (demo)")
    parser.add_argument("--n", type=int, default=16, help="target final sifted key length n")
    parser.add_argument("--delta", type=float, default=0.2, help="delta parameter in (4+delta)*n")
    parser.add_argument("--tolerance", type=float, default=0.11, help="maximum acceptable QBER on check bits")
    parser.add_argument("--backend", type=str, default="stabilizer", help="backend simulator type to use")
    args = parser.parse_args()
    
    backend = AerSimulator(method=args.backend)

    res = run_bb84(args.n, args.delta, args.tolerance, backend)
    if res.get("status") == "success":
        print("BB84 run successful")
        print(f"Total qubits sent: {res['total_qubits']}")
        print(f"Sifted bits available: {res['sifted_len']}")
        print(f"QBER on checked bits: {res['qber']:.4f}")
        print(f"Shared raw key ({len(res['shared_key_bits'])} bits): {''.join(map(str, res['shared_key_bits']))}")
    else:
        print("BB84 aborted:", res.get("reason"))