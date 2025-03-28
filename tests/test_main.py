"""Tests for main module."""

import pytest

from src.pybop.main import main


@pytest.mark.parametrize(
    "expected_output",
    [
        ("Hello from pybop!\n"),
    ],
)
def test_main_output(capsys, expected_output):
    """Test the main function output."""
    main()
    captured = capsys.readouterr()
    assert captured.out == expected_output


def test_main_return_value():
    """Test that main() returns None."""
    assert main() is None


@pytest.mark.parametrize(
    "exception",
    [
        (KeyboardInterrupt),
        (SystemExit),
    ],
)
def test_main_exception_handling(monkeypatch, exception):
    """Test that main() handles exceptions properly."""

    def mock_exit():
        # Accept and ignore the message parameter
        def inner(*args, **kwargs):
            raise exception

        return inner

    monkeypatch.setattr("builtins.print", mock_exit())
    with pytest.raises(exception):
        main()
