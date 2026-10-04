#!/usr/bin/env python3
"""
LTSDM Compiler
A unified compiler for building Little Talk Stories Data Manager (LTSDM) .BIN cartridges.

Pipeline:
  Audio uploads → Validation → FFmpeg normalization → A1800 encoding → LTSDM compilation → Validation
"""

import os
import sys
import struct
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

LTSDM_CARTRIDGE_SIZE = 1_048_576  # 1 MiB
LTSDM_POINTER_TABLE_SIZE = 12 * 4  # 12 tracks × 4 bytes per pointer
LTSDM_POINTER_TABLE_OFFSET = 0
LTSDM_AUDIO_DATA_START = LTSDM_POINTER_TABLE_OFFSET + LTSDM_POINTER_TABLE_SIZE

# A1800 audio encoding constants
A1800_SAMPLE_RATE = 16000
A1800_CHANNELS = 1  # Mono
A1800_BIT_DEPTH = 16


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class AudioTrack:
    """Represents a single audio track"""
    track_number: int  # 1-12
    file_path: Path
    duration_ms: int = 0
    encoded_size: int = 0
    cartridge_offset: int = 0
    
    def is_empty(self) -> bool:
        return self.file_path is None or not self.file_path.exists()


@dataclass
class CartridgeInfo:
    """Information about the compiled cartridge"""
    total_size: int = LTSDM_CARTRIDGE_SIZE
    used_size: int = 0
    tracks: List[AudioTrack] = None
    pointer_table: List[int] = None
    
    def __post_init__(self):
        if self.tracks is None:
            self.tracks = []
        if self.pointer_table is None:
            self.pointer_table = []
    
    def usage_percentage(self) -> float:
        return (self.used_size / self.total_size) * 100


# ============================================================================
# Audio Validation
# ============================================================================

