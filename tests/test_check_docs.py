from unittest.mock import patch

from hooks.check_docs import main


def test_check_docs_success(tmp_path):
    with patch("hooks.check_docs.Path") as mock_path:
        mock_path_instance = mock_path.return_value
        mock_path_instance.exists.return_value = True

        with patch("hooks.check_docs.shutil.rmtree") as mock_rmtree, patch(
            "hooks.check_docs.subprocess.run"
        ) as mock_run:
            mock_run.return_value.returncode = 0
            assert main() == 0

            mock_path.assert_called_once_with("docs")
            mock_rmtree.assert_called_once()
            mock_path_instance.mkdir.assert_called_once_with(exist_ok=True)
            mock_run.assert_called_once_with(
                ["pdoc", "-o", "docs/", "src/"],
                check=True,
                capture_output=True,
                text=True,
            )


def test_check_docs_subprocess_error(tmp_path):
    from subprocess import CalledProcessError

    with patch("hooks.check_docs.Path") as mock_path:
        mock_path_instance = mock_path.return_value
        mock_path_instance.exists.return_value = True

        with patch("hooks.check_docs.shutil.rmtree") as mock_rmtree, patch(
            "hooks.check_docs.subprocess.run"
        ) as mock_run:
            mock_run.side_effect = CalledProcessError(1, "pdoc", stderr="Error message")
            assert main() == 1

            mock_path.assert_called_once_with("docs")
            mock_rmtree.assert_called_once()
            mock_path_instance.mkdir.assert_called_once_with(exist_ok=True)


def test_check_docs_no_existing_docs():
    with patch("hooks.check_docs.Path") as mock_path:
        mock_path_instance = mock_path.return_value
        mock_path_instance.exists.return_value = False

        with patch("hooks.check_docs.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            assert main() == 0

            mock_path.assert_called_once_with("docs")
            mock_path_instance.mkdir.assert_called_once_with(exist_ok=True)


def test_normalize_line_endings_converts_windows_to_unix(tmp_path):
    """Test that Windows line endings (\r\n) are converted to Unix (\n)."""
    test_file = tmp_path / "test.html"
    test_file.write_text("Line1\r\nLine2\r\n")

    from hooks.check_docs import normalize_line_endings

    normalize_line_endings(tmp_path)

    assert test_file.read_text() == "Line1\nLine2\n"


def test_normalize_line_endings_adds_missing_newline(tmp_path):
    """Test that files without trailing newline get one added."""
    test_file = tmp_path / "test.js"
    test_file.write_text("Line1\nLine2")

    from hooks.check_docs import normalize_line_endings

    normalize_line_endings(tmp_path)

    assert test_file.read_text() == "Line1\nLine2\n"


def test_normalize_line_endings_ignores_non_html_js_files(tmp_path):
    """Test that only .html and .js files are processed."""
    test_file = tmp_path / "test.html"
    original_content = "Line1\r\nLine2"
    test_file.write_text(original_content)

    from hooks.check_docs import normalize_line_endings

    normalize_line_endings(tmp_path)

    assert test_file.read_text() == "Line1\nLine2\n"
