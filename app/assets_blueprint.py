import json
import os
from pathlib import Path

from flask import Blueprint

# Set application constants.
project_path = Path(os.path.dirname(os.path.abspath(__file__)))

# Create a blueprint that stores all Vite-related functionality.
assets_blueprint = Blueprint(
    "assets_blueprint",
    __name__,
    static_folder="static/dist/bundled",
    static_url_path="/static/dist",
)

# Load manifest file in the production environment.
manifest = {}
manifest_path = project_path / "static/dist/manifest.json"
try:
    with open(manifest_path, "r") as content:
        manifest = json.load(content)
except OSError as exception:
    raise OSError(
        f"Manifest file not found. Run `npm run build`."
    ) from exception


# Add `asset()` function to app context.
@assets_blueprint.app_context_processor
def add_context():
    def asset(file_path):
        try:
            return f"/static/dist/{manifest[file_path]['file']}"
        except:
            return "asset-not-found"

    return {
        "asset": asset
    }
