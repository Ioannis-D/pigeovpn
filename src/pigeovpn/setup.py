'''
Create the credentials.txt file from which the .ovpn file roots the 'auth-user-pass'
'''

import os
from pathlib import Path
import json
import tempfile

from pigeovpn.constants import CREDS_FILE, JSON_CONF
from pigeovpn.external_commands import execute_sudo_commands

def modify_json(key:str, value) -> None:
    """Modify values of the json configuration"""
    # Load the file
    with open(JSON_CONF, "r") as file:
           config = json.load(file)
    
    # Change the value
    config[key] = value
    with open(JSON_CONF, "w") as file:
        json.dump(config, file)


def setup_credentials(username: str, password: str):
    """
    Create a credentials file {CREDS_FILE} containing
        username\n
        password\n
    with mode 600
    From this file the .ovpn files read the setup_credentials
    """
    # OpenVPN reads the file as two lines: username and password.
    # Disallow control chars that can break this structure.
    if any(c in username for c in ("\n", "\r", "\x00")):
        return 1
    if any(c in password for c in ("\n", "\r", "\x00")):
        return 1

    temp_creds_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
        ) as tmp_file:
            tmp_file.write(f"{username}\n{password}\n")
            temp_creds_path = tmp_file.name

        os.chmod(temp_creds_path, 0o600)
        return execute_sudo_commands(
            ["sudo", "install", "-m", "600", temp_creds_path, CREDS_FILE]
        )
    finally:
        if temp_creds_path:
            try:
                os.remove(temp_creds_path)
            except OSError:
                pass


def setup_ovpnDirectory(directory: str | Path) -> None:
    """
    From the settings page, insert into the json file the directory given by the user
    """
    modify_json("ovpn_directory", directory)


def check_showing_settings() -> bool:
    """
    Check if the settings/welcome page should be shown
    """

    with open(JSON_CONF, "r") as file:
        config = json.load(file)

    return config["show_settings"]

def update_showing_settings() -> None:
    modify_json("show_settings", False)
