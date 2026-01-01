#!/usr/bin/env python3
"""
Project Renamer - A comprehensive tool to rename projects including all text and code references.

This tool can:
- Rename project directories and files
- Replace text references in code files
- Update configuration files
- Handle various file types intelligently
- Create backups before making changes
- Provide dry-run mode for testing
"""

import os
import re
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RenameConfig:
    """Configuration for project renaming operations."""
    old_name: str
    new_name: str
    project_path: Path
    backup_enabled: bool = True
    dry_run: bool = False
    file_types: Set[str] = None
    exclude_patterns: Set[str] = None
    case_sensitive: bool = False
    preserve_case: bool = False
    
    def __post_init__(self):
        if self.file_types is None:
            self.file_types = {
                '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
                '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
                '.html', '.htm', '.css', '.scss', '.sass', '.less',
                '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
                '.md', '.txt', '.rst', '.adoc',
                '.sh', '.bat', '.ps1', '.dockerfile', '.dockerignore',
                '.gitignore', '.gitattributes', '.env', '.env.example',
                'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
                'package.json', 'requirements.txt', 'setup.py', 'pyproject.toml',
                'Makefile', 'CMakeLists.txt', 'pom.xml', 'build.gradle'
            }
        
        if self.exclude_patterns is None:
            self.exclude_patterns = {
                '.git', '__pycache__', '.pytest_cache', 'node_modules',
                '.venv', 'venv', 'env', '.env', '.idea', '.vscode',
                '*.egg-info', 'dist', 'build', '.tox', '.coverage',
                '*.pyc', '*.pyo', '*.pyd', '.DS_Store', 'Thumbs.db'
            }


