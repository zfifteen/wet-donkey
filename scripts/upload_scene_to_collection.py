# scripts/upload_scene_to_collection.py
import argparse
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from xai_sdk import Client

SESSION_CONTRACT_VERSION = "1.0.0"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_scene_id(scene_file_path: str) -> str:
    """Extracts 'scene_01' from '/path/to/scene_01_intro.py'"""
    return Path(scene_file_path).stem.split('_')[0] + '_' + Path(scene_file_path).stem.split('_')[1]

def upload_validated_scene(project_dir, scene_file, qc_report):
    """Upload scene to collection after successful validation"""
    project_dir = Path(project_dir)
    management_api_key = os.getenv("XAI_MANAGEMENT_API_KEY")
    if not management_api_key:
        print("Warning: XAI_MANAGEMENT_API_KEY is not set. Skipping scene upload.")
        return

    client = Client(api_key=management_api_key)
    metadata_file = project_dir / ".collections_metadata.json"

    with open(metadata_file) as f:
        metadata = json.load(f)

    metadata.setdefault("contract_version", SESSION_CONTRACT_VERSION)
    metadata.setdefault("documents", [])
    metadata.setdefault("updated_at", utc_timestamp())

    project_collection_id = metadata["project_collection_id"]
    scene_id = extract_scene_id(scene_file)

    # Upload scene file
    print(f"Uploading scene file: {scene_file}")
    with open(scene_file, 'rb') as f:
        scene_doc = client.collections.upload_document(
            collection_id=project_collection_id,
            name=Path(scene_file).name,
            data=f.read(),
            fields={
                "scene_id": scene_id,
                "status": "validated",
                "timestamp": utc_timestamp(),
            },
        )
    print(f"Uploaded scene file with ID: {scene_doc.file_metadata.file_id}")

    # Upload QC report
    if qc_report and Path(qc_report).exists():
        print(f"Uploading QC report: {qc_report}")
        with open(qc_report, 'rb') as f:
            qc_doc = client.collections.upload_document(
                collection_id=project_collection_id,
                name=f"qc_{Path(scene_file).stem}.md",
                data=f.read(),
                fields={
                    "type": "qc_report",
                    "scene_id": scene_id
                }
            )
        print(f"Uploaded QC report with ID: {qc_doc.file_metadata.file_id}")
        
        # Update metadata
        metadata["documents"].extend([
            {"file_id": scene_doc.file_metadata.file_id, "name": scene_doc.name},
            {"file_id": qc_doc.file_metadata.file_id, "name": qc_doc.name}
        ])
    else:
        metadata["documents"].append({"file_id": scene_doc.file_metadata.file_id, "name": scene_doc.name})


    metadata["updated_at"] = utc_timestamp()
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Collection metadata updated in {metadata_file}")

def main():
    parser = argparse.ArgumentParser(description="Upload a validated scene and its QC report to the project's collection.")
    parser.add_argument("--project-dir", required=True, help="The project directory.")
    parser.add_argument("--scene-file", required=True, help="Path to the validated scene Python file.")
    parser.add_argument("--qc-report", help="Path to the scene's Quality Control report.")

    args = parser.parse_args()
    upload_validated_scene(args.project_dir, args.scene_file, args.qc_report)

if __name__ == "__main__":
    main()
