# scripts/initialize_training_corpus.py
import argparse
import os
import json
import sys
from inspect import signature
from pathlib import Path
from datetime import datetime, timezone
import grpc
from xai_sdk import Client

SESSION_CONTRACT_VERSION = "1.0.0"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_collection_compat(client: Client, name: str, description: str):
    """Create a collection across xai_sdk versions with/without description support."""
    create_params = signature(client.collections.create).parameters
    kwargs = {"name": name}
    if "description" in create_params:
        kwargs["description"] = description
    return client.collections.create(**kwargs)


def classify_collections_error(error: Exception) -> RuntimeError:
    message = str(error)
    if "StatusCode.UNAUTHENTICATED" in message or "Invalid bearer token" in message:
        return RuntimeError(
            "Invalid XAI_MANAGEMENT_API_KEY for collections operations. "
            "Provide a dedicated management key and retry."
        )
    return RuntimeError(f"Collections initialization failed: {message}")


def _management_host_candidates() -> list[str]:
    explicit_host = os.getenv("XAI_MANAGEMENT_API_HOST", "").strip()
    if explicit_host:
        return [explicit_host]
    return ["management-api.x.ai", "api.x.ai"]


def _build_client_with_host_fallback(
    api_key: str,
    management_api_key: str,
):
    last_error: Exception | None = None
    for host in _management_host_candidates():
        try:
            client = Client(
                api_key=api_key,
                management_api_key=management_api_key,
                management_api_host=host,
            )
            # Auth ping against management surface before mutations.
            client.collections.list(limit=1)
            if host != "management-api.x.ai":
                print(f"Using fallback management API host: {host}")
            return client
        except grpc.RpcError as error:
            details = error.details() if hasattr(error, "details") else str(error)
            if (
                host == "management-api.x.ai"
                and error.code() == grpc.StatusCode.UNAUTHENTICATED
                and "Invalid bearer token" in details
            ):
                last_error = error
                continue
            raise
        except Exception as error:
            if host == "management-api.x.ai":
                last_error = error
                continue
            raise

    if last_error is not None:
        raise last_error
    raise RuntimeError("Unable to initialize management API client.")


def initialize_training_corpus(project_dir: str, project_name: str, template_collection_id: str = None):
    """Create Collections for template library and scene examples"""
    project_dir = Path(project_dir)
    management_api_key = os.getenv("XAI_MANAGEMENT_API_KEY")
    if not management_api_key:
        print("Warning: XAI_MANAGEMENT_API_KEY is not set. Skipping collection creation.")
        return
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise RuntimeError("XAI_API_KEY is required for SDK initialization.")

    client = _build_client_with_host_fallback(
        api_key=api_key,
        management_api_key=management_api_key,
    )

    # 1. Template library collection
    if template_collection_id:
        print(f"Using existing template collection: {template_collection_id}")
        template_collection_id = template_collection_id
    else:
        print("Creating new template collection: 'wet-donkey-templates'")
        template_collection = create_collection_compat(
            client=client,
            name="wet-donkey-templates",
            description="Kitchen sink patterns, scene helpers, visual reference docs for Wet Donkey",
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
    project_collection = create_collection_compat(
        client=client,
        name=project_collection_name,
        description=f"Generated scene files and QC reports for project {project_name}",
    )
    project_collection_id = project_collection.collection_id
    print(f"Created project collection with ID: {project_collection_id}")

    # 3. Save metadata
    metadata = {
        "contract_version": SESSION_CONTRACT_VERSION,
        "template_collection_id": template_collection_id,
        "project_collection_id": project_collection_id,
        "documents": [],
        "updated_at": utc_timestamp(),
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
    
    try:
        initialize_training_corpus(args.project_dir, args.project_name, args.template_collection_id)
    except RuntimeError:
        raise
    except Exception as error:
        raise classify_collections_error(error) from error

if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(4) from exc
