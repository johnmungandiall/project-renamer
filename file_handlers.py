"""
Specialized file handlers for different project file types.

This module provides enhanced handling for specific file types that may require
special treatment during project renaming operations.
"""

import re
import json
import yaml
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from abc import ABC, abstractmethod


class BaseFileHandler(ABC):
    """Base class for specialized file handlers."""
    
    def __init__(self, old_name: str, new_name: str):
        self.old_name = old_name
        self.new_name = new_name
    
    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        pass
    
    @abstractmethod
    def process(self, file_path: Path, content: str) -> str:
        """Process the file content and return modified content."""
        pass
    
    def preserve_case(self, replacement: str, original: str) -> str:
        """Preserve the case pattern of the original text in the replacement."""
        if original.isupper():
            return replacement.upper()
        elif original.islower():
            return replacement.lower()
        elif original.istitle():
            return replacement.title()
        else:
            return replacement


class PythonFileHandler(BaseFileHandler):
    """Specialized handler for Python files."""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.py'
    
    def process(self, file_path: Path, content: str) -> str:
        """Process Python file content with additional considerations."""
        
        # Handle module name references
        patterns = [
            # import old_name
            rf'import\s+{re.escape(self.old_name)}\b',
            # from old_name import
            rf'from\s+{re.escape(self.old_name)}\b',
            # __all__ = ['old_name']
            rf"__all__\s*=\s*\[.*?['\"]{re.escape(self.old_name)}['\"]",
            # docstrings mentioning old_name
            r'(?i)(["\']..*?["\'].*?)',
        ]
        
        modified_content = content
        
        # Special handling for __init__.py files
        if file_path.name == '__init__.py':
            modified_content = self._handle_init_file(modified_content)
        
        # Handle class and function definitions
        modified_content = self._handle_definitions(modified_content)
        
        # Apply general patterns
        for pattern in patterns:
            modified_content = re.sub(pattern, self._replace_python_import, modified_content, flags=re.MULTILINE | re.DOTALL)
        
        return modified_content
    
    def _handle_init_file(self, content: str) -> str:
        """Handle special cases for __init__.py files."""
        # Update __version__ if it exists
        version_pattern = r"(__version__\s*=\s*['\"].*?['\"])"
        content = re.sub(version_pattern, lambda m: f'__version__ = "{self.new_name}"', content)
        
        # Update package name in setup.py imports if present
        if f'from {self.old_name}' in content:
            content = content.replace(f'from {self.old_name}', f'from {self.new_name}')
        
        return content
    
    def _handle_definitions(self, content: str) -> str:
        """Handle class and function definitions."""
        # Class definitions
        class_pattern = rf'class\s+{re.escape(self.old_name)}\b'
        content = re.sub(class_pattern, f'class {self.new_name}', content)
        
        # Function definitions
        func_pattern = rf'def\s+{re.escape(self.old_name)}\b'
        content = re.sub(func_pattern, f'def {self.new_name}', content)
        
        return content
    
    def _replace_python_import(self, match) -> str:
        """Replace Python import statements."""
        full_match = match.group(0)
        
        if full_match.startswith('import '):
            return full_match.replace(self.old_name, self.new_name)
        elif full_match.startswith('from '):
            return full_match.replace(self.old_name, self.new_name)
        else:
            return full_match


class JavaScriptFileHandler(BaseFileHandler):
    """Specialized handler for JavaScript/TypeScript files."""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.js', '.jsx', '.ts', '.tsx']
    
    def process(self, file_path: Path, content: str) -> str:
        """Process JavaScript/TypeScript file content."""
        
        # Handle import/export statements
        patterns = [
            rf'import.*?from\s+["\']\.\.?/?{re.escape(self.old_name)}["\']',
            rf'import\s*{re.escape(self.old_name)}',
            rf'from\s*["\']\.\.?/?{re.escape(self.old_name)}["\']',
        ]
        
        modified_content = content
        
        # Handle React components
        if file_path.suffix.lower() in ['.jsx', '.tsx']:
            modified_content = self._handle_react_components(modified_content)
        
        # Apply patterns
        for pattern in patterns:
            modified_content = re.sub(pattern, self._replace_js_import, modified_content)
        
        return modified_content
    
    def _handle_react_components(self, content: str) -> str:
        """Handle React component names."""
        # Component definitions
        comp_pattern = rf'(?:function|const)\s+{re.escape(self.old_name)}\s*(?:=|Component)'
        content = re.sub(comp_pattern, f'const {self.new_name} =', content)
        
        return content
    
    def _replace_js_import(self, match) -> str:
        """Replace JavaScript import statements."""
        return match.group(0).replace(self.old_name, self.new_name)


