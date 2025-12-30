"""
CMAT Template Installer - downloads and installs Claude Multi-Agent Template from GitHub.

This module provides functionality to:
- Download CMAT template from GitHub as a ZIP archive
- Extract and validate the template structure
- Install to user-specified directory with security validations
- Rollback on failure with automatic cleanup
"""

import os
import ssl
import tempfile
import shutil
import zipfile
import uuid
import json
from pathlib import Path
from typing import Optional, Callable, Tuple, List
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError


# =============================================================================
# Exception Hierarchy
# =============================================================================

class CMATInstallerError(Exception):
    """Base exception for installer errors."""
    error_title = "Installation Failed"


class SecurityError(CMATInstallerError):
    """Security validation failed."""
    error_title = "Installation Failed: Security Check Failed"


class NetworkError(CMATInstallerError):
    """Network operation failed."""
    error_title = "Installation Failed: Network Error"


class ValidationError(CMATInstallerError):
    """Installation validation failed."""
    error_title = "Installation Failed: Invalid Template"


# =============================================================================
# Configuration Constants
# =============================================================================

# GitHub repository configuration
# NOTE: These defaults point to the expected location but can be overridden in __init__
DEFAULT_GITHUB_OWNER = "dasien"
DEFAULT_GITHUB_REPO = "ClaudeMultiAgentTemplate"
DEFAULT_GITHUB_BRANCH = "main"

# Fallback files for CMAT validation (used only if manifest.json is missing)
# Updated for CMAT v10.0+ package structure
FALLBACK_REQUIRED_FILES = [
    "settings.json",
    "agents/agents.json",
    "skills/skills.json",
]


def get_templates_dir() -> Optional[Path]:
    """
    Find the templates directory from the installed CMAT package.

    Returns:
        Path to templates directory, or None if not found
    """
    # Try to find templates relative to this file's package location
    # src/ui/utils/cmat_installer.py -> src/ui/utils -> src/ui -> src -> templates
    this_file = Path(__file__).resolve()

    # Go up from src/ui/utils to src, then look for sibling templates/
    src_dir = this_file.parent.parent.parent  # src/
    templates_dir = src_dir.parent / "templates"

    if templates_dir.exists() and (templates_dir / ".claude").exists():
        return templates_dir

    # Also check if running from an installed package
    # In that case, templates might be in the package data
    try:
        import importlib.resources
        # Try to find templates in package resources
        # This would require templates to be included in package_data
        pass
    except ImportError:
        pass

    return None

# Manifest file location
MANIFEST_FILE = "manifest.json"

# System directories to block (cross-platform)
SYSTEM_DIRECTORIES = {
    # Unix/Linux/macOS
    "/usr", "/bin", "/sbin", "/etc", "/var", "/tmp", "/boot",
    "/dev", "/proc", "/sys", "/System", "/Library",
    # Windows
    "C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)",
    "C:\\ProgramData", "C:\\System32",
}

# Network timeouts
DOWNLOAD_TIMEOUT_SECONDS = 30
CONNECTION_TIMEOUT_SECONDS = 10

# Size limits
MAX_DOWNLOAD_SIZE_MB = 50
MIN_REQUIRED_DISK_SPACE_MB = 10


# =============================================================================
# Installation State Tracking
# =============================================================================

class InstallationState:
    """Track installation state for cleanup and rollback."""

    def __init__(self):
        self.temp_dir: Optional[Path] = None
        self.zip_path: Optional[Path] = None
        self.backup_path: Optional[Path] = None
        self.extracted_path: Optional[Path] = None


# =============================================================================
# CMATInstaller Class
# =============================================================================

