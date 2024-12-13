import asyncio
import logging
import requests

from tqdm import tqdm
from pathlib import Path

from qiime2 import Metadata, Artifact
from q2_types.multiplexed_sequences._formats import EMPSingleEndDirFmt
from q2_types.per_sample_sequences import FastqGzFormat

logger = logging.getLogger("DataHandler")


class Downloader:
    def __init__(self, config):
        self.config = config

    @staticmethod
    async def download_file(url: str, path: Path) -> None:
        if path.exists():
            logger.info(f'File {path} already exists')
            return

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
        base_urls = data["base_urls"]
        downloads = [
            (base_urls["ngs"] + data["barcodes"], Path(data["data_source"]) / data["barcodes"]),
            (base_urls["ngs"] + data["sequences"], Path(data["data_source"]) / data["sequences"]),
            (base_urls["ngs"] + data["metadata"], Path(data["data_source"]) / data["metadata"]),
            (base_urls["classifier"] + data["classifier"], Path(data["data_source"]) / data["classifier"])
        ]

        await asyncio.gather(*[self.download_file(url, path) for url, path in downloads])
        return [path for _, path in downloads]


class DataHandler:
    def __init__(self, config, action: str):
        self.action = action
        self.config = config
        self.downloader = Downloader(config)
        self.validate()
        self.import_sequences()

    def validate(self) -> None:
        fmt = EMPSingleEndDirFmt(mode="w")
        downloads = asyncio.run(self.downloader.download_data(self.action))
        fmt.barcodes.write_data(str(downloads[0]), FastqGzFormat)  # barcodes
        fmt.sequences.write_data(str(downloads[1]), FastqGzFormat)  # sequences
        Metadata.load(downloads[2])  # metadata
        Path(downloads[3]).resolve(strict=True)  # classifier
        fmt.validate()

    def import_sequences(self) -> None:
        data = self.config["actions"][self.action]["data"]
        out_path = Path(data["data_source"]) / data["qza_sequences"]
        if out_path.exists():
            logger.info(f'File {out_path} already exists')
            return

        artifact = Artifact.import_data(
            type="EMPSingleEndSequences",
            view=Path(data["data_source"]) / data["sequences"].split('/')[-2]
        )
        artifact.save(out_path)
