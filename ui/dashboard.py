# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from shared.configuration.user_config import CONFIG_PATH


class DashboardView:
    def show_dashboard(self) -> None:
        self._clear_window()
        self.root.configure(bg=self.BACKGROUND)

        shell = tk.Frame(self.root, bg=self.BACKGROUND)
        shell.pack(fill="both", expand=True)
        sidebar = tk.Frame(shell, bg=self.SIDEBAR, width=196)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._label(
            sidebar,
            "LTN\nANALYTICS",
            size=16,
            color="#ffffff",
            weight="bold",
            bg=self.SIDEBAR,
            justify="left",
        ).pack(anchor="w", padx=25, pady=(30, 4))
        self._label(
            sidebar,
            "GATEWAY  /  01",
            size=8,
            color="#a8b6ad",
            weight="bold",
            bg=self.SIDEBAR,
        ).pack(anchor="w", padx=25, pady=(0, 34))
        tk.Frame(sidebar, bg="#33473c", height=1).pack(fill="x", padx=20)
        tk.Label(
            sidebar,
            text="  Обзор",
            bg="#294137",
            fg=self.ACCENT,
            font=(self.FONT, 10, "bold"),
            anchor="w",
            padx=15,
            pady=13,
        ).pack(fill="x", padx=12, pady=(18, 5))
        self._label(
            sidebar,
            "ИСТОЧНИК",
            size=8,
            color="#9aaba1",
            weight="bold",
            bg=self.SIDEBAR,
        ).pack(anchor="w", padx=27, pady=(22, 8))
        self._label(
            sidebar,
            "JSONL  →  PostgreSQL",
            size=9,
            color="#ffffff",
            bg=self.SIDEBAR,
        ).pack(anchor="w", padx=27)
        self._label(
            sidebar,
            "Настройки хранятся локально",
            size=8,
            color="#9aaba1",
            bg=self.SIDEBAR,
            wraplength=168,
            justify="left",
        ).pack(side="bottom", anchor="w", padx=25, pady=24)

        main = tk.Frame(shell, bg=self.BACKGROUND)
        main.pack(side="left", fill="both", expand=True, padx=28, pady=22)
        top = tk.Frame(main, bg=self.BACKGROUND)
        top.pack(fill="x", pady=(0, 16))
        title = tk.Frame(top, bg=self.BACKGROUND)
        title.pack(side="left")
        self._label(title, "Рабочая панель", size=24, weight="bold", bg=self.BACKGROUND).pack(
            anchor="w"
        )
        self._label(
            title,
            "Импорт данных Factorio в базу",
            size=10,
            color=self.MUTED,
            bg=self.BACKGROUND,
        ).pack(anchor="w", pady=(5, 0))
        actions = tk.Frame(top, bg=self.BACKGROUND)
        actions.pack(side="right", anchor="n")
        self._button(actions, "Настройки", self._open_settings).pack(side="left", padx=(0, 8))
        test_button = self._button(actions, "Проверить подключение", self._test_saved_connection)
        test_button.pack(side="left", padx=(0, 8))
        run_button = self._button(actions, "Запустить импорт", self._start_import, primary=True)
        run_button.pack(side="left")
        self.busy_buttons.extend((test_button, run_button))

        self.dashboard_status = self._label(
            main,
            "",
            size=9,
            color=self.GREEN,
            bg=self.BACKGROUND,
        )
        self.dashboard_status.pack(fill="x", pady=(0, 12))

        stats_frame = tk.Frame(main, bg=self.BACKGROUND)
        stats_frame.pack(fill="x", pady=(0, 14))
        stats = self.config.statistics
        self._stat(stats_frame, "ЗАПУСКИ", str(stats.runs), "всего").pack(
            side="left", fill="both", expand=True, padx=(0, 10)
        )
        self._stat(stats_frame, "ЗАКАЗЫ", f"{stats.orders_sent:,}", "добавлено в БД").pack(
            side="left", fill="both", expand=True, padx=5
        )
        self._stat(stats_frame, "СОБЫТИЯ", f"{stats.events_sent:,}", "добавлено в БД").pack(
            side="left", fill="both", expand=True, padx=5
        )
        last_run = self._format_last_run(stats.last_run_at)
        self._stat(stats_frame, "ПОСЛЕДНИЙ ИМПОРТ", last_run, "локальная статистика").pack(
            side="left", fill="both", expand=True, padx=(5, 0)
        )

        connection_section = tk.Frame(
            main,
            bg=self.SURFACE,
            highlightthickness=1,
            highlightbackground=self.LINE,
        )
        connection_section.pack(fill="x", pady=(0, 14))
        connection_body = tk.Frame(connection_section, bg=self.SURFACE)
        connection_body.pack(fill="x", padx=22, pady=19)
        connection_header = tk.Frame(connection_body, bg=self.SURFACE)
        connection_header.pack(fill="x")
        self._label(
            connection_header,
            "НАЗНАЧЕНИЕ",
            size=8,
            color=self.MUTED,
            weight="bold",
        ).pack(side="left")
        self._label(connection_header, "PostgreSQL", size=12, weight="bold").pack(side="right")
        self._label(
            connection_body,
            f"{self.config.database.db_host}:{self.config.database.db_port}  /  {self.config.database.db_name}",
            size=10,
            color=self.MUTED,
        ).pack(anchor="w", pady=(9, 0))
        self._label(
            connection_body,
            "SSL/TLS включён" if self.config.database.db_ssl else "SSL/TLS выключен",
            size=9,
            color=self.GREEN if self.config.database.db_ssl else self.MUTED,
        ).pack(anchor="w", pady=(5, 0))

        source_section = tk.Frame(
            main,
            bg=self.SURFACE,
            highlightthickness=1,
            highlightbackground=self.LINE,
        )
        source_section.pack(fill="x", pady=(0, 14))
        source_body = tk.Frame(source_section, bg=self.SURFACE)
        source_body.pack(fill="x", padx=22, pady=18)
        source_header = tk.Frame(source_body, bg=self.SURFACE)
        source_header.pack(fill="x")
        self._label(
            source_header,
            "ИСТОЧНИК ДАННЫХ",
            size=8,
            color=self.MUTED,
            weight="bold",
        ).pack(side="left")
        source_path = Path(self.config.source_jsonl_path)
        source_state = "Файл найден" if source_path.is_file() else "Файл пока не найден"
        state_color = self.GREEN if source_path.is_file() else "#9b6a20"
        self._label(source_header, source_state, size=9, color=state_color, weight="bold").pack(
            side="right"
        )
        self._label(
            source_body,
            self.config.source_jsonl_path,
            size=10,
            color=self.INK,
            wraplength=710,
        ).pack(anchor="w", pady=(9, 0))

        self._label(
            main,
            f"Конфигурация: {CONFIG_PATH}",
            size=8,
            color=self.MUTED,
            bg=self.BACKGROUND,
            wraplength=760,
        ).pack(anchor="w", pady=(4, 0))

    def _stat(self, parent: tk.Frame, label: str, value: str, caption: str) -> tk.Frame:
        frame = tk.Frame(
            parent,
            bg=self.SURFACE,
            highlightthickness=1,
            highlightbackground=self.LINE,
        )
        body = tk.Frame(frame, bg=self.SURFACE)
        body.pack(fill="both", expand=True, padx=12, pady=10)
        self._label(body, label, size=8, color=self.MUTED, weight="bold").pack(anchor="w")
        self._label(body, value, size=16, weight="bold").pack(anchor="w", pady=(6, 1))
        self._label(body, caption, size=8, color=self.MUTED).pack(anchor="w")
        return frame

    @staticmethod
    def _format_last_run(value: str | None) -> str:
        if not value:
            return "—"
        try:
            return datetime.fromisoformat(value).astimezone().strftime("%d.%m.%Y %H:%M")
        except ValueError:
            return value

    def _open_settings(self) -> None:
        self.source_var = tk.StringVar(value=self.config.source_jsonl_path)
        self.host_var = tk.StringVar(value=self.config.database.db_host)
        self.port_var = tk.StringVar(value=str(self.config.database.db_port))
        self.database_var = tk.StringVar(value=self.config.database.db_name)
        self.user_var = tk.StringVar(value=self.config.database.db_user)
        self.password_var = tk.StringVar(value=self.config.database.db_password)
        self.ssl_var = tk.BooleanVar(value=self.config.database.db_ssl)
        self.settings_status: tk.Label | None = None
        self._render_settings_form()

    def _render_settings_form(self) -> None:
        self._clear_window()
        self.root.configure(bg=self.BACKGROUND)

        shell = tk.Frame(self.root, bg=self.BACKGROUND)
        shell.pack(fill="both", expand=True, padx=38, pady=24)
        header = tk.Frame(shell, bg=self.BACKGROUND)
        header.pack(fill="x", pady=(0, 18))
        titles = tk.Frame(header, bg=self.BACKGROUND)
        titles.pack(side="left")
        self._label(titles, "Настройки", size=22, weight="bold", bg=self.BACKGROUND).pack(
            anchor="w"
        )
        self._label(
            titles,
            "Источник данных и параметры PostgreSQL",
            size=10,
            color=self.MUTED,
            bg=self.BACKGROUND,
        ).pack(anchor="w", pady=(4, 0))
        self._button(header, "Отмена", self.show_dashboard).pack(side="right", anchor="n")

        form = tk.Frame(
            shell,
            bg=self.SURFACE,
            highlightthickness=1,
            highlightbackground=self.LINE,
        )
        form.pack(fill="both", expand=True)
        body = tk.Frame(form, bg=self.SURFACE)
        body.pack(fill="both", expand=True, padx=26, pady=20)

        self._label(body, "ИСТОЧНИК JSONL", size=9, color=self.MUTED, weight="bold").pack(
            anchor="w", pady=(0, 7)
        )
        source_row = tk.Frame(body, bg=self.SURFACE)
        source_row.pack(fill="x", pady=(0, 18))
        source_entry = tk.Entry(
            source_row,
            textvariable=self.source_var,
            relief="flat",
            bg="#f6f7f6",
            fg=self.INK,
            font=(self.FONT, 10),
            highlightthickness=1,
            highlightbackground=self.LINE,
        )
        source_entry.pack(side="left", fill="x", expand=True, ipady=9)
        self._bind_entry_clipboard(source_entry)
        self._button(source_row, "Обзор…", self._browse_source).pack(side="left", padx=(9, 0))

        self._label(body, "POSTGRESQL", size=9, color=self.MUTED, weight="bold").pack(
            anchor="w", pady=(0, 10)
        )
        grid = tk.Frame(body, bg=self.SURFACE)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=3)
        grid.columnconfigure(1, weight=1)
        self._entry(grid, "СЕРВЕР", self.host_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 12), pady=(0, 12)
        )
        self._entry(grid, "ПОРТ", self.port_var).grid(
            row=0, column=1, sticky="ew", pady=(0, 12)
        )
        self._entry(grid, "ИМЯ БАЗЫ", self.database_var).grid(
            row=1, column=0, sticky="ew", padx=(0, 12), pady=(0, 12)
        )
        self._entry(grid, "ПОЛЬЗОВАТЕЛЬ", self.user_var).grid(
            row=1, column=1, sticky="ew", pady=(0, 12)
        )
        self._entry(
            grid,
            "ПАРОЛЬ",
            self.password_var,
            show="●",
            reveal_toggle=True,
        ).grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Checkbutton(
            body,
            text="Использовать SSL/TLS с проверкой сертификата сервера",
            variable=self.ssl_var,
        ).pack(anchor="w", pady=(14, 0))

        footer = tk.Frame(shell, bg=self.BACKGROUND)
        footer.pack(fill="x", pady=(14, 0))
        self.settings_status = self._label(
            footer,
            "",
            size=9,
            color=self.MUTED,
            bg=self.BACKGROUND,
            wraplength=520,
        )
        self.settings_status.pack(side="left", fill="x", expand=True)
        save_button = self._button(
            footer,
            "Сохранить настройки",
            self._save_settings_form,
            primary=True,
        )
        save_button.pack(side="right")
        check_button = self._button(
            footer,
            "Проверить подключение",
            self._test_settings_connection,
        )
        check_button.pack(side="right", padx=(0, 8))
        self.busy_buttons.extend((save_button, check_button))
