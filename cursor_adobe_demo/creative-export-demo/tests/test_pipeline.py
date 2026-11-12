import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from creative_export.pipeline import export_assets, preview_destination


class ExportPipelineTests(unittest.TestCase):
    def test_single_asset_exports_preview_and_manifest(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            output = root / 'output'
            source.mkdir()
            (source / 'banner.asset').write_text('Layer: banner\n', encoding='utf-8')

            records = export_assets(source, output)

            self.assertEqual(1, len(records))
            self.assertTrue((output / 'banner.preview.txt').exists())
            manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(records, manifest['exports'])

    def test_distinct_basenames_do_not_collide(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            output = root / 'output'
            source.mkdir()
            (source / 'banner.asset').write_text('Banner\n', encoding='utf-8')
            (source / 'poster.asset').write_text('Poster\n', encoding='utf-8')
            records = export_assets(source, output)
            self.assertEqual(2, len({r['output'] for r in records}))

    def test_nested_same_basename_preserves_folder_and_contents(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            output = root / 'output'
            bodies = {
                'campaign/hero.asset': 'Campaign hero\n',
                'social/hero.asset': 'Social hero\n',
                'brand/q4/hero.asset': 'Brand q4 hero\n',
            }
            for relative, body in bodies.items():
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding='utf-8')

            records = export_assets(source, output)

            expected_sources = [
                'brand/q4/hero.asset',
                'campaign/hero.asset',
                'social/hero.asset',
            ]
            expected_outputs = [
                'brand/q4/hero.preview.txt',
                'campaign/hero.preview.txt',
                'social/hero.preview.txt',
            ]
            self.assertEqual(expected_sources, [record['source'] for record in records])
            self.assertEqual(expected_outputs, [record['output'] for record in records])
            self.assertEqual(len(records), len({record['output'] for record in records}))

            for source_rel, body in bodies.items():
                preview = output / Path(source_rel).with_name('hero.preview.txt')
                self.assertTrue(preview.is_file())
                text = preview.read_text(encoding='utf-8')
                self.assertIn(body, text)
                for other in bodies.values():
                    if other != body:
                        self.assertNotIn(other, text)

            self.assertTrue((output / 'brand' / 'q4').is_dir())
            self.assertTrue((output / 'campaign').is_dir())
            self.assertTrue((output / 'social').is_dir())

            manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(['exports'], list(manifest))
            self.assertEqual(records, manifest['exports'])
            for record in manifest['exports']:
                self.assertEqual({'source', 'output'}, set(record))

    def test_path_outside_source_root_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            output = root / 'output'
            outside = root / 'outside'
            source.mkdir()
            outside.mkdir()
            asset = outside / 'hero.asset'
            asset.write_text('Outside\n', encoding='utf-8')

            with self.assertRaises(ValueError):
                preview_destination(source, output, asset)
            self.assertFalse((output / 'hero.preview.txt').exists())


if __name__ == '__main__':
    unittest.main()
