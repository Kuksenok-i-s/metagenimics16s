from src.config import Config
from src.data_handler import DataHandler
config = Config("dummy_config.yml")

dh = DataHandler(config)
dh.run()