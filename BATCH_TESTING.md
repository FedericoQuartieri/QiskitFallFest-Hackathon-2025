# BB84 Quantum Key Distribution - Batch Testing

## Quick Start

### Run batch simulations with default parameters

```bash
python3 src/run_batch.py
```

This will run BB84 with:
- **n values**: 16, 32, 64, 128
- **error values**: 0, 2, 5, 10, 15, 20, 25, 30
- **Total runs**: 32 (4 n values × 8 error values)
- **Output**: `bb84_results.csv`

### Customize parameters

```bash
# Custom n range
python3 src/run_batch.py --n-range 16 32 64 128 256

# Custom error range  
python3 src/run_batch.py --error-range 0 5 10 15 20 25 

# Multiple repeats per configuration (for statistical analysis)
python3 src/run_batch.py --repeats 5

# Custom output file
python3 src/run_batch.py --output my_results.csv

# Combine all options
python3 src/run_batch.py --n-range 32 64 --error-range 0 10 20 30 --repeats 3 --output custom.csv
```

### Analyze results

```bash
# Print statistics
python3 src/analyze_results.py bb84_results.csv

# Generate plots (requires matplotlib)
python3 src/analyze_results.py bb84_results.csv --plot
```

## Output Format

The CSV file contains:
- `timestamp`: when the run was executed
- `n`: target key length
- `delta`: security margin parameter
- `tolerance`: maximum acceptable QBER
- `errors`: average number of errors introduced
- `backend`: simulator backend used
- `repeat`: repetition number
- `status`: "success" or "abort"
- `qber`: Quantum Bit Error Rate (for successful runs)
- `total_qubits`: total qubits sent by Alice
- `sifted_len`: number of bits after sifting
- `key_length`: final shared key length
- `reason`: abort reason (if aborted)

## Example Use Cases

### Test different key lengths with fixed error rate
```bash
python3 src/run_batch.py --n-range 8 16 32 64 128 256 --error-range 5.0 --repeats 10
```

### Test sensitivity to errors with fixed key length
```bash
python3 src/run_batch.py --n-range 32 --error-range 0 1 2 3 4 5 10 15 20 25 30 --repeats 5
```

### Quick test (fast)
```bash
python3 src/run_batch.py --n-range 16 --error-range 0 10 20 --repeats 1
```

### Comprehensive test (slow)
```bash
python3 src/run_batch.py --n-range 16 32 64 128 --error-range 0 2 5 10 15 20 25 30 --repeats 10
```

## Single Run (Manual Testing)

You can still run single BB84 instances:

```bash
# Basic run
python3 src/bb84.py

# Custom parameters
python3 src/bb84.py --n 32 --errors 10.0 --tolerance 0.15

# JSON output (used by batch runner)
python3 src/bb84.py --n 32 --errors 10.0 --json
```

## Understanding Results

### Success Rate
- **High errors** → more aborts (QBER exceeds tolerance)
- **Low errors** → high success rate
- Threshold typically around errors = 10-15 with default tolerance

### QBER (Quantum Bit Error Rate)
- QBER = (mismatched check bits) / (total check bits)
- **QBER ≈ 0%**: no errors or eavesdropping
- **QBER ≈ 3-5%**: low channel noise
- **QBER > 11%** (default tolerance): protocol aborts
- **QBER ≈ 25%**: theoretical maximum with full eavesdropping

### Key Length
- Successful runs produce `n` bits of raw key
- Sifted length is typically ~2n (before check bit selection)
- Total qubits sent = ceil((4 + delta) × n)

## Troubleshooting

### "No such file or directory"
Make sure you're in the project root directory:
```bash
cd /path/to/QiskitFallFest-Hackathon-2025
python3 src/run_batch.py
```

### Slow execution
- Reduce number of runs: use smaller `--n-range` and `--error-range`
- Reduce `--repeats`
- Use faster backend: `--backend stabilizer` (default, fastest)

### Plot generation fails
Install matplotlib:
```bash
python3 -m pip install --user --break-system-packages matplotlib
```

## Advanced Options

### Different backends
```bash
python3 src/run_batch.py --backend statevector
python3 src/run_batch.py --backend qasm
```

Available backends (AerSimulator): automatic, statevector, density_matrix, stabilizer, matrix_product_state, extended_stabilizer, unitary, superop

### Different tolerance levels
```bash
# More permissive (accept higher QBER)
python3 src/run_batch.py --tolerance 0.20

# More strict (lower QBER required)
python3 src/run_batch.py --tolerance 0.05
```

## Next Steps

After running batch simulations:
1. Analyze CSV with `analyze_results.py`
2. Import CSV into Excel/Python/R for custom analysis
3. Generate plots to visualize QBER vs errors, success rate, etc.
4. Tune parameters (`delta`, `tolerance`) based on results
5. Test on real quantum hardware (requires IBM Quantum account)
