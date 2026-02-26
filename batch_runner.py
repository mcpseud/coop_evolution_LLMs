#!/usr/bin/env python3
"""
Batch Experiment Runner for LLM Game Theory Simulations.

Runs multiple experiments (with replicates and parameter variations) from a
single CSV config file, with optional parallelism.

Usage:
    python batch_runner.py --batch config.csv --output results/ --workers 3 --dry-run
"""

import argparse
import csv
import json
import os
import re
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from statistics import mean


# ---------------------------------------------------------------------------
# Config loading and validation
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = {"experiment_name", "agents_csv", "experiment_csv"}
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def load_batch_config(batch_csv_path):
    """Read the batch config CSV and validate every row.

    Returns a list of dicts with keys:
        experiment_name, agents_csv, experiment_csv, replicates
    """
    batch_path = Path(batch_csv_path)
    if not batch_path.exists():
        sys.exit(f"Error: batch config file not found: {batch_path}")

    experiments = []
    with open(batch_path, newline="") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            sys.exit(f"Error: batch config file is empty: {batch_path}")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            sys.exit(
                f"Error: batch config missing required columns: {', '.join(sorted(missing))}"
            )

        for row_num, row in enumerate(reader, start=2):  # header is row 1
            name = row["experiment_name"].strip()
            if not name:
                sys.exit(f"Error (row {row_num}): experiment_name is empty")
            if not NAME_PATTERN.match(name):
                sys.exit(
                    f"Error (row {row_num}): experiment_name '{name}' contains "
                    f"invalid characters (only letters, digits, hyphens, underscores)"
                )

            agents_csv = row["agents_csv"].strip()
            if not Path(agents_csv).exists():
                sys.exit(
                    f"Error (row {row_num}): agents_csv file not found: {agents_csv}"
                )

            experiment_csv = row["experiment_csv"].strip()
            if not Path(experiment_csv).exists():
                sys.exit(
                    f"Error (row {row_num}): experiment_csv file not found: {experiment_csv}"
                )

            replicates_str = row.get("replicates", "1").strip()
            if not replicates_str:
                replicates_str = "1"
            try:
                replicates = int(replicates_str)
                if replicates < 1:
                    raise ValueError
            except ValueError:
                sys.exit(
                    f"Error (row {row_num}): replicates must be a positive integer, "
                    f"got '{replicates_str}'"
                )

            experiments.append(
                {
                    "experiment_name": name,
                    "agents_csv": agents_csv,
                    "experiment_csv": experiment_csv,
                    "replicates": replicates,
                }
            )

    if not experiments:
        sys.exit("Error: batch config file has no experiment rows")

    return experiments


# ---------------------------------------------------------------------------
# Job expansion
# ---------------------------------------------------------------------------


def expand_jobs(experiments, base_output):
    """Expand experiments × replicates into individual run jobs."""
    jobs = []
    for exp in experiments:
        for rep in range(1, exp["replicates"] + 1):
            output_dir = Path(base_output) / exp["experiment_name"] / f"rep_{rep}"
            jobs.append(
                {
                    "experiment_name": exp["experiment_name"],
                    "agents_csv": exp["agents_csv"],
                    "experiment_csv": exp["experiment_csv"],
                    "replicate": rep,
                    "output_dir": str(output_dir),
                }
            )
    return jobs


# ---------------------------------------------------------------------------
# Single experiment execution
# ---------------------------------------------------------------------------

EXPERIMENT_TIMEOUT = 3600  # 1 hour


def run_single_experiment(job, api_key=None, dry_run=False, verbose=False):
    """Run one experiment as a subprocess. Returns a result dict."""
    label = f"{job['experiment_name']}/rep_{job['replicate']}"
    start_time = time.time()

    cmd = [
        sys.executable,
        "game_theory_main.py",
        "--agents", job["agents_csv"],
        "--config", job["experiment_csv"],
        "--output", job["output_dir"],
    ]
    if api_key:
        cmd.extend(["--api-key", api_key])
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--verbose")

    result = {
        "experiment_name": job["experiment_name"],
        "replicate": job["replicate"],
        "output_dir": job["output_dir"],
        "label": label,
        "status": "unknown",
        "duration_seconds": 0,
        "error": None,
        "results_json": None,
    }

    try:
        proc = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True,
            timeout=EXPERIMENT_TIMEOUT,
        )
        duration = time.time() - start_time
        result["duration_seconds"] = round(duration, 1)

        if proc.returncode == 0:
            result["status"] = "success"
        else:
            result["status"] = "failed"
            stderr = proc.stderr if not verbose else ""
            result["error"] = (
                stderr.strip()[-500:] if stderr else f"exit code {proc.returncode}"
            )
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["duration_seconds"] = EXPERIMENT_TIMEOUT
        result["error"] = f"Exceeded {EXPERIMENT_TIMEOUT}s timeout"
    except Exception as e:
        result["status"] = "failed"
        result["duration_seconds"] = round(time.time() - start_time, 1)
        result["error"] = str(e)

    # Try to read the results JSON if it exists
    result["results_json"] = _find_results_json(job["output_dir"])
    return result


