"""Mishmash CLI — run analyses locally with proof-of-work verification."""
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time

import click
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

console = Console()

DEFAULT_API = "http://localhost:8000"


def get_config_path():
    return os.path.expanduser("~/.mishmash/config.json")


def load_config():
    path = get_config_path()
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_config(config):
    path = get_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)


def get_client():
    config = load_config()
    api_url = config.get("api_url", DEFAULT_API)
    token = config.get("token")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.Client(base_url=api_url, headers=headers, timeout=30.0)


@click.group()
def cli():
    """Mishmash — collaborative data analysis from your terminal."""
    pass


@cli.command()
@click.option("--api-url", default=DEFAULT_API, help="API base URL")
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
def login(api_url, email, password):
    """Authenticate with a Mishmash server."""
    with httpx.Client(base_url=api_url, timeout=10) as client:
        resp = client.post("/api/auth/login", json={"email": email, "password": password})
        if resp.status_code != 200:
            console.print(f"[red]Login failed:[/red] {resp.json().get('detail', 'Unknown error')}")
            return

    data = resp.json()
    config = load_config()
    config["api_url"] = api_url
    config["token"] = data["access_token"]
    config["user"] = data["user"]
    save_config(config)
    console.print(f"[green]Logged in as {data['user']['name']}[/green]")


