from pathlib import Path

from video_controller import VideoController


def test_supported_formats_include_common_extensions():
    formats = VideoController.get_supported_formats()

    assert ".mp4" in formats
    assert ".mov" in formats
    assert ".webm" in formats


def test_play_video_rejects_missing_path(tmp_path: Path):
    controller = VideoController()

    result = controller.play_video(str(tmp_path / "missing.mp4"))

    assert result is False
    assert controller.get_current_video() is None


def test_fast_video_validation_uses_extension_only(tmp_path: Path):
    controller = VideoController()
    valid_file = tmp_path / "clip.mov"
    valid_file.write_text("not a real video", encoding="utf-8")

    assert controller._is_valid_video_file_fast(str(valid_file)) is True
    assert controller._is_valid_video_file_fast(str(tmp_path / "clip.txt")) is False
