from pathlib import Path

from config_manager import ConfigManager


def test_legacy_vlc_settings_are_normalized(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    (config_dir / "songs.json").write_text('{"songs": {}}', encoding="utf-8")
    (config_dir / "settings.json").write_text(
        """
        {
          "audio": {"input_device": "0: MacBook Pro Microphone"},
          "vlc": {"fullscreen_display": 3, "video_directory": "clips/", "default_volume": 40}
        }
        """,
        encoding="utf-8",
    )

    manager = ConfigManager(str(config_dir))

    assert manager.get_setting("audio", "input_device") == "default"
    assert manager.get_setting("video", "fullscreen_display") == 3
    assert manager.get_setting("vlc", "video_directory") == "clips/"
    assert "vlc" not in manager.settings


def test_add_song_applies_expected_defaults(tmp_path: Path):
    manager = ConfigManager(str(tmp_path / "config"))

    added = manager.add_song(
        "Test Song",
        {
            "intensity": 200,
            "reactivity_mode": "medium",
            "color_bias": "blue",
        },
    )

    assert added is True
    song = manager.get_song_config("Test Song")
    assert song["video_path"] == ""
    assert song["visualization_mode"] == "none"
    assert song["secondary_color_bias"] == "none"
    assert song["notes"] == ""


def test_validate_song_config_flags_missing_video(tmp_path: Path):
    manager = ConfigManager(str(tmp_path / "config"))

    errors = manager.validate_song_config(
        {
            "intensity": 255,
            "reactivity_mode": "easy",
            "color_bias": "red",
            "video_path": "/does/not/exist.mp4",
        }
    )

    assert "Video file not found: /does/not/exist.mp4" in errors
