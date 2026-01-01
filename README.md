# Project Renamer 🔄

A comprehensive Python tool for renaming projects including all text and code references. Perfect for when you need to rebrand a project, change naming conventions, or restructure your codebase.

## ✨ Features

- **Complete Project Renaming**: Renames directories, files, and replaces all text references
- **Smart File Handling**: Specialized processors for different file types (Python, JavaScript, JSON, YAML, XML, etc.)
- **Case Preservation**: Maintains original case patterns when replacing text
- **Safety First**: Automatic backups and dry-run mode for testing
- **Flexible Configuration**: JSON/YAML config files, environment variables, and CLI arguments
- **Git Integration**: Warns about uncommitted changes and integrates with Git workflows
- **Multiple Project Types**: Presets for Python, web, and enterprise projects
- **Comprehensive Logging**: Detailed operation logs and error reporting

## 🚀 Quick Start

### Installation

```bash
# Clone or download the project renamer files
git clone <repository-url>
cd project-renamer

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Rename a project (creates backup automatically)
python cli.py old-project-name new-project-name /path/to/project

# See what would be changed without making changes
python cli.py old-project new-project . --dry-run

# Quick rename in current directory
python cli.py MyOldApp MyNewApp . --dry-run
```

### Common Use Cases

#### 1. Python Project Renaming
```bash
# Rename Python project with specialized handling
python cli.py my_old_lib my_new_lib . --preset python --preserve-case
```

#### 2. Web Project Renaming  
```bash
# Rename React/Vue/Angular project
python cli.py old-frontend new-frontend ./my-app --preset web --dry-run
```

#### 3. Enterprise Project Renaming
```bash
# Rename Java/C# enterprise project
python cli.py LegacyApp NewApp /path/to/enterprise-project --preset enterprise
```

## 📋 Command Line Options

### Required Arguments
- `old_name`: Current project name to be renamed
- `new_name`: New project name  
- `project_path`: Path to project directory

### Configuration Options
- `--config PATH`: Use configuration file (YAML/JSON)
- `--create-config PATH`: Create configuration template
- `--preset {python,web,enterprise}`: Use preset for project type

### Behavior Options
- `--dry-run`: Show changes without applying them
- `--no-backup`: Disable automatic backup creation
- `--force`: Force operation despite warnings

### Text Replacement Options
- `--case-sensitive`: Use case-sensitive matching
- `--preserve-case`: Preserve original case patterns (recommended)

### File Handling Options
- `--file-types .ext1 .ext2`: Add custom file extensions
- `--exclude pattern1 pattern2`: Add exclusion patterns
- `--encoding utf-8`: Set file encoding
- `--max-depth 10`: Limit directory depth
- `--max-file-size 10485760`: Maximum file size (bytes)

### Information Options
- `--estimate`: Show impact analysis
- `--validate-only`: Validate configuration only
- `--git-check`: Check Git repository status

### Output Options
- `--quiet`: Suppress non-error output
- `--verbose`: Enable detailed logging
- `--log-file PATH`: Write logs to file
- `--output-format {text,json}`: Output format

## ⚙️ Configuration File

Create a configuration file for complex renaming scenarios:

```bash
# Create a template configuration
python cli.py --create-config my-project-renamer.yaml
```

### Example Configuration (YAML)
```yaml
# Project renaming configuration
old_name: "my-old-project"
new_name: "my-new-project"
project_path: "/path/to/project"

# Behavior settings
backup_enabled: true
dry_run: false
case_sensitive: false
preserve_case: true

# File handling
file_types:
  - .py
  - .js
  - .ts
  - .jsx
  - .tsx
  - .html
  - .css
  - .json
  - .md
  - .yaml
  - .yml

exclude_patterns:
  - .git
  - __pycache__
  - node_modules
  - .venv
  - dist
  - build

# Custom rename rules
custom_rules:
  - pattern: "old-project"
    replacement: "new-project"
    case_sensitive: false
    preserve_case: true

# Advanced settings
log_level: "INFO"
max_file_size: 10485760
max_depth: 10
```

### Using Configuration Files
```bash
# Use configuration file
python cli.py --config my-project-renamer.yaml

# Override specific settings
python cli.py --config my-config.yaml --dry-run --verbose
```

## 🔧 Advanced Features

