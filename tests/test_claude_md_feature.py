"""
Tests for CLAUDE.md Management Feature.

Tests cover:
- Backend methods in CMATInterface
- File operations (copy, check status, open editor)
- Error handling and validation
- Platform-specific functionality
"""

import json
import os
import platform
import subprocess
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call

import pytest

from ui.utils.cmat_interface import CMATInterface


class TestClaudeMdBackendMethods:
    """Test suite for CLAUDE.md backend methods in CMATInterface."""

    @pytest.fixture
    def mock_interface(self, cmat_test_env):
        """Create a mock CMATInterface with test environment."""
        interface = CMATInterface(str(cmat_test_env))
        interface.tasks = MagicMock()
        return interface

    @pytest.fixture
    def sample_claude_md(self, cmat_test_env):
        """Create a sample CLAUDE.md file for testing."""
        content = """# Project Context

This is a test project using Python and pytest.

## Architecture
- Modular design with service layer
- Test-driven development
"""
        claude_md = cmat_test_env / "CLAUDE.md"
        claude_md.write_text(content)
        return claude_md

    # =========================================================================
    # check_claude_md_status() Tests
    # =========================================================================

    def test_check_status_when_file_exists(self, mock_interface, sample_claude_md):
        """Test check_claude_md_status() returns correct data when file exists."""
        result = mock_interface.check_claude_md_status()

        assert result["exists"] is True
        assert result["path"] == str(sample_claude_md)
        assert result["size"] > 0
        assert isinstance(result["modified"], datetime)

    def test_check_status_when_file_not_exists(self, mock_interface):
        """Test check_claude_md_status() returns correct data when file missing."""
        result = mock_interface.check_claude_md_status()

        assert result["exists"] is False
        assert result["path"] is None
        assert result["size"] == 0
        assert result["modified"] is None

    def test_check_status_returns_correct_size(self, mock_interface, cmat_test_env):
        """Test check_claude_md_status() returns accurate file size."""
        # Create file with known size
        test_content = "A" * 1000  # 1000 bytes
        claude_md = cmat_test_env / "CLAUDE.md"
        claude_md.write_text(test_content)

        result = mock_interface.check_claude_md_status()

        assert result["size"] == 1000

    def test_check_status_performance(self, mock_interface, sample_claude_md):
        """Test check_claude_md_status() completes quickly (< 10ms)."""
        import time

        start = time.time()
        mock_interface.check_claude_md_status()
        duration = time.time() - start

        # Should be essentially instantaneous
        assert duration < 0.01, f"Status check took {duration}s, expected < 0.01s"

    # =========================================================================
    # copy_file_to_claude_md() Tests
    # =========================================================================

    def test_copy_valid_markdown_file(self, mock_interface, temp_dir):
        """Test copy_file_to_claude_md() successfully copies valid .md file."""
        # Create source file
        source = temp_dir / "source.md"
        source.write_text("# Test Content")

        success, message = mock_interface.copy_file_to_claude_md(str(source), overwrite_existing=True)

        assert success is True
        assert "Copied to" in message
        assert (mock_interface.project_root / "CLAUDE.md").exists()
        assert (mock_interface.project_root / "CLAUDE.md").read_text() == "# Test Content"

    def test_copy_preserves_file_metadata(self, mock_interface, temp_dir):
        """Test copy_file_to_claude_md() preserves file timestamps."""
        source = temp_dir / "source.md"
        source.write_text("Content")

        # Set specific modification time
        os.utime(source, (1000000000, 1000000000))

        mock_interface.copy_file_to_claude_md(str(source), overwrite_existing=True)

        target = mock_interface.project_root / "CLAUDE.md"
        # shutil.copy2 should preserve mtime
        assert abs(target.stat().st_mtime - 1000000000) < 1

    def test_copy_rejects_non_md_extension(self, mock_interface, temp_dir):
        """Test copy_file_to_claude_md() rejects non-.md files."""
        source = temp_dir / "source.txt"
        source.write_text("Content")

        success, message = mock_interface.copy_file_to_claude_md(str(source))

        assert success is False
        assert "must be a .md file" in message

    def test_copy_rejects_nonexistent_file(self, mock_interface):
        """Test copy_file_to_claude_md() handles missing source file."""
        success, message = mock_interface.copy_file_to_claude_md("/nonexistent/file.md")

        assert success is False
        assert "not found" in message.lower()

    def test_copy_warns_on_large_file(self, mock_interface, temp_dir):
        """Test copy_file_to_claude_md() warns when file > 50KB."""
        # Create 51KB file
        source = temp_dir / "large.md"
        source.write_text("A" * 51 * 1024)

        success, message = mock_interface.copy_file_to_claude_md(str(source))

        assert success is False
        assert "large" in message.lower()
        assert "51KB" in message or "52KB" in message  # Allow rounding

    def test_copy_respects_overwrite_flag(self, mock_interface, cmat_test_env):
        """Test copy_file_to_claude_md() respects overwrite_existing flag."""
        # Create existing CLAUDE.md
        existing = cmat_test_env / "CLAUDE.md"
        existing.write_text("Existing content")

        # Create source
        source = cmat_test_env / "source.md"
        source.write_text("New content")

        # Try without overwrite
        success, message = mock_interface.copy_file_to_claude_md(str(source), overwrite_existing=False)

        assert success is False
        assert "already exists" in message.lower()
        assert existing.read_text() == "Existing content"  # Unchanged

    def test_copy_allows_overwrite_when_flagged(self, mock_interface, cmat_test_env):
        """Test copy_file_to_claude_md() overwrites when flag is True."""
        # Create existing
        existing = cmat_test_env / "CLAUDE.md"
        existing.write_text("Old")

        # Create source
        source = cmat_test_env / "source.md"
        source.write_text("New")

        success, message = mock_interface.copy_file_to_claude_md(str(source), overwrite_existing=True)

        assert success is True
        assert existing.read_text() == "New"

    @patch('shutil.copy2')
    def test_copy_handles_permission_error(self, mock_copy, mock_interface, temp_dir):
        """Test copy_file_to_claude_md() handles permission errors gracefully."""
        source = temp_dir / "source.md"
        source.write_text("Content")

        mock_copy.side_effect = PermissionError("Access denied")

        success, message = mock_interface.copy_file_to_claude_md(str(source), overwrite_existing=True)

        assert success is False
        assert "permission denied" in message.lower()

    # =========================================================================
    # open_claude_md_in_editor() Tests
    # =========================================================================

    def test_open_editor_when_file_not_exists(self, mock_interface):
        """Test open_claude_md_in_editor() returns error when file missing."""
        success, message = mock_interface.open_claude_md_in_editor()

        assert success is False
        assert "not found" in message.lower()

    @patch('platform.system')
    @patch('subprocess.Popen')
    def test_open_editor_on_macos(self, mock_popen, mock_system, mock_interface, sample_claude_md):
        """Test open_claude_md_in_editor() uses 'open' command on macOS."""
        mock_system.return_value = "Darwin"
        mock_popen.return_value = Mock()

        success, message = mock_interface.open_claude_md_in_editor()

        assert success is True
        mock_popen.assert_called_once_with(["open", str(sample_claude_md)])

    @patch('platform.system')
    def test_open_editor_on_windows(self, mock_system, mock_interface, sample_claude_md):
        """Test open_claude_md_in_editor() uses os.startfile on Windows."""
        mock_system.return_value = "Windows"

        # Mock os.startfile since it doesn't exist on non-Windows
        with patch('os.startfile', create=True) as mock_startfile:
            success, message = mock_interface.open_claude_md_in_editor()

            assert success is True
            mock_startfile.assert_called_once_with(str(sample_claude_md))

    @patch('platform.system')
    @patch('subprocess.Popen')
    def test_open_editor_on_linux(self, mock_popen, mock_system, mock_interface, sample_claude_md):
        """Test open_claude_md_in_editor() uses xdg-open on Linux."""
        mock_system.return_value = "Linux"
        mock_popen.return_value = Mock()

        success, message = mock_interface.open_claude_md_in_editor()

        assert success is True
        mock_popen.assert_called_once_with(["xdg-open", str(sample_claude_md)])

    @patch('platform.system')
    @patch('subprocess.Popen')
    def test_open_editor_handles_command_not_found(self, mock_popen, mock_system, mock_interface, sample_claude_md):
        """Test open_claude_md_in_editor() handles missing editor command."""
        mock_system.return_value = "Linux"
        mock_popen.side_effect = FileNotFoundError("xdg-open not found")

        success, message = mock_interface.open_claude_md_in_editor()

        assert success is False
        assert "not found" in message.lower()

    @patch('platform.system')
    @patch('subprocess.Popen')
    def test_open_editor_handles_generic_exception(self, mock_popen, mock_system, mock_interface, sample_claude_md):
        """Test open_claude_md_in_editor() handles unexpected errors."""
        mock_system.return_value = "Darwin"
        mock_popen.side_effect = Exception("Unexpected error")

        success, message = mock_interface.open_claude_md_in_editor()

        assert success is False
        assert "failed" in message.lower()

