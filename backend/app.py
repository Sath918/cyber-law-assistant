import uvicorn
import os
import sys

# Add the current backend directory to sys.path to enable loading app.main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)
