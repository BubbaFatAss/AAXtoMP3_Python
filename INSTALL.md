# Installation Guide

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/BubbaFatAss/AAXtoMP3_Python.git
   cd AAXtoMP3_Python
   ```

2. **Install system dependencies**

   ### macOS
   ```bash
   brew install ffmpeg mp4v2 mediainfo
   ```

   ### Ubuntu/Debian
   ```bash
   sudo apt-get update
   sudo apt-get install ffmpeg mp4v2-utils mediainfo
   ```

   ### RHEL/CentOS/Fedora
   ```bash
   sudo yum install ffmpeg
   ```

3. **Make the script executable** (if not already)
   ```bash
   chmod +x aaxtomp3.py
   ```

4. **Run the script**
   ```bash
   ./aaxtomp3.py --help
   ```

## Optional: Add to PATH

To use the script from anywhere, you can add it to your PATH:

### Option 1: Create a symlink
```bash
sudo ln -s /path/to/AAXtoMP3_Python/aaxtomp3.py /usr/local/bin/aaxtomp3
```

### Option 2: Add to PATH in your shell profile
Add to `~/.bashrc`, `~/.zshrc`, or equivalent:
```bash
export PATH="$PATH:/path/to/AAXtoMP3_Python"
```

Then reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

## Getting Your Audible Activation Bytes

To convert AAX files, you need your Audible activation bytes. Here are some methods:

### Method 1: Using audible-cli (Recommended)
```bash
pip install audible-cli
audible quickstart
audible activation-bytes
```

### Method 2: Using other tools
- [audible-activator](https://github.com/inAudible-NG/audible-activator)
- [RainbowCrack tables](http://rainbow.inaudible.com/)

## Testing the Installation

You can verify everything is working by checking the dependencies:

```bash
ffmpeg -version
ffprobe -version
mp4art --help  # Optional, for M4A/M4B
mp4chaps --help  # Optional, for M4A/M4B
mediainfo --version  # Optional
```

## Troubleshooting

### ffmpeg not found
Make sure ffmpeg is installed and in your PATH:
```bash
which ffmpeg
```

If not found, install it using the instructions above.

### Permission denied
If you get a "Permission denied" error, make the script executable:
```bash
chmod +x aaxtomp3.py
```

### Python version
This script requires Python 3.6 or higher. Check your version:
```bash
python3 --version
```

## Next Steps

See [README.md](README.md) for detailed usage instructions and examples.
