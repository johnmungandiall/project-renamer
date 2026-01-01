#!/usr/bin/env python3
"""
Command Line Interface for Project Renamer.

This module provides a user-friendly CLI for the project renamer tool.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional, List

from project_renamer import ProjectRenamer, RenameConfig
from config import ConfigLoader, ProjectRenamerConfig, create_config_template
from utils import estimate_rename_impact, get_git_info, format_file_size


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Rename projects including all text and code references",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python cli.py old-project-name new-project-name /path/to/project

  # Dry run to see what would be changed
  python cli.py old-project new-project . --dry-run

  # Create a configuration file
  python cli.py --create-config

  # Use configuration file
  python cli.py --config project-renamer.yaml

  # Web project with custom exclusions
  python cli.py old-app new-app . --exclude node_modules dist build

  # Python project with case preservation
  python cli.py MyOldProject MyNewProject . --preserve-case
        """
    )
    
    # Main arguments (positional)
    parser.add_argument(
        "old_name",
        nargs="?",
        help="Current project name to be renamed"
    )
    
    parser.add_argument(
        "new_name",
        nargs="?",
        help="New project name"
    )
    
    parser.add_argument(
        "project_path",
        nargs="?",
        type=Path,
        help="Path to the project directory (default: current directory)"
    )
    
    # Configuration options
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (YAML or JSON)"
    )
    
    parser.add_argument(
        "--create-config",
        type=Path,
        help="Create a configuration template file at the specified path"
    )
    
    parser.add_argument(
        "--preset",
        choices=["python", "web", "enterprise"],
        help="Use preset configuration for specific project types"
    )
    
    # Behavior options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making actual changes"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable automatic backup creation"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force renaming even if there are potential issues"
    )
    
    # Text replacement options
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Use case-sensitive text matching"
    )
    
    parser.add_argument(
        "--preserve-case",
        action="store_true",
        help="Preserve case when replacing text (recommended)"
    )
    
    # File handling options
    parser.add_argument(
        "--file-types",
        nargs="*",
        help="Additional file extensions to process (e.g., .custom .ext)"
    )
    
    parser.add_argument(
        "--exclude",
        nargs="*",
        help="Additional patterns to exclude (e.g., node_modules dist)"
    )
    
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding for file operations (default: utf-8)"
    )
    
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum directory depth to process (default: 10)"
    )
    
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=10485760,
        help="Maximum file size in bytes to process (default: 10MB)"
    )
    
    # Information and validation options
    parser.add_argument(
        "--estimate",
        action="store_true",
        help="Show estimate of changes without performing rename"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the configuration and show potential issues"
    )
    
    parser.add_argument(
        "--git-check",
        action="store_true",
        help="Check Git repository status and warn about uncommitted changes"
    )
    
    # Output options
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output except for errors"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write logs to specified file"
    )
    
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    return parser


def load_preset_config(preset: str, **kwargs) -> ProjectRenamerConfig:
    """Load preset configuration based on project type."""
    from config import get_python_project_config, get_web_project_config, get_enterprise_project_config
    
    presets = {
        "python": get_python_project_config,
        "web": get_web_project_config,
        "enterprise": get_enterprise_project_config
    }
    
    if preset not in presets:
        raise ValueError(f"Unknown preset: {preset}")
    
    config = presets[preset]()
    
    # Override with any provided kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config


def display_estimate(config: ProjectRenamerConfig, old_name: str, new_name: str):
    """Display estimate of rename operation."""
    project_path = config.project_path or Path.cwd()
    
    print(f"📊 Estimating rename impact for: {project_path}")
    print(f"   {old_name} → {new_name}")
    print()
    
    # Get Git info if requested
    git_info = get_git_info(project_path)
    if git_info['is_git_repo']:
        status = "⚠️  Has uncommitted changes" if git_info['has_uncommitted_changes'] else "✅ Clean"
        print(f"📁 Git status: {status}")
        if git_info['current_branch']:
            print(f"   Current branch: {git_info['current_branch']}")
        print()
    
    # Estimate impact
    impact = estimate_rename_impact(project_path, old_name, new_name)
    
    print("📈 Impact Analysis:")
    print(f"   Total files to scan: {impact['total_files']:,}")
    print(f"   Files to modify: {impact['files_to_modify']}")
    print(f"   Files to rename: {impact['files_to_rename']}")
    print(f"   Directories to rename: {impact['directories_to_rename']}")
    print(f"   Estimated total size: {format_file_size(impact['estimated_size_mb'] * 1024 * 1024)}")
    print(f"   Risk level: {impact['risk_level'].upper()}")
    print()
    
    if impact['risk_level'] == 'high':
        print("⚠️  High risk operation detected!")
        print("   Consider using --dry-run to review changes first.")
        print("   Large number of files may indicate significant project structure changes.")
    elif impact['risk_level'] == 'medium':
        print("⚠️  Medium risk operation.")
        print("   Review changes carefully before proceeding.")