def _find_results_json(output_dir):
    """Find and load results_*.json from an output directory."""
    out = Path(output_dir)
    if not out.exists():
        return None
    for f in sorted(out.glob("results_*.json"), reverse=True):
        try:
            with open(f) as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            continue
    return None


# ---------------------------------------------------------------------------
# Batch execution
# ---------------------------------------------------------------------------


def run_batch(jobs, workers=1, delay=1.0, api_key=None, dry_run=False, verbose=False):
    """Run all jobs with a ThreadPoolExecutor, returning results list."""
    results = []
    total = len(jobs)

    if workers == 1:
        # Sequential — simpler output
        for i, job in enumerate(jobs, 1):
            label = f"{job['experiment_name']}/rep_{job['replicate']}"
            print(f"  [{i}/{total}] STARTED  {label}")
            r = run_single_experiment(job, api_key, dry_run, verbose)
            status_icon = "DONE" if r["status"] == "success" else r["status"].upper()
            print(f"  [{i}/{total}] {status_icon:8s} {label} ({r['duration_seconds']}s)")
            results.append(r)
            if i < total:
                time.sleep(delay)
        return results

    # Parallel execution with staggered launches
    futures = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        try:
            for i, job in enumerate(jobs):
                label = f"{job['experiment_name']}/rep_{job['replicate']}"
                future = pool.submit(
                    run_single_experiment, job, api_key, dry_run, verbose
                )
                futures[future] = (i + 1, label)
                print(f"  [{i + 1}/{total}] STARTED  {label}")
                if i < len(jobs) - 1:
                    time.sleep(delay)

            for future in as_completed(futures):
                idx, label = futures[future]
                r = future.result()
                status_icon = (
                    "DONE" if r["status"] == "success" else r["status"].upper()
                )
                print(
                    f"  [{idx}/{total}] {status_icon:8s} {label} ({r['duration_seconds']}s)"
                )
                results.append(r)
        except KeyboardInterrupt:
            print("\n  Interrupted! Collecting completed results...")
            pool.shutdown(wait=False, cancel_futures=True)
            for future in futures:
                if future.done() and not future.cancelled():
                    results.append(future.result())

    return results


# ---------------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------------


def generate_batch_summary(results):
    """Aggregate results by experiment into a summary dict."""
    by_experiment = {}
    for r in results:
        name = r["experiment_name"]
        by_experiment.setdefault(name, []).append(r)

    summary = {"generated_at": datetime.now().isoformat(), "experiments": {}}

    for name, runs in by_experiment.items():
        coop_rates = []
        coop_ewan_rates = []
        api_calls = []
        total_rounds = []
        statuses = {"success": 0, "failed": 0, "timeout": 0}

        for r in runs:
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1
            rj = r.get("results_json")
            if rj:
                if "cooperation_rate" in rj:
                    coop_rates.append(rj["cooperation_rate"])
                if "coop_ewan" in rj:
                    coop_ewan_rates.append(rj["coop_ewan"])
                if "total_api_calls" in rj:
                    api_calls.append(rj["total_api_calls"])
                if "total_rounds" in rj:
                    total_rounds.append(rj["total_rounds"])

        exp_summary = {
            "replicates": len(runs),
            "statuses": statuses,
            "cooperation_rate": _agg_stats(coop_rates),
            "coop_ewan": _agg_stats(coop_ewan_rates),
            "total_api_calls": _agg_stats(api_calls),
            "total_rounds": _agg_stats(total_rounds),
            "runs": [
                {
                    "replicate": r["replicate"],
                    "status": r["status"],
                    "duration_seconds": r["duration_seconds"],
                    "error": r["error"],
                    "cooperation_rate": (
                        r["results_json"].get("cooperation_rate")
                        if r.get("results_json")
                        else None
                    ),
                    "coop_ewan": (
                        r["results_json"].get("coop_ewan")
                        if r.get("results_json")
                        else None
                    ),
                    "total_api_calls": (
                        r["results_json"].get("total_api_calls")
                        if r.get("results_json")
                        else None
                    ),
                    "total_rounds": (
                        r["results_json"].get("total_rounds")
                        if r.get("results_json")
                        else None
                    ),
                    "output_dir": r["output_dir"],
                }
                for r in runs
            ],
        }
        summary["experiments"][name] = exp_summary

    return summary


