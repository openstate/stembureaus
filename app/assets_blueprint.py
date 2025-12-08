import json
import os
from pathlib import Path

from flask import Blueprint

# Set application constants.
project_path = Path(os.path.dirname(os.path.abspath(__file__)))

class AssetsBlueprintFactory:
    @classmethod
    def create_assets_blueprint(cls, app):
        cls.app = app
        # Create a blueprint that stores all Vite-related functionality.
        cls.assets_blueprint = Blueprint(
            "assets_blueprint",
            __name__,
            static_folder="static/dist/bundled",
            static_url_path="/static/dist",
        )
        # Add `asset()` function to app context.
        @cls.assets_blueprint.app_context_processor
        def add_context():
            def asset(file_path):
                # When vite recompiles assets we should reread the manifest file. The easiest solution is simply
                # to always read the manifest file in debug/development mode
                if cls.app.debug:
                    cls.load_manifest()

                try:
                    return f"/static/dist/{cls.manifest[file_path]['file']}"
                except:
                    return "asset-not-found"

            return {
                "asset": asset
            }


        cls.load_manifest()
        return cls.assets_blueprint

    @classmethod
    def load_manifest(cls):
        cls.manifest = {}
        manifest_path = project_path / "static/dist/manifest.json"
        try:
            with open(manifest_path, "r") as content:
                cls.manifest = json.load(content)
        except OSError as exception:
            raise OSError(
                f"Manifest file not found. Run `npm run build`."
            ) from exception
        cls.app.logger.info(f"...just read assets manifest")