def display_validation_results(config: ProjectRenamerConfig):
    """Display validation results."""
    print("🔍 Validation Results:")
    
    issues = []
    
    # Check if names are provided
    if not config.old_name:
        issues.append("❌ Old name not provided")
    if not config.new_name:
        issues.append("❌ New name not provided")
    
    # Check if names are different
    if config.old_name and config.new_name and config.old_name == config.new_name:
        issues.append("❌ Old and new names must be different")
    
    # Check project path
    if config.project_path and not config.project_path.exists():
        issues.append(f"❌ Project path does not exist: {config.project_path}")
    
    # Check write permissions
    if config.project_path and not os.access(config.project_path, os.W_OK):
        issues.append(f"❌ Project path is not writable: {config.project_path}")
    
    if not issues:
        print("   ✅ All validation checks passed")
    else:
        print("   Issues found:")
        for issue in issues:
            print(f"   {issue}")
    
    return len(issues) == 0


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle special commands
    if args.create_config:
        try:
            config_path = create_config_template(args.create_config)
            print(f"✅ Configuration template created at: {config_path}")
            return 0
        except Exception as e:
            print(f"❌ Failed to create configuration file: {e}")
            return 1
    
    # Validate required arguments
    if not args.old_name and not args.config:
        parser.error("Either provide old_name and new_name arguments, or use --config")
    
    if not args.new_name and not args.config:
        parser.error("Either provide new_name argument, or use --config")
    
    if not args.project_path and not args.config:
        args.project_path = Path.cwd()
    
    try:
        # Load configuration
        if args.config:
            # Load from file
            from config import ConfigLoader
            config_data = ConfigLoader.load_config(
                config_path=args.config,
                old_name=args.old_name,
                new_name=args.new_name,
                project_path=args.project_path,
                dry_run=args.dry_run,
                backup_enabled=not args.no_backup,
                case_sensitive=args.case_sensitive,
                preserve_case=args.preserve_case
            )
        else:
            # Use preset or defaults
            if args.preset:
                config_data = load_preset_config(
                    args.preset,
                    old_name=args.old_name,
                    new_name=args.new_name,
                    project_path=args.project_path or Path.cwd(),
                    dry_run=args.dry_run,
                    backup_enabled=not args.no_backup,
                    case_sensitive=args.case_sensitive,
                    preserve_case=args.preserve_case,
                    encoding=args.encoding,
                    max_depth=args.max_depth,
                    max_file_size=args.max_file_size
                )
            else:
                from config import ProjectRenamerConfig
                config_data = ProjectRenamerConfig(
                    old_name=args.old_name,
                    new_name=args.new_name,
                    project_path=args.project_path or Path.cwd(),
                    dry_run=args.dry_run,
                    backup_enabled=not args.no_backup,
                    case_sensitive=args.case_sensitive,
                    preserve_case=args.preserve_case,
                    encoding=args.encoding,
                    max_depth=args.max_depth,
                    max_file_size=args.max_file_size
                )
        
        # Add custom file types and exclusions
        if args.file_types:
            config_data.file_types.update(args.file_types)
        
        if args.exclude:
            config_data.exclude_patterns.update(args.exclude)
        
        # Set logging level
        if args.quiet:
            import logging
            logging.getLogger().setLevel(logging.ERROR)
        elif args.verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
        
        if args.log_file:
            config_data.log_file = args.log_file
        
        # Handle information-only commands
        if args.validate_only:
            success = display_validation_results(config_data)
            return 0 if success else 1
        
        if args.estimate:
            display_estimate(config_data, args.old_name, args.new_name)
            return 0
        
        # Check Git status if requested
        if args.git_check:
            git_info = get_git_info(config_data.project_path)
            if git_info['is_git_repo']:
                if git_info['has_uncommitted_changes']:
                    print("⚠️  WARNING: Git repository has uncommitted changes!")
                    print("   Consider committing or stashing changes before renaming.")
                    if not args.force:
                        response = input("   Continue anyway? (y/N): ")
                        if response.lower() != 'y':
                            return 1
                else:
                    print("✅ Git repository is clean")
            else:
                print("ℹ️  Not a Git repository")
        
        # Validate configuration
        if not display_validation_results(config_data):
            return 1
        
        # Create renamer and execute
        renamer = ProjectRenamer(config_data)
        
        if not args.quiet:
            print(f"🚀 Starting rename operation:")
            print(f"   From: {config_data.old_name}")
            print(f"   To: {config_data.new_name}")
            print(f"   Path: {config_data.project_path}")
            print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
            print()
        
        success = renamer.rename_project()
        summary = renamer.get_summary()
        
        # Display results
        if args.output_format == 'json':
            print(json.dumps(summary, indent=2, default=str))
        else:
            print("\n" + "="*50)
            print("📋 SUMMARY")
            print("="*50)
            print(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
            print(f"Files changed: {summary['files_changed']}")
            
            if summary['backup_created']:
                print(f"Backup created: {len(summary['backup_paths'])}")
                for backup in summary['backup_paths']:
                    print(f"   {backup}")
            
            if summary['errors']:
                print(f"Errors: {len(summary['errors'])}")
                for error in summary['errors']:
                    print(f"   ❌ {error}")
            
            if not args.dry_run and success:
                print("\n🎉 Project renamed successfully!")
                print(f"   You can now use '{config_data.new_name}' as your project name.")
        
        return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    import os
    sys.exit(main())