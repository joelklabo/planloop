"""Plugin system for custom domain-specific analyzers."""
from __future__ import annotations

import importlib.util
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .suggest import TaskSuggestion


class AnalyzerPlugin(ABC):
    """Base class for analyzer plugins."""
    
    @abstractmethod
    def analyze(self, project_root: Path) -> list[dict[str, Any]]:
        """Analyze project and return findings.
        
        Args:
            project_root: Root directory of project
            
        Returns:
            List of findings (plugin-specific format)
        """
        pass
    
    @abstractmethod
    def generate_suggestions(self, findings: list[dict[str, Any]]) -> list[TaskSuggestion]:
        """Generate task suggestions from findings.
        
        Args:
            findings: Analysis findings
            
        Returns:
            List of task suggestions
        """
        pass


class PluginRegistry:
    """Registry for managing analyzer plugins."""
    
    def __init__(self):
        """Initialize empty plugin registry."""
        self._plugins: dict[str, AnalyzerPlugin] = {}
    
    def register(self, name: str, plugin: AnalyzerPlugin) -> None:
        """Register a plugin.
        
        Args:
            name: Plugin identifier
            plugin: Plugin instance
        """
        self._plugins[name] = plugin
    
    def get_plugin(self, name: str) -> AnalyzerPlugin | None:
        """Get a registered plugin.
        
        Args:
            name: Plugin identifier
            
        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(name)
    
    def list_plugins(self) -> list[str]:
        """List all registered plugin names.
        
        Returns:
            List of plugin identifiers
        """
        return list(self._plugins.keys())
    
    def load_from_directory(self, plugin_dir: Path) -> int:
        """Load plugins from a directory.
        
        Args:
            plugin_dir: Directory containing plugin files
            
        Returns:
            Number of plugins loaded
        """
        if not plugin_dir.exists():
            return 0
        
        loaded_count = 0
        
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
                
            try:
                # Load module
                spec = importlib.util.spec_from_file_location(
                    f"planloop_plugin_{plugin_file.stem}",
                    plugin_file
                )
                
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = module
                    spec.loader.exec_module(module)
                    
                    # Find AnalyzerPlugin subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, AnalyzerPlugin) and 
                            attr is not AnalyzerPlugin):
                            # Instantiate and register
                            plugin_instance = attr()
                            self.register(plugin_file.stem, plugin_instance)
                            loaded_count += 1
                            
            except Exception:
                # Silently skip plugins that fail to load
                pass
        
        return loaded_count
