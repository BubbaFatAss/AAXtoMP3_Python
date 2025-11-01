# AAXtoMP3_Python

Python port of [AAXtoMP3](https://github.com/KrumpetPirate/AAXtoMP3) - Convert Audible AAX/AAXC files to various audio formats.

## Description

AAXtoMP3_Python is a Python script that converts Audible's proprietary AAX and AAXC audiobook formats to more common audio formats like MP3, M4A, M4B, FLAC, and Opus. It preserves metadata, chapter information, and cover art.

## Features

- Convert AAX/AAXC files to MP3, M4A, M4B, FLAC, or Opus
- Support for both single file and chaptered output
- Preserve metadata (title, author, album, genre, etc.)
- Extract and embed cover art
- Generate M3U playlists for chaptered output
- Customizable output directory and file naming schemes
- Validation mode to check file integrity without conversion

## Requirements

### System Dependencies

The script requires the following external tools:

#### Required
- **Python 3.6+** (uses only standard library)
- **ffmpeg** - For audio conversion
- **ffprobe** - For metadata extraction (usually comes with ffmpeg)

#### Optional
- **mp4v2-utils** - For M4A/M4B support (provides `mp4art` and `mp4chaps`)
- **mediainfo** - For additional metadata extraction

### Installation

#### macOS (using Homebrew)
```bash
brew install ffmpeg
brew install mp4v2  # Optional, for M4A/M4B support
brew install mediainfo  # Optional
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install ffmpeg
sudo apt-get install mp4v2-utils  # Optional, for M4A/M4B support
sudo apt-get install mediainfo  # Optional
```

#### RHEL/CentOS/Fedora
```bash
sudo yum install ffmpeg
```

## Usage

### Basic Usage

```bash
./aaxtomp3.py -A <AUTHCODE> <AAX_FILE>
```

This will create a chaptered MP3 output in a directory structure: `genre/artist/title/`

### Authentication

#### For AAX files
You need your Audible activation bytes (authcode):
```bash
./aaxtomp3.py -A <AUTHCODE> audiobook.aax
```

#### For AAXC files
AAXC files require a `.voucher` file with the same base name:
- `audiobook.aaxc`
- `audiobook.voucher`

No authcode is needed for AAXC files.

### Output Formats

#### MP3 (default)
```bash
./aaxtomp3.py -A <AUTHCODE> audiobook.aax
```

#### Single MP3 file
```bash
./aaxtomp3.py -A <AUTHCODE> --single audiobook.aax
```

#### FLAC
```bash
./aaxtomp3.py -A <AUTHCODE> --flac audiobook.aax
```

#### Opus
```bash
./aaxtomp3.py -A <AUTHCODE> --opus audiobook.aax
```

#### M4A
```bash
./aaxtomp3.py -A <AUTHCODE> -e:m4a audiobook.aax
```

#### M4B (audiobook format)
```bash
./aaxtomp3.py -A <AUTHCODE> -e:m4b audiobook.aax
```

### Output Options

#### Custom output directory
```bash
./aaxtomp3.py -A <AUTHCODE> -t /path/to/output audiobook.aax
```

#### Move original files after conversion
```bash
./aaxtomp3.py -A <AUTHCODE> -C /path/to/completed audiobook.aax
```

#### Don't overwrite existing directories
```bash
./aaxtomp3.py -A <AUTHCODE> --no-clobber audiobook.aax
```

### Naming Schemes

#### Custom directory naming
```bash
./aaxtomp3.py -A <AUTHCODE> -D '$genre/$artist/$title' audiobook.aax
```

Available variables: `$genre`, `$artist`, `$title`

#### Custom file naming
```bash
./aaxtomp3.py -A <AUTHCODE> -F '$artist - $title' audiobook.aax
```

Available variables: `$title`, `$artist`

#### Custom chapter naming
```bash
./aaxtomp3.py -A <AUTHCODE> --chapter-naming-scheme '$title - Chapter $chapternum - $chapter' audiobook.aax
```

Available variables: `$title`, `$chapternum`, `$chapter`

### Quality Settings

Set compression level (codec-specific):
```bash
# MP3: 0 (best) to 9 (worst), default is based on codec
./aaxtomp3.py -A <AUTHCODE> --level 2 audiobook.aax

# FLAC: 0 (fast) to 8 (slow/best), default is 5
./aaxtomp3.py -A <AUTHCODE> --flac --level 8 audiobook.aax

# Opus: 0 (fast) to 10 (slow/best)
./aaxtomp3.py -A <AUTHCODE> --opus --level 10 audiobook.aax
```

### Metadata Options

#### Override author
```bash
./aaxtomp3.py -A <AUTHCODE> --author "New Author Name" audiobook.aax
```

#### Keep specific author from list
If the file has multiple authors (comma-separated), keep only the first:
```bash
./aaxtomp3.py -A <AUTHCODE> --keep-author 0 audiobook.aax
```

### Validation

Validate AAX files without converting:
```bash
./aaxtomp3.py -A <AUTHCODE> --validate audiobook.aax
```

### Logging

#### Progress only (quiet mode)
```bash
./aaxtomp3.py -A <AUTHCODE> --loglevel 0 audiobook.aax
```

#### Default logging
```bash
./aaxtomp3.py -A <AUTHCODE> audiobook.aax
```

#### Verbose logging
```bash
./aaxtomp3.py -A <AUTHCODE> --loglevel 2 audiobook.aax
```

#### Debug logging
```bash
./aaxtomp3.py -A <AUTHCODE> --debug audiobook.aax
# or
./aaxtomp3.py -A <AUTHCODE> --loglevel 3 audiobook.aax
```

### Advanced Options

#### Continue chapter splitting from specific chapter
```bash
./aaxtomp3.py -A <AUTHCODE> --continue 5 audiobook.aax
```

#### Custom ffmpeg path
```bash
./aaxtomp3.py -A <AUTHCODE> --ffmpeg-path /custom/path/to/ffmpeg audiobook.aax
```

#### Custom ffmpeg/ffprobe binary names
```bash
./aaxtomp3.py -A <AUTHCODE> --ffmpeg-name ffmpeg-custom --ffprobe-name ffprobe-custom audiobook.aax
```

## Complete Example

Convert an AAX file to chaptered MP3 with custom naming and move the original to a completed directory:

```bash
./aaxtomp3.py \
  -A 1234567890abcdef \
  --chaptered \
  -t ~/Audiobooks \
  -C ~/Audiobooks/Completed \
  -D '$genre/$artist/$title' \
  -F '$artist - $title' \
  --chapter-naming-scheme '$title-$chapternum $chapter' \
  --level 2 \
  --loglevel 2 \
  my_audiobook.aax
```

## Output Structure

### Chaptered Mode (default)
```
genre/
└── artist/
    └── title/
        ├── title-01 Chapter 1.mp3
        ├── title-02 Chapter 2.mp3
        ├── title-03 Chapter 3.mp3
        └── title.m3u
```

### Single File Mode
```
genre/
└── artist/
    └── title/
        └── title.mp3
```

For M4B files, an additional `.chapters.txt` file is created in the output directory. This file contains chapter markers and is used by `mp4chaps` to embed chapters in the M4B file. The file is intentionally kept for user reference.

## Differences from Original Bash Script

This Python port maintains feature parity with the original bash script while providing:

- Cross-platform compatibility
- More readable and maintainable code
- Better error handling
- Consistent behavior across different systems

Some advanced features from the original that are not yet implemented:
- `--use-audible-cli-data` flag
- `--audible-cli-library-file` flag for integration with audible-cli
- Full mediainfo integration for narrator, description, and publisher metadata

## License

This is a port of the original AAXtoMP3 script. Please refer to the original project for licensing information.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## Acknowledgments

- Original [AAXtoMP3](https://github.com/KrumpetPirate/AAXtoMP3) by KrumpetPirate
- FFmpeg team for the excellent media processing tools