class CMATInstaller:
    """
    Installer for Claude Multi-Agent Template (CMAT).

    Handles download from GitHub, extraction to target directory,
    validation of installation, and rollback on failure.

    Example:
        installer = CMATInstaller(Path("/home/user/myproject"))
        success = installer.install(progress_callback=my_progress_fn)
    """

    def __init__(
        self,
        target_directory: Path,
        github_owner: str = DEFAULT_GITHUB_OWNER,
        github_repo: str = DEFAULT_GITHUB_REPO,
        github_branch: str = DEFAULT_GITHUB_BRANCH
    ):
        """
        Initialize installer.

        Args:
            target_directory: Directory where .claude/ will be installed
            github_owner: GitHub repository owner (default: "anthropics")
            github_repo: GitHub repository name (default: "ClaudeMultiAgentTemplate")
            github_branch: Branch to download from (default: "main")

        Raises:
            ValueError: If target_directory is invalid
        """
        if not isinstance(target_directory, Path):
            target_directory = Path(target_directory)

        self.target_directory = target_directory.resolve()
        self.owner = github_owner
        self.repo = github_repo
        self.branch = github_branch

        # Construct GitHub URL
        self.github_url = (
            f"https://github.com/{self.owner}/{self.repo}/"
            f"archive/refs/heads/{self.branch}.zip"
        )

    def install(
        self,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        overwrite: bool = False
    ) -> bool:
        """
        Perform complete installation: download → extract → validate → install.

        Args:
            progress_callback: Optional callback(message: str, percent: int)
            overwrite: Whether to overwrite existing .claude folder

        Returns:
            True if installation successful, False otherwise

        Raises:
            CMATInstallerError: If installation fails
            SecurityError: If security validation fails
            NetworkError: If download fails
            ValidationError: If validation fails
        """
        state = InstallationState()

        if progress_callback is None:
            # Provide no-op callback if none provided
            progress_callback = lambda msg, pct: None

        try:
            progress_callback("Initializing installation...", 0)

            # Pre-flight validations
            is_valid, error_msg = self.validate_target_directory()
            if not is_valid:
                raise SecurityError(f"Invalid target directory: {error_msg}")

            # Check for existing installation
            if not overwrite and self.check_existing_installation():
                raise ValidationError(
                    "A .claude folder already exists in the target directory. "
                    "Please remove it or choose a different directory."
                )

            # Backup existing installation if overwriting
            if overwrite and self.check_existing_installation():
                progress_callback("Backing up existing installation...", 5)
                state.backup_path = self._backup_existing()

            # Create temp directory
            state.temp_dir = Path(tempfile.mkdtemp(prefix="cmat_install_"))

            # Download ZIP from GitHub
            progress_callback("Downloading template from GitHub...", 10)
            state.zip_path = self._download_zip(state.temp_dir, progress_callback)
            progress_callback("Download complete, extracting...", 30)

            # Extract ZIP
            state.extracted_path = self._extract_zip(state.zip_path, state.temp_dir, progress_callback)
            progress_callback("Extraction complete, validating...", 70)

            # Validate structure
            if not self._validate_structure(state.extracted_path):
                raise ValidationError(
                    "Downloaded template does not have the expected CMAT structure. "
                    "Required files are missing."
                )
            progress_callback("Validation complete, finalizing installation...", 90)

            # Move to target (atomic operation)
            self._move_to_target(state.extracted_path)

            # Success - cleanup temp files
            self._cleanup_temp(state.temp_dir)
            if state.backup_path:
                # Remove backup since installation succeeded
                shutil.rmtree(state.backup_path, ignore_errors=True)

            progress_callback("Installation complete!", 100)
            return True

        except Exception as e:
            # Rollback on any error
            progress_callback("Installation failed, cleaning up...", 0)
            self._rollback(state)
            raise

    def install_local(
        self,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        overwrite: bool = False
    ) -> bool:
        """
        Perform local installation from bundled templates (no network required).

        This copies templates from the installed CMAT package to the target directory.

        Args:
            progress_callback: Optional callback(message: str, percent: int)
            overwrite: Whether to overwrite existing .claude folder

        Returns:
            True if installation successful, False otherwise

        Raises:
            CMATInstallerError: If installation fails
            ValidationError: If templates not found or validation fails
        """
        state = InstallationState()

        if progress_callback is None:
            progress_callback = lambda msg, pct: None

        try:
            progress_callback("Initializing local installation...", 0)

            # Find templates directory
            templates_dir = get_templates_dir()
            if not templates_dir:
                raise ValidationError(
                    "Could not find CMAT templates. "
                    "Please ensure CMAT is properly installed."
                )

            source_claude = templates_dir / ".claude"
            if not source_claude.exists():
                raise ValidationError(
                    f"Templates directory missing .claude folder: {templates_dir}"
                )

            progress_callback("Found templates, validating target...", 10)

            # Pre-flight validations
            is_valid, error_msg = self.validate_target_directory()
            if not is_valid:
                raise SecurityError(f"Invalid target directory: {error_msg}")

            # Check for existing installation
            target_claude = self.target_directory / ".claude"
            if not overwrite and target_claude.exists():
                raise ValidationError(
                    "A .claude folder already exists in the target directory. "
                    "Please remove it or choose a different directory."
                )

            # Backup existing installation if overwriting
            if overwrite and target_claude.exists():
                progress_callback("Backing up existing installation...", 20)
                state.backup_path = self._backup_existing()

            progress_callback("Copying templates...", 30)

            # Copy .claude folder
            try:
                if target_claude.exists():
                    shutil.rmtree(target_claude)
                shutil.copytree(source_claude, target_claude)
            except Exception as e:
                raise ValidationError(f"Failed to copy templates: {str(e)}")

            progress_callback("Validating installation...", 70)

            # Validate the copied structure
            if not self._validate_structure(target_claude):
                raise ValidationError(
                    "Installation validation failed. Required files may be missing."
                )

            progress_callback("Creating enhancements directory...", 85)

            # Create enhancements directory
            enhancements_dir = self.target_directory / "enhancements"
            enhancements_dir.mkdir(exist_ok=True)

            # Remove backup since installation succeeded
            if state.backup_path:
                shutil.rmtree(state.backup_path, ignore_errors=True)

            progress_callback("Installation complete!", 100)
            return True

        except Exception as e:
            progress_callback("Installation failed, cleaning up...", 0)
            self._rollback(state)
            raise

    def validate_target_directory(self) -> Tuple[bool, Optional[str]]:
        """
        Validate target directory is safe and writable.

        Returns:
            (is_valid, error_message) tuple
        """
        # Check if it's a system directory
        if self._is_system_directory(self.target_directory):
            return False, "Cannot install to system directories"

        # Check if directory exists
        if not self.target_directory.exists():
            return False, "Directory does not exist"

        # Check if it's a directory
        if not self.target_directory.is_dir():
            return False, "Path is not a directory"

        # Check if writable
        if not self._check_writable(self.target_directory):
            return False, "Directory is not writable (permission denied)"

        return True, None

    def check_existing_installation(self) -> bool:
        """
        Check if .claude folder already exists.

        Returns:
            True if .claude exists, False otherwise
        """
        claude_dir = self.target_directory / ".claude"
        return claude_dir.exists() and claude_dir.is_dir()

    # =========================================================================
    # Private Methods - Download
    # =========================================================================

    def _download_zip(
        self,
        temp_dir: Path,
        progress_callback: Callable[[str, int], None]
    ) -> Path:
        """
        Download ZIP from GitHub to temp directory.

        Args:
            temp_dir: Temporary directory for download
            progress_callback: Progress callback function

        Returns:
            Path to downloaded ZIP file

        Raises:
            NetworkError: If download fails
            SecurityError: If URL is not HTTPS
        """
        # Ensure HTTPS
        if not self.github_url.startswith("https://"):
            raise SecurityError("Only HTTPS downloads are allowed")

        zip_path = temp_dir / f"{self.repo}.zip"

        try:
            # Create SSL context with certificate verification
            context = ssl.create_default_context()

            # Create request
            req = urllib_request.Request(self.github_url)
            req.add_header('User-Agent', 'ClaudeMultiAgentUI-Installer/1.0')

            # Download with timeout
            with urllib_request.urlopen(req, timeout=DOWNLOAD_TIMEOUT_SECONDS, context=context) as response:
                total_size = int(response.headers.get('Content-Length', 0))

                # Check size limit
                if total_size > MAX_DOWNLOAD_SIZE_MB * 1024 * 1024:
                    raise NetworkError(
                        f"Download size ({total_size / 1024 / 1024:.1f} MB) exceeds "
                        f"maximum allowed ({MAX_DOWNLOAD_SIZE_MB} MB)"
                    )

                # Download in chunks with progress
                downloaded = 0
                chunk_size = 8192
                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Update progress (10-30% range for download)
                        if total_size > 0:
                            percent = 10 + int((downloaded / total_size) * 20)
                            progress_callback(
                                f"Downloading... {downloaded / 1024 / 1024:.1f} MB "
                                f"/ {total_size / 1024 / 1024:.1f} MB",
                                percent
                            )

            return zip_path

        except HTTPError as e:
            if e.code == 404:
                raise NetworkError(
                    f"Template repository not found at {self.github_url}. "
                    "Please verify the repository exists."
                )
            else:
                raise NetworkError(f"HTTP error {e.code}: {e.reason}")

        except URLError as e:
            raise NetworkError(f"Network error: {e.reason}")

        except Exception as e:
            raise NetworkError(f"Download failed: {str(e)}")

    # =========================================================================
    # Private Methods - Extraction
    # =========================================================================

    def _extract_zip(
        self,
        zip_path: Path,
        temp_dir: Path,
        progress_callback: Callable[[str, int], None]
    ) -> Path:
        """
        Safely extract ZIP to temp directory.

        Args:
            zip_path: Path to ZIP file
            temp_dir: Temporary directory for extraction
            progress_callback: Progress callback function

        Returns:
            Path to extracted .claude folder

        Raises:
            SecurityError: If ZIP contains unsafe entries
            ValidationError: If ZIP is corrupted or invalid
        """
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Validate ZIP integrity
                if zf.testzip() is not None:
                    raise ValidationError("ZIP file is corrupted")

                members = zf.namelist()
                total_members = len(members)

                for idx, member in enumerate(members):
                    # Security validation
                    if not self._validate_zip_entry(member):
                        raise SecurityError(f"ZIP contains unsafe entry: {member}")

                    # Extract member
                    zf.extract(member, extract_dir)

                    # Update progress (30-70% range for extraction)
                    if idx % 10 == 0 or idx == total_members - 1:
                        percent = 30 + int((idx / total_members) * 40)
                        progress_callback(
                            f"Extracting files... {idx + 1} / {total_members}",
                            percent
                        )

        except zipfile.BadZipFile:
            raise ValidationError("Invalid or corrupted ZIP file")
        except Exception as e:
            if isinstance(e, (SecurityError, ValidationError)):
                raise
            raise ValidationError(f"Extraction failed: {str(e)}")

        # Find the .claude folder in the extracted content
        # GitHub ZIP archives have format: {repo}-{branch}/.claude/...
        claude_dir = None
        for item in extract_dir.iterdir():
            if item.is_dir():
                potential_claude = item / ".claude"
                if potential_claude.exists() and potential_claude.is_dir():
                    claude_dir = potential_claude
                    break

        if not claude_dir:
            raise ValidationError(
                "Could not find .claude folder in downloaded template. "
                "The repository structure may have changed."
            )

        return claude_dir

    def _validate_zip_entry(self, zip_entry_name: str) -> bool:
        """
        Validate ZIP entry doesn't contain directory traversal.

        Args:
            zip_entry_name: Name of ZIP entry

        Returns:
            True if safe, False if dangerous
        """
        # Normalize path
        normalized = os.path.normpath(zip_entry_name)

        # Check for directory traversal
        if ".." in normalized.split(os.sep):
            return False

        # Check for absolute path
        if os.path.isabs(normalized):
            return False

        # Check for suspicious characters (Windows)
        if any(char in normalized for char in ['<', '>', ':', '"', '|', '?', '*']):
            return False

        return True

    # =========================================================================
    # Private Methods - Validation
    # =========================================================================

    def _validate_structure(self, claude_dir: Path) -> bool:
        """
        Validate extracted .claude folder using manifest.json or fallback validation.

        Args:
            claude_dir: Path to .claude folder

        Returns:
            True if valid structure, False otherwise
        """
        manifest_path = claude_dir / MANIFEST_FILE

        # Try manifest-based validation first
        if manifest_path.exists():
            try:
                return self._validate_with_manifest(claude_dir, manifest_path)
            except Exception:
                # If manifest validation fails, fall back to hardcoded validation
                pass

        # Fallback to hardcoded validation
        return self._validate_with_fallback(claude_dir)

    def _validate_with_manifest(self, claude_dir: Path, manifest_path: Path) -> bool:
        """
        Validate structure using manifest.json.

        Args:
            claude_dir: Path to .claude folder
            manifest_path: Path to manifest.json file

        Returns:
            True if all required files/directories exist, False otherwise
        """
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            # Get the structure definition
            structure = manifest.get('structure', {})
            claude_structure = structure.get('.claude', {})

            if not claude_structure:
                return False

            # Validate the structure recursively
            missing_files = self._validate_structure_recursive(claude_dir, claude_structure)

            # Return True only if no files are missing
            return len(missing_files) == 0

        except (json.JSONDecodeError, KeyError, IOError):
            return False

    def _validate_structure_recursive(
        self,
        base_path: Path,
        structure: dict,
        rel_path: str = ""
    ) -> List[str]:
        """
        Recursively validate directory structure against manifest.

        Args:
            base_path: Base directory path
            structure: Structure definition from manifest
            rel_path: Relative path for error reporting

        Returns:
            List of missing file paths (empty if all present)
        """
        missing = []

        for key, value in structure.items():
            current_rel = f"{rel_path}/{key}" if rel_path else key

            # Handle special _files key (files directly in current directory)
            if key == '_files' and isinstance(value, list):
                for filename in value:
                    file_path = base_path / filename
                    if not file_path.exists():
                        missing.append(f"{rel_path}/{filename}" if rel_path else filename)
                continue

            if isinstance(value, list):
                # It's a directory with a list of files
                dir_path = base_path / key

                # Directory should exist (unless it's explicitly marked as optional like 'logs')
                if not dir_path.exists() and len(value) > 0:
                    missing.append(f"{current_rel}/ (directory)")
                    continue

                # Check each file in the directory
                for filename in value:
                    file_path = dir_path / filename
                    if not file_path.exists():
                        missing.append(f"{current_rel}/{filename}")

            elif isinstance(value, dict):
                # It's a nested structure (like 'skills')
                dir_path = base_path / key

                if not dir_path.exists():
                    missing.append(f"{current_rel}/ (directory)")
                    continue

                # Check for _files key (files directly in this directory)
                if '_files' in value:
                    for filename in value['_files']:
                        file_path = dir_path / filename
                        if not file_path.exists():
                            missing.append(f"{current_rel}/{filename}")

                # Recursively validate subdirectories
                for subkey, subvalue in value.items():
                    if subkey == '_files':
                        continue

                    if isinstance(subvalue, list):
                        # Subdirectory with files
                        subdir_path = dir_path / subkey

                        if not subdir_path.exists() and len(subvalue) > 0:
                            missing.append(f"{current_rel}/{subkey}/ (directory)")
                            continue

                        for filename in subvalue:
                            file_path = subdir_path / filename
                            if not file_path.exists():
                                missing.append(f"{current_rel}/{subkey}/{filename}")

        return missing

    def _validate_with_fallback(self, claude_dir: Path) -> bool:
        """
        Fallback validation using hardcoded required files.

        Args:
            claude_dir: Path to .claude folder

        Returns:
            True if all fallback files exist, False otherwise
        """
        for required_file in FALLBACK_REQUIRED_FILES:
            # Remove .claude/ prefix since we're already in the .claude dir
            file_path = claude_dir / required_file.replace(".claude/", "")
            if not file_path.exists():
                return False

        return True

    # =========================================================================
    # Private Methods - Installation
    # =========================================================================

    def _move_to_target(self, claude_dir: Path) -> None:
        """
        Atomically move .claude from temp to target.

        Args:
            claude_dir: Path to source .claude folder

        Raises:
            ValidationError: If move operation fails
        """
        target_claude = self.target_directory / ".claude"

        try:
            # If target exists, remove it (we already backed it up if needed)
            if target_claude.exists():
                shutil.rmtree(target_claude)

            # Move .claude folder to target
            shutil.move(str(claude_dir), str(target_claude))

        except Exception as e:
            raise ValidationError(f"Failed to install .claude folder: {str(e)}")

    def _backup_existing(self) -> Optional[Path]:
        """
        Backup existing .claude folder if present.

        Returns:
            Path to backup or None if no backup created
        """
        claude_dir = self.target_directory / ".claude"
        if not claude_dir.exists():
            return None

        # Create backup with timestamp
        backup_name = f".claude_backup_{uuid.uuid4().hex[:8]}"
        backup_path = self.target_directory / backup_name

        try:
            shutil.copytree(claude_dir, backup_path)
            return backup_path
        except Exception:
            # If backup fails, don't block installation
            return None

    def _rollback(self, state: InstallationState) -> None:
        """
        Restore from backup on failure.

        Args:
            state: Installation state with backup information
        """
        target_claude = self.target_directory / ".claude"

        try:
            # Remove partial installation if it exists
            if target_claude.exists():
                shutil.rmtree(target_claude, ignore_errors=True)

            # Restore backup if available
            if state.backup_path and state.backup_path.exists():
                shutil.move(str(state.backup_path), str(target_claude))

        except Exception:
            # Best effort rollback - don't raise exceptions here
            pass
        finally:
            # Always cleanup temp files
            if state.temp_dir and state.temp_dir.exists():
                self._cleanup_temp(state.temp_dir)

    def _cleanup_temp(self, temp_dir: Path) -> None:
        """
        Clean up temporary files.

        Args:
            temp_dir: Temporary directory to remove
        """
        try:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            # Best effort cleanup
            pass

    # =========================================================================
    # Private Methods - Security Validation
    # =========================================================================

    def _is_system_directory(self, path: Path) -> bool:
        """
        Check if path is or is within a system directory.

        Args:
            path: Path to check

        Returns:
            True if system directory, False otherwise
        """
        try:
            resolved = path.resolve()
            path_str = str(resolved)

            for sys_dir in SYSTEM_DIRECTORIES:
                # Case-insensitive prefix matching
                if path_str.lower().startswith(sys_dir.lower()):
                    return True

            return False
        except Exception:
            # If we can't resolve the path, be conservative
            return True

    def _check_writable(self, path: Path) -> bool:
        """
        Test if directory is writable.

        Args:
            path: Directory to test

        Returns:
            True if writable, False otherwise
        """
        test_file = path / f".write_test_{uuid.uuid4().hex[:8]}"
        try:
            test_file.touch()
            test_file.unlink()
            return True
        except (OSError, PermissionError):
            return False
