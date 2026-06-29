import xml.etree.ElementTree as ET

from app.parameters import NotesHolderParameters
from app.svg_export import SVG_NAMESPACE, export_svg


def test_svg_is_created_with_five_part_groups(tmp_path):
    output_path = export_svg(
        NotesHolderParameters(),
        tmp_path / "example_notes_holder.svg",
    )

    assert output_path.exists()
    root = ET.parse(output_path).getroot()
    cut_group = root.find(f"{{{SVG_NAMESPACE}}}g[@id='CUT']")
    assert cut_group is not None

    part_groups = cut_group.findall(f"{{{SVG_NAMESPACE}}}g")
    assert len(part_groups) == 5
    assert root.findall(f".//{{{SVG_NAMESPACE}}}text") == []