class JSONFileHandler(BaseFileHandler):
    """Specialized handler for JSON files."""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.json'
    
    def process(self, file_path: Path, content: str) -> str:
        """Process JSON file content."""
        try:
            data = json.loads(content)
            
            # Handle specific JSON files
            if file_path.name == 'package.json':
                return self._handle_package_json(data)
            elif file_path.name in ['tsconfig.json', 'jsconfig.json']:
                return self._handle_config_json(data)
            elif file_path.name == 'angular.json':
                return self._handle_angular_json(data)
            
            # General JSON replacement
            return self._replace_in_json_data(data, self.old_name, self.new_name)
        
        except json.JSONDecodeError:
            # Fallback to text replacement
            return content.replace(self.old_name, self.new_name)
    
    def _handle_package_json(self, data: Dict) -> str:
        """Handle package.json specific fields."""
        if 'name' in data:
            data['name'] = self.new_name
        
        if 'description' in data:
            data['description'] = data['description'].replace(self.old_name, self.new_name)
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _handle_config_json(self, data: Dict) -> str:
        """Handle configuration JSON files."""
        if 'compilerOptions' in data:
            opts = data['compilerOptions']
            if 'baseUrl' in opts and self.old_name in str(opts['baseUrl']):
                opts['baseUrl'] = str(opts['baseUrl']).replace(self.old_name, self.new_name)
        
        return json.dumps(data, indent=2)
    
    def _handle_angular_json(self, data: Dict) -> str:
        """Handle Angular configuration files."""
        if 'projects' in data:
            if self.old_name in data['projects']:
                data['projects'][self.new_name] = data['projects'].pop(self.old_name)
        
        return json.dumps(data, indent=2)
    
    def _replace_in_json_data(self, data: Any, old: str, new: str) -> Any:
        """Recursively replace strings in JSON data."""
        if isinstance(data, dict):
            return {k: self._replace_in_json_data(v, old, new) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_in_json_data(item, old, new) for item in data]
        elif isinstance(data, str):
            return data.replace(old, new)
        else:
            return data


class YAMLFileHandler(BaseFileHandler):
    """Specialized handler for YAML files."""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.yaml', '.yml']
    
    def process(self, file_path: Path, content: str) -> str:
        """Process YAML file content."""
        try:
            data = yaml.safe_load(content)
            
            # Handle specific YAML files
            if 'docker-compose' in content.lower():
                return self._handle_docker_compose(data)
            elif 'kubernetes' in content.lower() or 'k8s' in content.lower():
                return self._handle_k8s_yaml(data)
            
            # General YAML replacement
            modified_data = self._replace_in_yaml_data(data, self.old_name, self.new_name)
            return yaml.dump(modified_data, default_flow_style=False, allow_unicode=True)
        
        except yaml.YAMLError:
            # Fallback to text replacement
            return content.replace(self.old_name, self.new_name)
    
    def _handle_docker_compose(self, data: Dict) -> str:
        """Handle Docker Compose files."""
        if 'services' in data:
            if self.old_name in data['services']:
                data['services'][self.new_name] = data['services'].pop(self.old_name)
        
        return yaml.dump(data, default_flow_style=False)
    
    def _handle_k8s_yaml(self, data: Dict) -> str:
        """Handle Kubernetes YAML files."""
        if 'metadata' in data and 'name' in data['metadata']:
            if data['metadata']['name'] == self.old_name:
                data['metadata']['name'] = self.new_name
        
        return yaml.dump(data, default_flow_style=False)
    
    def _replace_in_yaml_data(self, data: Any, old: str, new: str) -> Any:
        """Recursively replace strings in YAML data."""
        if isinstance(data, dict):
            return {k: self._replace_in_yaml_data(v, old, new) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_in_yaml_data(item, old, new) for item in data]
        elif isinstance(data, str):
            return data.replace(old, new)
        else:
            return data


