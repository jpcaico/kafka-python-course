from SchemaRegistryWrapper import SchemaRegistryAdmin
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("schema-registry-demo")

def clean_start_demo(sr, subject):
    """Clean up existing schemas for a fresh start"""
    try:
        # Check if subject exists
        existing_versions = sr.get_versions(subject)
        if existing_versions:
            log.info(f"Subject '{subject}' already exists with versions: {existing_versions}")
            log.info(f"Deleting subject '{subject}' for a clean start...")
            
            # MUST do soft delete first
            sr.delete_subject(subject, permanent=False)  # or just sr.delete_subject(subject)
            log.info(f"Soft deleted subject '{subject}'")
            
            # THEN permanent delete
            sr.delete_subject(subject, permanent=True)
            log.info(f"Permanently deleted subject '{subject}'")
            
    except Exception as e:
        # Subject doesn't exist, which is fine
        log.info(f"Subject '{subject}' doesn't exist yet (or error checking): {e}")

def main():
    sr = SchemaRegistryAdmin(url="http://localhost:8082")
    
    # Set global compatibility
    if not sr.set_compatibility("BACKWARD"):
        log.error("Failed to set global compatibility to BACKWARD.")
        sys.exit(1)
    
    subject = "demo-topic-value"
    
    # Option 1: Clean start (delete existing schemas)
    # Uncomment this if you want to start fresh
    # clean_start_demo(sr, subject)
    
    # Option 2: Check existing state first
    existing_versions = sr.get_versions(subject)
    if existing_versions:
        log.warning(f"Subject '{subject}' already has versions: {existing_versions}")
        latest = sr.get_latest(subject)
        if latest:
            log.info(f"Latest version info: version={latest.get('version')}, id={latest.get('id')}")
        
        user_input = input("\nDo you want to:\n1. Delete and start fresh (y)\n2. Continue with existing versions (n)\n3. Exit (any other key)\nChoice: ")
        
        if user_input.lower() == 'y':
            clean_start_demo(sr, subject)
        elif user_input.lower() != 'n':
            log.info("Exiting...")
            sys.exit(0)
    
    # Define schemas
    avro_v1 = """
    {
        "type": "record",
        "name": "UserEvent",
        "namespace": "demo",
        "fields": [
            {"name": "user_id", "type": "int"},
            {"name": "event", "type": "string"},
            {"name": "timestamp", "type": "long"}
        ]
    }
    """
    
    avro_v2 = """
    {
        "type": "record",
        "name": "UserEvent",
        "namespace": "demo",
        "fields": [
            {"name": "user_id", "type": "int"},
            {"name": "event", "type": "string"},
            {"name": "timestamp", "type": "long"},
            {"name": "source", "type": ["null","string"], "default": null}
        ]
    }
    """
    
    # Get the starting version number
    versions_before = sr.get_versions(subject) or []
    starting_version = max(versions_before) + 1 if versions_before else 1
    
    log.info(f"Starting from version {starting_version}")
    
    # Register v1
    info_v1 = sr.register_avro(subject, avro_v1)
    if not info_v1:
        log.error("v1 registration failed.")
        sys.exit(1)
    
    log.info("v1: id=%s, assigned_version=%s, latest_after_register=%s",
             info_v1["id"], info_v1["version"], info_v1["latest_after_register"])
    
    # Check if this is the expected version
    expected_v1_version = starting_version
    if info_v1["version"] != expected_v1_version:
        log.warning(f"Expected v1 assigned version={expected_v1_version}, got {info_v1['version']}")
        log.info("This suggests the schema was already registered before.")
    
    # Compatibility check for v2
    ok = sr.test_compatibility(subject, avro_v2, "AVRO")
    log.info("Can evolve to v2 under BACKWARD? %s", ok)
    
    if ok is not True:
        log.error("Compatibility failed — v2 should be backward compatible (added optional field with default).")
        sys.exit(1)
    
    # Register v2
    info_v2 = sr.register_avro(subject, avro_v2)
    if not info_v2:
        log.error("v2 registration failed.")
        sys.exit(1)
    
    log.info("v2: id=%s, assigned_version=%s, latest_after_register=%s",
             info_v2["id"], info_v2["version"], info_v2["latest_after_register"])
    
    # Check if versions are sequential
    if info_v2["version"] != info_v1["version"] + 1:
        log.warning(f"v2 version ({info_v2['version']}) is not v1 version + 1 ({info_v1['version'] + 1})")
        log.info("This might indicate the same schema was already registered.")
    
    # Verify versions list
    versions = sr.get_versions(subject)
    log.info("All versions for '%s': %s", subject, versions)
    
    # Fetch schema by ID
    latest = sr.get_latest(subject)
    latest_id = latest["id"] if latest else None
    
    if latest_id:
        fetched_schema = sr.get_schema_by_id(latest_id)
        if not fetched_schema:
            log.error("Failed to fetch schema by latest id=%s", latest_id)
            sys.exit(1)
    
    # Summary
    log.info(f"Global compat: BACKWARD")
    log.info(f"v1 assigned_version={info_v1['version']}")
    log.info(f"v2 assigned_version={info_v2['version']}")
    log.info(f"get_versions(subject) = {versions}")
    log.info(f"get_latest(subject) shows version={latest.get('version') if latest else 'N/A'}")
    log.info(f"get_schema_by_id(latest_id) returns schema: {'✓' if fetched_schema else '✗'}")
    
    if starting_version == 1:
        log.info("\n Clean start achieved, versions started from 1")
    else:
        log.info(f"\nContinued from existing state, versions started from {starting_version}")

if __name__ == "__main__":
    main()