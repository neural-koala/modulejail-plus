import os
import re
from pathlib import Path


script_dir = Path(__file__).resolve().parent
MODULES_LIST = str(script_dir / "builtin_modules_blacklist.txt")
# Automatically targets your current running kernel
MODINFO_FILE = f"/lib/modules/{os.uname().release}/modules.builtin.modinfo"

if not os.path.exists(MODULES_LIST):
    print(f"Error: {MODULES_LIST} not found.")
    exit(1)

if not os.path.exists(MODINFO_FILE):
    print(f"Error: {MODINFO_FILE} not found. Are you running this on the target machine?")
    exit(1)

# Read and normalize the blacklist module names
blacklist = []
with open(MODULES_LIST, "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            # Extract just the filename without path or extension (e.g., virtio_blk)
            name = os.path.basename(line).replace(".ko", "")
            # Normalize dashes to underscores for searching
            normalized_name = name.replace("-", "_")
            blacklist.append((line, normalized_name))

# Read the null-byte separated modinfo file
with open(MODINFO_FILE, "rb") as f:
    # Split by null bytes and decode safely
    modinfo_content = f.read().decode("utf-8", errors="ignore").split("\0")

print("=== Suggested .config modifications ===\n")

# Process each blacklisted module
for original_path, mod_name in blacklist:
    found = False
    
    # Search for matching patterns inside the modinfo array
    for entry in modinfo_content:
        # Match pattern: module_name.file= or module_name.cfg=
        # We also check for normalized underscore variants
        if entry.startswith(f"{mod_name}.") and "=" in entry:
            key, val = entry.split("=", 1)
            
            # Look for the internal Kbuild alias variable
            if key.endswith(".file") or key.endswith(".cfg"):
                # Clean up the configuration name
                config_name = val.strip('"').upper()
                
                # If it's just a file path, extract the upper case variable name
                if "/" in config_name:
                    config_name = os.path.basename(config_name).replace(".KO", "").replace("-", "_")
                
                print(f"# Module: {original_path}")
                print(f"CONFIG_{config_name}=n")
                print("-" * 38)
                found = True
                break
                
    if not found:
        # Fallback manual guess step if modinfo doesn't explicitly flag it
        guess = os.path.basename(original_path).replace(".ko", "").replace("-", "_").upper()
        print(f"# Warning: Exact mapping missed for {original_path}")
        print(f"# Best guess: CONFIG_{guess}=n")
        print("-" * 38)