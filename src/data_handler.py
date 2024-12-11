import asyncio
import logging
from pathlib import Path
import requests
from tqdm import tqdm
from q2_types.multiplexed_sequences._formats import EMPSingleEndDirFmt
from q2_types.per_sample_sequences import FastqGzFormat
from qiime2 import Metadata

logger = logging.getLogger("DataHandler")


class Downloader:
    def __init__(self, config):
        self.config = config

    @staticmethod
    async def download_file(url: str, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True) as r:
            if r.status_code == 200:
                total_size = int(r.headers.get("content-length", 0))
                with open(path, "wb") as f:
                    with tqdm(total=total_size, unit="iB", unit_scale=True, desc=f"Downloading {path.name}") as pbar:
                        for chunk in r.iter_content(chunk_size=8192):
                            size = f.write(chunk)
                            pbar.update(size)
                logger.info(f"{path.name} downloaded successfully.")
            else:
                logger.error(f"Failed to download {url}.")
                raise ValueError(f"Download failed for {url}")

    async def download_data(self, action: str) -> list[Path]:
        data = self.config["actions"][action]["data"]
        base_url = data["basic_url"]
        downloads = [
            (base_url + data["barcodes"], Path(data["data_source"]) / data["barcodes"].split("/")[-1]),
            (base_url + data["sequences"], Path(data["data_source"]) / data["sequences"].split("/")[-1]),
            (base_url + data["metadata"], Path(data["data_source"]) / data["metadata"].split("/")[-1]),
        ]

        await asyncio.gather(*[self.download_file(url, path) for url, path in downloads])
        return [path for _, path in downloads]


class DataHandler:
    def __init__(self, config):
        self.config = config
        self.downloader = Downloader(config)

    def validate(self):
        fmt = EMPSingleEndDirFmt(mode="w")
        downloads = asyncio.run(self.downloader.download_data("qiime2-16s-pipeline"))
        fmt.barcodes.write_data(str(downloads[0]), FastqGzFormat)
        fmt.sequences.write_data(str(downloads[1]), FastqGzFormat)
        Metadata.load(downloads[2])
        fmt.validate()
        return fmt
