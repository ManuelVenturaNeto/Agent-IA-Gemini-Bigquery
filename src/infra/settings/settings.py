import os
import logging
from dotenv import load_dotenv


class Settings:
    """
    Centralized settings — loads .env once and exposes all
    environment variables needed across the application.
    """

    def __init__(self):
        load_dotenv()
        self.log = logging.getLogger(self.__class__.__name__)

        self.GEN_IA_KEY: str = os.getenv("GEN_IA_KEY", "")
        self.PROJECT: str = os.getenv("PROJECT", "")
        self.PROJECT_SA: str = os.getenv("PROJECT_SA", "")

        self.DB_INSTANCE_NAME: str = str(os.getenv("DB_INSTANCE_NAME", ""))
        self.DB_USER: str = str(os.getenv("DB_USER", ""))
        self.DB_PASSWORD: str = str(os.getenv("DB_PASSWORD", ""))
        self.DB_NAME: str = str(os.getenv("DB_NAME", ""))

        self._validate()
        self._set_google_credentials()

    def _validate(self):
        missing = [
            name
            for name, value in {
                "GEN_IA_KEY": self.GEN_IA_KEY,
                "PROJECT": self.PROJECT,
                "PROJECT_SA": self.PROJECT_SA,
            }.items()
            if not value
        ]
        if missing:
            self.log.error(f"Missing environment variables: {', '.join(missing)}")
            raise EnvironmentError(
                f"The following environment variables are not set: {', '.join(missing)}"
            )

    def _set_google_credentials(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.PROJECT_SA
        self.log.debug("GOOGLE_APPLICATION_CREDENTIALS configured via settings.")


# Module-level singleton — import this everywhere
settings = Settings()
