import logging
from typing import Dict, List, Optional, Union
import json

from confluent_kafka.schema_registry import SchemaRegistryClient, Schema, SchemaReference
from confluent_kafka.schema_registry.error import SchemaRegistryError

logging.basicConfig(level=logging.INFO, format = "%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class SchemaRegistryAdmin:

    def __init__(self, url: str = "http://localhost:8082") -> None:

        self.url = url
        self.client = SchemaRegistryClient({"url": url})
        logger.info(f"Schema Registry initialized at {url}")


    @staticmethod
    def build_schema(

        schema_str: str,
        schema_type: str,
        references: Optional[List[SchemaReference]] = None
    ) -> Schema:
        
        st = schema_type.upper()

        if st == "AVRO":
            try:
                json.loads(schema_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid Avro Schema: {e}")
            return Schema(schema_str, schema_type="AVRO", references= references or [])
        
        elif st in ("JSON", "JSONSCHEMA"):
            try:
                json.loads(schema_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON schema: {e}")
            return Schema(schema_str, schema_type = "JSON", references= references or [])
        elif st in ("PROTOBUF", "PROTO"):
            return Schema(schema_str, schema_type="PROTOBUF", references=references or [])

        else:
            raise ValueError(
                f"Unsupported schema type: {schema_type}. Please use AVRO, JSON or PROTOBUF"
            )


    def list_subjects(self) -> List[str]:
        try:
            subs = self.client.get_subjects()
            logger.info(f"Subjects found: {subs}")
            return subs
        except SchemaRegistryError as e:
            logger.error(f"Failed to list subjects: {e}")
            return []
        
    
    def get_versions(self, subject: str) -> List[int]:
        try:
            vers = self.client.get_versions(subject)
            logger.info(f"Versions for {subject}: {vers}")
            return vers
        except SchemaRegistryError as e:
            logger.error(f"Failed to get versions for {subject}: {e}")
            return []
        
    
    def get_latest(self, subject: str) -> Optional[Dict[str, Union[int, str]]]:
        try:
            meta = self.client.get_latest_version(subject)

            out = {

                "subject": meta.subject,
                "version": meta.version,
                "id": meta.schema_id,
                "schema_type": meta.schema.schema_type,
                "schema_str": meta.schema.schema_str

            }

            logger.info(
                f"Latest for {out['subject']} -> id={out['id']} version={out['version']} type={out['schema_type']}"
            )

            return out
        except SchemaRegistryError as e:
            logger.error(f"Failed to get latest for {subject}: {e}")
            return None
        
    
    def get_schema_by_id(self, schema_id: int) -> Optional[str]:
        try:
            schema = self.client.get_schema(schema_id)
            logger.info(f"Fetched schema id={schema_id} type={schema.schema_type}")
            return schema.schema_str
        except SchemaRegistryError as e:
            logger.error(f"Failed to fetch schema id={schema_id}: {e}")
            return None
        

    
    def register_schema(
            self,
            subject: str,
            schema_str: str,
            schema_type: str,
            *,
            references: Optional[List[SchemaReference]] = None

    ) -> Optional[Dict[str, Union[int, str]]]:
        
        try:
            schema_obj = self.build_schema(schema_str, schema_type, references)
            schema_id = self.client.register_schema(subject, schema_obj)

            registered_schema = self.client.lookup_schema(subject_name=subject, 
                                                      schema=schema_obj)
            assigned_version = registered_schema.version

            latest_meta = self.client.get_latest_version(subject)
            latest_version = latest_meta.version

            out = {"subject": subject, "id": schema_id,
                   "version": assigned_version,     
                   "latest_after_register": latest_version}

            logger.info(
                f"Registered {schema_type.upper()} for subject={subject}, id={schema_id} "
                f"assigned version={assigned_version}, latest now={latest_version}"
            )
            return out
        except SchemaRegistryError as e:
            logger.error(f"Failed to register schema for {subject}: {e}")
            return None
        
    
    def register_avro(self, subject: str, schema_str: str, **kwargs) -> Optional[Dict[str, Union[int, str]]]:
        return self.register_schema(subject, schema_str, "AVRO", **kwargs)
    

    def register_json(self, subject: str, schema_str: str, **kwargs) -> Optional[Dict[str, Union[int, str]]]:
        return self.register_schema(subject, schema_str, "JSON", **kwargs)
    

    def register_protobuf(self, subject: str, schema_str: str, **kwargs) -> Optional[Dict[str, Union[int, str]]]:
        return self.register_schema(subject, schema_str, "PROTOBUF", **kwargs)
    
    

    def set_compatibility(self, level: str, subject: Optional[str]= None) -> bool:
        #BACKWARD, FORWARD, BACKWARD_TRANSITIVE, etc
        try:
            lvl = level.upper()

            if subject:
                self.client.set_compatibility(level=lvl, subject_name=subject)
                logger.info(f"Set compatibility for {subject} = {lvl}")
            else:
                self.client.set_compatibility(level=lvl)
                logger.info(f"Setting global compatibility = {lvl}")
            return True
        except SchemaRegistryError as e:
            logger.error(f"Failed to set compatibility: {e}")
            return False
        

    def get_compatibility(self, subject: Optional[str] = None) -> Optional[str]:
        try:
            if subject:
                lvl = self.client.get_compatibility(subject_name=subject)
                logger.info(f"Subject = {subject}, compatibility = {lvl}")
                return lvl
            lvl = self.client.get_compatibility()
            logger.info("global compatibility = {lvl}")
            return lvl
        except SchemaRegistryError as e:
            logger.error(f"Failed to get compatibility: {e}")
            return None
        

    def test_compatibility(self, subject: str, schema_str: str, schema_type: str) -> Optional[bool]:
        try:
            schema_obj = self.build_schema(schema_str, schema_type)
            ok = self.client.test_compatibility(subject_name= subject, schema=schema_obj)
            logger.info(f"Compatibility test for {subject} ({schema_type.upper()}) = {ok}")
            return bool(ok)
        except SchemaRegistryError as e:
            logger.error(f"Failed to test compatibility for {subject}: {e}")
            return None
        
    
    def delete_subject(self, subject: str, *, permanent: bool = False) -> List[int]:
        try:
            versions = self.client.delete_subject(subject_name=subject, permanent=permanent)
            logger.info(f"Deleted subject={subject} (permanent={permanent}): {versions}")
            return versions
        except SchemaRegistryError as e:
            logger.error(f"Failed to delete subject {subject}: {e}")
            return []
        
    
    def delete_version(self, subject: str, version: Union[int, str]) -> Optional[int]:
        try:
            deleted = self.client.delete_version(subject_name=subject, version=version)
            logger.info(f"Deleted subject = {subject}, version={version}")
            return deleted
        except SchemaRegistryError as e:
            logger.error(f"Failed to delete version {version} for {subject}: {e}")
            return None
        

