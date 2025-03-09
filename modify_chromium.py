import os
import pyppeteer
from pathlib import Path
import re
# Define the correct Chromium version
CHROMIUM_REVISION = '1263111'  # A working version

# Locate Pyppeteer's init.py
PYPPETEER_DIR = Path(pyppeteer.__file__).parent
INIT_FILE = PYPPETEER_DIR / '__init__.py'
print(INIT_FILE)
def modify_chromium_version():
    """Modify the Chromium revision in __init__.py dynamically."""
    if INIT_FILE.exists():
        with open(INIT_FILE, 'r') as file:
            content = file.read()

        # Check if we need to modify the file
        if f"__chromium_revision__ = '{CHROMIUM_REVISION}'" not in content:
            print("Updating Chromium version in Pyppeteer's init.py...")
            # Replace the old revision with the new one
            updated_content = re.sub(
                r"__chromium_revision__ = '(\d+)'", 
                f"__chromium_revision__ = '{CHROMIUM_REVISION}'",
                content
            )
            with open(INIT_FILE, 'w') as file:
                file.write(updated_content)
            print("Chromium version updated successfully!")
        else:
            print("Chromium version is already up-to-date.")


# Run the modification and installation
modify_chromium_version()
