from pathlib import Path

from src.api.chat_store import ChatStoreManager
from src.infra.logging_utils import LoggedComponent, configure_file_logging


configure_file_logging()
project_root = Path(__file__).resolve().parents[2]
frontend_dir = project_root / "frontend"
assets_dir = frontend_dir / "assets"
login_page = frontend_dir / "login.html"


class ApiAuditService(LoggedComponent):
    def __init__(self) -> None:
        super().__init__()


chat_store_manager = ChatStoreManager(project_root)
api_audit = ApiAuditService()