class TestClaudeMdIntegrationScenarios:
    """Integration tests for complete CLAUDE.md workflows."""

    @pytest.fixture
    def interface(self, cmat_test_env):
        """Create real CMATInterface for integration tests."""
        interface = CMATInterface(str(cmat_test_env))
        return interface

    def test_complete_workflow_create_check_edit(self, interface, temp_dir):
        """Test complete workflow: create → check status → edit."""
        # 1. Initial status check
        status = interface.check_claude_md_status()
        assert status["exists"] is False

        # 2. Copy a file to create CLAUDE.md
        source = temp_dir / "template.md"
        source.write_text("# Project Template")
        success, _ = interface.copy_file_to_claude_md(str(source), overwrite_existing=True)
        assert success is True

        # 3. Verify status updated
        status = interface.check_claude_md_status()
        assert status["exists"] is True
        assert status["size"] > 0

        # 4. Edit should now work (mock the editor)
        with patch('platform.system', return_value="Darwin"):
            with patch('subprocess.Popen') as mock_popen:
                success, _ = interface.open_claude_md_in_editor()
                assert success is True
                assert mock_popen.called

    def test_overwrite_protection_workflow(self, interface, temp_dir):
        """Test workflow where overwrite protection prevents data loss."""
        # Create original
        source1 = temp_dir / "original.md"
        source1.write_text("Original content")
        interface.copy_file_to_claude_md(str(source1), overwrite_existing=True)

        # Try to overwrite without flag
        source2 = temp_dir / "new.md"
        source2.write_text("New content")
        success, message = interface.copy_file_to_claude_md(str(source2), overwrite_existing=False)

        assert success is False
        assert "already exists" in message.lower()

        # Verify original unchanged
        claude_md = interface.project_root / "CLAUDE.md"
        assert claude_md.read_text() == "Original content"

    def test_large_file_warning_workflow(self, interface, temp_dir):
        """Test workflow with large file warning."""
        # Create large file
        large = temp_dir / "large.md"
        large.write_text("X" * 60 * 1024)  # 60KB

        success, message = interface.copy_file_to_claude_md(str(large))

        assert success is False
        assert "large" in message.lower() or "60" in message


class TestClaudeMdEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def interface(self, cmat_test_env):
        return CMATInterface(str(cmat_test_env))

    def test_check_status_with_special_characters_in_path(self, temp_dir):
        """Test status check works with special characters in path."""
        # Create dir with spaces and special chars
        special_dir = temp_dir / "My Project (Test)"
        special_dir.mkdir()
        (special_dir / ".claude").mkdir()

        interface = CMATInterface(str(special_dir))

        # Create CLAUDE.md
        (special_dir / "CLAUDE.md").write_text("Test")

        status = interface.check_claude_md_status()
        assert status["exists"] is True

    def test_copy_with_unicode_content(self, interface, temp_dir):
        """Test copying file with unicode content."""
        source = temp_dir / "unicode.md"
        source.write_text("# 你好世界\n\nTesting emoji: 🚀🎉")

        success, _ = interface.copy_file_to_claude_md(str(source), overwrite_existing=True)

        assert success is True
        claude_md = interface.project_root / "CLAUDE.md"
        assert "你好世界" in claude_md.read_text()
        assert "🚀" in claude_md.read_text()

    def test_copy_empty_markdown_file(self, interface, temp_dir):
        """Test copying empty .md file is allowed."""
        source = temp_dir / "empty.md"
        source.write_text("")

        success, _ = interface.copy_file_to_claude_md(str(source), overwrite_existing=True)

        assert success is True
        assert (interface.project_root / "CLAUDE.md").exists()

    def test_copy_markdown_with_uppercase_extension(self, interface, temp_dir):
        """Test .MD (uppercase) extension is accepted (case insensitive)."""
        source = temp_dir / "file.MD"
        source.write_text("Content")

        success, message = interface.copy_file_to_claude_md(str(source), overwrite_existing=True)

        # Implementation uses .lower() == ".md" so .MD should be accepted
        assert success is True
        assert (interface.project_root / "CLAUDE.md").exists()

    def test_concurrent_status_checks(self, interface, temp_dir):
        """Test multiple concurrent status checks don't cause issues."""
        import threading

        results = []

        def check_status():
            result = interface.check_claude_md_status()
            results.append(result)

        threads = [threading.Thread(target=check_status) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should return consistent results
        assert len(results) == 10
        assert all(r["exists"] == results[0]["exists"] for r in results)


# Additional test for acceptance criteria validation
class TestAcceptanceCriteria:
    """Tests mapped to specific acceptance criteria from requirements."""

    @pytest.fixture
    def interface(self, cmat_test_env):
        interface = CMATInterface(str(cmat_test_env))
        interface.tasks = MagicMock()
        return interface

    def test_ac_us2_copy_existing_file(self, interface, temp_dir):
        """
        US-2 AC: System copies file to project root as CLAUDE.md.
        """
        source = temp_dir / "existing.md"
        source.write_text("# Existing Config")

        success, _ = interface.copy_file_to_claude_md(str(source), overwrite_existing=True)

        assert success is True
        target = interface.project_root / "CLAUDE.md"
        assert target.exists()
        assert target.name == "CLAUDE.md"

    def test_ac_us2_warn_if_exists(self, interface, temp_dir):
        """
        US-2 AC: User is warned if CLAUDE.md already exists with option to overwrite.
        """
        # Create existing
        (interface.project_root / "CLAUDE.md").write_text("Existing")

        source = temp_dir / "new.md"
        source.write_text("New")

        success, message = interface.copy_file_to_claude_md(str(source), overwrite_existing=False)

        assert success is False
        assert "already exists" in message.lower()

    def test_ac_us3_edit_opens_file(self, interface):
        """
        US-3 AC: File opens in appropriate editor.
        """
        # Create file
        (interface.project_root / "CLAUDE.md").write_text("Content")

        with patch('platform.system', return_value="Darwin"):
            with patch('subprocess.Popen') as mock_popen:
                success, _ = interface.open_claude_md_in_editor()

                assert success is True
                assert mock_popen.called

    def test_ac_us4_status_shows_present_or_not(self, interface):
        """
        US-4 AC: Status shows "Present" or "Not configured".
        """
        # Test not present
        status = interface.check_claude_md_status()
        assert status["exists"] is False

        # Create file
        (interface.project_root / "CLAUDE.md").write_text("Content")

        # Test present
        status = interface.check_claude_md_status()
        assert status["exists"] is True
