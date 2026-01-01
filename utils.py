"""
Utility functions for the Project Renamer.

This module provides various utility functions for:
- File system operations
- Text processing
- Pattern matching
- Validation
- Backup and recovery
"""

import os
import re
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from datetime import datetime
import difflib


def calculate_file_hash(file_path: Path, algorithm: str = 'md5') -> str:
    """Calculate hash of a file for integrity checking."""
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def find_files_by_pattern(
    directory: Path,
    patterns: Union[str, List[str]],
    exclude_patterns: Optional[Set[str]] = None,
    case_sensitive: bool = False,
    max_depth: int = 10
) -> List[Path]:
    """Find files matching patterns in a directory tree."""
    
    if isinstance(patterns, str):
        patterns = [patterns]
    
    if exclude_patterns is None:
        exclude_patterns = set()
    
    matched_files = []
    
    try:
        for root, dirs, files in os.walk(directory, topdown=True):
            current_depth = len(Path(root).relative_to(directory).parts)
            
            if current_depth > max_depth:
                # Clear dirs to prevent further recursion
                dirs[:] = []
                continue
            
            # Filter directories
            dirs[:] = [d for d in dirs if not _matches_any_pattern(d, exclude_patterns, case_sensitive)]
            
            for file in files:
                if _matches_any_pattern(file, exclude_patterns, case_sensitive):
                    continue
                
                file_path = Path(root) / file
                
                if _matches_any_pattern(file, patterns, case_sensitive):
                    matched_files.append(file_path)
    
    except Exception as e:
        logging.error(f"Error during file search: {e}")
    
    return matched_files


def _matches_any_pattern(text: str, patterns: Union[str, List[str]], case_sensitive: bool = False) -> bool:
    """Check if text matches any of the given patterns."""
    if isinstance(patterns, str):
        patterns = [patterns]
    
    text_to_check = text if case_sensitive else text.lower()
    
    for pattern in patterns:
        pattern_to_check = pattern if case_sensitive else pattern.lower()
        
        # Handle wildcard patterns
        if '*' in pattern or '?' in pattern:
            regex_pattern = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')
            if re.match(regex_pattern, text_to_check):
                return True
        else:
            if text_to_check == pattern_to_check:
                return True
    
    return False


def get_file_encoding(file_path: Path) -> str:
    """Detect file encoding."""
    try:
        with open(file_path, 'rb') as f:
            # Read first few bytes to detect BOM
            raw_data = f.read(4)
            
        if raw_data.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'
        elif raw_data.startswith(b'\xff\xfe'):
            return 'utf-16-le'
        elif raw_data.startswith(b'\xfe\xff'):
            return 'utf-16-be'
        else:
            return 'utf-8'
    
    except Exception:
        return 'utf-8'


def safe_read_file(file_path: Path, encoding: str = 'utf-8', errors: str = 'ignore') -> Optional[str]:
    """Safely read a file with error handling."""
    try:
        with open(file_path, 'r', encoding=encoding, errors=errors) as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encodings
        for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(file_path, 'r', encoding=enc, errors=errors) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
    except Exception as e:
        logging.error(f"Failed to read file {file_path}: {e}")
    
    return None


def safe_write_file(file_path: Path, content: str, encoding: str = 'utf-8', create_backup: bool = True) -> bool:
    """Safely write content to a file with backup option."""
    try:
        if create_backup and file_path.exists():
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(file_path, backup_path)
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return True
    
    except Exception as e:
        logging.error(f"Failed to write file {file_path}: {e}")
        return False


