#!/usr/bin/env python3
"""
Demo script showing how to use the Project Renamer programmatically.

This script demonstrates various use cases and features of the Project Renamer.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from project_renamer import ProjectRenamer, RenameConfig
from config import ProjectRenamerConfig, get_python_project_config
from utils import estimate_rename_impact


def demo_basic_usage():
    """Demonstrate basic project renaming."""
    print("🔄 Demo 1: Basic Project Renaming")
    print("="*50)
    
    # Create a configuration for basic renaming
    config = RenameConfig(
        old_name="demo-old-project",
        new_name="demo-new-project",
        project_path=Path.cwd() / "demo-project",
        backup_enabled=True,
        dry_run=True,  # Always start with dry-run!
        preserve_case=True
    )
    
    # Create renamer
    renamer = ProjectRenamer(config)
    
    # Scan project first
    print("📊 Scanning project...")
    scan_results = renamer.scan_project()
    
    print(f"   Files found: {scan_results['total_files']}")
    print(f"   Files to modify: {len(scan_results['files_to_modify'])}")
    print(f"   Files to rename: {len(scan_results['files_to_rename'])}")
    print(f"   Directories to rename: {len(scan_results['directories_to_rename'])}")
    
    # Perform dry run
    print("\n🚀 Performing dry run...")
    success = renamer.rename_project()
    
    # Get summary
    summary = renamer.get_summary()
    print(f"\n✅ Operation {'successful' if success else 'failed'}")
    print(f"   Files that would be changed: {summary['files_changed']}")
    print(f"   Backup would be created: {summary['backup_created']}")
    
    return summary


def demo_python_project():
    """Demonstrate Python project-specific renaming."""
    print("\n🐍 Demo 2: Python Project Renaming")
    print("="*50)
    
    # Use Python project preset
    config = get_python_project_config()
    config.old_name = "my-awesome-library"
    config.new_name = "super-awesome-library"
    config.project_path = Path.cwd() / "python-demo"
    config.dry_run = True
    config.preserve_case = True
    
    # Create renamer
    renamer = ProjectRenamer(config)
    
    # Get impact estimate
    print("📊 Estimating impact...")
    impact = estimate_rename_impact(
        config.project_path, 
        config.old_name, 
        config.new_name
    )
    
    print(f"   Total files: {impact['total_files']}")
    print(f"   Files to modify: {impact['files_to_modify']}")
    print(f"   Risk level: {impact['risk_level']}")
    
    return renamer


def demo_configuration_loading():
    """Demonstrate loading configuration from file."""
    print("\n⚙️  Demo 3: Configuration Loading")
    print("="*50)
    
    try:
        from config import ConfigLoader
        
        # Load configuration from example file
        config_path = Path(__file__).parent / "example_config.yaml"
        if config_path.exists():
            print(f"📁 Loading configuration from: {config_path}")
            config = ConfigLoader.load_config(
                config_path=config_path,
                project_path=Path.cwd() / "config-demo"
            )
            
            print(f"   Old name: {config.old_name}")
            print(f"   New name: {config.new_name}")
            print(f"   File types: {len(config.file_types)} extensions")
            print(f"   Exclude patterns: {len(config.exclude_patterns)} patterns")
            print(f"   Custom rules: {len(config.custom_rules)} rules")
            
            return config
        else:
            print("   ⚠️  Example config file not found")
            return None
            
    except Exception as e:
        print(f"   ❌ Error loading configuration: {e}")
        return None


def demo_custom_file_handlers():
    """Demonstrate custom file handling."""
    print("\n📄 Demo 4: Custom File Handlers")
    print("="*50)
    
    from file_handlers import FileHandlerRegistry
    
    # Create handler registry
    registry = FileHandlerRegistry("old-name", "new-name")
    
    # Test with different file types
    test_files = [
        Path("test.py"),
        Path("test.js"),
        Path("test.json"),
        Path("test.yaml"),
        Path("test.xml"),
        Path("README.md"),
        Path("unknown.txt")
    ]
    
    print("🔍 File type detection:")
    for file_path in test_files:
        handler = registry.get_handler(file_path)
        handler_name = handler.__class__.__name__ if handler else "BaseHandler"
        print(f"   {file_path.suffix:<8} -> {handler_name}")
    
    return registry


def demo_error_handling():
    """Demonstrate error handling scenarios."""
    print("\n🛡️  Demo 5: Error Handling")
    print("="*50)
    
    # Test various error scenarios
    test_cases = [
        ("Empty names", {"old_name": "", "new_name": "new", "project_path": Path.cwd()}),
        ("Same names", {"old_name": "same", "new_name": "same", "project_path": Path.cwd()}),
        ("Non-existent path", {"old_name": "old", "new_name": "new", "project_path": Path("/non/existent/path")}),
    ]
    
    for test_name, kwargs in test_cases:
        print(f"\n🔍 Testing: {test_name}")
        try:
            config = RenameConfig(**kwargs)
            print("   ✅ Configuration created successfully")
        except Exception as e:
            print(f"   ❌ Error: {e}")


def create_demo_project():
    """Create a demo project structure for testing."""
    print("\n🏗️  Creating Demo Project")
    print("="*50)
    
    demo_dir = Path.cwd() / "demo-project"
    demo_dir.mkdir(exist_ok=True)
    
    # Create some sample files
    files_to_create = {
        "README.md": f"""# Demo Old Project

This is a demo project called 'demo-old-project'.

## Features
- Great functionality
- Old project references
- Import statements like `from demo_old_project import something`

## Installation
```bash
pip install demo-old-project
```
""",
        "setup.py": f"""from setuptools import setup, find_packages

setup(
    name="demo-old-project",
    version="1.0.0",
    description="Demo old project",
    packages=find_packages(),
)
""",
        "demo_old_project/__init__.py": f'''"""Demo old project package."""

__version__ = "1.0.0"
__author__ = "Demo Author"

from .main import DemoOldProject

__all__ = ["DemoOldProject"]
''',
        "demo_old_project/main.py": f"""\"\"\"Main module for demo old project.\"\"\"

class DemoOldProject:
    def __init__(self):
        self.name = "demo-old-project"
    
    def get_info(self):
        return f"This is {{self.name}}"
"""
    }
    
    for file_path, content in files_to_create.items():
        full_path = demo_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
    
    print(f"✅ Demo project created at: {demo_dir}")
    print(f"   Files created: {len(files_to_create)}")


def main():
    """Run all demonstrations."""
    print("🚀 Project Renamer - Feature Demonstrations")
    print("="*60)
    
    # Create demo project
    create_demo_project()
    
    # Run demonstrations
    try:
        demo_basic_usage()
        demo_python_project()
        demo_configuration_loading()
        demo_custom_file_handlers()
        demo_error_handling()
        
        print("\n🎉 All demonstrations completed!")
        print("\nNext steps:")
        print("1. Review the created demo project")
        print("2. Try the CLI: python cli.py demo-old-project demo-new-project demo-project --dry-run")
        print("3. Check the configuration examples")
        print("4. Test on your own projects (always use --dry-run first!)")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()