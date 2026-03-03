from pathlib import Path

from src.api.chat_store import ChatStoreManager
from src.infra.config.config_google.storage_manager import StorageManager
from src.infra.logging_utils import LoggedComponent, configure_file_logging


backend_root = Path(__file__).resolve().parents[2]
project_root = backend_root.parent
configure_file_logging(str(backend_root / "pipeline_logs.log"))
pipeline_log_path = backend_root / "pipeline_logs.log"
frontend_dir = project_root / "frontend"
assets_dir = frontend_dir / "assets"
login_page = frontend_dir / "login.html"


class ApiAuditService(LoggedComponent):
    def __init__(self) -> None:
        super().__init__()


storage_manager = StorageManager()
chat_store_manager = ChatStoreManager(backend_root, storage_manager=storage_manager)
api_audit = ApiAuditService()