def convert_case(text: str, case_style: str) -> str:
    """Convert text to specified case style."""
    case_style = case_style.lower()
    
    if case_style == 'original':
        return text
    
    elif case_style == 'snake_case':
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    elif case_style == 'pascal_case':
        return ''.join(word.capitalize() for word in re.split(r'[-_\s]+', text))
    
    elif case_style == 'camel_case':
        words = re.split(r'[-_\s]+', text)
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    elif case_style == 'kebab_case':
        return re.sub(r'[-_\s]+', '-', text.lower())
    
    elif case_style == 'upper_case':
        return text.upper()
    
    elif case_style == 'lower_case':
        return text.lower()
    
    else:
        raise ValueError(f"Unsupported case style: {case_style}")


def preserve_case(original: str, replacement: str) -> str:
    """Replace text while preserving the case pattern of the original."""
    if original.isupper():
        return replacement.upper()
    elif original.islower():
        return replacement.lower()
    elif original.istitle():
        return replacement.title()
    else:
        # Mixed case - try to preserve pattern
        result = ""
        rep_index = 0
        
        for char in original:
            if rep_index >= len(replacement):
                result += char
                continue
            
            if char.isupper():
                result += replacement[rep_index].upper()
            elif char.islower():
                result += replacement[rep_index].lower()
            elif char.isdigit():
                result += replacement[rep_index]
            else:
                result += replacement[rep_index]
            
            rep_index += 1
        
        # Add remaining characters from replacement if any
        if rep_index < len(replacement):
            result += replacement[rep_index:]
        
        return result


def generate_diff(original: str, modified: str, fromfile: str = 'original', tofile: str = 'modified') -> str:
    """Generate a unified diff between two texts."""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=fromfile,
        tofile=tofile,
        lineterm=''
    )
    
    return '\n'.join(diff)


def create_backup_directory(source_path: Path, backup_base: Optional[Path] = None) -> Path:
    """Create a backup directory with timestamp."""
    if backup_base is None:
        backup_base = source_path.parent
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{source_path.name}_backup_{timestamp}"
    backup_path = backup_base / backup_name
    
    if source_path.is_file():
        shutil.copy2(source_path, backup_path)
    else:
        shutil.copytree(source_path, backup_path, ignore=shutil.ignore_patterns('.git'))
    
    return backup_path


def restore_from_backup(backup_path: Path, original_path: Path) -> bool:
    """Restore original from backup."""
    try:
        if backup_path.is_file():
            shutil.copy2(backup_path, original_path)
        else:
            if original_path.exists():
                if original_path.is_file():
                    original_path.unlink()
                else:
                    shutil.rmtree(original_path)
            
            shutil.copytree(backup_path, original_path)
        
        return True
    
    except Exception as e:
        logging.error(f"Failed to restore from backup {backup_path}: {e}")
        return False


def validate_file_operations(file_paths: List[Path], operations: List[str]) -> Dict[Path, Dict[str, Any]]:
    """Validate file operations before execution."""
    results = {}
    
    for file_path in file_paths:
        result = {
            'exists': file_path.exists(),
            'readable': False,
            'writable': False,
            'size': 0,
            'errors': []
        }
        
        try:
            if file_path.exists():
                result['readable'] = os.access(file_path, os.R_OK)
                result['writable'] = os.access(file_path, os.W_OK)
                result['size'] = file_path.stat().st_size
            else:
                # Check if parent directory is writable
                parent = file_path.parent
                if parent.exists():
                    result['writable'] = os.access(parent, os.W_OK)
                else:
                    result['errors'].append("Parent directory does not exist")
        
        except Exception as e:
            result['errors'].append(f"Validation error: {e}")
        
        results[file_path] = result
    
    return results


