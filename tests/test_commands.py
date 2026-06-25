from bookworm.commands import CommandResult, handle_command


def test_bare_text_is_not_a_command(tmp_path):
    output = []

    result = handle_command(
        "init",
        working_dir=tmp_path,
        set_mode=lambda mode: None,
        output=output.append,
    )

    assert result == CommandResult.NOT_A_COMMAND
    assert output == []
    assert not (tmp_path / ".bookworm").exists()


def test_slash_init_creates_bookworm_dirs(tmp_path):
    output = []

    result = handle_command(
        "/init",
        working_dir=tmp_path,
        set_mode=lambda mode: None,
        output=output.append,
    )

    assert result == CommandResult.HANDLED
    assert (tmp_path / ".bookworm" / "sources").is_dir()
    assert (tmp_path / ".bookworm" / "index").is_dir()
    assert output == ["Initialized .bookworm directory in the project root."]


def test_slash_mode_switches_exactly_one_mode_argument(tmp_path):
    output = []
    modes = []

    result = handle_command(
        "/mode build",
        working_dir=tmp_path,
        set_mode=modes.append,
        output=output.append,
    )

    assert result == CommandResult.HANDLED
    assert modes == ["build"]
    assert output == ["Switched to Build mode."]


def test_slash_mode_rejects_extra_text(tmp_path):
    output = []
    modes = []

    result = handle_command(
        "/mode build please read my repo",
        working_dir=tmp_path,
        set_mode=modes.append,
        output=output.append,
    )

    assert result == CommandResult.HANDLED
    assert modes == []
    assert output == ["Usage: /mode <plan|build|research>"]
