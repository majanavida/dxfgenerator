"""Параметры салфетницы и простое преобразование значений GUI."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NotesHolderParameters:
    """Основные размеры изделия в миллиметрах."""

    inner_width: float = 78.0
    inner_depth: float = 78.0
    inner_height: float = 35.0
    material_thickness: float = 3.0
    front_opening_percent: float = 40.0
    finger_width: float = 6.0
    joint_clearance: float = 0.1
    output_filename: str = "notes_holder.dxf"

    @classmethod
    def from_strings(
        cls,
        values: dict[str, str],
        *,
        output_filename: str,
    ) -> "NotesHolderParameters":
        """Создать параметры из строк GUI с минимальной валидацией."""

        if not output_filename.strip():
            raise ValueError("Имя выходного файла не должно быть пустым.")

        numeric_fields = {
            "inner_width": "Длина (внутренняя ширина)",
            "inner_depth": "Глубина (внутренняя глубина)",
            "inner_height": "Высота (внутренняя высота)",
            "material_thickness": "Толщина материала",
            "front_opening_percent": "Открытость передней стенки",
            "finger_width": "Ширина шипа",
            "joint_clearance": "Зазор шип-паз",
        }
        numbers: dict[str, float] = {}
        for field_name, label in numeric_fields.items():
            raw_value = values.get(field_name, "").strip().replace(",", ".")
            if not raw_value:
                raise ValueError(f"Поле «{label}» не должно быть пустым.")
            try:
                numbers[field_name] = float(raw_value)
            except ValueError as exc:
                raise ValueError(f"Поле «{label}» должно быть числом.") from exc

        return cls(
            **numbers,
            output_filename=output_filename.strip(),
        )
