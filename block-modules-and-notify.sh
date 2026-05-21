#!/bin/bash
# Run modulejail in offline mode
export MODULEJAIL_NO_UPDATE_CHECK=1
echo "Generating blacklist..."
chmod +x ./modulejail
sudo install -d -m 0755 /etc/modulejail
sudo install -m 0644 additional_whitelist_modules.conf /etc/modulejail/whitelist.conf
sudo ./modulejail -p desktop --whitelist-file /etc/modulejail/whitelist.conf -o /etc/modprobe.d/custom_blacklist.conf
sed -i "s|^\(install \)\([a-zA-Z0-9_]\+\).*|\1\2 /usr/local/bin/mod-block-notify \2|" /etc/modprobe.d/custom_blacklist.conf
# options for profiles: minimal, conservative(default value of modulejail.sh), desktop

echo "Generating a description of all the modules in the blacklist, saving into disabled_modules_info.txt..."
python3 ./save_disabled_mod_descriptions.py

echo "Setting up logging and notification for attempts to load modules in the blacklist"
sudo mkdir -p /usr/local/bin
sudo cp ./mod-block-notify /usr/local/bin
sudo chmod 744 /usr/local/bin/mod-block-notify

echo "Testing functionality... If you see a modprobe error and a desktop notification, it means the script is working normally. "
sudo modprobe 6lowpan