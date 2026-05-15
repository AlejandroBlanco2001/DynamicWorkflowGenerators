import os
import pathlib
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app

AGENTS_DIR = str(pathlib.Path(__file__).parent)

app = get_fast_api_app(
    agents_dir=AGENTS_DIR,
    web=True,
)

if __name__ == "__main__":
    port = os.getenv("AGENTS_PORT", 8000)
    port = int(port)
    uvicorn.run(app, host="0.0.0.0", port=port)