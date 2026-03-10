from pathlib import Path

REPO_ROOT = Path(__file__).parents[3]

CONFIG_PATH = REPO_ROOT / "configs"
DATA_PATH = REPO_ROOT / "data"
LOG_PATH = REPO_ROOT / "logs"
NOTEBOOK_PATH = REPO_ROOT / "notebooks"
SOURCE_PATH = REPO_ROOT / "backend"
PACKAGE_PATH = SOURCE_PATH / "app"

# DATA_CONFIG_PATH = CONFIG_PATH / "data.yaml"
# FEATURE_CONFIG_PATH = CONFIG_PATH / "feature.yaml"
# MODEL_CONFIG_PATH = CONFIG_PATH / "model.yaml"

# RAW_DATA_PATH = DATA_PATH / "raw"
# INTERMEDIATE_DATA_PATH = DATA_PATH / "intermediate"
# PROCESSED_DATA_PATH = DATA_PATH / "processed"