class ProjectRenamer:
    """Main class for handling project renaming operations."""
    
    def __init__(self, config: RenameConfig):
        self.config = config
        self.changed_files: List[Path] = []
        self.backup_paths: List[Path] = []
        self.errors: List[str] = []
        
        # Set up logging
        self._setup_logging()
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        log_level = logging.DEBUG if self.config.dry_run else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.config.project_path / 'rename_log.txt')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _compile_patterns(self):
        """Compile regex patterns for text replacement."""
        flags = 0 if self.config.case_sensitive else re.IGNORECASE
        
        # Basic text replacement
        if self.config.preserve_case:
            self.patterns = [
                self._create_case_preserving_pattern(self.config.old_name),
                self._create_case_preserving_pattern(self._to_pascal_case(self.config.old_name)),
                self._create_case_preserving_pattern(self._to_snake_case(self.config.old_name)),
                self._create_case_preserving_pattern(self._to_kebab_case(self.config.old_name)),
            ]
        else:
            self.patterns = [
                re.compile(re.escape(self.config.old_name), flags),
                re.compile(re.escape(self._to_pascal_case(self.config.old_name)), flags),
                re.compile(re.escape(self._to_snake_case(self.config.old_name)), flags),
                re.compile(re.escape(self._to_kebab_case(self.config.old_name)), flags),
            ]
    
    def _create_case_preserving_pattern(self, text: str) -> re.Pattern:
        """Create a case-preserving regex pattern."""
        def repl(match):
            replacement = self.config.new_name
            original = match.group(0)
            
            if original.isupper():
                return replacement.upper()
            elif original.islower():
                return replacement.lower()
            elif original.istitle():
                return replacement.title()
            else:
                return replacement
        
        return re.compile(re.escape(text), re.IGNORECASE, repl=repl)
    
    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase."""
        return ''.join(word.capitalize() for word in re.split(r'[-_\s]+', text))
    
    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_kebab_case(self, text: str) -> str:
        """Convert text to kebab-case."""
        return re.sub(r'[-_\s]+', '-', text.lower())
    
    def scan_project(self) -> Dict[str, Any]:
        """Scan the project and identify files that need changes."""
        self.logger.info(f"Scanning project at: {self.config.project_path}")
        
        scan_results = {
            'files_to_modify': [],
            'files_to_rename': [],
            'directories_to_rename': [],
            'total_files': 0,
            'total_directories': 0
        }
        
        for root, dirs, files in os.walk(self.config.project_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self._is_excluded(d)]
            
            for file in files:
                if self._is_excluded(file):
                    continue
                
                file_path = Path(root) / file
                scan_results['total_files'] += 1
                
                # Check if file needs renaming
                if self._should_rename_file(file_path):
                    scan_results['files_to_rename'].append(file_path)
                
                # Check if file needs text modification
                if self._should_modify_file(file_path):
                    if self._contains_target_text(file_path):
                        scan_results['files_to_modify'].append(file_path)
            
            # Check if directory needs renaming
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                scan_results['total_directories'] += 1
                
                if self._should_rename_directory(dir_path):
                    scan_results['directories_to_rename'].append(dir_path)
        
        return scan_results
    
    def _is_excluded(self, name: str) -> bool:
        """Check if a file/directory should be excluded."""
        for pattern in self.config.exclude_patterns:
            if pattern.startswith('*.') and name.endswith(pattern[1:]):
                return True
            if pattern == name:
                return True
            if pattern in name:
                return True
        return False
    
    def _should_rename_file(self, file_path: Path) -> bool:
        """Check if a file should be renamed."""
        if file_path.name == self.config.old_name:
            return True
        if self._to_snake_case(file_path.stem) == self._to_snake_case(self.config.old_name):
            return True
        if self._to_pascal_case(file_path.stem) == self._to_pascal_case(self.config.old_name):
            return True
        return False
    
    def _should_rename_directory(self, dir_path: Path) -> bool:
        """Check if a directory should be renamed."""
        if dir_path.name == self.config.old_name:
            return True
        if self._to_snake_case(dir_path.name) == self._to_snake_case(self.config.old_name):
            return True
        if self._to_pascal_case(dir_path.name) == self._to_pascal_case(dir_path.name):
            return True
        return False
    
    def _should_modify_file(self, file_path: Path) -> bool:
        """Check if a file should have its content modified."""
        return file_path.suffix.lower() in self.config.file_types
    
    def _contains_target_text(self, file_path: Path) -> bool:
        """Check if a file contains the target text to replace."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for pattern in self.patterns:
                    if pattern.search(content):
                        return True
        except Exception as e:
            self.logger.warning(f"Could not read file {file_path}: {e}")
        return False
    
    def create_backup(self) -> bool:
        """Create a backup of the project."""
        if not self.config.backup_enabled:
            return True
        
        backup_dir = self.config.project_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            self.logger.info(f"Creating backup at: {backup_dir}")
            shutil.copytree(self.config.project_path, backup_dir, ignore=shutil.ignore_patterns(*self.config.exclude_patterns))
            self.backup_paths.append(backup_dir)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def rename_project(self) -> bool:
        """Perform the complete renaming operation."""
        self.logger.info("Starting project rename operation")
        
        # Create backup
        if not self.create_backup():
            return False
        
        # Scan project
        scan_results = self.scan_project()
        
        if self.config.dry_run:
            self._log_dry_run_results(scan_results)
            return True
        
        # Perform operations
        success = True
        
        # Rename files first
        for file_path in scan_results['files_to_rename']:
            if not self._rename_file(file_path):
                success = False
        
        # Rename directories (bottom-up to avoid path issues)
        for dir_path in sorted(scan_results['directories_to_rename'], key=len, reverse=True):
            if not self._rename_directory(dir_path):
                success = False
        
        # Modify file contents
        for file_path in scan_results['files_to_modify']:
            if not self._modify_file_content(file_path):
                success = False
        
        if success:
            self.logger.info("Project rename completed successfully")
        else:
            self.logger.error("Project rename completed with errors")
        
        return success
    
    def _rename_file(self, file_path: Path) -> bool:
        """Rename a single file."""
        try:
            new_name = self._generate_new_name(file_path.name)
            new_path = file_path.parent / new_name
            
            if not self.config.dry_run:
                file_path.rename(new_path)
            
            self.logger.info(f"Renamed file: {file_path} -> {new_path}")
            self.changed_files.append(file_path)
            return True
        except Exception as e:
            error_msg = f"Failed to rename file {file_path}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def _rename_directory(self, dir_path: Path) -> bool:
        """Rename a single directory."""
        try:
            new_name = self._generate_new_name(dir_path.name)
            new_path = dir_path.parent / new_name
            
            if not self.config.dry_run:
                dir_path.rename(new_path)
            
            self.logger.info(f"Renamed directory: {dir_path} -> {new_path}")
            self.changed_files.append(dir_path)
            return True
        except Exception as e:
            error_msg = f"Failed to rename directory {dir_path}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def _modify_file_content(self, file_path: Path) -> bool:
        """Modify the content of a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            modified_content = original_content
            for pattern in self.patterns:
                modified_content = pattern.sub(self.config.new_name, modified_content)
            
            if modified_content != original_content:
                if not self.config.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                
                self.logger.info(f"Modified content in: {file_path}")
                self.changed_files.append(file_path)
                return True
            else:
                return True
        except Exception as e:
            error_msg = f"Failed to modify file {file_path}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def _generate_new_name(self, original_name: str) -> str:
        """Generate a new name based on the original and configuration."""
        if original_name == self.config.old_name:
            return self.config.new_name
        
        # Handle case conversions
        if original_name.lower() == self.config.old_name.lower():
            return self.config.new_name.lower()
        elif original_name.upper() == self.config.old_name.upper():
            return self.config.new_name.upper()
        elif original_name.title() == self.config.old_name.title():
            return self.config.new_name.title()
        else:
            # Complex case - try to match the pattern
            if self._to_snake_case(original_name) == self._to_snake_case(self.config.old_name):
                return self._to_snake_case(self.config.new_name)
            elif self._to_pascal_case(original_name) == self._to_pascal_case(self.config.old_name):
                return self._to_pascal_case(self.config.new_name)
            else:
                return self.config.new_name
    
    def _log_dry_run_results(self, scan_results: Dict[str, Any]):
        """Log the results of a dry run."""
        self.logger.info("=== DRY RUN RESULTS ===")
        self.logger.info(f"Total files scanned: {scan_results['total_files']}")
        self.logger.info(f"Total directories scanned: {scan_results['total_directories']}")
        self.logger.info(f"Files to rename: {len(scan_results['files_to_rename'])}")
        self.logger.info(f"Directories to rename: {len(scan_results['directories_to_rename'])}")
        self.logger.info(f"Files to modify: {len(scan_results['files_to_modify'])}")
        
        if scan_results['files_to_rename']:
            self.logger.info("\nFiles to rename:")
            for file_path in scan_results['files_to_rename']:
                new_name = self._generate_new_name(file_path.name)
                self.logger.info(f"  {file_path} -> {file_path.parent / new_name}")
        
        if scan_results['directories_to_rename']:
            self.logger.info("\nDirectories to rename:")
            for dir_path in scan_results['directories_to_rename']:
                new_name = self._generate_new_name(dir_path.name)
                self.logger.info(f"  {dir_path} -> {dir_path.parent / new_name}")
        
        if scan_results['files_to_modify']:
            self.logger.info("\nFiles to modify:")
            for file_path in scan_results['files_to_modify']:
                self.logger.info(f"  {file_path}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the renaming operation."""
        return {
            'old_name': self.config.old_name,
            'new_name': self.config.new_name,
            'project_path': str(self.config.project_path),
            'backup_created': len(self.backup_paths) > 0,
            'backup_paths': [str(p) for p in self.backup_paths],
            'files_changed': len(self.changed_files),
            'changed_files': [str(f) for f in self.changed_files],
            'errors': self.errors,
            'dry_run': self.config.dry_run
        }


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rename a project including all references")
    parser.add_argument("old_name", help="Current project name")
    parser.add_argument("new_name", help="New project name")
    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("--no-backup", action="store_true", help="Disable backup creation")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--case-sensitive", action="store_true", help="Use case-sensitive matching")
    parser.add_argument("--preserve-case", action="store_true", help="Preserve case when replacing text")
    parser.add_argument("--file-types", nargs="*", help="Additional file types to process")
    parser.add_argument("--exclude", nargs="*", help="Additional patterns to exclude")
    
    args = parser.parse_args()
    
    # Create configuration
    config = RenameConfig(
        old_name=args.old_name,
        new_name=args.new_name,
        project_path=Path(args.project_path),
        backup_enabled=not args.no_backup,
        dry_run=args.dry_run,
        case_sensitive=args.case_sensitive,
        preserve_case=args.preserve_case
    )
    
    if args.file_types:
        config.file_types.update(args.file_types)
    
    if args.exclude:
        config.exclude_patterns.update(args.exclude)
    
    # Create renamer and execute
    renamer = ProjectRenamer(config)
    success = renamer.rename_project()
    
    # Print summary
    summary = renamer.get_summary()
    print("\n=== SUMMARY ===")
    print(f"Old name: {summary['old_name']}")
    print(f"New name: {summary['new_name']}")
    print(f"Backup created: {summary['backup_created']}")
    print(f"Files changed: {summary['files_changed']}")
    if summary['errors']:
        print(f"Errors: {len(summary['errors'])}")
        for error in summary['errors']:
            print(f"  - {error}")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())