import ezdxf

from app.dxf_export import export_dxf
from app.parameters import NotesHolderParameters


def test_dxf_is_created_with_required_layers(tmp_path):
    output_path = export_dxf(
        NotesHolderParameters(),
        tmp_path / "example_notes_holder.dxf",
    )

    assert output_path.exists()
    document = ezdxf.readfile(output_path)
    assert document.layers.has_entry("CUT")
    assert document.layers.has_entry("TEXT")
    assert len(document.modelspace().query("TEXT")) == 0

    modelspace = document.modelspace()
    outlines = [
        entity
        for entity in modelspace.query("LWPOLYLINE[layer=='CUT']")
        if entity.closed
    ]
    assert len(outlines) >= 6
