"""Tests for agents.md guide versioning and updates (Task 6).

Verifies that guide content can be updated when prompts change,
preventing agents from working with stale instructions.
"""


from planloop.guide import detect_marker, insert_guide, render_guide


def test_guide_can_be_updated_when_prompts_change(tmp_path):
    """Guide content should be updatable when prompts change."""
    target = tmp_path / "AGENTS.md"

    # First installation
    guide_v1 = render_guide()
    insert_guide(target, guide_v1)

    assert target.exists()
    content_v1 = target.read_text()
    assert "PLANLOOP-INSTALLED" in content_v1

    # Simulate prompt change (mock new version)
    guide_v2 = guide_v1 + "\n\n## New Section\nThis is updated content."

    # Should update when force=True
    insert_guide(target, guide_v2, force=True)

    content_v2 = target.read_text()
    assert "New Section" in content_v2
    assert "updated content" in content_v2


def test_guide_marker_includes_version():
    """Marker should include version for tracking changes."""
    from planloop.guide import MARKER, get_guide_version

    # Marker should have version info
    assert "version" in MARKER.lower() or "v" in MARKER.lower()

    # Should be able to extract version
    version = get_guide_version()
    assert version is not None
    assert isinstance(version, str)


def test_detect_outdated_guide(tmp_path):
    """Should detect when installed guide is outdated."""
    from planloop.guide import is_guide_outdated

    target = tmp_path / "AGENTS.md"

    # Install old version
    old_marker = "<!-- PLANLOOP-INSTALLED v1.0 -->"
    target.write_text(f"# Guide\n{old_marker}\nOld content")

    assert detect_marker(target.read_text())

    # Current version is newer
    assert is_guide_outdated(target.read_text()) is True


def test_guide_update_preserves_custom_content(tmp_path):
    """Updating guide should preserve user's custom additions."""
    target = tmp_path / "AGENTS.md"

    # Initial install with user additions
    guide_v1 = render_guide()
    insert_guide(target, guide_v1)

    # User adds custom content
    with target.open("a") as f:
        f.write("\n\n## My Custom Section\nUser-specific notes")

    content_before = target.read_text()
    assert "My Custom Section" in content_before

    # Update guide
    guide_v2 = render_guide()
    insert_guide(target, guide_v2, force=True)

    content_after = target.read_text()
    # Custom content should still be there
    assert "My Custom Section" in content_after
    assert "User-specific notes" in content_after


def test_guide_cli_apply_respects_version(tmp_path, monkeypatch):
    """planloop guide --apply should update when version changes."""
    import os

    # Change to tmp_path so relative paths work
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Create docs directory
        agents_md = tmp_path / "docs" / "agents.md"
        agents_md.parent.mkdir(parents=True)

        from typer.testing import CliRunner

        from planloop.cli import app

        runner = CliRunner()

        # First apply (using default path)
        result = runner.invoke(app, ["guide", "--apply"])
        assert result.exit_code == 0
        assert agents_md.exists()

        content = agents_md.read_text()
        assert "PLANLOOP-INSTALLED v2.0" in content

        # Modify to simulate old version
        content = content.replace("v2.0", "v1.0")
        agents_md.write_text(content)

        # Second apply with new version should update
        result = runner.invoke(app, ["guide", "--apply"])
        assert result.exit_code == 0

        final_content = agents_md.read_text()
        # Should have latest version marker
        assert "v2.0" in final_content
        assert final_content.count("v1.0") == 0  # Old version should be gone
    finally:
        os.chdir(original_cwd)
