import sys
import logging
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wrappers.SchemaRegistryWrapper import SchemaRegistryAdmin
import yaml

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("schema-verify")

def load_config():
    config_path = Path(__file__).parent.parent / "config" / "pipeline_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
    

def load_schema(schema_name: str) -> str:

    schema_path = Path(__file__).parent / f"{schema_name}.avsc"

    try:
        with open(schema_path, 'r') as f:
            schema_str = f.read()
            json.loads(schema_str)
            logger.info(f"Schema loaded and validated: {schema_name}")
            return schema_str
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in schema file: {e}")
        sys.exit(1)


def verify_schema_registry():

    config = load_config()

    schema_admin = SchemaRegistryAdmin(url=config["kafka"]["schema_registry_url"])

    schema_str = load_schema('purchase_event')

    topic_name = config['kafka']['topics']['purchases']
    subject_name = f"{topic_name}-value"

    registration_info = schema_admin.register_avro(subject_name, schema_str)

    if registration_info:
        schema_id = registration_info.get('id')
        logger.info(f"Schema registered successfully with ID: {schema_id}")

        retrieved_schema = schema_admin.get_latest(subject_name)
        if retrieved_schema:
            version = retrieved_schema.get('version')
            logger.info(f"Schema registration successful, version = {version}")
        else:
            logger.error(f"Failed to retrieve registered schema")
            return False
    else:
        logger.error("Schema registration failed")
        return False
    
    logger.info("All registered subjects in Schema Registry: \n")
    subjects = schema_admin.list_subjects()
    if subjects:
        for sub in subjects:
            logger.info(f" - {sub}")
    else:
        logger.info("No subjects found")

    return True


if __name__ == "__main__":
    try:
        if verify_schema_registry():
            logger.info("Schema registry verification complete")
        else:
            logger.error("Schema registry verification failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Verification failed with an unexpected error: {e}")
        sys.exit(1)