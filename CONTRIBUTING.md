# Contributing to pige.ovpn

Do you want to contribute to **pige.ovpn**? That's great news! :raised_hands:

Any kind of contribution is welcome: bug reports, feature requests and especially **code changes**.

Especially right now that the project is on its first steps, code changes are super important. 

If you want to contribute, you can also send me a message.

---

## Ways to contribute

You can help by:

- Submitting Pull Requests
- Fixing issues
- Reporting bugs
- Suggesting new features

---

## Reporting bugs

If you find a bug, please open a GitHub Issue and include:

- Your Linux distribution and version
- Python version (`python --version`)
- OpenVPN version (`openvpn --version`)
- Terminal emulator used
- Steps to reproduce the problem
- Expected behavior vs actual behavior
- Any relevant logs or screenshots

⚠️ Please **remove sensitive information** (VPN credentials, IPs, config secrets, etc.) before posting logs.

---

## Suggesting features

Feature requests are more than welcome.

When opening a feature request, please describe:

- The problem you are trying to solve
- What solution you propose
- Any alternatives you have considered

---

## Development setup

### 1. Fork and clone the repository

```bash
git clone https://github.com/<your-username>/pigeovpn.git
cd pigeovpn
```

### 2. Install with pipx
```bash
pipx install -e .
```

### 3. Run the app locally
```bash
pigeovpn
```

----

## Branch naming & commit messages

Please use clear and descriptive branch names:
- fix/auth-error
- feature/killswitch

Write concese and descriptive commit messages, for example:
- Fix authentication error handling
- Added automatic killswitch

---- 

Thank you for helping improve **pige.ovpn** :heart:
