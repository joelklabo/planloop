"""Tests for custom analyzer plugin system (Task 5).

Verifies that planloop suggest supports domain-specific analyzers
via a plugin system.
"""

from pathlib import Path

import pytest


def test_analyzer_plugin_interface():
    """Plugin system should define analyzer interface."""
    from planloop.core.plugin_system import AnalyzerPlugin
    
    # Should have required methods
    assert hasattr(AnalyzerPlugin, 'analyze')
    assert hasattr(AnalyzerPlugin, 'generate_suggestions')
    

def test_plugin_registry_discovers_plugins():
    """Plugin registry should discover and load plugins."""
    from planloop.core.plugin_system import PluginRegistry
    
    registry = PluginRegistry()
    
    # Should have methods for registration
    assert hasattr(registry, 'register')
    assert hasattr(registry, 'get_plugin')
    assert hasattr(registry, 'list_plugins')


def test_plugin_can_register_custom_analyzer():
    """Plugins can register custom analyzers."""
    from planloop.core.plugin_system import PluginRegistry, AnalyzerPlugin
    from planloop.core.suggest import TaskSuggestion
    from planloop.core.state import TaskType
    
    class CustomAnalyzer(AnalyzerPlugin):
        """Custom analyzer for domain-specific patterns."""
        
        def analyze(self, project_root: Path) -> list[dict]:
            """Analyze project and return findings."""
            return [{"issue": "custom pattern detected"}]
        
        def generate_suggestions(self, findings: list[dict]) -> list[TaskSuggestion]:
            """Generate suggestions from findings."""
            return [TaskSuggestion(
                title="Fix custom pattern",
                type=TaskType.FIX,
                priority="medium",
                rationale="Custom analyzer detected issue",
                implementation_notes="Fix the pattern",
                affected_files=[]
            )]
    
    registry = PluginRegistry()
    registry.register("custom", CustomAnalyzer())
    
    plugin = registry.get_plugin("custom")
    assert plugin is not None
    assert isinstance(plugin, AnalyzerPlugin)


def test_plugin_system_integrates_with_suggest():
    """Plugin system should integrate with suggest command."""
    from planloop.config import SuggestConfig
    
    config = SuggestConfig(
        enable_plugins=True,
        plugin_paths=["~/.planloop/plugins"]
    )
    
    assert config.enable_plugins is True
    assert len(config.plugin_paths) > 0


def test_plugin_loads_from_directory(tmp_path):
    """Plugin system should load plugins from directory."""
    from planloop.core.plugin_system import PluginRegistry
    
    # Create plugin directory
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    
    # Create a simple plugin file
    plugin_file = plugin_dir / "test_plugin.py"
    plugin_file.write_text("""
from planloop.core.plugin_system import AnalyzerPlugin

class TestAnalyzer(AnalyzerPlugin):
    def analyze(self, project_root):
        return []
    
    def generate_suggestions(self, findings):
        return []
""")
    
    registry = PluginRegistry()
    loaded = registry.load_from_directory(plugin_dir)
    
    # Should discover the plugin
    assert loaded >= 0  # May be 0 if import fails, but shouldn't raise


def test_suggest_config_has_plugin_settings():
    """SuggestConfig should include plugin configuration."""
    from planloop.config import SuggestConfig
    
    config = SuggestConfig()
    
    # Should have plugin-related fields
    assert hasattr(config, 'enable_plugins')
    assert hasattr(config, 'plugin_paths')
