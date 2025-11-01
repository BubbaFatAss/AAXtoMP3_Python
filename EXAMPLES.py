#!/usr/bin/env python3
"""
Examples of using AAXtoMP3_Python

These examples demonstrate common use cases for the script.
"""

# Example 1: Basic conversion to MP3 (chaptered)
# ./aaxtomp3.py -A 1234abcd mybook.aax
#
# Output structure:
# Audiobook/
# └── Author Name/
#     └── Book Title/
#         ├── Book Title-01 Chapter 1.mp3
#         ├── Book Title-02 Chapter 2.mp3
#         ├── Book Title-03 Chapter 3.mp3
#         └── Book Title.m3u

# Example 2: Single MP3 file
# ./aaxtomp3.py -A 1234abcd --single mybook.aax
#
# Output structure:
# Audiobook/
# └── Author Name/
#     └── Book Title/
#         └── Book Title.mp3

# Example 3: Convert to M4B (audiobook format)
# ./aaxtomp3.py -A 1234abcd -e:m4b mybook.aax
#
# Output structure:
# Audiobook/
# └── Author Name/
#     └── Book Title/
#         └── Book Title.m4b

# Example 4: Convert to FLAC with high quality
# ./aaxtomp3.py -A 1234abcd --flac --level 8 mybook.aax
#
# Output structure:
# Audiobook/
# └── Author Name/
#     └── Book Title/
#         └── Book Title.flac

# Example 5: Custom output directory
# ./aaxtomp3.py -A 1234abcd -t ~/MyAudiobooks mybook.aax
#
# Output structure:
# ~/MyAudiobooks/
# └── Audiobook/
#     └── Author Name/
#         └── Book Title/
#             ├── Book Title-01 Chapter 1.mp3
#             └── ...

# Example 6: Custom naming scheme
# ./aaxtomp3.py -A 1234abcd \
#   -D '$artist/$title' \
#   -F '$artist - $title' \
#   --chapter-naming-scheme 'Chapter $chapternum - $chapter' \
#   mybook.aax
#
# Output structure:
# Author Name/
# └── Book Title/
#     ├── Chapter 01 - Introduction.mp3
#     ├── Chapter 02 - The Beginning.mp3
#     └── ...

# Example 7: Process multiple files
# ./aaxtomp3.py -A 1234abcd book1.aax book2.aax book3.aax

# Example 8: Validate files without converting
# ./aaxtomp3.py -A 1234abcd --validate mybook.aax

# Example 9: AAXC file (no authcode needed)
# ./aaxtomp3.py mybook.aaxc
# 
# Note: Requires mybook.voucher in the same directory

# Example 10: Complete workflow with organization
# ./aaxtomp3.py -A 1234abcd \
#   -t ~/Audiobooks \
#   -C ~/Audiobooks/Completed \
#   --chaptered \
#   --level 2 \
#   --loglevel 2 \
#   ~/Downloads/*.aax
#
# This will:
# - Convert all AAX files in Downloads
# - Put output in ~/Audiobooks
# - Move original AAX files to ~/Audiobooks/Completed
# - Create chaptered output
# - Use quality level 2
# - Show verbose logging

# Example 11: Handle multi-author books
# ./aaxtomp3.py -A 1234abcd --keep-author 0 mybook.aax
# 
# If the book has authors "John Doe, Jane Smith", this keeps only "John Doe"

# Example 12: Override author metadata
# ./aaxtomp3.py -A 1234abcd --author "Preferred Author Name" mybook.aax

# Example 13: Continue chapter splitting from chapter 5
# ./aaxtomp3.py -A 1234abcd --continue 5 mybook.aax
#
# Useful if the conversion failed partway through

# Example 14: Batch conversion with custom ffmpeg
# ./aaxtomp3.py -A 1234abcd \
#   --ffmpeg-path /usr/local/bin \
#   --ffmpeg-name ffmpeg-custom \
#   *.aax

# Example 15: Debug mode for troubleshooting
# ./aaxtomp3.py -A 1234abcd --debug mybook.aax
