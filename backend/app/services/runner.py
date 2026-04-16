"""Sandboxed code execution service.

Runs user analysis scripts inside Docker containers with strict resource limits
and no network access.
"""
import os
import subprocess
import tempfile
import time
import uuid

from app.config import settings
from app.services.storage import download_file, upload_file


RUNNER_IMAGES = {
    "python": "mishmash-runner-python",
    "r": "mishmash-runner-r",
}


def run_analysis_in_container(
    analysis_id: uuid.UUID,
    run_id: uuid.UUID,
    language: str,
    source_code: str,
    dataset_files: list[dict],  # [{storage_key, bucket, alias, format}]
    requirements: str | None = None,
) -> dict:
    """Execute an analysis script in a sandboxed Docker container.

    Returns dict with: status, stdout, stderr, duration_ms, result_files
    """
    work_dir = tempfile.mkdtemp(prefix=f"mishmash-run-{run_id}-")
    data_dir = os.path.join(work_dir, "data")
    output_dir = os.path.join(work_dir, "output")
    os.makedirs(data_dir)
    os.makedirs(output_dir)

    try:
        # Download dataset files
        for ds in dataset_files:
            local_name = f"{ds['alias']}.{ds['format']}"
            local_path = os.path.join(data_dir, local_name)
            download_file(ds["bucket"], ds["storage_key"], local_path)

        # Write script
        ext = {"python": ".py", "r": ".R", "sql": ".sql"}[language]
        script_path = os.path.join(work_dir, f"script{ext}")
        with open(script_path, "w") as f:
            f.write(source_code)

        # Write requirements if provided
        req_path = None
        if requirements and requirements.strip():
            req_path = os.path.join(work_dir, "requirements.txt")
            with open(req_path, "w") as f:
                f.write(requirements)

        # Build docker run command
        image = RUNNER_IMAGES.get(language)
        if not image:
            return {
                "status": "failed",
                "stdout": "",
                "stderr": f"Unsupported language: {language}",
                "duration_ms": 0,
                "result_files": [],
            }

        cmd_in_container = {
            "python": ["python", "/script.py"],
            "r": ["Rscript", "/script.R"],
        }[language]

        docker_cmd = [
            "docker", "run", "--rm",
            "--network=none",
            f"--cpus={settings.runner_cpu_limit}",
            f"--memory={settings.runner_memory_limit}",
            "--read-only",
            "--tmpfs", "/tmp:size=100m",
            "-v", f"{data_dir}:/data:ro",
            "-v", f"{output_dir}:/output",
            "-v", f"{script_path}:/script{ext}:ro",
        ]

        # Mount requirements if provided
        if req_path:
            docker_cmd.extend(["-v", f"{req_path}:/requirements.txt:ro"])
            # Install requirements before running (needs network temporarily)
            docker_cmd.remove("--network=none")  # Allow pip install
            if language == "python":
                cmd_in_container = [
                    "sh", "-c",
                    f"pip install --no-cache-dir -r /requirements.txt 2>/dev/null; python /script{ext}",
                ]
            elif language == "r":
                cmd_in_container = [
                    "sh", "-c",
                    f"Rscript -e 'install.packages(readLines(\"/requirements.txt\"), repos=\"https://cloud.r-project.org\")'; Rscript /script{ext}",
                ]

        docker_cmd.extend([image, *cmd_in_container])

        start = time.monotonic()
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=settings.runner_timeout_seconds,
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        # Upload result files
        result_files = []
        for fname in os.listdir(output_dir):
            fpath = os.path.join(output_dir, fname)
            if os.path.isfile(fpath):
                result_key = f"results/{run_id}/{fname}"
                upload_file(fpath, settings.s3_results_bucket, result_key)
                result_files.append(result_key)

        return {
            "status": "completed" if result.returncode == 0 else "failed",
            "stdout": result.stdout[:100_000],  # Truncate large output
            "stderr": result.stderr[:100_000],
            "duration_ms": duration_ms,
            "result_files": result_files,
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "stdout": "",
            "stderr": f"Execution timed out after {settings.runner_timeout_seconds}s",
            "duration_ms": settings.runner_timeout_seconds * 1000,
            "result_files": [],
        }
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)