def _agg_stats(values):
    """Return mean/min/max/values dict, or None if no data."""
    if not values:
        return None
    return {
        "mean": round(mean(values), 4),
        "min": min(values),
        "max": max(values),
        "values": values,
    }


# ---------------------------------------------------------------------------
# Terminal output helpers
# ---------------------------------------------------------------------------


def print_plan(experiments, jobs, workers, dry_run):
    """Print the execution plan before starting."""
    total_replicates = sum(e["replicates"] for e in experiments)
    print(f"\n{'=' * 60}")
    print(f"  Batch Runner — {len(experiments)} experiment(s), "
          f"{total_replicates} total run(s)")
    if dry_run:
        print("  Mode: DRY RUN (no API calls)")
    print(f"  Workers: {workers}")
    print(f"{'=' * 60}")
    for exp in experiments:
        print(f"  {exp['experiment_name']:20s}  "
              f"agents={exp['agents_csv']:30s}  "
              f"config={exp['experiment_csv']:30s}  "
              f"reps={exp['replicates']}")
    print(f"{'=' * 60}\n")


def print_summary_table(summary):
    """Print a comparison table of results across experiments."""
    print(f"\n{'=' * 85}")
    print(f"  {'Experiment':<20s} {'Reps':>5s} {'OK':>4s} {'Fail':>5s} "
          f"{'Coop Rate':>12s} {'Coop (Ewan)':>13s} {'API Calls':>12s}")
    print(f"  {'-' * 77}")
    for name, exp in summary["experiments"].items():
        ok = exp["statuses"].get("success", 0)
        fail = exp["statuses"].get("failed", 0) + exp["statuses"].get("timeout", 0)
        coop = exp["cooperation_rate"]
        coop_ewan = exp.get("coop_ewan")
        api = exp["total_api_calls"]
        coop_str = f"{coop['mean']:.2%}" if coop else "n/a"
        coop_ewan_str = f"{coop_ewan['mean']:.2%}" if coop_ewan else "n/a"
        api_str = f"{api['mean']:.0f}" if api else "n/a"
        print(f"  {name:<20s} {exp['replicates']:>5d} {ok:>4d} {fail:>5d} "
              f"{coop_str:>12s} {coop_ewan_str:>13s} {api_str:>12s}")
    print(f"{'=' * 85}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Run batches of LLM game theory experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python batch_runner.py --batch example_batch_config.csv --output results/ --dry-run
  python batch_runner.py --batch example_batch_config.csv --output results/ --workers 3
        """,
    )
    parser.add_argument(
        "--batch", required=True, help="Path to batch config CSV"
    )
    parser.add_argument(
        "--output", default="results", help="Base output directory (default: results)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Max parallel experiments (default: 1)",
    )
    parser.add_argument(
        "--api-key", help="OpenAI API key (passed through to each experiment)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Pass --dry-run to each experiment",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show subprocess output in real time",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds between job launches (default: 1.0)",
    )

    args = parser.parse_args()

    if args.workers < 1:
        sys.exit("Error: --workers must be at least 1")

    # Load and validate
    experiments = load_batch_config(args.batch)
    jobs = expand_jobs(experiments, args.output)

    # Print plan
    print_plan(experiments, jobs, args.workers, args.dry_run)

    # Create base output directory
    Path(args.output).mkdir(parents=True, exist_ok=True)

    # Run
    print("Running experiments...\n")
    start = time.time()
    results = run_batch(
        jobs,
        workers=args.workers,
        delay=args.delay,
        api_key=args.api_key,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    elapsed = round(time.time() - start, 1)

    # Generate and save summary
    summary = generate_batch_summary(results)
    summary["total_duration_seconds"] = elapsed

    summary_path = Path(args.output) / "batch_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nBatch summary saved to: {summary_path}")

    # Print results table
    print_summary_table(summary)

    total = len(jobs)
    succeeded = sum(1 for r in results if r["status"] == "success")
    print(f"Completed {succeeded}/{total} runs in {elapsed}s")

    if succeeded < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
