"""Proof-of-work verification for locally-run computations.

The system allows users to run analyses on their own machines and submit
results with cryptographic proof that the computation was actually performed.

How it works:
1. User requests a "computation challenge" for an analysis + dataset combo
2. Server returns a challenge containing:
   - analysis source code hash
   - dataset content hashes
   - a random nonce seed
   - difficulty target
3. User runs the analysis locally using the mishmash CLI
4. CLI computes: SHA-256(source_hash | dataset_hashes | output_hash | nonce)
   and finds a nonce where the hash meets the difficulty target
5. User submits: output files, stdout/stderr, the nonce, environment info
6. Server verifies the proof and records the result

This doesn't prevent someone from fabricating results, but it proves they
did computational work proportional to the difficulty, and ties the result
to specific inputs. Combined with the environment hash (Python version,
package versions, OS), it provides a reasonable chain of evidence.
"""
import hashlib
import json
import uuid


def compute_source_hash(source_code: str) -> str:
    """Hash the analysis source code."""
    return hashlib.sha256(source_code.encode("utf-8")).hexdigest()


def compute_data_hash(data: bytes) -> str:
    """Hash dataset content."""
    return hashlib.sha256(data).hexdigest()


def compute_output_hash(outputs: dict[str, bytes]) -> str:
    """Hash all output files in deterministic order."""
    h = hashlib.sha256()
    for key in sorted(outputs.keys()):
        h.update(key.encode("utf-8"))
        h.update(outputs[key])
    return h.hexdigest()


def compute_environment_hash(env_info: dict) -> str:
    """Hash the execution environment info."""
    canonical = json.dumps(env_info, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_challenge(
    analysis_id: uuid.UUID,
    source_hash: str,
    dataset_hashes: list[str],
    difficulty: int = 4,
) -> dict:
    """Create a computation challenge.

    difficulty: number of leading zero hex digits required in the proof hash.
    4 = ~65k iterations average, takes a few seconds on modern hardware.
    """
    nonce_seed = uuid.uuid4().hex
    return {
        "analysis_id": str(analysis_id),
        "source_hash": source_hash,
        "dataset_hashes": sorted(dataset_hashes),
        "nonce_seed": nonce_seed,
        "difficulty": difficulty,
    }


def compute_proof(
    source_hash: str,
    dataset_hashes: list[str],
    output_hash: str,
    nonce_seed: str,
    difficulty: int = 4,
) -> tuple[str, str]:
    """Find a nonce that satisfies the difficulty target.

    Returns (proof_hash, nonce).
    """
    target_prefix = "0" * difficulty
    base = f"{source_hash}|{'|'.join(sorted(dataset_hashes))}|{output_hash}|{nonce_seed}|"

    nonce = 0
    while True:
        candidate = f"{base}{nonce}"
        h = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        if h.startswith(target_prefix):
            return h, str(nonce)
        nonce += 1


def verify_proof(
    source_hash: str,
    dataset_hashes: list[str],
    output_hash: str,
    nonce_seed: str,
    nonce: str,
    proof_hash: str,
    difficulty: int = 4,
) -> bool:
    """Verify a proof-of-work submission."""
    target_prefix = "0" * difficulty
    base = f"{source_hash}|{'|'.join(sorted(dataset_hashes))}|{output_hash}|{nonce_seed}|{nonce}"
    h = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return h == proof_hash and h.startswith(target_prefix)
