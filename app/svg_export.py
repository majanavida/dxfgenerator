from pathlib import Path
import xml.etree.ElementTree as ET

from .geometry import Contour, Part, build_parts, layout_parts
from .parameters import NotesHolderParameters

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NAMESPACE)


def _number(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _path_data(
    contour: Contour,
    *,
    min_x: float,
    max_y: float,
    padding: float,
) -> str:
    points = [
        (x - min_x + padding, max_y - y + padding)
        for x, y in contour
    ]
    commands = [f"M {_number(points[0][0])} {_number(points[0][1])}"]
    commands.extend(f"L {_number(x)} {_number(y)}" for x, y in points[1:])
    commands.append("Z")
    return " ".join(commands)


def create_svg(
    params: NotesHolderParameters,
    *,
    parts: list[Part] | None = None,
) -> ET.ElementTree:
    arranged_parts = layout_parts(parts or build_parts(params))
    contours = [
        contour
        for part in arranged_parts
        for contour in [part.outline, *part.cutouts]
    ]
    all_points = [point for contour in contours for point in contour]
    min_x = min(x for x, _ in all_points)
    max_x = max(x for x, _ in all_points)
    min_y = min(y for _, y in all_points)
    max_y = max(y for _, y in all_points)
    padding = 5.0
    width = max_x - min_x + padding * 2.0
    height = max_y - min_y + padding * 2.0

    root = ET.Element(
        f"{{{SVG_NAMESPACE}}}svg",
        {
            "width": f"{_number(width)}mm",
            "height": f"{_number(height)}mm",
            "viewBox": f"0 0 {_number(width)} {_number(height)}",
        },
    )
    cut_group = ET.SubElement(
        root,
        f"{{{SVG_NAMESPACE}}}g",
        {
            "id": "CUT",
            "fill": "none",
            "stroke": "#000000",
            "stroke-width": "0.2",
            "stroke-linejoin": "round",
        },
    )

    for part in arranged_parts:
        part_group = ET.SubElement(
            cut_group,
            f"{{{SVG_NAMESPACE}}}g",
            {"id": part.name},
        )
        for contour in [part.outline, *part.cutouts]:
            ET.SubElement(
                part_group,
                f"{{{SVG_NAMESPACE}}}path",
                {
                    "d": _path_data(
                        contour,
                        min_x=min_x,
                        max_y=max_y,
                        padding=padding,
                    )
                },
            )
    return ET.ElementTree(root)


def export_svg(params: NotesHolderParameters, output_path: str | Path) -> Path:
    path = Path(output_path)
    if path.suffix.lower() != ".svg":
        path = path.with_suffix(".svg")
    path.parent.mkdir(parents=True, exist_ok=True)
    create_svg(params).write(path, encoding="utf-8", xml_declaration=True)
    return path
