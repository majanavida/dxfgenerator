"""Простой tkinter-интерфейс генератора."""

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from .dxf_export import export_dxf
from .parameters import NotesHolderParameters


class NotesHolderApp:
    """Окно с параметрами и одной основной кнопкой."""

    FIELD_DEFINITIONS = (
        ("inner_width", "Длина (внутренняя ширина), мм"),
        ("inner_depth", "Глубина (внутренняя глубина), мм"),
        ("inner_height", "Высота (внутренняя высота), мм"),
        ("material_thickness", "Толщина материала, мм"),
        ("front_opening_percent", "Открытость передней стенки, %"),
        ("finger_width", "Ширина шипа, мм"),
        ("joint_clearance", "Зазор шип-паз, мм"),
    )

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NotesHolder — генератор DXF")
        self.root.resizable(False, False)
        defaults = NotesHolderParameters()

        frame = ttk.Frame(root, padding=14)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(
            frame,
            text="Салфетница NotesHolder",
            font=("TkDefaultFont", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10))

        self.numeric_vars: dict[str, tk.StringVar] = {}
        for row, (field_name, label) in enumerate(self.FIELD_DEFINITIONS, start=1):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=3)
            variable = tk.StringVar(value=str(getattr(defaults, field_name)))
            self.numeric_vars[field_name] = variable
            ttk.Entry(frame, textvariable=variable, width=22).grid(
                row=row, column=1, sticky="ew", padx=(12, 0), pady=3
            )

        filename_row = len(self.FIELD_DEFINITIONS) + 1
        ttk.Label(frame, text="Имя выходного файла").grid(
            row=filename_row, column=0, sticky="w", pady=3
        )
        self.filename_var = tk.StringVar(value=defaults.output_filename)
        ttk.Entry(frame, textvariable=self.filename_var, width=22).grid(
            row=filename_row, column=1, sticky="ew", padx=(12, 0), pady=3
        )

        ttk.Button(
            frame,
            text="Сгенерировать DXF",
            command=self.generate,
        ).grid(row=filename_row + 1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def generate(self) -> None:
        """Прочитать форму и сохранить DXF в output/examples."""

        try:
            params = NotesHolderParameters.from_strings(
                {name: variable.get() for name, variable in self.numeric_vars.items()},
                output_filename=self.filename_var.get(),
            )
            project_root = Path(__file__).resolve().parent.parent
            output_path = project_root / "output" / "examples" / params.output_filename
            saved_path = export_dxf(params, output_path)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Ошибка", str(exc))
            return

        messagebox.showinfo("Готово", f"DXF сохранён:\n{saved_path}")


def run_app() -> None:
    root = tk.Tk()
    NotesHolderApp(root)
    root.mainloop()
