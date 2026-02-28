"""
This module stores the 'external' commands that other modules use. 
Also includes the sudo  commands, which are handled with a new terminal window, where the user is asked for the sudo password.
"""

import subprocess
import webbrowser
from pathlib import Path
import os
import warnings

from pigeovpn.constants import GITHUB_REPO, CREDS_FILE, COMMON_TERMINALS

def execute_sudo_commands(sudo_command: str | list[str]):
    """
    As the app has to do with OpenVPN connections, some of the commands have to run with sudo privileges. 
    Of course, storing the sudo password as plain text, or keep it in Python's memory is out of question.
    Textual doesn't support something similar to getpass(), which allows Python's module to safely ask the sudo password. 
    To achieve something similar, a new terminal window is opened, and the sudo command runs explicitely in that window. 
    The user gives the sudo password to the new window (which can also handle incorrect passwords and ask the user to repeat it).
    One negative effect though is that the user has to give the sudo password every time, even if no time has passed. 
    """
    if isinstance(sudo_command, str):
        # Backward-compatible path for existing string commands.
        # Wrapped through a shell to preserve previous behavior.
        command_parts = ["sh", "-lc", sudo_command]
    else:
        command_parts = [str(arg) for arg in sudo_command]

    for terminal, flag in COMMON_TERMINALS.items():
        try:
            result = subprocess.Popen(
                [
                terminal,
                flag,
                *command_parts
                ]
            )
        except Exception as e:
            returncode = e
            pass
        else:
            result.wait()
            returncode = result.returncode
            return returncode

    return returncode

def connect_vpn(ovpn_file: str | Path):
    """
    Connect to the selected ovpn configuration
    Returns True if the execution has been operated, but doesn't mean that the connection to the ovpn service has succeeded.
    Else, returns False
    """
    sudo_command = [
        "sudo",
        "openvpn",
        "--config",
        str(ovpn_file),
        "--auth-user-pass",
        CREDS_FILE,
        "--daemon",
    ]

    return execute_sudo_commands(sudo_command)

def disconnect_vpn():
    """
    Disconnect the OpenVPN.
    Kills all openvpn instances.
    """
    sudo_command = [
        "sudo",
        "killall",
        "openvpn",
    ]
    
    return execute_sudo_commands(sudo_command)

def open_url_browser(url: str = GITHUB_REPO) -> bool:
    """
    Opens the GitHub repo with the default browser
    """
    try:
        os.environ["QT_LOGGING_RULES"] = "qt.qpa.*=false" # Removes warning related to Qt with Wayland 
        with warnings.catch_warnings(): # Ignore other warnings that can arise by opening the default browser
            warnings.simplefilter("ignore")
            webbrowser.open(url)
    except:
        return False
    else:
        return True
