import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare", ROOT / "tools/prepare_photos.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class PhotoTests(unittest.TestCase):
    def test_bit_order_and_polarity(self):
        image = Image.new("1", (400, 300), 1)
        image.putpixel((0, 0), 0)
        raw = prepare.prepare_image(image).tobytes()
        self.assertEqual(len(raw), 15000)
        self.assertEqual(raw[0], 0x7F)
        self.assertEqual(raw[1:], b'\xff' * 14999)

    def test_portrait_contain_and_cover(self):
        image = Image.new("RGB", (100, 200), "black")
        fit = prepare.prepare_image(image)
        self.assertEqual(fit.getpixel((0, 150)), 255)
        self.assertEqual(fit.getpixel((200, 150)), 0)
        self.assertEqual(prepare.prepare_image(image, "cover").tobytes(), b'\0' * 15000)

    def test_alpha_is_white(self):
        image = Image.new("RGBA", (400, 300), (0, 0, 0, 0))
        self.assertEqual(prepare.prepare_image(image).tobytes(), b'\xff' * 15000)

    def test_exif_rotation(self):
        image = Image.new("RGB", (100, 200), "black")
        image.getexif()[274] = 6
        result = prepare.prepare_image(image)
        self.assertEqual(result.getpixel((200, 0)), 255)
        self.assertEqual(result.getpixel((0, 150)), 0)

    def test_generated_cpp_matches_previews_and_empty_input_preserves(self):
        with tempfile.TemporaryDirectory() as tmp:
            sketch, preview = Path(tmp)/"sketch", Path(tmp)/"preview"
            manifest = prepare.build_album(prepare.demo_images(), sketch, preview)
            self.assertEqual(manifest['pixel_bytes'], 45000)
            source = (sketch/"Photos.cpp").read_text()
            raw = bytes(int(x, 16) for x in re.findall(r'0x([0-9a-f]{2})', source))
            self.assertEqual(len(raw), 45000)
            for i in range(3):
                with Image.open(preview/f'{i+1:03d}.png') as image:
                    self.assertEqual(raw[i*15000:(i+1)*15000], image.tobytes())
            self.assertEqual(json.loads((preview/"manifest.json").read_text())['count'], 3)
            with self.assertRaises(ValueError):
                prepare.build_album([], sketch, preview)
            self.assertEqual((sketch/"Photos.cpp").read_text(), source)

    def test_capacity_limit(self):
        with self.assertRaises(ValueError):
            prepare.build_album([(str(i), Image.new("L", (1, 1))) for i in range(101)],
                                Path("unused"), Path("unused"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
