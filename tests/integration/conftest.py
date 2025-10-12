import os
import shutil
import subprocess
import uuid
import pytest
import time
import re

from . import docker_helpers


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
    # Default to runtime to match README smoke-test usage
    stage = os.environ.get("MODHOST_TEST_STAGE", "runtime").lower()
    if stage not in ("builder", "runtime", "final"):
        stage = "builder"

    # Use a stable local image tag that matches the README smoke test
    tag = os.environ.get("MODHOST_TEST_TAG", "marlise-audio:local")

    # Build the image (builder or runtime/final). Use the same Dockerfile as README.
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
def modhost_container(modhost_image_tag):
    """Start a single runtime container for the whole test session and
    yield (container_id, host_port, host_port_fb).

    This avoids repeatedly starting/stopping containers for each test and
    speeds up the test suite. The container is torn down at session end.
    """
    tag, stage = modhost_image_tag
    # We only support runtime containers for the session fixture
    if stage != "runtime":
        pytest.skip("modhost_container requires MODHOST_TEST_STAGE=runtime")

    # Use centralized helper to start and wait for runtime container readiness
    container_id, host_port, host_port_fb = docker_helpers.start_runtime_container(tag)
    try:
        yield container_id, host_port, host_port_fb
    finally:
        docker_helpers.stop_container(container_id)


@pytest.fixture(scope="session")
def modhost_builder_tag(modhost_image_tag):
    """Compatibility shim that returns the builder tag when stage=builder."""
    tag, stage = modhost_image_tag
    if stage != "builder":
        pytest.skip("modhost_builder_tag fixture requires MODHOST_TEST_STAGE=builder")
    return tag
