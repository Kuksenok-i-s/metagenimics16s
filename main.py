import logging
from src import Config, DataHandler, ExecutionHandler
from qiime2 import Artifact, Metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MainWorkflow")


def main():

    config = Config("dummy_config.yml").get_config()

    data_handler = DataHandler(config)
    fmt = data_handler.validate()

    seqs = Artifact.load("emp-single-end-sequences.qza")
    metadata = Metadata.load("sample-metadata.tsv")
    classifier = Artifact.load("gg-13-8-99-515-806-nb-classifier.qza")

    computation_handler = ExecutionHandler(seqs, metadata, classifier)
    results = computation_handler.run_workflow()

    print(results)

if __name__ == "__main__":
    main()
