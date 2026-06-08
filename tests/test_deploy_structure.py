import json
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeployArtifactTests(unittest.TestCase):
    def test_base_model_and_labels_match(self):
        labels = json.loads((ROOT / "training_outputs" / "label_classes.json").read_text(encoding="utf-8"))
        with zipfile.ZipFile(ROOT / "training_outputs" / "final_models" / "transformer.keras") as archive:
            config = json.loads(archive.read("config.json"))
        output_units = config["config"]["layers"][-1]["config"]["units"]
        self.assertEqual(output_units, len(labels))
        self.assertEqual(output_units, 36)

    def test_required_deploy_files_exist(self):
        required = [
            "deploy/backend/main.py",
            "deploy/backend/services/realtime_predictor.py",
            "deploy/backend/services/llm_translator.py",
            "deploy/frontend/manage.py",
            "deploy/frontend/web/templates/web/camera.html",
            "docker-compose.yml",
            ".env.example",
        ]
        for relative_path in required:
            self.assertTrue((ROOT / relative_path).exists(), relative_path)


if __name__ == "__main__":
    unittest.main()
