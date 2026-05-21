import re
import subprocess
from pathlib import Path
import collections

# Paths configuration
CONFIG_PATH = "/etc/modprobe.d/custom_blacklist.conf"
OUTPUT_PATH = "disabled_modules_info.txt"


def get_blacklisted_modules(config_file):
    """Parses the config file and returns a list of target module names."""
    modules = []
    # Match lines starting with blacklist or install, followed by whitespace, then capture the module name
    pattern = re.compile(r"^(?:blacklist|install)\s+(\S+)")

    try:
        with open(config_file, "r") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    modules.append(match.group(1))
    except FileNotFoundError:
        print(f"Error: {config_file} not found.")
    return modules


def generate_descriptions():
    # 1. Get the list of modules
    modules = get_blacklisted_modules(CONFIG_PATH)

    if not modules:
        print("No modules found to process.")
        return

    # 2. Run modinfo ONCE for all modules
    # We ask for filename to help us map the output back to the module name
    cmd = ["modinfo",] + modules

    # capture_output=True keeps stderr out of our way if a module isn't found
    modinfo_output = subprocess.run(cmd, capture_output=True, text=True).stdout
    



    parsed_data = collections.OrderedDict()
    current_module = None
    output_lines=[]

    # Process line by line
    for line in modinfo_output.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # modinfo separate tags and values by whitespace/tabs (e.g., "filename:    /path/to/mod.ko")
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # The 'filename' field indicates the start of a brand new module block
            if key == "filename":
                # Extract the module name from the file path filename (e.g., /path/to/ext4.ko -> ext4)
                base_name = value.split("/")[-1]
                if base_name.endswith(".ko") or base_name.endswith(".ko.xz") or base_name.endswith(".ko.zst"):
                    current_module = base_name.split(".ko")[0].replace("-", "_")
                else:
                    current_module = base_name  # Fallback
                
                if current_module not in parsed_data:
                    parsed_data[current_module] = []
            
            # Collect descriptions if a module block has been established
            elif key == "description" and current_module:
                parsed_data[current_module].append(value)

    # Merge multiple descriptions together
    merged_descriptions = {}
    for mod, desc_list in parsed_data.items():
        if desc_list:
            # Join separate descriptions with a semicolon or a space
            merged_descriptions[mod] = " | ".join(desc_list)
        else:
            merged_descriptions[mod] = "No description provided."
    merged_descriptions = merged_descriptions.values()
    # print(f"len(merged_descriptions): {len(merged_descriptions)}")
    # print(f"len(modules):{len(modules)}")
    for a, b in zip(modules,merged_descriptions):
        output_lines.append(f"{a}\n{b}\n\n")

    
    if output_lines:
        with open(OUTPUT_PATH, "w") as f:
            f.writelines(output_lines)
        print(f"Descriptions successfully saved to {OUTPUT_PATH}")
    else:
        print(
            "No description data could be retrieved."
        )


if __name__ == "__main__":
    generate_descriptions()