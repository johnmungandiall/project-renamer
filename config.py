"""
Configuration system for the Project Renamer.

This module provides flexible configuration management including:
- JSON/YAML configuration files
- Environment variable support
- Command-line argument integration
- Validation and defaults
"""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum


class CaseStyle(Enum):
    """Supported case styles for naming conventions."""
    ORIGINAL = "original"
    SNAKE_CASE = "snake_case"
    PASCAL_CASE = "PascalCase"
    CAMEL_CASE = "camelCase"
    KEBAB_CASE = "kebab-case"
    UPPER_CASE = "UPPER_CASE"
    LOWER_CASE = "lower_case"


@dataclass
class FileTypeConfig:
    """Configuration for file type handling."""
    extensions: Set[str]
    encoding: str = "utf-8"
    backup_required: bool = True
    special_handling: bool = False
    handler: Optional[str] = None


@dataclass
class RenameRule:
    """A single rename rule configuration."""
    pattern: str
    replacement: str
    case_sensitive: bool = False
    preserve_case: bool = True
    file_types: Optional[Set[str]] = None
    exclude_patterns: Optional[Set[str]] = None


@dataclass
class ProjectRenamerConfig:
    """Complete configuration for the project renamer."""
    
    # Basic rename information
    old_name: str
    new_name: str
    project_path: Path
    
    # Behavior settings
    backup_enabled: bool = True
    dry_run: bool = False
    case_sensitive: bool = False
    preserve_case: bool = True
    follow_symlinks: bool = False
    
    # File handling
    file_types: Set[str] = None
    exclude_patterns: Set[str] = None
    encoding: str = "utf-8"
    errors: str = "ignore"
    
    # Advanced settings
    custom_rules: List[RenameRule] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_depth: int = 10
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    
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
        
        if self.custom_rules is None:
            self.custom_rules = []