class XMLFileHandler(BaseFileHandler):
    """Specialized handler for XML files."""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.xml'
    
    def process(self, file_path: Path, content: str) -> str:
        """Process XML file content."""
        try:
            root = ET.fromstring(content)
            
            # Handle XML attributes and text content
            self._process_xml_element(root)
            
            # Convert back to string
            return ET.tostring(root, encoding='unicode', xml_declaration=True)
        
        except ET.ParseError:
            # Fallback to text replacement
            return content.replace(self.old_name, self.new_name)
    
    def _process_xml_element(self, element):
        """Recursively process XML elements."""
        # Process attributes
        for attr_name, attr_value in element.attrib.items():
            if self.old_name in attr_value:
                element.set(attr_name, attr_value.replace(self.old_name, self.new_name))
        
        # Process text content
        if element.text and self.old_name in element.text:
            element.text = element.text.replace(self.old_name, self.new_name)
        
        if element.tail and self.old_name in element.tail:
            element.tail = element.tail.replace(self.old_name, self.new_name)
        
        # Process child elements
        for child in element:
            self._process_xml_element(child)


class MarkdownFileHandler(BaseFileHandler):
    """Specialized handler for Markdown files."""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.md', '.rst', '.adoc']
    
    def process(self, file_path: Path, content: str) -> str:
        """Process Markdown file content."""
        
        # Handle links and references
        link_pattern = rf'\[([^\]]*?)\]\([^)]*?{re.escape(self.old_name)}[^)]*?\)'
        content = re.sub(link_pattern, rf'[\1]({self.new_name})', content)
        
        # Handle code blocks that might contain imports
        code_block_pattern = r'```[\s\S]*?```'
        content = re.sub(code_block_pattern, lambda m: self._process_code_block(m.group(0)), content)
        
        # Handle inline code
        inline_code_pattern = r'`([^`]*?)`'
        content = re.sub(inline_code_pattern, lambda m: self._process_inline_code(m.group(1)), content)
        
        # General text replacement
        content = content.replace(self.old_name, self.new_name)
        
        return content
    
    def _process_code_block(self, code_block: str) -> str:
        """Process code within code blocks."""
        # Extract language if present
        lang_match = re.match(r'```(\w+)?', code_block)
        language = lang_match.group(1) if lang_match else None
        
        code_content = re.sub(r'```\w*\n([\s\S]*?)```', r'\1', code_block)
        
        # Apply language-specific handlers
        if language:
            handler = self._get_handler_for_language(language)
            if handler:
                code_content = handler.process(Path(f'temp.{language}'), code_content)
        
        return f'```{language or ""}\n{code_content}\n```'
    
    def _process_inline_code(self, code: str) -> str:
        """Process inline code."""
        if any(keyword in code for keyword in ['import', 'from', 'require']):
            return code.replace(self.old_name, self.new_name)
        return f'`{code}`'
    
    def _get_handler_for_language(self, language: str) -> Optional[BaseFileHandler]:
        """Get the appropriate handler for a programming language."""
        handlers = {
            'python': PythonFileHandler,
            'javascript': JavaScriptFileHandler,
            'js': JavaScriptFileHandler,
            'typescript': JavaScriptFileHandler,
            'ts': JavaScriptFileHandler,
        }
        
        handler_class = handlers.get(language.lower())
        if handler_class:
            return handler_class(self.old_name, self.new_name)
        return None


class FileHandlerRegistry:
    """Registry for managing file handlers."""
    
    def __init__(self, old_name: str, new_name: str):
        self.handlers: List[BaseFileHandler] = [
            PythonFileHandler(old_name, new_name),
            JavaScriptFileHandler(old_name, new_name),
            JSONFileHandler(old_name, new_name),
            YAMLFileHandler(old_name, new_name),
            XMLFileHandler(old_name, new_name),
            MarkdownFileHandler(old_name, new_name),
        ]
    
    def get_handler(self, file_path: Path) -> Optional[BaseFileHandler]:
        """Get the appropriate handler for a file."""
        for handler in self.handlers:
            if handler.can_handle(file_path):
                return handler
        return None
    
    def process_file(self, file_path: Path, content: str) -> str:
        """Process a file with the appropriate handler."""
        handler = self.get_handler(file_path)
        if handler:
            return handler.process(file_path, content)
        return content.replace(self.old_name, self.new_name)