def get_git_info(project_path: Path) -> Dict[str, Any]:
    """Get Git repository information if available."""
    git_info = {
        'is_git_repo': False,
        'has_uncommitted_changes': False,
        'current_branch': None,
        'last_commit': None
    }
    
    try:
        git_dir = project_path / '.git'
        if not git_dir.exists():
            return git_info
        
        git_info['is_git_repo'] = True
        
        # Check for uncommitted changes
        os.chdir(project_path)
        import subprocess
        
        # Check current branch
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, cwd=project_path)
        if result.returncode == 0:
            git_info['current_branch'] = result.stdout.strip()
        
        # Check for uncommitted changes
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd=project_path)
        if result.returncode == 0 and result.stdout.strip():
            git_info['has_uncommitted_changes'] = True
        
        # Get last commit info
        result = subprocess.run(['git', 'log', '-1', '--pretty=format:%H|%an|%ad|%s', 
                               '--date=iso'], 
                              capture_output=True, text=True, cwd=project_path)
        if result.returncode == 0:
            commit_info = result.stdout.strip().split('|', 3)
            if len(commit_info) == 4:
                git_info['last_commit'] = {
                    'hash': commit_info[0],
                    'author': commit_info[1],
                    'date': commit_info[2],
                    'message': commit_info[3]
                }
    
    except Exception as e:
        logging.warning(f"Could not get Git info: {e}")
    
    return git_info


def estimate_rename_impact(project_path: Path, old_name: str, new_name: str) -> Dict[str, Any]:
    """Estimate the impact of a rename operation."""
    impact = {
        'total_files': 0,
        'files_to_modify': 0,
        'files_to_rename': 0,
        'directories_to_rename': 0,
        'estimated_size_mb': 0,
        'risk_level': 'low'
    }
    
    try:
        for root, dirs, files in os.walk(project_path):
            impact['total_files'] += len(files)
            
            for file in files:
                file_path = Path(root) / file
                
                # Estimate file size
                try:
                    impact['estimated_size_mb'] += file_path.stat().st_size / (1024 * 1024)
                except:
                    pass
                
                # Check if file needs modification
                try:
                    content = safe_read_file(file_path)
                    if content and old_name in content:
                        impact['files_to_modify'] += 1
                except:
                    pass
                
                # Check if file needs renaming
                if old_name in file:
                    impact['files_to_rename'] += 1
            
            for dir_name in dirs:
                if old_name in dir_name:
                    impact['directories_to_rename'] += 1
    
    except Exception as e:
        logging.error(f"Error estimating rename impact: {e}")
    
    # Determine risk level
    total_changes = impact['files_to_modify'] + impact['files_to_rename']
    if total_changes > 100:
        impact['risk_level'] = 'high'
    elif total_changes > 20:
        impact['risk_level'] = 'medium'
    
    return impact


def cleanup_temp_files(cleanup_patterns: Set[str] = None) -> None:
    """Clean up temporary files created during operations."""
    if cleanup_patterns is None:
        cleanup_patterns = {
            '*.backup_*',
            '*.tmp',
            '*.temp',
            'rename_log.txt'
        }
    
    current_dir = Path.cwd()
    
    for pattern in cleanup_patterns:
        try:
            # Simple pattern matching - could be enhanced with glob
            for file_path in current_dir.iterdir():
                if file_path.name.endswith(pattern.replace('*', '')):
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
        except Exception as e:
            logging.warning(f"Could not cleanup {pattern}: {e}")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """Sanitize filename by removing invalid characters."""
    # Characters not allowed in filenames
    invalid_chars = r'[<>:"/\\|?*]'
    
    # Replace invalid characters
    sanitized = re.sub(invalid_chars, replacement, filename)
    
    # Remove trailing periods and spaces
    sanitized = sanitized.rstrip('. ')
    
    # Ensure not empty
    if not sanitized:
        sanitized = 'unnamed'
    
    return sanitized


def is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary."""
    try:
        with open(file_path, 'rb') as f:
            # Read first chunk
            chunk = f.read(1024)
            
            # Check for null bytes (binary indicator)
            if b'\0' in chunk:
                return True
            
            # Check if most bytes are non-printable
            text_chars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x7e)))
            if len(chunk) > 0:
                non_text = len(chunk) - len(chunk.translate(None, text_chars))
                return non_text / len(chunk) > 0.3
    
    except Exception:
        return True  # Assume binary if can't read
    
    return False