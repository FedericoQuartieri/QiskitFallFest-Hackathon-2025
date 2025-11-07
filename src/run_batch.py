"""
Batch runner for BB84 simulations.
Runs multiple BB84 instances with varying n and errors parameters,
and saves results to CSV for analysis.

Usage:
    python3 src/run_batch.py
    python3 src/run_batch.py --n-range 16 32 64 128 --error-range 0 5 10 15 20 25 30
    python3 src/run_batch.py --workers 8  # Use 8 parallel workers
"""

import argparse
import subprocess
import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool, cpu_count
from functools import partial

def run_bb84_json(n, delta, tolerance, errors, backend="stabilizer", bobperfect=False, eve=False):
    """Run BB84 and return parsed JSON result."""
    cmd = [
        "python3", "src/bb84.py",
        "--n", str(n),
        "--delta", str(delta),
        "--tolerance", str(tolerance),
        "--errors", str(errors),
        "--backend", backend,
        "--json"
    ]
    
    if bobperfect:
        cmd.append("--bobperfect")
    
    if eve:
        cmd.append("--eve")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        # Parse JSON from stdout
        output = result.stdout.strip()
        if output:
            data = json.loads(output)
            return data
        else:
            return {"status": "error", "reason": "No output", "stderr": result.stderr}
    except json.JSONDecodeError as e:
        return {"status": "error", "reason": f"JSON parse error: {e}", "stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def run_single_config(config):
    """Wrapper function for parallel execution. Returns config + result."""
    n, delta, tolerance, errors, backend, repeat, bobperfect, eve = config
    result = run_bb84_json(n, delta, tolerance, errors, backend, bobperfect, eve)
    
    # Add config info to result
    return {
        'config': config,
        'result': result,
        'timestamp': datetime.now().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="Run batch BB84 simulations")
    parser.add_argument("--n-range", nargs="+", type=int, default=[16, 32, 64, 128, 256],
                        help="List of n values to test (default: 16 32 64 128)")
    parser.add_argument("--error-range", nargs="+", type=float, default=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125],
                        help="List of error values to test (default: 0 to 125 in steps of 5)")
    parser.add_argument("--delta", type=float, default=0.2,
                        help="Delta parameter (default: 0.2)")
    parser.add_argument("--tolerance", type=float, default=0.11,
                        help="QBER tolerance (default: 0.11)")
    parser.add_argument("--backend", type=str, default="stabilizer",
                        help="Backend to use (default: stabilizer)")
    parser.add_argument("--output", type=str, default="bb84_results.csv",
                        help="Output CSV file (default: bb84_results.csv)")
    parser.add_argument("--repeats", type=int, default=5,
                        help="Number of repetitions per configuration (default: 5)")
    parser.add_argument("--workers", type=int, default=None,
                        help=f"Number of parallel workers (default: auto = {cpu_count()})")
    parser.add_argument("--bobperfect", action="store_true", 
                        help="Bob always exactly guesses Alice's bases (no sifting losses)")
    parser.add_argument("--eve", action="store_true", 
                        help="Enable Eve's interference on the quantum channel")

    args = parser.parse_args()
    
    # Determine number of workers
    if args.workers is None:
        workers = cpu_count()
    else:
        workers = max(1, min(args.workers, cpu_count()))
    
    # Prepare CSV output
    output_path = Path(args.output)
    
    # Build all configurations to run
    configs = []
    for n in args.n_range:
        for errors in args.error_range:
            for repeat in range(args.repeats):
                configs.append((n, args.delta, args.tolerance, errors, args.backend, repeat + 1, args.bobperfect, args.eve))
    
    total_runs = len(configs)
    
    print(f"Starting batch BB84 simulation:")
    print(f"  n values: {args.n_range}")
    print(f"  error values: {args.error_range}")
    print(f"  repeats per config: {args.repeats}")
    print(f"  total runs: {total_runs}")
    print(f"  parallel workers: {workers}")
    print(f"  Bob perfect: {args.bobperfect}")
    print(f"  Eve present: {args.eve}")
    print(f"  output: {output_path}")
    print()
    
    # Run simulations in parallel
    print("Running simulations...")
    completed = 0
    results_list = []
    
    with Pool(workers) as pool:
        # Use imap_unordered for progress updates
        for run_result in pool.imap_unordered(run_single_config, configs):
            completed += 1
            n, delta, tolerance, errors, backend, repeat, bobperfect, eve = run_result['config']
            result = run_result['result']
            timestamp = run_result['timestamp']
            
            status_symbol = "✓" if result.get('status') == 'success' else "✗"
            print(f"[{completed}/{total_runs}] n={n}, errors={errors:.1f}, repeat={repeat} {status_symbol}")
            sys.stdout.flush()
            
            # Store result
            results_list.append({
                'timestamp': timestamp,
                'n': n,
                'delta': delta,
                'tolerance': tolerance,
                'errors': errors,
                'backend': backend,
                'repeat': repeat,
                'status': result.get('status', 'unknown'),
                'qber': result.get('qber', ''),
                'total_qubits': result.get('total_qubits', ''),
                'sifted_len': result.get('sifted_len', ''),
                'key_length': len(result.get('shared_key_bits', [])) if 'shared_key_bits' in result else '',
                'reason': result.get('reason', '')
            })
    
    # Write all results to CSV
    print(f"\nWriting results to {output_path}...")
    with open(output_path, 'w', newline='') as csv_file:
        fieldnames = [
            'timestamp', 'n', 'delta', 'tolerance', 'errors', 'backend', 'repeat',
            'status', 'qber', 'total_qubits', 'sifted_len', 'key_length', 'reason'
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_list)
    
    print()
    print(f"Batch simulation complete. Results saved to: {output_path}")
    print()
    print("Summary:")
    
    # Quick summary
    total = len(results_list)
    success = sum(1 for r in results_list if r['status'] == 'success')
    abort = total - success
    
    print(f"  Total runs: {total}")
    print(f"  Successful: {success} ({100*success/total:.1f}%)")
    print(f"  Aborted: {abort} ({100*abort/total:.1f}%)")
    
    if success > 0:
        qbers = [float(r['qber']) for r in results_list if r['status'] == 'success' and r['qber']]
        if qbers:
            print(f"  QBER range (successful runs): {min(qbers):.4f} - {max(qbers):.4f}")


if __name__ == "__main__":
    main()
