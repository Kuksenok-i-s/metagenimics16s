import yaml
from pathlib import Path
import schema


class Config:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def __unmarshall_config(self):
        return yaml.safe_load(Path(self.config_path).read_text())

    def __validate_config(self):
        try:
            return schema.Schema(
                {
                    "actions": {
                        str: {
                            "check_installation": bool,
                            "download_data": bool,
                            "check_environment": bool,
                            "run_basic_pipeline": bool,
                            "data": {
                                "data_source": str,
                                "data_path": str,
                                "data_url": str,
                                "metadata_url": str,
                                "metadata_path": str,
                            },
                        }
                    }
                }
            ).validate(self.__unmarshall_config())
        except schema.SchemaError as e:
            raise ValueError(e)

    def get_config(self):
        return self.__validate_config()
