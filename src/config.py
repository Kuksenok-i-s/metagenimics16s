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
            # Define the actions schema
            actions_schema = schema.Schema(
                {
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
            )

            # Define shared schemas for reuse
            shared_denoise_params = {
                "trim_left": int,
                "trim_right": int,
                "trunc_len": int,
                "max_ee": float,
                "trunc_q": int,
            }

            shared_alpha_metrics = {
                "faith_pd": bool,
                "shannon": bool,
                "observed_features": bool,
                "evenness": bool,
            }

            shared_beta_metrics = {
                "unweighted_unifrac": bool,
                "weighted_unifrac": bool,
                "jaccard": bool,
                "bray_curtis": bool,
            }

            # Define the qiime_params schema
            qiime_params_schema = schema.Schema(
                {
                    "validation_params": {
                        "show_metadata": bool,
                    },
                    "demux_params": {
                        "run_demux": bool,
                        "params": {
                            "demux_method": str,
                            "demux_params": {
                                "demux_seq": str,
                                "demux_qual": str,
                                "demux_barcode": str,
                                "demux_trunc_len": int,
                                "demux_max_ee": float,
                                "demux_trunc_q": int,
                            },
                        },
                    },
                    "denoise_params": {
                        "run_denoise": bool,
                        "params": shared_denoise_params,
                    },
                    "deblur_params": {
                        "run_deblur": bool,
                        "deblur_params": {
                            "trim_length": int,
                            "min_reads": int,
                            "min_size": int,
                        },
                    },
                    "dada2_params": {
                        "run_dada2": bool,
                        "params": {**shared_denoise_params, "n_threads": int},
                    },
                    "phylogeny_params": {
                        "run_phylogeny": bool,
                        "params": {
                            "mafft_params": {"n_threads": int},
                            "mask_params": {"min_conservation": float},
                            "fasttree_params": {"n_threads": int, "gtr": bool},
                        },
                    },
                    "diversity_params": {
                        "run_diversity": bool,
                        "params": {
                            "sampling_depth": int,
                            "alpha_metrics": shared_alpha_metrics,
                            "beta_metrics": shared_beta_metrics,
                            "beta_group_significance": {
                                "permutations": int,
                                "pairwise": bool,
                            },
                        },
                    },
                    "alpha_rarefaction_params": {
                        "run_alpha_rarefaction": bool,
                        "params": {
                            "max_depth": int,
                            "min_depth": int,
                            "steps": int,
                            "iterations": int,
                        },
                    },
                }
            )

            # Combine the schemas
            config_schema = schema.Schema(
                {
                    schema.Optional("actions"): actions_schema,
                    schema.Optional("qiime_params"): qiime_params_schema,
                }
            )

            return config_schema.validate(self.__unmarshall_config())
        except schema.SchemaError as e:
            raise ValueError(f"Invalid configuration: {e}")

    def get_config(self):
        return self.__validate_config()
