import logging

from src import Config, DataHandler, ExecutionHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MainWorkflow")


def main():
    action = "qiime2-16s-pipeline"
    config = Config("dummy_config.yml").get_config()

    data_handler = DataHandler(config, action=action)
    computation_handler = ExecutionHandler(config, action=action)
    results = computation_handler.run_workflow()

    print(results)


if __name__ == "__main__":
    main()
