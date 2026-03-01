import os
from pathlib import Path

import uvicorn

from src.infra.logging_utils import LoggedComponent, configure_file_logging


class ServerRunner(LoggedComponent):
    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        backend_root = Path(__file__).resolve().parent
        os.chdir(backend_root)
        host = os.getenv("APP_HOST", "127.0.0.1")
        port = int(os.getenv("APP_PORT", "8000"))
        self.log_info(f"Starting agent server on {host}:{port}.")
        uvicorn.run("src.api.app:app", host=host, port=port, reload=True)


def run_server() -> None:
    ServerRunner().run()


if __name__ == "__main__":
    configure_file_logging(str(Path(__file__).resolve().with_name("pipeline_logs.log")))
    run_server()
