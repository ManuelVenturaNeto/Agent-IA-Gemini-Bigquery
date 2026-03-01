import logging
from pathlib import Path


def configure_file_logging(log_path: str = "./pipeline_logs.log") -> None:
    root_logger = logging.getLogger()
    target_path = Path(log_path).resolve()

    for handler in root_logger.handlers:
        if not isinstance(handler, logging.FileHandler):
            continue

        base_filename = getattr(handler, "baseFilename", "")
        if base_filename and Path(base_filename).resolve() == target_path:
            if root_logger.level == logging.NOTSET or root_logger.level > logging.DEBUG:
                root_logger.setLevel(logging.DEBUG)
            return

    file_handler = logging.FileHandler(target_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s, %(message)s")
    )
    root_logger.addHandler(file_handler)

    if root_logger.level == logging.NOTSET or root_logger.level > logging.DEBUG:
        root_logger.setLevel(logging.DEBUG)


class LoggedComponent:
    def __init__(self, logger_name: str | None = None) -> None:
        self.log = logging.getLogger(logger_name or self.__class__.__name__)

    def _tracking_scope(
        self,
        user_email: str | None = None,
        chat_id: str | None = None,
        question_id: str | None = None,
    ) -> str:
        return (
            f"[FROM: {user_email or 'SYSTEM'} | "
            f"CHAT_ID: {chat_id or 'N/A'} | "
            f"QUESTION_ID: {question_id or 'N/A'}]"
        )

    def _tracking_message(
        self,
        message: str,
        user_email: str | None = None,
        chat_id: str | None = None,
        question_id: str | None = None,
    ) -> str:
        return f"{self._tracking_scope(user_email, chat_id, question_id)} - {message}"

    def log_debug(
        self,
        message: str,
        user_email: str | None = None,
        chat_id: str | None = None,
        question_id: str | None = None,
    ) -> None:
        self.log.debug(
            f"[DEBUG] {self._tracking_message(message, user_email, chat_id, question_id)}"
        )

    def log_info(
        self,
        message: str,
        user_email: str | None = None,
        chat_id: str | None = None,
        question_id: str | None = None,
    ) -> None:
        self.log.info(
            f"[INFO] {self._tracking_message(message, user_email, chat_id, question_id)}"
        )

    def log_warning(
        self,
        message: str,
        user_email: str | None = None,
        chat_id: str | None = None,
        question_id: str | None = None,
    ) -> None:
        self.log.warning(
            f"[WARNING] {self._tracking_message(message, user_email, chat_id, question_id)}"
        )

    def log_error(
        self,
        message: str,
        user_email: str | None = None,
        chat_id: str | None = None,
        question_id: str | None = None,
    ) -> None:
        self.log.error(
            f"[ERROR] {self._tracking_message(message, user_email, chat_id, question_id)}"
        )

    def log_critical(
        self,
        message: str,
        user_email: str | None = None,
        chat_id: str | None = None,
        question_id: str | None = None,
    ) -> None:
        self.log.critical(
            f"[CRITICAL] {self._tracking_message(message, user_email, chat_id, question_id)}"
        )
