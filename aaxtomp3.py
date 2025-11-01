#!/usr/bin/env python3
"""
AAXtoMP3 - Convert Audible AAX/AAXC files to various audio formats
Python port of https://github.com/KrumpetPirate/AAXtoMP3
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class AAXConverter:
    """Main class for converting AAX/AAXC files to various audio formats."""

    def __init__(self, args):
        """Initialize the converter with command-line arguments."""
        self.args = args
        self.setup_logging()
        self.setup_codec()
        self.validate_dependencies()

    def setup_logging(self):
        """Configure logging based on log level."""
        levels = {
            0: logging.WARNING,
            1: logging.INFO,
            2: logging.INFO,
            3: logging.DEBUG
        }
        level = levels.get(self.args.loglevel, logging.INFO)
        
        if self.args.loglevel > 1:
            log_format = '%(asctime)s %(levelname)s %(message)s'
            date_format = '%Y-%m-%d %H:%M:%S%z'
        else:
            log_format = '%(message)s'
            date_format = None
            
        logging.basicConfig(level=level, format=log_format, datefmt=date_format)
        self.logger = logging.getLogger(__name__)

    def setup_codec(self):
        """Set up codec, extension, mode, and container based on arguments."""
        # Handle codec-specific arguments
        if self.args.flac:
            self.codec = 'flac'
            self.extension = 'flac'
            self.mode = 'single'
            self.container = 'flac'
        elif self.args.opus:
            self.codec = 'libopus'
            self.extension = 'opus'
            self.mode = self.args.mode
            self.container = 'ogg'
        elif self.args.aac or self.args.e_m4a:
            self.codec = 'copy'
            self.extension = 'm4a'
            self.mode = 'single'
            self.container = 'mp4'
        elif self.args.e_m4b:
            self.codec = 'copy'
            self.extension = 'm4b'
            self.mode = 'single'
            self.container = 'mp4'
        elif self.args.e_mp3:
            self.codec = 'libmp3lame'
            self.extension = 'mp3'
            self.mode = 'single'
            self.container = 'mp3'
        else:
            # Default to mp3
            self.codec = 'libmp3lame'
            self.extension = 'mp3'
            self.mode = self.args.mode
            self.container = 'mp3'

    def validate_dependencies(self):
        """Validate that required external tools are available."""
        # Check for ffmpeg
        self.ffmpeg = self.args.ffmpeg_name
        if self.args.ffmpeg_path:
            self.ffmpeg = os.path.join(self.args.ffmpeg_path, self.args.ffmpeg_name)
        
        if not shutil.which(self.ffmpeg):
            self.logger.error(f"ERROR: {self.ffmpeg} was not found on your PATH")
            self.logger.error("Installation instructions:")
            self.logger.error("  MacOS:   brew install ffmpeg")
            self.logger.error("  Ubuntu:  sudo apt-get update; sudo apt-get install ffmpeg")
            self.logger.error("  RHEL:    yum install ffmpeg")
            sys.exit(1)

        # Check for ffprobe
        self.ffprobe = self.args.ffprobe_name
        if self.args.ffmpeg_path:
            self.ffprobe = os.path.join(self.args.ffmpeg_path, self.args.ffprobe_name)
        
        if not shutil.which(self.ffprobe):
            self.logger.error(f"ERROR: {self.ffprobe} was not found on your PATH")
            self.logger.error("Installation instructions:")
            self.logger.error("  MacOS:   brew install ffmpeg")
            self.logger.error("  Ubuntu:  sudo apt-get update; sudo apt-get install ffmpeg")
            sys.exit(1)

        # Check for optional tools
        if self.container == 'mp4':
            if not shutil.which('mp4art'):
                self.logger.warning("WARN: mp4art was not found on your PATH")
                self.logger.warning("  MacOS:   brew install mp4v2")
                self.logger.warning("  Ubuntu:  sudo apt-get install mp4v2-utils")
            
            if not shutil.which('mp4chaps'):
                self.logger.warning("WARN: mp4chaps was not found on your PATH")
                self.logger.warning("  MacOS:   brew install mp4v2")
                self.logger.warning("  Ubuntu:  sudo apt-get install mp4v2-utils")

        # Check for mediainfo (optional)
        self.has_mediainfo = shutil.which('mediainfo') is not None

    def validate_aax_file(self, aax_file: str, decrypt_param: List[str]) -> bool:
        """Validate an AAX/AAXC file."""
        # Test for existence
        if not os.path.isfile(aax_file):
            self.logger.error(f"ERROR: File NOT Found: {aax_file}")
            return False
        
        if self.args.validate:
            self.logger.info(f"Test 1 SUCCESS: {aax_file}")

        # Test with ffprobe
        try:
            cmd = [self.ffprobe, '-loglevel', 'warning'] + decrypt_param + ['-i', aax_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"ERROR: Invalid File: {aax_file}")
                self.logger.debug(result.stderr)
                return False
            elif self.args.validate:
                self.logger.info(f"Test 2 SUCCESS: {aax_file}")
        except Exception as e:
            self.logger.error(f"ERROR: Failed to validate {aax_file}: {e}")
            return False

        # Extended validation if --validate flag is set
        if self.args.validate:
            try:
                cmd = [self.ffmpeg, '-hide_banner'] + decrypt_param + [
                    '-i', aax_file, '-vn', '-f', 'null', '-'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.logger.error(f"ERROR: Invalid File: {aax_file}")
                    self.logger.debug(result.stderr)
                    return False
                else:
                    self.logger.info(f"Test 3 SUCCESS: {aax_file}")
            except Exception as e:
                self.logger.error(f"ERROR: Failed extended validation: {e}")
                return False

        return True

    def get_metadata(self, aax_file: str, decrypt_param: List[str]) -> Dict[str, str]:
        """Extract metadata from AAX/AAXC file."""
        metadata = {}
        
        # Get metadata from ffprobe
        try:
            cmd = [self.ffprobe] + decrypt_param + ['-i', aax_file]
            result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
            
            # Parse ffprobe output
            output = result.stdout
            
            # Extract metadata fields
            patterns = {
                'title': r'title\s*:\s*(.+)',
                'artist': r'artist\s*:\s*(.+)',
                'album': r'album\s*:\s*(.+)',
                'album_artist': r'album_artist\s*:\s*(.+)',
                'date': r'date\s*:\s*(.+)',
                'genre': r'genre\s*:\s*(.+)',
                'copyright': r'copyright\s*:\s*(.+)',
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    metadata[key] = match.group(1).strip()
                else:
                    metadata[key] = ''

            # Try to get bitrate
            bitrate_match = re.search(r'bitrate:\s*(\d+)\s*kb/s', output, re.IGNORECASE)
            if bitrate_match:
                metadata['bitrate'] = bitrate_match.group(1)
            else:
                metadata['bitrate'] = '64'

        except Exception as e:
            self.logger.error(f"ERROR: Failed to extract metadata: {e}")
            return {}

        # Get additional metadata from mediainfo if available
        if self.has_mediainfo:
            try:
                cmd = ['mediainfo', aax_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                output = result.stdout
                
                # Extract narrator, publisher, description
                narrator_match = re.search(r'Narrator\s*:\s*(.+)', output)
                if narrator_match:
                    metadata['narrator'] = narrator_match.group(1).strip()
                
                publisher_match = re.search(r'Publisher\s*:\s*(.+)', output)
                if publisher_match:
                    metadata['publisher'] = publisher_match.group(1).strip()
                    
            except Exception as e:
                self.logger.debug(f"mediainfo extraction failed: {e}")

        return metadata

    def get_cover_art(self, aax_file: str, decrypt_param: List[str], output_dir: str) -> Optional[str]:
        """Extract cover art from AAX/AAXC file."""
        cover_file = os.path.join(output_dir, 'cover.jpg')
        
        try:
            cmd = [self.ffmpeg, '-loglevel', 'error'] + decrypt_param + [
                '-i', aax_file, '-an', '-vcodec', 'copy', cover_file
            ]
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0 and os.path.isfile(cover_file):
                return cover_file
        except Exception as e:
            self.logger.debug(f"Failed to extract cover art: {e}")
        
        return None

    def get_chapters(self, aax_file: str, decrypt_param: List[str]) -> List[Dict[str, str]]:
        """Extract chapter information from AAX/AAXC file."""
        chapters = []
        
        try:
            cmd = [self.ffprobe, '-i', aax_file, '-print_format', 'json',
                   '-show_chapters', '-loglevel', 'error'] + decrypt_param
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'chapters' in data:
                    for i, chapter in enumerate(data['chapters']):
                        chapters.append({
                            'num': i + 1,
                            'start': float(chapter.get('start_time', 0)),
                            'end': float(chapter.get('end_time', 0)),
                            'title': chapter.get('tags', {}).get('title', f'Chapter {i + 1}')
                        })
        except Exception as e:
            self.logger.debug(f"Failed to extract chapters: {e}")
        
        return chapters

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename by removing invalid characters."""
        # Remove or replace characters that are invalid in filenames
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        # Limit length
        return filename[:255]

    def get_output_directory(self, metadata: Dict[str, str]) -> str:
        """Determine the output directory based on naming scheme."""
        if self.args.dir_naming_scheme:
            # Custom directory naming scheme
            scheme = self.args.dir_naming_scheme
            scheme = scheme.replace('$genre', metadata.get('genre', 'Unknown'))
            scheme = scheme.replace('$artist', metadata.get('artist', 'Unknown'))
            scheme = scheme.replace('$title', metadata.get('title', 'Unknown'))
            dir_name = scheme
        else:
            # Default: genre/artist/title
            genre = metadata.get('genre', 'Unknown')
            artist = metadata.get('artist', 'Unknown')
            title = metadata.get('title', 'Unknown')
            dir_name = os.path.join(genre, artist, title)

        # Sanitize each path component
        parts = dir_name.split(os.sep)
        sanitized_parts = [self.sanitize_filename(part) for part in parts]
        dir_name = os.path.join(*sanitized_parts)

        if self.args.target_dir:
            return os.path.join(self.args.target_dir, dir_name)
        else:
            # Use the directory of the AAX file
            return dir_name

    def get_output_filename(self, metadata: Dict[str, str]) -> str:
        """Determine the output filename based on naming scheme."""
        if self.args.file_naming_scheme:
            # Custom file naming scheme
            scheme = self.args.file_naming_scheme
            scheme = scheme.replace('$title', metadata.get('title', 'Unknown'))
            scheme = scheme.replace('$artist', metadata.get('artist', 'Unknown'))
            filename = scheme
        else:
            # Default: title
            filename = metadata.get('title', 'Unknown')

        return self.sanitize_filename(filename)

    def get_chapter_filename(self, metadata: Dict[str, str], chapter_num: int, 
                            chapter_title: str, total_chapters: int) -> str:
        """Determine the chapter filename based on naming scheme."""
        title = metadata.get('title', 'Unknown')
        
        if self.args.chapter_naming_scheme:
            # Custom chapter naming scheme
            scheme = self.args.chapter_naming_scheme
            scheme = scheme.replace('$title', title)
            scheme = scheme.replace('$chapter', chapter_title)
            # Handle chapter number formatting
            num_width = len(str(total_chapters))
            chapter_num_str = str(chapter_num).zfill(num_width)
            scheme = scheme.replace('$chapternum', chapter_num_str)
            filename = scheme
        else:
            # Default: Title-01 Chapter Name
            num_width = len(str(total_chapters))
            chapter_num_str = str(chapter_num).zfill(num_width)
            filename = f"{title}-{chapter_num_str} {chapter_title}"

        return self.sanitize_filename(filename)

    def transcode_file(self, aax_file: str, output_file: str, decrypt_param: List[str],
                       metadata: Dict[str, str], cover_file: Optional[str] = None) -> bool:
        """Transcode AAX/AAXC file to output format."""
        self.logger.info(f"Transcoding {os.path.basename(aax_file)} to {self.extension}")
        
        # Build ffmpeg command
        cmd = [self.ffmpeg, '-nostats', '-loglevel', 'error'] + decrypt_param + [
            '-i', aax_file
        ]

        # Add codec and quality settings
        if self.codec == 'copy':
            cmd.extend(['-c:a', 'copy'])
        else:
            cmd.extend(['-c:a', self.codec])
            if self.args.level > -1:
                if self.codec == 'libmp3lame':
                    cmd.extend(['-q:a', str(self.args.level)])
                elif self.codec == 'flac':
                    cmd.extend(['-compression_level', str(self.args.level)])
                elif self.codec == 'libopus':
                    cmd.extend(['-compression_level', str(self.args.level)])

        # Add metadata
        if metadata.get('title'):
            cmd.extend(['-metadata', f"title={metadata['title']}"])
        if metadata.get('artist'):
            cmd.extend(['-metadata', f"artist={metadata['artist']}"])
        if metadata.get('album'):
            cmd.extend(['-metadata', f"album={metadata['album']}"])
        if metadata.get('album_artist'):
            cmd.extend(['-metadata', f"album_artist={metadata['album_artist']}"])
        if metadata.get('date'):
            cmd.extend(['-metadata', f"date={metadata['date']}"])
        if metadata.get('genre'):
            cmd.extend(['-metadata', f"genre={metadata['genre']}"])
        if metadata.get('copyright'):
            cmd.extend(['-metadata', f"copyright={metadata['copyright']}"])

        # Set container format
        cmd.extend(['-f', self.container])
        
        # Output file
        cmd.append(output_file)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"ERROR: Transcoding failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"ERROR: Transcoding failed: {e}")
            return False

        # Add cover art if available
        if cover_file and os.path.isfile(cover_file):
            self.add_cover_art(output_file, cover_file)

        return True

    def add_cover_art(self, audio_file: str, cover_file: str):
        """Add cover art to the output file."""
        self.logger.info("Adding cover art")
        
        if self.container == 'mp4':
            # Use mp4art for mp4 containers
            if shutil.which('mp4art'):
                try:
                    cmd = ['mp4art', '--add', cover_file, audio_file]
                    subprocess.run(cmd, capture_output=True, check=True)
                except Exception as e:
                    self.logger.debug(f"Failed to add cover art with mp4art: {e}")
        else:
            # Use ffmpeg for other containers
            temp_file = audio_file + '.tmp'
            try:
                cmd = [
                    self.ffmpeg, '-loglevel', 'error', '-nostats',
                    '-i', audio_file, '-i', cover_file,
                    '-map', '0:a:0', '-map', '1:v:0',
                    '-c:a', 'copy', '-c:v', 'copy',
                    '-id3v2_version', '3',
                    '-metadata:s:v', 'title=Album cover',
                    '-metadata:s:v', 'comment=Cover (front)',
                    temp_file
                ]
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode == 0:
                    shutil.move(temp_file, audio_file)
            except Exception as e:
                self.logger.debug(f"Failed to add cover art with ffmpeg: {e}")
                if os.path.isfile(temp_file):
                    os.remove(temp_file)

    def split_chapters(self, aax_file: str, output_dir: str, decrypt_param: List[str],
                      metadata: Dict[str, str], chapters: List[Dict[str, str]],
                      cover_file: Optional[str] = None):
        """Split AAX/AAXC file into chapters."""
        total_chapters = len(chapters)
        self.logger.info(f"Splitting into {total_chapters} chapters")

        # Create playlist file
        playlist_file = os.path.join(output_dir, f"{metadata.get('title', 'audiobook')}.m3u")
        
        with open(playlist_file, 'w', encoding='utf-8') as pf:
            pf.write("#EXTM3U\n")
            
            for chapter in chapters:
                chapter_num = chapter['num']
                
                # Skip chapters if continue option is used
                if self.args.continue_at > 0 and chapter_num < self.args.continue_at:
                    continue

                chapter_title = chapter['title']
                start_time = chapter['start']
                end_time = chapter['end']
                duration = end_time - start_time

                # Get chapter filename
                chapter_filename = self.get_chapter_filename(
                    metadata, chapter_num, chapter_title, total_chapters
                )
                chapter_file = os.path.join(output_dir, f"{chapter_filename}.{self.extension}")

                # Show progress
                if self.args.loglevel < 2:
                    self.show_progress(chapter_num, total_chapters)

                # Build ffmpeg command for chapter extraction
                cmd = [self.ffmpeg, '-nostats', '-loglevel', 'error'] + decrypt_param + [
                    '-i', aax_file, '-ss', str(start_time), '-to', str(end_time)
                ]

                # Add codec settings
                if self.codec == 'copy':
                    cmd.extend(['-c:a', 'copy'])
                else:
                    cmd.extend(['-c:a', self.codec])
                    if self.args.level > -1:
                        if self.codec == 'libmp3lame':
                            cmd.extend(['-q:a', str(self.args.level)])
                        elif self.codec == 'flac':
                            cmd.extend(['-compression_level', str(self.args.level)])
                        elif self.codec == 'libopus':
                            cmd.extend(['-compression_level', str(self.args.level)])

                # Add metadata
                cmd.extend([
                    '-metadata', f"title={chapter_title}",
                    '-metadata', f"track={chapter_num}",
                ])
                if metadata.get('artist'):
                    cmd.extend(['-metadata', f"artist={metadata['artist']}"])
                if metadata.get('album'):
                    cmd.extend(['-metadata', f"album={metadata['album']}"])

                # Add cover art if available
                if cover_file and os.path.isfile(cover_file):
                    cmd.extend(['-i', cover_file, '-map', '0:0', '-map', '1:0',
                               '-metadata:s:v', 'title=Album cover',
                               '-metadata:s:v', 'comment=Cover (front)'])

                # Remove chapter metadata
                cmd.extend(['-map_chapters', '-1'])

                # Set container format
                cmd.extend(['-f', self.container, chapter_file])

                try:
                    result = subprocess.run(cmd, capture_output=True)
                    if result.returncode != 0:
                        self.logger.error(f"Failed to create chapter {chapter_num}")
                        continue
                except Exception as e:
                    self.logger.error(f"Failed to create chapter {chapter_num}: {e}")
                    continue

                # Add to playlist
                pf.write(f"#EXTINF:{int(duration)},{metadata.get('title', 'Unknown')} - {chapter_title}\n")
                pf.write(f"{chapter_filename}.{self.extension}\n")

        if self.args.loglevel < 2:
            print()  # End progress bar

    def show_progress(self, current: int, total: int):
        """Display a progress bar."""
        percentage = (current * 100) // total
        bar_length = 20
        filled = (current * bar_length) // total
        bar = '#' * filled + ' ' * (bar_length - filled)
        print(f'\rprocess: |{bar}| {percentage:3d}% ({current}/{total})', end='', flush=True)

    def process_file(self, aax_file: str):
        """Process a single AAX/AAXC file."""
        # Determine if file is AAXC
        is_aaxc = aax_file.lower().endswith('.aaxc')
        
        # Set up decryption parameters
        decrypt_param = []
        
        if is_aaxc:
            # For AAXC files, we need the voucher file
            voucher_file = os.path.splitext(aax_file)[0] + '.voucher'
            if not os.path.isfile(voucher_file):
                self.logger.error(f"ERROR: Voucher file not found: {voucher_file}")
                return
            
            try:
                with open(voucher_file, 'r') as f:
                    voucher_data = json.load(f)
                    key = voucher_data['content_license']['license_response']['key']
                    iv = voucher_data['content_license']['license_response']['iv']
                    decrypt_param = ['-audible_key', key, '-audible_iv', iv]
            except Exception as e:
                self.logger.error(f"ERROR: Failed to read voucher file: {e}")
                return
        else:
            # For AAX files, we need the activation bytes
            if not self.args.authcode:
                self.logger.error(f"ERROR: Missing authcode for {aax_file}")
                return
            decrypt_param = ['-activation_bytes', self.args.authcode]

        # Validate the file
        if not self.validate_aax_file(aax_file, decrypt_param):
            return
        
        if self.args.validate:
            # If only validating, we're done
            return

        # Extract metadata
        metadata = self.get_metadata(aax_file, decrypt_param)
        if not metadata:
            self.logger.error("ERROR: Failed to extract metadata")
            return

        # Handle author override
        if self.args.author:
            metadata['artist'] = self.args.author
            metadata['album_artist'] = self.args.author
        elif self.args.keep_author > -1:
            # Keep only specified author from comma-separated list
            artists = metadata.get('artist', '').split(',')
            if self.args.keep_author < len(artists):
                author = artists[self.args.keep_author].strip()
                # Remove extra spaces from initials like "C. S. Lewis" -> "C.S. Lewis"
                author = re.sub(r'\.\s+', '.', author)
                metadata['artist'] = author
                metadata['album_artist'] = author

        # Limit title length
        if metadata.get('title'):
            metadata['title'] = metadata['title'][:128]

        # Determine output directory
        output_dir = self.get_output_directory(metadata)
        
        # Check for existing directory
        if os.path.isdir(output_dir) and self.args.no_clobber:
            self.logger.info(f"Skipping {aax_file} - output directory exists")
            return

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Extract cover art
        cover_file = self.get_cover_art(aax_file, decrypt_param, output_dir)

        # Get output filename
        output_filename = self.get_output_filename(metadata)

        if self.mode == 'chaptered':
            # Extract chapters
            chapters = self.get_chapters(aax_file, decrypt_param)
            
            if chapters:
                # First transcode the whole file (needed for chapter splitting)
                temp_file = os.path.join(output_dir, f"temp.{self.extension}")
                if self.transcode_file(aax_file, temp_file, decrypt_param, metadata):
                    # Split into chapters
                    self.split_chapters(aax_file, output_dir, decrypt_param, 
                                      metadata, chapters, cover_file)
                    # Remove temp file
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                else:
                    self.logger.error("ERROR: Failed to transcode file")
                    return
            else:
                self.logger.warning("No chapters found, creating single file")
                self.mode = 'single'

        if self.mode == 'single':
            # Create single output file
            output_file = os.path.join(output_dir, f"{output_filename}.{self.extension}")
            if not self.transcode_file(aax_file, output_file, decrypt_param, metadata, cover_file):
                self.logger.error("ERROR: Failed to transcode file")
                return

            # Add chapters to m4b file if available
            if self.container == 'mp4' and shutil.which('mp4chaps'):
                chapters = self.get_chapters(aax_file, decrypt_param)
                if chapters:
                    # Create chapters file for mp4chaps
                    chapters_file = os.path.join(output_dir, f"{output_filename}.chapters.txt")
                    with open(chapters_file, 'w', encoding='utf-8') as cf:
                        for chapter in chapters:
                            start_time = chapter['start']
                            hours = int(start_time // 3600)
                            minutes = int((start_time % 3600) // 60)
                            seconds = start_time % 60
                            cf.write(f"CHAPTER{chapter['num']:02d}={hours:02d}:{minutes:02d}:{seconds:06.3f}\n")
                            cf.write(f"CHAPTER{chapter['num']:02d}NAME={chapter['title']}\n")
                    
                    try:
                        subprocess.run(['mp4chaps', '-i', output_file], capture_output=True)
                    except Exception as e:
                        self.logger.debug(f"Failed to add chapters: {e}")

        # Clean up cover file
        if cover_file and os.path.isfile(cover_file):
            os.remove(cover_file)

        self.logger.info(f"Complete {metadata.get('title', 'Unknown')}")

        # Move original file if complete_dir is set
        if self.args.complete_dir:
            self.logger.info(f"Moving {aax_file} to {self.args.complete_dir}")
            os.makedirs(self.args.complete_dir, exist_ok=True)
            shutil.move(aax_file, self.args.complete_dir)

    def run(self):
        """Run the converter on all input files."""
        for aax_file in self.args.files:
            self.process_file(aax_file)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert Audible AAX/AAXC files to various audio formats',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Codec options
    codec_group = parser.add_argument_group('codec options')
    codec_group.add_argument('-f', '--flac', action='store_true',
                            help='Encode to FLAC format')
    codec_group.add_argument('-o', '--opus', action='store_true',
                            help='Encode to Opus format')
    codec_group.add_argument('-a', '--aac', action='store_true',
                            help='Encode to AAC format (M4A)')
    codec_group.add_argument('-e:mp3', dest='e_mp3', action='store_true',
                            help='Encode to MP3 format (single file)')
    codec_group.add_argument('-e:m4a', dest='e_m4a', action='store_true',
                            help='Encode to M4A format')
    codec_group.add_argument('-e:m4b', dest='e_m4b', action='store_true',
                            help='Encode to M4B format (audiobook)')
    
    # Mode options
    mode_group = parser.add_argument_group('mode options')
    mode_group.add_argument('-s', '--single', dest='mode', action='store_const',
                           const='single', default='chaptered',
                           help='Create a single output file')
    mode_group.add_argument('-c', '--chaptered', dest='mode', action='store_const',
                           const='chaptered',
                           help='Create a separate file for each chapter (default)')
    
    # Quality options
    quality_group = parser.add_argument_group('quality options')
    quality_group.add_argument('--level', type=int, default=-1,
                              help='Compression level (codec-specific)')
    
    # Output options
    output_group = parser.add_argument_group('output options')
    output_group.add_argument('-t', '--target_dir', metavar='PATH',
                             help='Target directory for output files')
    output_group.add_argument('-C', '--complete_dir', metavar='PATH',
                             help='Directory to move AAX files after completion')
    output_group.add_argument('-D', '--dir-naming-scheme', metavar='SCHEME',
                             help='Custom directory naming scheme')
    output_group.add_argument('-F', '--file-naming-scheme', metavar='SCHEME',
                             help='Custom file naming scheme')
    output_group.add_argument('--chapter-naming-scheme', metavar='SCHEME',
                             help='Custom chapter naming scheme')
    output_group.add_argument('-n', '--no-clobber', action='store_true',
                             help='Do not overwrite existing directories')
    
    # Authentication options
    auth_group = parser.add_argument_group('authentication options')
    auth_group.add_argument('-A', '--authcode', metavar='CODE',
                           help='Activation bytes for AAX files')
    
    # Metadata options
    metadata_group = parser.add_argument_group('metadata options')
    metadata_group.add_argument('--keep-author', type=int, default=-1, metavar='N',
                               help='Keep author number N from comma-separated list')
    metadata_group.add_argument('--author', metavar='AUTHOR',
                               help='Override author metadata')
    
    # Validation options
    validation_group = parser.add_argument_group('validation options')
    validation_group.add_argument('-V', '--validate', action='store_true',
                                 help='Validate AAX files only (no transcoding)')
    
    # Logging options
    logging_group = parser.add_argument_group('logging options')
    logging_group.add_argument('-l', '--loglevel', type=int, default=1, choices=[0, 1, 2, 3],
                              help='Log level (0=progress only, 1=default, 2=verbose, 3=debug)')
    logging_group.add_argument('-d', '--debug', action='store_const', const=3, dest='loglevel',
                              help='Enable debug logging')
    
    # Advanced options
    advanced_group = parser.add_argument_group('advanced options')
    advanced_group.add_argument('--continue', type=int, default=0, dest='continue_at',
                               metavar='CHAPTER',
                               help='Continue chapter splitting from chapter N')
    advanced_group.add_argument('--ffmpeg-path', metavar='PATH',
                               help='Path to ffmpeg/ffprobe binaries')
    advanced_group.add_argument('--ffmpeg-name', default='ffmpeg',
                               help='Custom ffmpeg binary name')
    advanced_group.add_argument('--ffprobe-name', default='ffprobe',
                               help='Custom ffprobe binary name')
    
    # Files
    parser.add_argument('files', nargs='+', metavar='FILE',
                       help='AAX/AAXC files to convert')
    
    args = parser.parse_args()
    
    # Create converter and run
    converter = AAXConverter(args)
    converter.run()


if __name__ == '__main__':
    main()
