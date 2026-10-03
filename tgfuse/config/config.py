import os
import tempfile
import configparser
from pathlib import Path

class Config:
    log_level: str = "INFO"
    tg_id: int = 0
    tg_hash: str = ''
    tg_token: str = ''
    chat_id: int = 0
    tg_upload_workers: int = 4
    tg_upload_buffer_parts: int = 16
    cache_dir: str = ""
    remote_name: str = 'default'
    session_name: str = 'tgfs_session'
    sync_on_mount: bool = True
    extensions: list = []

    @classmethod
    def load(cls, remote_name=None):
        cls.remote_name = remote_name or 'default'
        config_dir = Path.home() / ".config" / "tgfuse"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = config_dir / "config.ini"
        ini_values = {}
        
        if remote_name and config_path.exists():
            parser = configparser.ConfigParser()
            parser.read(config_path)
            if remote_name in parser:
                ini_values = dict(parser[remote_name])

        cls.session_name = str(config_dir / f"session_{cls.remote_name}")
        cls.cache_dir = os.path.join(tempfile.gettempdir(), f"tgfuse_cache_{cls.remote_name}")

        global_env_path = config_dir / ".env"
        dotenv_values = cls._read_dotenv(str(global_env_path))
        
        local_env_values = cls._read_dotenv(".env")
        dotenv_values.update(local_env_values)

        for key in cls.__annotations__:
            env_key = key.upper()
            val = os.getenv(env_key)
            if val is None:
                val = ini_values.get(key)
            if val is None:
                val = dotenv_values.get(env_key)

            if val is not None:
                current_value = getattr(cls, key)
                if isinstance(current_value, bool):
                    setattr(cls, key, str(val).lower() in ('true', '1', 'yes'))
                elif isinstance(current_value, int):
                    setattr(cls, key, int(val))
                elif isinstance(current_value, list):
                    ext_list = [x.strip().lower().strip('.') for x in str(val).split(",") if x.strip()]
                    setattr(cls, key, ext_list)    
                else:
                    setattr(cls, key, str(val))

    @staticmethod
    def _read_dotenv(path: str = ".env") -> dict[str, str]:
        values = {}
        try:
            with open(path, "r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key:
                        values[key] = value
        except FileNotFoundError:
            pass
        return values

Config.load()