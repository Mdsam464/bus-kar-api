import sys
import os

# Guarantee absolute project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Change current working directory to project directory so relative DB paths work
os.chdir(BASE_DIR)

from app.mcp_server import mcp

if __name__ == "__main__":
    mcp.run()
