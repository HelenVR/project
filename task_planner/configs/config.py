from pydantic import BaseModel
from loguru import logger
import ujson
import yaml
import os


class DB(BaseModel):
    host: str
    port: int = 5432
    db_name: str = "tasks"
    user: str = "luna"
    password: str = "luna"


class Config(BaseModel):
    db: DB


def load_config(config_file: str = None):
    if not config_file:
        config_file = os.getenv('CONFIG_FILE', 'config.yaml')
    with open(config_file, "r") as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
    logger.info('Config is loaded')
    return Config.model_validate_json(ujson.dumps(config))