@cli.command()
@click.option("--email", prompt=True)
@click.option("--username", prompt=True)
@click.option("--name", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--api-url", default=DEFAULT_API)
def register(email, username, name, password, api_url):
    """Create a new Mishmash account."""
    with httpx.Client(base_url=api_url, timeout=10) as client:
        resp = client.post("/api/auth/register", json={
            "email": email, "username": username, "name": name, "password": password,
        })
        if resp.status_code != 201:
            console.print(f"[red]Registration failed:[/red] {resp.json().get('detail', 'Unknown error')}")
            return

    data = resp.json()
    config = load_config()
    config["api_url"] = api_url
    config["token"] = data["access_token"]
    config["user"] = data["user"]
    save_config(config)
    console.print(f"[green]Account created! Logged in as {data['user']['name']}[/green]")


@cli.command()
def whoami():
    """Show current logged-in user."""
    config = load_config()
    if "user" not in config:
        console.print("[yellow]Not logged in. Run 'mishmash login' first.[/yellow]")
        return
    u = config["user"]
    console.print(f"Logged in as [bold]{u['name']}[/bold] ({u['email']})")


@cli.command()
@click.argument("analysis_id")
def run(analysis_id):
    """Run an analysis locally with proof-of-work verification."""
    client = get_client()

    # 1. Fetch analysis
    console.print(f"[bold]Fetching analysis {analysis_id}...[/bold]")
    resp = client.get(f"/api/analyses/{analysis_id}")
    if resp.status_code != 200:
        console.print(f"[red]Failed to fetch analysis:[/red] {resp.text}")
        return
    analysis = resp.json()

    console.print(Panel(
        f"[bold]{analysis['title']}[/bold]\n"
        f"Language: {analysis['language']}\n"
        f"Datasets: {len(analysis['datasets'])}",
        title="Analysis",
    ))

    # 2. Get challenge
    console.print("Requesting computation challenge...")
    resp = client.post(f"/api/analyses/{analysis_id}/challenge")
    if resp.status_code != 200:
        console.print(f"[red]Failed to get challenge:[/red] {resp.text}")
        return
    challenge = resp.json()

    # 3. Download datasets
    work_dir = tempfile.mkdtemp(prefix="mishmash-local-")
    data_dir = os.path.join(work_dir, "data")
    output_dir = os.path.join(work_dir, "output")
    os.makedirs(data_dir)
    os.makedirs(output_dir)

    console.print("Downloading datasets...")
    for ds_link in analysis["datasets"]:
        ds_id = ds_link["dataset_id"]
        alias = ds_link["alias"] or ds_id[:8]

        resp = client.get(f"/api/datasets/{ds_id}/download")
        if resp.status_code != 200:
            console.print(f"[red]Failed to get download URL for {ds_id}[/red]")
            continue

        download_url = resp.json()["download_url"]
        # Fetch the actual file
        file_resp = httpx.get(download_url, follow_redirects=True)
        # Detect format from dataset info
        ds_resp = client.get(f"/api/datasets/{ds_id}")
        ds_info = ds_resp.json()
        ext = ds_info.get("format", "csv")

        local_path = os.path.join(data_dir, f"{alias}.{ext}")
        with open(local_path, "wb") as f:
            f.write(file_resp.content)
        console.print(f"  Downloaded {alias}.{ext} ({len(file_resp.content)} bytes)")

    # 4. Write and run script
    ext_map = {"python": ".py", "r": ".R", "sql": ".sql"}
    script_ext = ext_map.get(analysis["language"], ".py")
    script_path = os.path.join(work_dir, f"script{script_ext}")
    with open(script_path, "w") as f:
        f.write(analysis["source_code"])

    cmd_map = {
        "python": [sys.executable, script_path],
        "r": ["Rscript", script_path],
    }
    cmd = cmd_map.get(analysis["language"])
    if not cmd:
        console.print(f"[red]Unsupported language: {analysis['language']}[/red]")
        return

    env = os.environ.copy()
    env["MISHMASH_DATA_DIR"] = data_dir
    env["MISHMASH_OUTPUT_DIR"] = output_dir

    console.print(f"\n[bold]Running {analysis['language']} script...[/bold]\n")
    start = time.monotonic()
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=work_dir, env=env, timeout=300,
    )
    duration_ms = int((time.monotonic() - start) * 1000)

    if result.stdout:
        console.print(Panel(result.stdout[:5000], title="stdout"))
    if result.stderr:
        console.print(Panel(result.stderr[:5000], title="stderr", style="red"))
    console.print(f"Exit code: {result.returncode}, Duration: {duration_ms}ms")

    # 5. Compute output hash
    outputs = {}
    for fname in sorted(os.listdir(output_dir)):
        fpath = os.path.join(output_dir, fname)
        if os.path.isfile(fpath):
            with open(fpath, "rb") as f:
                outputs[fname] = f.read()

    output_hash = _compute_output_hash(outputs)

    # 6. Compute proof of work
    console.print("\n[bold]Computing proof of work...[/bold]")
    source_hash = challenge["source_hash"]
    dataset_hashes = challenge["dataset_hashes"]
    nonce_seed = challenge["nonce_seed"]
    difficulty = challenge["difficulty"]

    proof_hash, nonce = _compute_proof(
        source_hash, dataset_hashes, output_hash, nonce_seed, difficulty,
    )
    console.print(f"[green]Proof found![/green] Hash: {proof_hash[:16]}... Nonce: {nonce}")

    # 7. Gather environment info
    env_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
    try:
        import pandas
        env_info["pandas_version"] = pandas.__version__
    except ImportError:
        pass
    try:
        import numpy
        env_info["numpy_version"] = numpy.__version__
    except ImportError:
        pass

    # 8. Submit proof
    console.print("Submitting proof to server...")
    resp = client.post(f"/api/analyses/{analysis_id}/submit-proof", json={
        "proof_hash": proof_hash,
        "nonce": nonce,
        "output_hash": output_hash,
        "environment_info": env_info,
        "stdout": result.stdout[:50000] if result.stdout else None,
        "stderr": result.stderr[:50000] if result.stderr else None,
        "duration_ms": duration_ms,
    })

    if resp.status_code == 201:
        run_data = resp.json()
        console.print(f"\n[green bold]Success![/green bold] Run recorded: {run_data['id']}")
        console.print(f"  Status: {run_data['status']}")
        console.print(f"  Proof verified: {run_data['pow_verified']}")
    else:
        console.print(f"[red]Submission failed:[/red] {resp.text}")

    # Cleanup
    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--name", required=True, help="Dataset name")
