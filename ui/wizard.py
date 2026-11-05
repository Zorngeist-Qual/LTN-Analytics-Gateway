# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, ttk


class WizardView:
    STEPS = (
        ("Источник данных", "Укажите JSONL-файл, созданный модом Factorio."),
        ("Назначение данных", "Заказы и события будут записаны в PostgreSQL."),
        ("Подключение", "Введите реквизиты целевой базы данных."),
        ("Проверка и сохранение", "Проверим доступ к базе и сохраним настройки."),
    )

    def show_wizard(self) -> None:
        self._clear_window()
        self.root.configure(bg=self.BACKGROUND)
        self.wizard_step = 0
        current = self.config
        self.source_var = tk.StringVar(value=current.source_jsonl_path)
        self.host_var = tk.StringVar(value=current.database.db_host)
        self.port_var = tk.StringVar(value=str(current.database.db_port))
        self.database_var = tk.StringVar(value=current.database.db_name)
        self.user_var = tk.StringVar(value=current.database.db_user)
        self.password_var = tk.StringVar(value=current.database.db_password)
        self.ssl_var = tk.BooleanVar(value=current.database.db_ssl)
        self.wizard_status: tk.Label | None = None
        self._render_wizard_step()

    def _render_wizard_step(self) -> None:
        self._clear_window()
        shell = tk.Frame(self.root, bg=self.BACKGROUND)
        shell.pack(fill="both", expand=True, padx=42, pady=26)

        masthead = tk.Frame(shell, bg=self.BACKGROUND)
        masthead.pack(fill="x", pady=(0, 20))
        self._label(
            masthead,
            "LTN ANALYTICS  /  GATEWAY",
            size=10,
            color=self.GREEN,
            weight="bold",
            bg=self.BACKGROUND,
        ).pack(side="left")
        self._label(
            masthead,
            "ПЕРВИЧНАЯ НАСТРОЙКА",
            size=9,
            color=self.MUTED,
            weight="bold",
            bg=self.BACKGROUND,
        ).pack(side="right")

        self._label(
            shell,
            self.STEPS[self.wizard_step][0],
            size=27,
            weight="bold",
            bg=self.BACKGROUND,
        ).pack(anchor="w")
        self._label(
            shell,
            f"Шаг {self.wizard_step + 1} из 4  ·  {self.STEPS[self.wizard_step][1]}",
            size=11,
            color=self.MUTED,
            bg=self.BACKGROUND,
        ).pack(anchor="w", pady=(6, 16))

        progress = tk.Frame(shell, bg=self.BACKGROUND)
        progress.pack(fill="x", pady=(0, 18))
        for index, _ in enumerate(self.STEPS):
            segment = tk.Frame(
                progress,
                bg=self.GREEN if index <= self.wizard_step else self.LINE,
                height=4,
            )
            segment.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else 6, 0))
            segment.pack_propagate(False)

        content = tk.Frame(
            shell,
            bg=self.SURFACE,
            highlightthickness=1,
            highlightbackground=self.LINE,
        )
        content.pack(fill="both", expand=True)
        body = tk.Frame(content, bg=self.SURFACE)
        body.pack(fill="both", expand=True, padx=28, pady=22)
        self._render_wizard_content(body)

        footer = tk.Frame(shell, bg=self.BACKGROUND)
        footer.pack(fill="x", pady=(14, 0))
        self.wizard_status = self._label(
            footer,
            self.load_error or "",
            size=9,
            color=self.RED if self.load_error else self.MUTED,
            bg=self.BACKGROUND,
        )
        self.wizard_status.pack(side="left")

        if self.wizard_step > 0:
            back = self._button(footer, "Назад", self._previous_step)
            back.pack(side="right", padx=(8, 0))
            self.busy_buttons.append(back)
        if self.wizard_step < 3:
            next_button = self._button(
                footer,
                "Далее  →",
                self._next_step,
                primary=True,
            )
            next_button.pack(side="right")
        else:
            save_button = self._button(
                footer,
                "Проверить и сохранить",
                self._check_and_save,
                primary=True,
            )
            save_button.pack(side="right")
            self.busy_buttons.append(save_button)

    def _render_wizard_content(self, parent: tk.Frame) -> None:
        if self.wizard_step == 0:
            self._label(parent, "Файл снимков Factorio", size=16, weight="bold").pack(
                anchor="w", pady=(2, 8)
            )
            self._label(
                parent,
                "JSONL-файл, который мод записывает в script-output.",
                size=10,
                color=self.MUTED,
            ).pack(anchor="w", pady=(0, 22))
            row = tk.Frame(parent, bg=self.SURFACE)
            row.pack(fill="x")
            path_entry = tk.Entry(
                row,
                textvariable=self.source_var,
                relief="flat",
                bg="#f6f7f6",
                fg=self.INK,
                font=(self.FONT, 10),
                highlightthickness=1,
                highlightbackground=self.LINE,
            )
            path_entry.pack(side="left", fill="x", expand=True, ipady=12)
            self._bind_entry_clipboard(path_entry)
            self._button(row, "Обзор…", self._browse_source).pack(side="left", padx=(10, 0))
        elif self.wizard_step == 1:
            self._label(parent, "Куда загружать данные", size=16, weight="bold").pack(
                anchor="w", pady=(2, 8)
            )
            self._label(
                parent,
                "Доступное назначение",
                size=9,
                color=self.MUTED,
                weight="bold",
            ).pack(anchor="w", pady=(12, 8))
            destination = tk.Frame(
                parent,
                bg="#f6f7f6",
                highlightthickness=1,
                highlightbackground=self.GREEN,
            )
            destination.pack(fill="x")
            self._label(
                destination,
                "01",
                size=11,
                color=self.GREEN,
                weight="bold",
                bg="#f6f7f6",
            ).pack(side="left", padx=18, pady=20)
            details = tk.Frame(destination, bg="#f6f7f6")
            details.pack(side="left", fill="x", expand=True, pady=16)
            self._label(details, "PostgreSQL", size=14, weight="bold", bg="#f6f7f6").pack(
                anchor="w"
            )
            self._label(
                details,
                "Таблицы orders и order_events",
                size=10,
                color=self.MUTED,
                bg="#f6f7f6",
            ).pack(anchor="w", pady=(4, 0))
            self._label(
                parent,
                "Записи с уже существующими идентификаторами будут пропущены.",
                size=10,
                color=self.MUTED,
            ).pack(anchor="w", pady=(16, 0))
        elif self.wizard_step == 2:
            self._label(parent, "Реквизиты PostgreSQL", size=16, weight="bold").pack(
                anchor="w", pady=(2, 22)
            )
            grid = tk.Frame(parent, bg=self.SURFACE)
            grid.pack(fill="x")
            grid.columnconfigure(0, weight=3)
            grid.columnconfigure(1, weight=1)
            self._entry(grid, "СЕРВЕР", self.host_var).grid(
                row=0, column=0, sticky="ew", padx=(0, 14), pady=(0, 18)
            )
            self._entry(grid, "ПОРТ", self.port_var).grid(
                row=0, column=1, sticky="ew", pady=(0, 18)
            )
            self._entry(grid, "ИМЯ БАЗЫ", self.database_var).grid(
                row=1, column=0, sticky="ew", padx=(0, 14), pady=(0, 18)
            )
            self._entry(grid, "ПОЛЬЗОВАТЕЛЬ", self.user_var).grid(
                row=1, column=1, sticky="ew", pady=(0, 18)
            )
            self._entry(
                grid,
                "ПАРОЛЬ",
                self.password_var,
                show="●",
                reveal_toggle=True,
            ).grid(row=2, column=0, columnspan=2, sticky="ew")
            ttk.Checkbutton(
                grid,
                text="Использовать SSL/TLS с проверкой сертификата сервера",
                variable=self.ssl_var,
            ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(14, 0))
        else:
            self._label(parent, "Проверьте параметры", size=16, weight="bold").pack(
                anchor="w", pady=(2, 18)
            )
            rows = (
                ("Источник", self.source_var.get()),
                ("Назначение", "PostgreSQL"),
                ("Сервер", f"{self.host_var.get()}:{self.port_var.get()}"),
                ("База данных", self.database_var.get()),
                ("Пользователь", self.user_var.get()),
                ("SSL/TLS", "Включено" if self.ssl_var.get() else "Отключено"),
            )
            for index, (name, value) in enumerate(rows):
                row = tk.Frame(parent, bg=self.SURFACE)
                row.pack(fill="x", pady=8)
                self._label(row, name.upper(), size=9, color=self.MUTED, weight="bold").pack(
                    side="left", anchor="n", ipadx=5
                )
                self._label(
                    row,
                    value,
                    size=10,
                    anchor="e",
                    wraplength=650,
                    justify="right",
                ).pack(side="right", fill="x", expand=True)
                if index < len(rows) - 1:
                    tk.Frame(parent, bg=self.LINE, height=1).pack(fill="x", pady=(2, 0))

    def _browse_source(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self.root,
            title="Выберите JSONL-файл",
            filetypes=(("JSON Lines", "*.jsonl"), ("Все файлы", "*.*")),
        )
        if selected:
            self.source_var.set(selected)
