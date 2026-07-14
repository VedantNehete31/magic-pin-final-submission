from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from magicpin_bot.api.app import app
from magicpin_bot.engines.composer import compose

__all__ = ["app", "compose"]
