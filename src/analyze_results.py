"""
Analyze and visualize BB84 batch simulation results.

Usage:
    python3 src/analyze_results.py bb84_results.csv
    python3 src/analyze_results.py bb84_results.csv --plot
    python3 src/analyze_results.py bb84_results.csv --plot --qber-only
    python3 src/analyze_results.py bb84_results.csv --plot --show-all-qber
    python3 src/analyze_results.py bb84_results.csv --plot --smooth
"""

import argparse
import csv
import sys
from pathlib import Path
from collections import defaultdict

def analyze_csv(csv_path, show_plot=False, qber_only=False, show_all_qber=False, smooth_curves=False):
    """Analyze BB84 results CSV and print statistics.
    
    Args:
        csv_path: Path to CSV file
        show_plot: Generate matplotlib plots
        qber_only: Count only QBER-related aborts (ignore insufficient sifting)
        show_all_qber: Include all runs (success+abort) in QBER plot, not just successful
        smooth_curves: Use spline interpolation for smooth QBER curves
    """
    
    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("No data in CSV file.")
        return
    
    print(f"BB84 Batch Results Analysis")
    print(f"{'='*60}")
    print(f"Total runs: {len(rows)}")
    print()
    
    # Overall statistics
    success_count = sum(1 for r in rows if r['status'] == 'success')
    abort_count = len(rows) - success_count
    
    print(f"Overall Success Rate:")
    print(f"  Successful: {success_count} ({100*success_count/len(rows):.1f}%)")
    print(f"  Aborted: {abort_count} ({100*abort_count/len(rows):.1f}%)")
    print()
    
    # Group by n value
    by_n = defaultdict(list)
    for row in rows:
        by_n[int(row['n'])].append(row)
    
    print(f"Results by n (key length):")
    for n in sorted(by_n.keys()):
        n_rows = by_n[n]
        n_success = sum(1 for r in n_rows if r['status'] == 'success')
        print(f"  n={n:3d}: {n_success:3d}/{len(n_rows):3d} successful ({100*n_success/len(n_rows):5.1f}%)")
    print()
    
    # Group by errors
    by_errors = defaultdict(list)
    for row in rows:
        errors = float(row['errors'])
        by_errors[errors].append(row)
    
    print(f"Results by error level:")
    for errors in sorted(by_errors.keys()):
        e_rows = by_errors[errors]
        e_success = sum(1 for r in e_rows if r['status'] == 'success')
        qbers = [float(r['qber']) for r in e_rows if r['status'] == 'success' and r['qber']]
        avg_qber = sum(qbers) / len(qbers) if qbers else 0
        print(f"  errors={errors:5.1f}: {e_success:3d}/{len(e_rows):3d} successful ({100*e_success/len(e_rows):5.1f}%), avg QBER={avg_qber:.4f}")
    print()
    
    # QBER statistics for successful runs
    successful_rows = [r for r in rows if r['status'] == 'success' and r['qber']]
    if successful_rows:
        qbers = [float(r['qber']) for r in successful_rows]
        print(f"QBER Statistics (successful runs only):")
        print(f"  Min:  {min(qbers):.4f}")
        print(f"  Max:  {max(qbers):.4f}")
        print(f"  Mean: {sum(qbers)/len(qbers):.4f}")
        print()
    
    # Abort reasons
    abort_rows = [r for r in rows if r['status'] == 'abort']
    if abort_rows:
        reasons = defaultdict(int)
        for r in abort_rows:
            reason_key = r['reason'].split(':')[0] if ':' in r['reason'] else r['reason']
            reasons[reason_key] += 1
        
        print(f"Abort Reasons:")
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
            print(f"  {reason}: {count} ({100*count/len(abort_rows):.1f}%)")
        print()
    
    # Plot if requested
    if show_plot:
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Set dark background style
            plt.style.use('dark_background')
            
            # Plot 1: QBER vs Errors for each n
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            
            for idx, n in enumerate(sorted(by_n.keys())):
                n_rows = by_n[n]
                
                # Group by error level and calculate mean QBER
                error_qber_map = defaultdict(list)
                for row in n_rows:
                    # Include runs based on show_all_qber flag
                    if show_all_qber:
                        # Include all runs that have a QBER value (success or abort with QBER)
                        if row['qber']:
                            error_qber_map[float(row['errors'])].append(float(row['qber']))
                    else:
                        # Only successful runs
                        if row['status'] == 'success' and row['qber']:
                            error_qber_map[float(row['errors'])].append(float(row['qber']))
                
                # Sort by error level and compute means
                errors_sorted = sorted(error_qber_map.keys())
                qber_means = [np.mean(error_qber_map[e]) for e in errors_sorted]
                
                if errors_sorted and len(errors_sorted) > 1:
                    if smooth_curves and len(errors_sorted) >= 4:
                        # Use moving average for smooth curves (less oscillation than spline)
                        from scipy.ndimage import gaussian_filter1d
                        
                        # Apply Gaussian smoothing
                        qber_smooth = gaussian_filter1d(qber_means, sigma=1.5)
                        
                        ax1.plot(errors_sorted, qber_smooth, 
                                label=f'n={n}', 
                                color=colors[idx % len(colors)],
                                linewidth=2.5, 
                                alpha=0.85)
                    else:
                        # Plot line without markers
                        ax1.plot(errors_sorted, qber_means, 
                                label=f'n={n}', 
                                color=colors[idx % len(colors)],
                                linewidth=2, 
                                alpha=0.8)
            
            title_qber = 'QBER vs Error Level (all runs)' if show_all_qber else 'QBER vs Error Level (successful runs)'
            ax1.axhline(y=0.11, color='r', linestyle='--', linewidth=2, label='Default tolerance (0.11)')
            ax1.set_xlabel('Errors (avg number)', fontsize=11)
            ax1.set_ylabel('QBER', fontsize=11)
            ax1.set_title(title_qber, fontsize=12, fontweight='bold')
            ax1.legend(loc='best')
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Success rate vs Errors
            error_levels = sorted(by_errors.keys())
            success_rates = []
            for errors in error_levels:
                e_rows = by_errors[errors]
                if qber_only:
                    # Count only: success + aborts NOT due to QBER (i.e., ignore sifting failures)
                    # Success if: status == 'success' OR (status == 'abort' AND reason contains 'Not enough sifted')
                    valid_runs = sum(1 for r in e_rows 
                                   if r['status'] == 'success' 
                                   or (r['status'] == 'abort' and 'Not enough sifted' in r.get('reason', '')))
                    e_success = sum(1 for r in e_rows if r['status'] == 'success')
                    # Success rate among runs that didn't fail due to sifting
                    success_rates.append(100 * e_success / valid_runs if valid_runs > 0 else 0)
                else:
                    e_success = sum(1 for r in e_rows if r['status'] == 'success')
                    success_rates.append(100 * e_success / len(e_rows))
            
            title_suffix = ' (QBER failures only)' if qber_only else ''
            ax2.plot(error_levels, success_rates, 
                    marker='o', 
                    linewidth=2.5, 
                    markersize=7,
                    color='#1f77b4',
                    markerfacecolor='white',
                    markeredgewidth=2,
                    markeredgecolor='#1f77b4')
            ax2.fill_between(error_levels, 0, success_rates, alpha=0.2, color='#1f77b4')
            ax2.set_xlabel('Errors (avg number)', fontsize=11)
            ax2.set_ylabel('Success Rate (%)', fontsize=11)
            ax2.set_title(f'Success Rate vs Error Level{title_suffix}', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, 105)
            
            plt.tight_layout()
            plot_file = csv_path.replace('.csv', '_plot.png')
            plt.savefig(plot_file, dpi=150)
            print(f"Plot saved to: {plot_file}")
            plt.show()
            
        except ImportError:
            print("matplotlib not installed. Install with: pip install matplotlib")
            print("Skipping plot generation.")


def main():
    parser = argparse.ArgumentParser(description="Analyze BB84 batch results")
    parser.add_argument("csv_file", help="CSV file with batch results")
    parser.add_argument("--plot", action="store_true", help="Generate plots (requires matplotlib)")
    parser.add_argument("--qber-only", action="store_true", 
                        help="Success rate: ignore aborts due to insufficient sifting (count only QBER failures)")
    parser.add_argument("--show-all-qber", action="store_true",
                        help="QBER plot: include all runs (success + abort), not just successful runs")
    parser.add_argument("--smooth", action="store_true",
                        help="QBER plot: use smooth spline interpolation for curves (requires scipy)")
    
    args = parser.parse_args()
    
    analyze_csv(args.csv_file, args.plot, args.qber_only, args.show_all_qber, args.smooth)


if __name__ == "__main__":
    main()
