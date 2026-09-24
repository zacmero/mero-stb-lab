import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from video_library_server import library, select_range


class VideoLibraryTest(unittest.TestCase):
    def test_library_excludes_nonvideo_and_escape_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Videos"
            root.mkdir()
            video = root / "clip.mp4"
            video.write_bytes(b"video")
            (root / "notes.txt").write_text("private")
            (root / "outside.ts").symlink_to(Path(directory) / "private.ts")
            (Path(directory) / "private.ts").write_bytes(b"private")
            self.assertEqual(list(library(root.resolve()).values()), [video.resolve()])

    def test_range_parsing(self) -> None:
        self.assertEqual(select_range("bytes=10-19", 100), (10, 19, True))
        self.assertEqual(select_range("bytes=-10", 100), (90, 99, True))
        self.assertEqual(select_range("bytes=90-", 100), (90, 99, True))
        self.assertEqual(select_range(None, 100), (0, 99, False))
        with self.assertRaises(ValueError):
            select_range("bytes=100-", 100)


if __name__ == "__main__":
    unittest.main()
