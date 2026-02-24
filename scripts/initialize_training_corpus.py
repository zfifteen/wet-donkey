# scripts/initialize_training_corpus.py
import argparse
import os
import json
from pathlib import Path
from xai_sdk import Client

def initialize_training_corpus(project_dir: str, project_name: str, template_collection_id: str = None):
    """Create Collections for template library and scene examples"""
    project_dir = Path(project_dir)
    management_api_key = os.getenv("XAI_MANAGEMENT_API_KEY")
    if not management_api_key:
        print("Warning: XAI_MANAGEMENT_API_KEY is not set. Skipping collection creation.")
        return

    client = Client(api_key=management_api_key)

    # 1. Template library collection
    if template_collection_id:
        print(f"Using existing template collection: {template_collection_id}")
        template_collection_id = template_collection_id
    else:
        print("Creating new template collection: 'wet-donkey-templates'")
        template_collection = client.collections.create(
            name="wet-donkey-templates",
            description="Kitchen sink patterns, scene helpers, visual reference docs for Wet Donkey"
        )
        template_collection_id = template_collection.collection_id
        print(f"Created template collection with ID: {template_collection_id}")
        # In a real scenario, you would upload template files here.
        # For now, we are just creating the collection.
        print("Uploading template files...")
        # for template_path in Path("harness/templates").glob("*.py"):
        #     ...

    # 2. Project-specific collection
    project_collection_name = f"{project_name}-scenes"
    print(f"Creating project-specific collection: '{project_collection_name}'")
    project_collection = client.collections.create(
        name=project_collection_name,
        description=f"Generated scene files and QC reports for project {project_name}"
    )
    project_collection_id = project_collection.collection_id
    print(f"Created project collection with ID: {project_collection_id}")

    # 3. Save metadata
    metadata = {
        "template_collection_id": template_collection_id,
        "project_collection_id": project_collection_id,
        "documents": []
    }
    metadata_file = project_dir / ".collections_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Collection metadata saved to {metadata_file}")


def main():
    parser = argparse.ArgumentParser(description="Initialize xAI Collections for a new project.")
    parser.add_argument("--project-dir", required=True, help="The project directory.")
    parser.add_argument("--project-name", required=True, help="The name of the project.")
    parser.add_argument("--template-collection-id", help="Reuse an existing template collection.")
    
    args = parser.parse_args()
    
    initialize_training_corpus(args.project_dir, args.project_name, args.template_collection_id)

if __name__ == "__main__":
    main()
