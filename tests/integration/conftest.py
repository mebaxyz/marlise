import os
import shutil
import subprocess
import uuid
import pytest


def _docker_available() -> bool:
    return shutil.which("docker") is not None


@pytest.fixture(scope="session")
def modhost_image_tag():
    """Build the Docker image for the chosen stage and yield (tag, stage).

    The stage is selected by the environment variable `MODHOST_TEST_STAGE`.
    Supported values: `builder` (default) and `runtime`.
    """
    if not _docker_available():
        pytest.skip("docker is required for mod-host integration tests")

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dockerfile = os.path.join(repo_root, "docker", "audio-engine", "Dockerfile")
    stage = os.environ.get("MODHOST_TEST_STAGE", "builder").lower()
    if stage not in ("builder", "runtime", "final"):
        stage = "builder"

    tag = f"marlise-modhost-{stage}:test-{uuid.uuid4().hex[:8]}"

    if stage == "builder":
        build_cmd = [
            "docker",
            "build",
            "--target",
            "builder",
            "-f",
            dockerfile,
            "-t",
            tag,
            repo_root,
        ]
    else:
        build_cmd = [
            "docker",
            "build",
            "-f",
            dockerfile,
            "-t",
            tag,
            repo_root,
        ]

    print(f"[modhost-test] building docker image (stage={stage}) with tag: {tag}")
    subprocess.check_call(build_cmd)

    yield tag, stage

    # Teardown: attempt to remove the temporary image
    try:
        subprocess.run(["docker", "rmi", "-f", tag], check=False)
    except Exception:
        pass


@pytest.fixture(scope="session")
def modhost_builder_tag(modhost_image_tag):
    """Compatibility shim that returns the builder tag when stage=builder."""
    tag, stage = modhost_image_tag
    if stage != "builder":
        pytest.skip("modhost_builder_tag fixture requires MODHOST_TEST_STAGE=builder")
    return tag