### Environment Variables

Set default values using environment variables:

```bash
export PR_OLD_NAME="default-old-name"
export PR_NEW_NAME="default-new-name"
export PR_PROJECT_PATH="/default/path"
export PR_DRY_RUN="true"
export PR_BACKUP_ENABLED="false"
```

### Custom File Handlers

The tool includes specialized handlers for:

- **Python**: Import statements, class/function definitions, `__init__.py`
- **JavaScript/TypeScript**: Import/export statements, React components
- **JSON**: Package names, configuration values
- **YAML**: Docker Compose, Kubernetes manifests
- **XML**: Attribute and text content
- **Markdown**: Links, code blocks, documentation

### Git Integration

```bash
# Check Git status before renaming
python cli.py old-name new-name . --git-check --dry-run

# The tool will warn about:
# - Uncommitted changes
# - Untracked files
# - Current branch status
```

## 📊 Impact Analysis

Get a preview of what will be changed:

```bash
python cli.py old-project new-project . --estimate
```

Output example:
```
📊 Estimating rename impact for: /path/to/project
   old-project → new-project

📁 Git status: ✅ Clean
   Current branch: main

📈 Impact Analysis:
   Total files to scan: 1,247
   Files to modify: 23
   Files to rename: 5
   Directories to rename: 2
   Estimated total size: 15.2 MB
   Risk level: MEDIUM
```

## 🛡️ Safety Features

### Automatic Backups
```bash
# Backups are created automatically (unless disabled)
# Format: project_backup_YYYYMMDD_HHMMSS/
ls -la project_backup_*/
```

### Dry Run Mode
```bash
# Always test with dry-run first
python cli.py old-name new-name . --dry-run --verbose
```

### Validation
```bash
# Validate configuration without renaming
python cli.py --validate-only --config my-config.yaml
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Permission Errors
```bash
# Ensure write permissions on project directory
chmod -R u+w /path/to/project
```

#### 2. Large Files
```bash
# Increase file size limit
python cli.py old-name new-name . --max-file-size 52428800  # 50MB
```

#### 3. Encoding Issues
```bash
# Specify encoding if needed
python cli.py old-name new-name . --encoding latin-1
```

#### 4. Deep Directory Structure
```bash
# Limit search depth
python cli.py old-name new-name . --max-depth 5
```

### Debug Mode
```bash
# Enable verbose logging
python cli.py old-name new-name . --verbose --log-file debug.log
```

## 📚 Examples

### Example 1: Python Library Renaming
```bash
# Before: my-awesome-lib/
# After: super-awesome-lib/

python cli.py my-awesome-lib super-awesome-lib ./my-awesome-lib --preset python
```

### Example 2: React Application Rebranding
```bash
# Before: old-frontend/
# After: new-frontend/

python cli.py old-frontend new-frontend ./old-frontend --preset web --dry-run
```

### Example 3: Multi-language Project
```bash
# Rename enterprise project with multiple languages
python cli.py LegacySystem NewSystem /path/to/enterprise --preset enterprise --git-check
```

### Example 4: Custom File Types
```bash
# Include custom file extensions
python cli.py old-name new-name . --file-types .custom .special .biz
```

### Example 5: Exclude Patterns
```bash
# Exclude specific directories
python cli.py old-name new-name . --exclude node_modules dist build .cache logs
```

## 🏗️ Programmatic Usage

```python
from project_renamer import ProjectRenamer, RenameConfig
from pathlib import Path

# Create configuration
config = RenameConfig(
    old_name="old-project",
    new_name="new-project", 
    project_path=Path("/path/to/project"),
    backup_enabled=True,
    dry_run=False,
    preserve_case=True
)

# Create renamer and execute
renamer = ProjectRenamer(config)
success = renamer.rename_project()

# Get summary
summary = renamer.get_summary()
print(f"Files changed: {summary['files_changed']}")
```

## 📄 License

This project is provided as-is for educational and practical use. Feel free to modify and adapt for your needs.

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional file type handlers
- More configuration presets
- Enhanced Git integration
- GUI interface
- Performance optimizations

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Use `--dry-run` and `--verbose` for debugging
3. Review the configuration file examples
4. Check the generated log files

---

**Remember: Always use `--dry-run` first to preview changes before applying them!**