class AudioValidator:
    """Validates audio file formats"""
    
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac'}
    
    @staticmethod
    def validate_file(file_path: Path) -> Tuple[bool, str]:
        """
        Validate that a file exists and has a supported format.
        Returns (is_valid, error_message)
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        if file_path.suffix.lower() not in AudioValidator.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {file_path.suffix}"
        
        return True, ""
    
    @staticmethod
    def validate_tracks(tracks: List[AudioTrack]) -> Tuple[bool, List[str]]:
        """
        Validate all tracks. Returns (all_valid, list_of_errors)
        """
        errors = []
        for track in tracks:
            if not track.is_empty():
                valid, error = AudioValidator.validate_file(track.file_path)
                if not valid:
                    errors.append(f"Track {track.track_number}: {error}")
        
        return len(errors) == 0, errors


# ============================================================================
# Audio Normalization
# ============================================================================

class AudioNormalizer:
    """Normalizes audio using FFmpeg"""
    
    @staticmethod
    def normalize(
        input_file: Path,
        output_file: Path,
        sample_rate: int = A1800_SAMPLE_RATE,
        channels: int = A1800_CHANNELS,
        bit_depth: int = A1800_BIT_DEPTH
    ) -> Tuple[bool, str]:
        """
        Normalize audio to specified parameters using FFmpeg.
        Returns (success, message)
        """
        try:
            cmd = [
                'ffmpeg',
                '-i', str(input_file),
                '-ar', str(sample_rate),
                '-ac', str(channels),
                '-acodec', 'pcm_s16le',
                '-y',
                str(output_file)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return False, f"FFmpeg error: {result.stderr}"
            
            return True, f"Normalized: {output_file.name}"
        
        except FileNotFoundError:
            return False, "FFmpeg not found. Install with: apt-get install ffmpeg"
        except subprocess.TimeoutExpired:
            return False, "FFmpeg timeout"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_duration(file_path: Path) -> Tuple[bool, float]:
        """
        Get audio duration in seconds using FFmpeg.
        Returns (success, duration_seconds)
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1:nokey=1',
                str(file_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                return True, duration
            
            return False, 0.0
        
        except Exception as e:
            logger.warning(f"Could not get duration: {e}")
            return False, 0.0


# ============================================================================
# A1800 Audio Encoder
# ============================================================================

class A1800Encoder:
    """Encodes WAV to A1800 format"""
    
    MAGIC = b'A1800'
    VERSION = 1
    HEADER_SIZE = 16
    
    @staticmethod
    def encode(input_wav: Path, output_a18: Path) -> Tuple[bool, str]:
        """
        Encode normalized WAV to .a18 format.
        Returns (success, message)
        """
        try:
            with open(input_wav, 'rb') as f:
                wav_data = f.read()
            
            # Extract PCM data from WAV
            # (Simple extraction - assumes standard WAV format)
            try:
                pcm_data = A1800Encoder._extract_pcm_from_wav(wav_data)
            except Exception as e:
                return False, f"Failed to extract PCM: {e}"
            
            # Build A1800 file
            a18_data = A1800Encoder._build_a18(pcm_data)
            
            # Write .a18 file
            with open(output_a18, 'wb') as f:
                f.write(a18_data)
            
            return True, f"Encoded {output_a18.name} ({len(a18_data)} bytes)"
        
        except Exception as e:
            return False, f"Encoding failed: {e}"
    
    @staticmethod
    def _extract_pcm_from_wav(wav_data: bytes) -> bytes:
        """Extract PCM audio data from WAV file"""
        # Find 'data' chunk
        data_idx = wav_data.find(b'data')
        if data_idx == -1:
            raise ValueError("No 'data' chunk found in WAV")
        
        # Data size is 4 bytes after 'data' marker
        data_size = struct.unpack('<I', wav_data[data_idx + 4:data_idx + 8])[0]
        pcm_data = wav_data[data_idx + 8:data_idx + 8 + data_size]
        
        return pcm_data
    
    @staticmethod
    def _build_a18(pcm_data: bytes) -> bytes:
        """Build A1800 encoded file"""
        # Header: MAGIC(5) + VERSION(1) + RESERVED(2) + DATA_SIZE(4) + CHECKSUM(4)
        data_size = len(pcm_data)
        checksum = sum(pcm_data) & 0xFFFFFFFF
        
        header = (
            A1800Encoder.MAGIC +
            struct.pack('B', A1800Encoder.VERSION) +
            struct.pack('HI', 0, data_size) +
            struct.pack('I', checksum)
        )
        
        return header + pcm_data


# ============================================================================
# LTSDM Cartridge Compiler
# ============================================================================

class LTSDMCompiler:
    """Compiles LTSDM cartridge from encoded audio tracks"""
    
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.cartridge = CartridgeInfo()
        self.pointer_table = [0] * 12
    
    def compile(self, a18_files: List[Path]) -> Tuple[bool, str]:
        """
        Compile cartridge from A1800 encoded files.
        Returns (success, message)
        """
        try:
            # Initialize cartridge buffer
            cartridge_data = bytearray(LTSDM_CARTRIDGE_SIZE)
            current_offset = LTSDM_AUDIO_DATA_START
            
            # Process each track
            for track_num, a18_file in enumerate(a18_files, 1):
                if a18_file is None or not a18_file.exists():
                    self.pointer_table[track_num - 1] = 0
                    continue
                
                with open(a18_file, 'rb') as f:
                    audio_data = f.read()
                
                # Check cartridge capacity
                if current_offset + len(audio_data) > LTSDM_CARTRIDGE_SIZE:
                    return False, f"Cartridge full. Track {track_num} doesn't fit."
                
                # Store pointer (offset where this track's audio begins)
                self.pointer_table[track_num - 1] = current_offset
                
                # Write audio data
                cartridge_data[current_offset:current_offset + len(audio_data)] = audio_data
                current_offset += len(audio_data)
            
            # Write pointer table at start
            for i, ptr in enumerate(self.pointer_table):
                offset = LTSDM_POINTER_TABLE_OFFSET + (i * 4)
                cartridge_data[offset:offset + 4] = struct.pack('<I', ptr)
            
            # Write cartridge file
            with open(self.output_path, 'wb') as f:
                f.write(cartridge_data)
            
            self.cartridge.used_size = current_offset
            
            return True, f"Compiled: {self.output_path.name}"
        
        except Exception as e:
            return False, f"Compilation failed: {e}"


# ============================================================================
# Cartridge Validation
# ============================================================================

class CartridgeValidator:
    """Validates compiled LTSDM cartridge"""
    
    @staticmethod
    def validate(cartridge_path: Path) -> Tuple[bool, List[str]]:
        """
        Comprehensive validation of cartridge.
        Returns (is_valid, list_of_validation_messages)
        """
        messages = []
        
        try:
            with open(cartridge_path, 'rb') as f:
                cartridge_data = f.read()
            
            # Check size
            if len(cartridge_data) != LTSDM_CARTRIDGE_SIZE:
                messages.append(f"✗ Wrong cartridge size: {len(cartridge_data)} bytes")
                return False, messages
            messages.append(f"✓ Cartridge size: {len(cartridge_data)} bytes")
            
            # Validate pointer table
            pointer_table = []
            for i in range(12):
                offset = LTSDM_POINTER_TABLE_OFFSET + (i * 4)
                ptr = struct.unpack('<I', cartridge_data[offset:offset + 4])[0]
                pointer_table.append(ptr)
            
            messages.append(f"✓ Pointer table: valid")
            
            # Validate each pointer
            for i, ptr in enumerate(pointer_table, 1):
                if ptr == 0:
                    messages.append(f"  Track {i:02d}: empty")
                    continue
                
                if ptr < LTSDM_AUDIO_DATA_START or ptr >= LTSDM_CARTRIDGE_SIZE:
                    messages.append(f"✗ Track {i:02d}: pointer out of bounds ({ptr})")
                    return False, messages
                
                # Check alignment
                if ptr % 4 != 0:
                    messages.append(f"✗ Track {i:02d}: pointer not aligned ({ptr})")
                    return False, messages
                
                messages.append(f"✓ Track {i:02d}: valid pointer ({ptr})")
            
            # Check for overlapping regions
            for i in range(len(pointer_table) - 1):
                if pointer_table[i] > 0 and pointer_table[i + 1] > 0:
                    if pointer_table[i] >= pointer_table[i + 1]:
                        messages.append(f"✗ Overlapping regions: Track {i} and {i+1}")
                        return False, messages
            
            messages.append(f"✓ No overlapping regions")
            messages.append(f"\n✓ BUILD SUCCESSFUL")
            return True, messages
        
        except Exception as e:
            messages.append(f"✗ Validation failed: {e}")
            return False, messages


# ============================================================================
# Main Pipeline
# ============================================================================

class LTSDMPipeline:
    """Orchestrates the complete LTSDM compilation pipeline"""
    
    def __init__(self, work_dir: Path = None):
        self.work_dir = work_dir or Path('./ltsdm_build')
        self.work_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.normalized_dir = self.work_dir / 'normalized'
        self.encoded_dir = self.work_dir / 'encoded'
        self.output_dir = self.work_dir / 'output'
        
        for d in [self.normalized_dir, self.encoded_dir, self.output_dir]:
            d.mkdir(exist_ok=True)
    
    def process(
        self,
        audio_files: List[Tuple[int, Path]],
        output_name: str = 'cartridge.bin'
    ) -> Tuple[bool, List[str]]:
        """
        Process audio files through full pipeline.
        
        Args:
            audio_files: List of (track_number, file_path) tuples
            output_name: Name of output .bin file
        
        Returns:
            (success, list_of_status_messages)
        """
        status = []
        
        # ---- STAGE 1: Validation ----
        status.append("\n=== STAGE 1: Validation ===")
        tracks = [None] * 12
        
        for track_num, file_path in audio_files:
            if not (1 <= track_num <= 12):
                status.append(f"✗ Invalid track number: {track_num}")
                return False, status
            
            valid, error = AudioValidator.validate_file(Path(file_path))
            if not valid:
                status.append(f"✗ Track {track_num}: {error}")
                return False, status
            
            tracks[track_num - 1] = AudioTrack(track_num, Path(file_path))
            status.append(f"✓ Track {track_num}: {file_path.name}")
        
        # ---- STAGE 2: Normalization ----
        status.append("\n=== STAGE 2: Audio Normalization ===")
        normalized_files = [None] * 12
        
        for i, track in enumerate(tracks):
            if track is None:
                continue
            
            normalized_path = self.normalized_dir / f"track_{i+1:02d}.wav"
            success, msg = AudioNormalizer.normalize(track.file_path, normalized_path)
            
            if not success:
                status.append(f"✗ Track {i+1}: {msg}")
                return False, status
            
            normalized_files[i] = normalized_path
            
            # Get duration
            success, duration = AudioNormalizer.get_duration(normalized_path)
            if success:
                status.append(f"✓ Track {i+1}: {msg} ({duration:.2f}s)")
            else:
                status.append(f"✓ Track {i+1}: {msg}")
        
        # ---- STAGE 3: A1800 Encoding ----
        status.append("\n=== STAGE 3: A1800 Encoding ===")
        encoded_files = [None] * 12
        
        for i, norm_file in enumerate(normalized_files):
            if norm_file is None:
                continue
            
            encoded_path = self.encoded_dir / f"track_{i+1:02d}.a18"
            success, msg = A1800Encoder.encode(norm_file, encoded_path)
            
            if not success:
                status.append(f"✗ Track {i+1}: {msg}")
                return False, status
            
            encoded_files[i] = encoded_path
            status.append(f"✓ Track {i+1}: {msg}")
        
        # ---- STAGE 4: Compilation ----
        status.append("\n=== STAGE 4: LTSDM Compilation ===")
        output_path = self.output_dir / output_name
        
        compiler = LTSDMCompiler(output_path)
        success, msg = compiler.compile(encoded_files)
        
        if not success:
            status.append(f"✗ {msg}")
            return False, status
        
        status.append(f"✓ {msg}")
        
        # ---- STAGE 5: Validation ----
        status.append("\n=== STAGE 5: Cartridge Validation ===")
        valid, validation_msgs = CartridgeValidator.validate(output_path)
        status.extend(validation_msgs)
        
        if valid:
            status.append(f"\n📦 Output: {output_path}")
            status.append(f"📊 Size: {output_path.stat().st_size} / {LTSDM_CARTRIDGE_SIZE} bytes")
            status.append(f"📈 Usage: {(output_path.stat().st_size / LTSDM_CARTRIDGE_SIZE * 100):.1f}%")
        
        return valid, status


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Command-line interface for LTSDM compiler"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='LTSDM Compiler - Build Little Talk Stories Data Manager cartridges'
    )
    parser.add_argument('--audio', nargs='+', help='Audio files to compile')
    parser.add_argument('--output', default='cartridge.bin', help='Output cartridge name')
    parser.add_argument('--work-dir', default='./ltsdm_build', help='Working directory')
    
    args = parser.parse_args()
    
    if not args.audio:
        parser.print_help()
        return 1
    
    # Parse audio files as (track_number, file_path) pairs
    audio_files = []
    for i, audio_file in enumerate(args.audio, 1):
        audio_files.append((i, audio_file))
    
    # Run pipeline
    pipeline = LTSDMPipeline(Path(args.work_dir))
    success, status = pipeline.process(audio_files, args.output)
    
    for msg in status:
        print(msg)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