@click.option("--description", default=None)
@click.option("--tags", default="", help="Comma-separated tags")
def upload(file_path, name, description, tags):
    """Upload a dataset file."""
    client = get_client()

    ext = os.path.splitext(file_path)[1].lower()
    format_map = {".csv": "csv", ".json": "json", ".parquet": "parquet"}
    fmt = format_map.get(ext)
    if not fmt:
        console.print(f"[red]Unsupported file format: {ext}[/red]")
        return

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    # Create dataset
    resp = client.post("/api/datasets", json={
        "name": name,
        "description": description,
        "tags": tag_list,
        "format": fmt,
    })
    if resp.status_code != 201:
        console.print(f"[red]Failed to create dataset:[/red] {resp.text}")
        return
    dataset = resp.json()
    console.print(f"Created dataset: {dataset['slug']}")

    # Get upload URL
    filename = os.path.basename(file_path)
    resp = client.post(f"/api/datasets/{dataset['id']}/upload?filename={filename}")
    if resp.status_code != 200:
        console.print(f"[red]Failed to get upload URL:[/red] {resp.text}")
        return
    upload_info = resp.json()

    # Upload file
    with open(file_path, "rb") as f:
        file_data = f.read()

    console.print(f"Uploading {filename} ({len(file_data)} bytes)...")
    upload_resp = httpx.put(
        upload_info["upload_url"],
        content=file_data,
        headers={"Content-Type": "application/octet-stream"},
    )
    if upload_resp.status_code not in (200, 204):
        console.print(f"[red]Upload failed:[/red] {upload_resp.status_code}")
        return

    # Complete upload
    resp = client.post(f"/api/datasets/{dataset['id']}/upload/complete", json={
        "dataset_id": dataset["id"],
        "storage_key": upload_info["storage_key"],
        "file_size_bytes": len(file_data),
    })
    if resp.status_code == 201:
        console.print(f"[green]Dataset uploaded successfully![/green]")
        console.print(f"  URL: {client.base_url}/datasets/{dataset['slug']}")
    else:
        console.print(f"[red]Failed to complete upload:[/red] {resp.text}")


@cli.command("list-datasets")
@click.option("--query", "-q", default=None)
@click.option("--limit", default=20)
def list_datasets(query, limit):
    """List available datasets."""
    client = get_client()
    params = {"page_size": limit}
    if query:
        params["q"] = query

    resp = client.get("/api/datasets", params=params)
    if resp.status_code != 200:
        console.print(f"[red]Failed:[/red] {resp.text}")
        return

    data = resp.json()
    console.print(f"[bold]Datasets ({data['total']} total)[/bold]\n")
    for ds in data["items"]:
        stars = f"[yellow]*{ds['star_count']}[/yellow]" if ds.get("star_count") else ""
        rows = f"{ds['row_count']:,} rows" if ds.get("row_count") else "no data"
        console.print(f"  {ds['slug']} — {ds['name']} ({rows}) {stars}")


@cli.command("list-analyses")
@click.option("--query", "-q", default=None)
def list_analyses(query):
    """List available analyses."""
    client = get_client()
    params = {}
    if query:
        params["q"] = query

    resp = client.get("/api/analyses", params=params)
    if resp.status_code != 200:
        console.print(f"[red]Failed:[/red] {resp.text}")
        return

    data = resp.json()
    console.print(f"[bold]Analyses ({data['total']} total)[/bold]\n")
    for a in data["items"]:
        console.print(f"  {a['id'][:8]}... — {a['title']} [{a['language']}] ({a['status']})")


def _compute_output_hash(outputs: dict[str, bytes]) -> str:
    h = hashlib.sha256()
    for key in sorted(outputs.keys()):
        h.update(key.encode("utf-8"))
        h.update(outputs[key])
    return h.hexdigest()


def _compute_proof(
    source_hash: str, dataset_hashes: list[str], output_hash: str,
    nonce_seed: str, difficulty: int,
) -> tuple[str, str]:
    target_prefix = "0" * difficulty
    base = f"{source_hash}|{'|'.join(sorted(dataset_hashes))}|{output_hash}|{nonce_seed}|"
    nonce = 0
    while True:
        candidate = f"{base}{nonce}"
        h = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        if h.startswith(target_prefix):
            return h, str(nonce)
        nonce += 1
        if nonce % 100000 == 0:
            console.print(f"  ...tried {nonce:,} nonces", style="dim")


if __name__ == "__main__":
    cli()
