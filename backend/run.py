import os
import sys
from pathlib import Path


def _use_project_venv() -> None:
    """Re-exec the server with the local venv when available."""
    backend_root = Path(__file__).resolve().parent
    venv_python = backend_root / "venv" / "bin" / "python"
    current_python = Path(sys.executable).absolute()

    if not venv_python.exists() or current_python == venv_python:
        return

    os.execv(str(venv_python), [str(venv_python), *sys.argv])


_use_project_venv()

import uvicorn
from src.infra.config import settings
from src.infra.logging_utils import LoggedComponent, configure_file_logging


class ServerRunner(LoggedComponent):
    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        backend_root = Path(__file__).resolve().parent
        os.chdir(backend_root)
        host = settings.app_host
        port = settings.app_port
        self.log_info(f"Starting agent server on {host}:{port}.")
        uvicorn.run("src.api.app:app", host=host, port=port, reload=True)


def run_server() -> None:
    ServerRunner().run()


if __name__ == "__main__":
    configure_file_logging(str(Path(__file__).resolve().with_name("pipeline_logs.log")))
    run_server()
