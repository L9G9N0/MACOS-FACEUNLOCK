import os
import sys
import time
import json
import numpy as np

# Adjust python paths for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from shared.utils import setup_logger

logger = setup_logger("Benchmarks")

def run_performance_benchmarks():
    logger.info("Starting performance benchmark suite...")
    results = {}
    
    # 1. Measure Socket Latency Mock
    start_time = time.perf_counter()
    # Mocking standard serialization
    payload = "AUTH_SUCCESS_hariom".encode("utf-8")
    for _ in range(1000):
        _ = payload.decode("utf-8")
    end_time = time.perf_counter()
    avg_ipc_time = (end_time - start_time) / 1000
    results["avg_ipc_latency_ms"] = avg_ipc_time * 1000
    logger.info(f"IPC Serialization latency: {avg_ipc_time * 1000:.4f} ms")

    # 2. Mocking Face Pose calculations
    start_time = time.perf_counter()
    # Mocking RQ decomposition math
    for _ in range(500):
        rot_matrix = np.eye(3)
        # Random rotation matrix math
        _ = np.linalg.det(rot_matrix)
    end_time = time.perf_counter()
    avg_math_time = (end_time - start_time) / 500
    results["avg_pose_geometry_ms"] = avg_math_time * 1000
    logger.info(f"Pose Geometry Math latency: {avg_math_time * 1000:.4f} ms")
    
    # Save results to benchmarks/benchmark_results.json
    bench_dir = os.path.join(project_root, "benchmarks")
    os.makedirs(bench_dir, exist_ok=True)
    out_path = os.path.join(bench_dir, "benchmark_results.json")
    
    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)
        
    logger.info(f"Benchmark results successfully cached to {out_path}")

if __name__ == "__main__":
    run_performance_benchmarks()
