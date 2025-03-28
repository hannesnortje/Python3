# Woda Browser

The Woda Browser is a custom-built browser leveraging PyQt6, designed for enhanced functionality within the Woda ™ platform. This browser includes JavaScript injection, developer tools, and more, and is distributed under the AGPL-3.0 license.

## Table of Contents
1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Licensing](#licensing)
5. [Troubleshooting](#troubleshooting)

---

## Requirements

- **Python 3.8 or higher**
- **Qt6 Open Source Version** (automatically installed with PyQt6)
  - The browser uses Qt6 under LGPL v3
  - PyQt6 components are automatically installed via pip
  - No commercial Qt license is required for use

## Installation

### Quick Install
Install directly from GitHub using pipx:
```bash
pipx install git+https://github.com/hannesnortje/WodaBrowser.git
```

### Development Install
For development or to modify the source:
```bash
# Clone the repository
git clone https://github.com/hannesnortje/WodaBrowser.git
cd WodaBrowser

# Install in development mode
pipx install -e .
```

### Updating
To update to the latest version:
```bash
pipx upgrade wodabrowser
```

Or force reinstall:
```bash
pipx install --force git+https://github.com/hannesnortje/WodaBrowser.git
```

### Install Python 3

If Python 3 is not installed, follow the instructions below for your operating system.

#### Windows

1. Download the latest Python 3 installer from [python.org](https://www.python.org/downloads/).
2. Run the installer. Make sure to check **Add Python to PATH** before clicking **Install Now**.
3. Verify the installation by opening Command Prompt and running:
   ```bash
   python --version
   ```

#### macOS

1. Python 3 is often pre-installed on macOS, but it may be outdated. To install or update Python 3, use Homebrew:
   ```bash
   brew install python
   ```

2. Verify the installation:
   ```bash
   python3 --version
   ```

#### Linux

1. Python 3 usually comes pre-installed on most Linux distributions. To check if it’s installed:
   ```bash
   python3 --version
   ```

2. If not installed, use the following command for Debian/Ubuntu-based systems:
   ```bash
   sudo apt update && sudo apt install python3
   ```

   For other distributions, refer to the package manager’s documentation.

---

### Install `pipx`

With Python 3 installed, install `pipx` to handle isolated installations of Python applications.

#### Windows

1. Open PowerShell as Administrator and install `pipx`:
   ```powershell
   python -m pip install --user pipx
   python -m pipx ensurepath
   ```

2. **Restart PowerShell** to ensure `pipx` is in your PATH.

#### macOS

1. Install `pipx` using `brew` (recommended) or `pip`:

   ```bash
   brew install pipx
   ```

   or if you don’t use Homebrew:

   ```bash
   python3 -m pip install --user pipx
   python3 -m pipx ensurepath
   ```

2. **Restart the terminal** to apply changes to your PATH.

#### Linux

1. Use your package manager to install `pipx`, or install it via `pip`.

   For Debian-based systems:
   ```bash
   sudo apt update && sudo apt install pipx
   ```

   For other Linux distributions, install with `pip`:
   ```bash
   python3 -m pip install --user pipx
   python3 -m pipx ensurepath
   ```

2. **Restart the terminal** after installation.

---

## Usage

Once installed, run the Woda Browser with the following command:

```bash
wodabrowser
```

The browser will launch with the Woda platform’s custom features.

---

## Licensing

This software is distributed under multiple licenses:

- **Browser Code**: GNU Affero General Public License v3 (AGPL-3.0)
- **Qt6 Components**: LGPL v3 (GNU Lesser General Public License version 3)
- **PyQt6**: GPL v3 (GNU General Public License version 3)

The use of Qt6 in this project is compliant with the open-source licensing terms of Qt and does not require a commercial Qt license for use or distribution.

---

## Troubleshooting

- **Error: `No module named 'PyQt6.QtWebEngineWidgets'`**: Ensure `PyQt6-WebEngine` is included in the package dependencies. Reinstall with `pipx install --force git+https://github.com/hannesnortje/woda_browser.git`.
- **Command Not Found**: If `pipx` commands are not recognized, confirm `pipx` is added to your PATH by restarting your terminal or following the installation instructions.

---

## License

This software is distributed under the GNU Affero General Public License v3 (AGPL-3.0). See the [LICENSE](LICENSE) file for details.

---