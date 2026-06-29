"""Экспорт рассчитанных деталей в DXF при помощи ezdxf."""

from pathlib import Path

import ezdxf

from .geometry import Part, build_parts, layout_parts
from .parameters import NotesHolderParameters


def create_document(
    params: NotesHolderParameters,
    *,
    parts: list[Part] | None = None,
) -> ezdxf.document.Drawing:
    """Создать DXF-документ с контурами на слое CUT."""

    document = ezdxf.new("R2010", setup=True)
    document.units = ezdxf.units.MM
    document.layers.add("CUT", color=1)
    document.layers.add("TEXT", color=7)
    modelspace = document.modelspace()

    arranged_parts = layout_parts(parts or build_parts(params))
    for part in arranged_parts:
        modelspace.add_lwpolyline(
            part.outline,
            close=True,
            dxfattribs={"layer": "CUT"},
        )
        for cutout in part.cutouts:
            modelspace.add_lwpolyline(
                cutout,
                close=True,
                dxfattribs={"layer": "CUT"},
            )
    return document


def export_dxf(params: NotesHolderParameters, output_path: str | Path) -> Path:
    """Сохранить готовый DXF и вернуть фактический путь."""

    path = Path(output_path)
    if path.suffix.lower() != ".dxf":
        path = path.with_suffix(".dxf")
    path.parent.mkdir(parents=True, exist_ok=True)
    create_document(params).saveas(path)
    return path