class ConfigLoader:
    """Configuration loader with multiple sources."""
    
    DEFAULT_CONFIG_NAME = "project-renamer.yaml"
    
    @classmethod
    def load_config(
        cls,
        config_path: Optional[Path] = None,
        old_name: Optional[str] = None,
        new_name: Optional[str] = None,
        project_path: Optional[Path] = None,
        **kwargs
    ) -> ProjectRenamerConfig:
        """Load configuration from various sources."""
        
        config = cls._load_from_config_file(config_path)
        config = cls._load_from_environment(config)
        config = cls._load_from_args(config, old_name, new_name, project_path, **kwargs)
        
        return cls._validate_and_finalize(config)
    
    @classmethod
    def _load_from_config_file(cls, config_path: Optional[Path]) -> ProjectRenamerConfig:
        """Load configuration from file."""
        if config_path is None:
            # Look for default config files
            search_paths = [
                Path.cwd() / cls.DEFAULT_CONFIG_NAME,
                Path.cwd() / ".project-renamer.yaml",
                Path.cwd() / "project-renamer.json",
                Path.home() / ".project-renamer.yaml",
            ]
            
            for path in search_paths:
                if path.exists():
                    config_path = path
                    break
        
        if config_path and config_path.exists():
            return cls._parse_config_file(config_path)
        
        # Return default config structure
        return ProjectRenamerConfig(
            old_name="",
            new_name="",
            project_path=Path.cwd()
        )
    
    @classmethod
    def _parse_config_file(cls, config_path: Path) -> ProjectRenamerConfig:
        """Parse configuration file (YAML or JSON)."""
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(content)
            elif config_path.suffix.lower() == '.json':
                data = json.loads(content)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        except Exception as e:
            raise ValueError(f"Failed to parse configuration file {config_path}: {e}")
        
        # Convert to config object
        return cls._dict_to_config(data)
    
    @classmethod
    def _dict_to_config(cls, data: Dict[str, Any]) -> ProjectRenamerConfig:
        """Convert dictionary to ProjectRenamerConfig."""
        # Handle nested objects
        if 'custom_rules' in data:
            data['custom_rules'] = [
                RenameRule(**rule_data) if isinstance(rule_data, dict) else rule_data
                for rule_data in data['custom_rules']
            ]
        
        if 'file_types' in data and isinstance(data['file_types'], list):
            data['file_types'] = set(data['file_types'])
        
        if 'exclude_patterns' in data and isinstance(data['exclude_patterns'], list):
            data['exclude_patterns'] = set(data['exclude_patterns'])
        
        if 'project_path' in data:
            data['project_path'] = Path(data['project_path'])
        
        return ProjectRenamerConfig(**data)
    
    @classmethod
    def _load_from_environment(cls, config: ProjectRenamerConfig) -> ProjectRenamerConfig:
        """Load configuration from environment variables."""
        env_mappings = {
            'PR_OLD_NAME': ('old_name', str),
            'PR_NEW_NAME': ('new_name', str),
            'PR_PROJECT_PATH': ('project_path', lambda x: Path(x)),
            'PR_BACKUP_ENABLED': ('backup_enabled', lambda x: x.lower() == 'true'),
            'PR_DRY_RUN': ('dry_run', lambda x: x.lower() == 'true'),
            'PR_CASE_SENSITIVE': ('case_sensitive', lambda x: x.lower() == 'true'),
            'PR_PRESERVE_CASE': ('preserve_case', lambda x: x.lower() == 'true'),
            'PR_LOG_LEVEL': ('log_level', str),
            'PR_FILE_ENCODING': ('encoding', str),
        }
        
        config_dict = asdict(config)
        
        for env_var, (attr_name, converter) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    config_dict[attr_name] = converter(env_value)
                except Exception as e:
                    raise ValueError(f"Invalid environment variable {env_var}={env_value}: {e}")
        
        return ProjectRenamerConfig(**config_dict)
    
    @classmethod
    def _load_from_args(
        cls,
        config: ProjectRenamerConfig,
        old_name: Optional[str],
        new_name: Optional[str],
        project_path: Optional[Path],
        **kwargs
    ) -> ProjectRenamerConfig:
        """Load configuration from function arguments."""
        config_dict = asdict(config)
        
        if old_name is not None:
            config_dict['old_name'] = old_name
        
        if new_name is not None:
            config_dict['new_name'] = new_name
        
        if project_path is not None:
            config_dict['project_path'] = project_path
        
        # Override with any additional kwargs
        for key, value in kwargs.items():
            if hasattr(config, key):
                config_dict[key] = value
        
        return ProjectRenamerConfig(**config_dict)
    
    @classmethod
    def _validate_and_finalize(cls, config: ProjectRenamerConfig) -> ProjectRenamerConfig:
        """Validate and finalize configuration."""
        if not config.old_name:
            raise ValueError("old_name is required")
        
        if not config.new_name:
            raise ValueError("new_name is required")
        
        if not config.project_path.exists():
            raise ValueError(f"Project path does not exist: {config.project_path}")
        
        if config.old_name == config.new_name:
            raise ValueError("old_name and new_name must be different")
        
        # Normalize paths
        config.project_path = config.project_path.resolve()
        
        return config
    
    @classmethod
    def save_config_template(cls, output_path: Path = None) -> Path:
        """Save a configuration template to file."""
        if output_path is None:
            output_path = Path.cwd() / cls.DEFAULT_CONFIG_NAME
        
        template = {
            'old_name': 'old-project-name',
            'new_name': 'new-project-name',
            'project_path': '/path/to/project',
            'backup_enabled': True,
            'dry_run': False,
            'case_sensitive': False,
            'preserve_case': True,
            'file_types': [
                '.py', '.js', '.ts', '.jsx', '.tsx',
                '.html', '.css', '.json', '.md',
                '.yaml', '.yml', '.xml'
            ],
            'exclude_patterns': [
                '.git', '__pycache__', 'node_modules',
                '.venv', 'dist', 'build'
            ],
            'custom_rules': [
                {
                    'pattern': r'old-project-name',
                    'replacement': 'new-project-name',
                    'case_sensitive': False,
                    'preserve_case': True
                }
            ],
            'log_level': 'INFO',
            'max_file_size': 10485760,
            'max_depth': 10
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(template, f, default_flow_style=False, allow_unicode=True)
        
        return output_path


class ConfigValidator:
    """Configuration validation utilities."""
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate project name format."""
        if not name or not name.strip():
            return False
        
        # Check for invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, name):
            return False
        
        # Check length
        if len(name) > 255:
            return False
        
        return True
    
    @staticmethod
    def validate_path(path: Path) -> bool:
        """Validate project path."""
        try:
            if not path.exists():
                return False
            
            if not path.is_dir():
                return False
            
            # Check write permissions
            if not os.access(path, os.W_OK):
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_file_types(file_types: Set[str]) -> bool:
        """Validate file type extensions."""
        for ext in file_types:
            if not ext.startswith('.'):
                return False
            
            if len(ext) > 10:  # Reasonable limit
                return False
        
        return True
    
    @staticmethod
    def validate_exclude_patterns(patterns: Set[str]) -> bool:
        """Validate exclude patterns."""
        for pattern in patterns:
            if not pattern or len(pattern) > 100:
                return False
        
        return True


def create_config_template():
    """Create a sample configuration file."""
    return ConfigLoader.save_config_template()


# Utility functions for common configurations

def get_python_project_config() -> ProjectRenamerConfig:
    """Get configuration optimized for Python projects."""
    return ProjectRenamerConfig(
        file_types={
            '.py', '.pyx', '.pxd', '.pxi',
            '.txt', '.md', '.rst',
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
            '.sh', '.bat', '.dockerfile', '.dockerignore',
            '.gitignore', '.gitattributes', '.env',
            'setup.py', 'pyproject.toml', 'requirements.txt',
            'Makefile', 'CMakeLists.txt'
        },
        exclude_patterns={
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.venv', 'venv', 'env', '.tox', '.coverage',
            '*.egg-info', 'dist', 'build', '.cache',
            '*.pyc', '*.pyo', '*.pyd', '.DS_Store'
        }
    )


def get_web_project_config() -> ProjectRenamerConfig:
    """Get configuration optimized for web projects."""
    return ProjectRenamerConfig(
        file_types={
            '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte',
            '.html', '.htm', '.css', '.scss', '.sass', '.less',
            '.json', '.xml', '.yaml', '.yml',
            '.md', '.txt', '.rst',
            '.sh', '.bat', '.ps1', '.dockerfile', '.dockerignore',
            '.gitignore', '.gitattributes', '.env',
            'package.json', 'package-lock.json', 'yarn.lock',
            'Dockerfile', 'docker-compose.yml',
            'webpack.config.js', 'babel.config.js',
            '.eslintrc.js', '.prettierrc'
        },
        exclude_patterns={
            '.git', 'node_modules', 'bower_components',
            '.cache', '.next', '.nuxt', 'dist', 'build',
            '.coverage', '.nyc_output',
            '.DS_Store', 'Thumbs.db'
        }
    )


def get_enterprise_project_config() -> ProjectRenamerConfig:
    """Get configuration optimized for enterprise projects."""
    return ProjectRenamerConfig(
        file_types={
            '.java', '.kt', '.scala', '.groovy',
            '.cs', '.vb', '.fs',
            '.cpp', '.c', '.h', '.hpp',
            '.go', '.rs', '.swift',
            '.py', '.js', '.ts', '.rb', '.php',
            '.xml', '.json', '.yaml', '.yml', '.properties',
            '.md', '.txt', '.rst', '.adoc',
            '.sh', '.bat', '.ps1', '.dockerfile',
            '.gitignore', '.gitattributes',
            'pom.xml', 'build.gradle', 'CMakeLists.txt',
            'Makefile', 'docker-compose.yml'
        },
        exclude_patterns={
            '.git', 'target', 'build', 'dist', 'out',
            'node_modules', '__pycache__', '.pytest_cache',
            '.idea', '.vscode', '.eclipse',
            '.class', '.jar', '.war', '.ear',
            '*.pyc', '*.pyo', '*.pyd',
            '.DS_Store', 'Thumbs.db'
        }
    )