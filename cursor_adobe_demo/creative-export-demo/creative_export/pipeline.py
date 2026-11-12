"""Export mock previews for a source tree of creative assets."""
from pathlib import Path
from .discovery import find_assets
from .manifest import write_manifest
from .render import render_preview


def preview_destination(source_root: Path, output_root: Path, asset: Path) -> Path:
    """Return the preview path for asset, mirroring its source-relative folders.

    Raises ValueError if asset is outside source_root, or if the destination
    would resolve outside output_root.
    """
    relative = asset.relative_to(source_root)
    destination = output_root / relative.with_name(f'{relative.stem}.preview.txt')
    if not destination.resolve().is_relative_to(output_root.resolve()):
        raise ValueError(f'output path escapes output root: {destination}')
    return destination


def export_assets(source_root: Path, output_root: Path) -> list[dict[str, str]]:
    """Export each input .asset file and write a manifest.

    Preview paths keep the source folder structure relative to source_root,
    so identical basenames in different folders do not overwrite each other.
    """
    source_root = Path(source_root)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    records = []
    for asset in find_assets(source_root):
        destination = preview_destination(source_root, output_root, asset)
        render_preview(asset, destination)
        records.append({'source': asset.relative_to(source_root).as_posix(),
                        'output': destination.relative_to(output_root).as_posix()})
    write_manifest(output_root, records)
    return records
