from src.config import Config
from pathlib import Path
import requests
import asyncio
from  tqdm import tqdm
import logging

logger = logging.getLogger("DataHandler")


class Downloader:
    def __init__(self, conf: Config):
        self.config = conf.get_config()

    @staticmethod
    async def download_file(url: str, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True) as r:
            if r.status_code == 200:
                total_size = int(r.headers.get('content-length', 0))
                with open(path, "wb") as f:
                    with tqdm(total=total_size, unit='iB', unit_scale=True, desc=f'Downloading {path.name}') as pbar:
                        for chunk in r.iter_content(chunk_size=8192):
                            size = f.write(chunk)
                            pbar.update(size)
                logger.info("Data downloaded successfully.")
            else:
                logger.error("Data download failed.")
                raise ValueError("Data download failed.")
    async def download_data(self, action: str) -> None:
        """
        Зачем этот оверинженинг?
        Во-первых - это красиво.
        Дальше я не придумал.
        """
        data = self.config["actions"][action]["data"]
        await asyncio.gather(
            self.download_file(
                data["data_url"],
                Path(data["data_path"]),
            ),
            self.download_file(
                data["metadata_url"],
                Path(data["metadata_path"]),
            ),
        )

class DataHandler:
    def __init__(self, conf: Config):
        self.config = conf.get_config()
        self.downloader = Downloader(conf)
    
    def run(self) -> None:
        for action in self.config["actions"]:
            asyncio.run(self.downloader.download_data(action))
        else:
            logger.info("No data download required.")