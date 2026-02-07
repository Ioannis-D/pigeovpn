![pigeovpn logo](./images/pigeovpn_logo.png "pigeovpn logo")
# pige.ovpn
A TUI that makes it easier to connect to VPNs and monitor internet usage.

Made for Linux distros.

##  Features
- Connect/Disconnect to VPN.
- Show IP info (IP address, city, country).
- Monitor network usage.

## Prerequisites
- Python 3.9 or above.
- A supported terminal emulator:
    - gnome-terminal
    - konsole
    - x-terminal-emulator
    - xfce4-terminal
    - alacritty
    - terminator
    - kitty
    - mate-terminal
- OpenVPN installed on your system.

## Installation
#### pipx installation (recommended)
pige.ovpn is available in PyPy and can be installed via **pipx** by running:

```bash
pipx install pigeovpn
```

Launch pige.ovpn with the following:

``` bash
pigeovpn
```

You can also use **pip** (`pip install pigeovpn`) but it is <u> highly unrecommended </u> for avoiding dependency issues.

#### GitHub repo clone installation
If you don't want to use `pipx`, you can download the GitHub repo by running:
``

Run the program from the repo's directory with:
```bash
python3 -m tui_app.py
```

## How the app works
### First run
The first time you run the app, you will see the welcome page: 
![Screenshot of welcome page](./images/Welcome_Page.png)

From there, you will have to:
- Provide your provider's credentials (username and password) which will create the credentials.txt file at [path]  
- Indicate the directory the .ovpn conf files rest.

Once these steps are complete, you will see the main app: 
[photo of the main app]

### Main app
The app has two main panels, the left and the right. 

On the left, all the `.ovpn` files contained in the directory provided are shown.

By pressing `s`, the user can dynamically search the files (regex is used): [gif demostration]

To connect to a file, you can simply click on it, or press `Enter`. 

The right panel is the information and the control panel. 

Until a file is not selected, the IP address information isn't automatically shown to not ... the url address. You can manually update it any moment by pressing the [key]. 

By pressing `q` you can exit the app, **but the VPN connection will still be active and running**. 

### Technical characteristics
#### sudo commands
The app has to use sudo privileges to:
- connect to an .ovpn configuration.
- disconnect the OpenVPN.
- create the credentials file

For security and operational reasons, **the app isn't run with sudo priviledges**. Instead, every time a command that needs to run with sudo, a new terminal window appears that asks the user for the sudo password. Although this can be frustrating as it will ask for the password every time a new connection has to be done, it's a safe way to ensure two things:
- the password isn't stored in memory
- if the password given is wrong, the terminal will automatically notify the user and will re-ask for the correct one

The app will try to open whichever terminal in the list is installed, and execute the command via the terminal (you can find the terminals at the `constants.py` module). The user, apart from the sudo password, will not notice anything else.


## FAQs
### When I try to connect, I insert my sudo password but I get a 'AUTH verification' error.
This means that the VPN's credentials are incorrect. Try to re-insert them (by Logging out) or manually create them (/etc/openvpn/credentials.txt)

### I connect to the VPN without errors, but the connection isn't active.
Probably the VPN's credentials are incorrect. Try to re-insert them (by Logging out) or manually create them (/etc/openvpn/credentials.txt). 
If the issue continues, please open an Issue.

### The city and/or country are incorrect.
pige.ovpn tries to use the '' website for IP information. However, if multiple requests are sent in a short period, the '' is used, which free plan isn't as precise. 

In future versions, the option to insert different APIs is to be added.

### Why pige.ovpn and how is it pronounced?
Pige.ovpn takes its name from the bird pigeon, which is how it is pronounced (pigeo - vpn). 
For the moment, the app only serves OpenVPN connections via the `.ovpn` configurtion files.

Pigeons can be found almost everywhere and racing pigeons can even travel 1.000 km in a day, changing cities and even countries. 
Also, for many years, they have been used as messengers.
For that reason, the app is called after them, as the VPN allows you to be connected to different locations around the globe.

### Why did I make this application?
When I moved from Ubuntu to CachyOS, I realized that the grand mayority of VPN providers don't provide any GUI application for Linux, other than for Debian-based distributions. Almost all of them provide the .ovpn configurations and you have to "manually" connect to them.

I decided to create one which could fill the gap and provide the essentials that the GUI apps have.

### Why a TUI and not a GUI?
There are two main reasons I decided to make a TUI rather than a GUI:

1. The app is ... to linux users, especially for those who use Arch or Arch-based distros. It is not a secret that we prefer doing stuff with the terminal rather than other tools.
2. I am a data analyst, and I am better in using Python, which isn't a 'fast' language. Nevetherless, running a TUI with Python doesn't make the app run considerably slower.
3. I saw the Textual framework and I loved it. So, this app is also a way for me to experiment with this framework.


### Why not cross-platform?
The main purpose of the app is to try to provide an application that misses from Linux distros (especially those that are not Debian based). 
As far as I know, all VPN providers have already their own apps for Windows and MacOS, which are rich in feauters. 

So, at least for the moment, the app is focused on providing a better experience to those who don't have access to similar apps.

## pige.ovpn development
pige.ovpn is currently under development.

Anyone who is interested in collaborating is more than welcome. Please see [Contributing.md] for more details.
### Roadmap
There are plenty of features I would like to include in the next versions. Some of them are:
- [ ] Enable autoinput with `tab` for the directory selection.
- [ ] Include an automatic killswitch.
- [ ] Include more keybindings (f.e. for the buttons)
- [ ] Use vim keyrings for the directory tree navigation.
- [ ] Only select an .ovpn file from the tree directory with double click.
- [ ] Show loading widget when refresh ip data is pressed.
- [ ] Include the option of different APIs for IP detection.
- [ ] When a new directory is given, update only the directory tree, not the whole screen.
- [ ] Replace current graph with a line graph.

The list can be amplified based on user's requests.

## License
![GPLv3 or Greater Logo](https://www.gnu.org/graphics/gplv3-or-later.svg "GNU GPL V3 LOGO")
