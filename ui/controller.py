# -*- coding: utf-8 -*-
import asyncio
import queue
import threading
from collections.abc import Coroutine
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from typing import Any, Callable

from main import ImportResult, import_jsonl_data, test_connection
from shared.configuration.provider import ConfigProvider
from shared.configuration.user_config import (
    CONFIG_PATH,
    DatabaseConfig,
    GatewayConfig,
    RunStatistics,
    load_user_config,
    save_user_config,
)
from .dashboard import DashboardView
from .widgets import GatewayWidgets
from .wizard import WizardView


class GatewayApp(GatewayWidgets, WizardView, DashboardView):
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("LTN Analytics Gateway")
        self.root.geometry("960x640")
        self.root.minsize(860, 570)
        self.root.configure(bg=self.BACKGROUND)
        self._configure_styles()

        self.result_queue: queue.Queue[tuple] = queue.Queue()
        self.busy_buttons: list[tk.Button] = []
        self.dashboard_status: tk.Label | None = None
        self.settings_status: tk.Label | None = None
        self.wizard_status: tk.Label | None = None
        self.load_error: str | None = None
        try:
            self.config = load_user_config()
        except Exception as error:
            self.config = None
            self.load_error = f"Файл настроек не прочитан: {error}"

        self._start_polling()
        if self.config is None:
            self.config = GatewayConfig()
            self.show_wizard()
        else:
            self.show_dashboard()

    def run(self) -> None:
        self.root.mainloop()

    def _clear_window(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        self.busy_buttons = []

    def _start_polling(self) -> None:
        self.root.after(120, self._poll_results)

    def _poll_results(self) -> None:
        try:
            while True:
                result = self.result_queue.get_nowait()
                if result[0] == "error":
                    self._set_busy(False)
                    self._show_error(result[1])
                else:
                    self._set_busy(False)
                    result[2](result[1])
        except queue.Empty:
            pass
        self.root.after(120, self._poll_results)

    def _run_async(
        self,
        operation: Callable[[], Coroutine[Any, Any, object]],
        on_success: Callable[[object], None],
    ) -> None:
        self._set_busy(True)

        def worker() -> None:
            try:
                result = asyncio.run(operation())
            except Exception as error:
                self.result_queue.put(("error", str(error)))
            else:
                self.result_queue.put(("success", result, on_success))

        threading.Thread(target=worker, daemon=True).start()

    def _set_busy(self, busy: bool) -> None:
        for button in self.busy_buttons:
            button.configure(state="disabled" if busy else "normal")

    def _show_error(self, details: str) -> None:
        if self.dashboard_status and self.dashboard_status.winfo_exists():
            self.dashboard_status.configure(
                text=f"Не удалось выполнить операцию: {details}",
                fg=self.RED,
            )
        elif self.settings_status and self.settings_status.winfo_exists():
            self.settings_status.configure(text=details, fg=self.RED)
        elif self.wizard_status and self.wizard_status.winfo_exists():
            self.wizard_status.configure(text=details, fg=self.RED)
        else:
            messagebox.showerror("Не удалось выполнить операцию", details, parent=self.root)

    def _next_step(self) -> None:
        if self.wizard_step == 0 and not self.source_var.get().strip():
            self._set_wizard_status("Укажите путь к JSONL-файлу.", error=True)
            return
        if self.wizard_step == 2:
            try:
                self._database_from_form()
            except ValueError as error:
                self._set_wizard_status(str(error), error=True)
                return
        self.load_error = None
        self.wizard_step += 1
        self._render_wizard_step()

    def _previous_step(self) -> None:
        self.wizard_step -= 1
        self._render_wizard_step()

    def _database_from_form(self) -> DatabaseConfig:
        try:
            database = DatabaseConfig(
                db_user=self.user_var.get().strip(),
                db_password=self.password_var.get(),
                db_host=self.host_var.get().strip(),
                db_port=int(self.port_var.get().strip()),
                db_name=self.database_var.get().strip(),
                db_ssl=self.ssl_var.get(),
            )
        except (ValueError, TypeError) as error:
            raise ValueError("Порт должен быть целым числом.") from error
        if not all((database.db_user, database.db_password, database.db_host, database.db_name)):
            raise ValueError("Заполните сервер, базу данных, пользователя и пароль.")
        if not 1 <= database.db_port <= 65535:
            raise ValueError("Порт должен быть в диапазоне от 1 до 65535.")
        return database

    def _set_wizard_status(self, text: str, *, error: bool = False) -> None:
        if self.wizard_status and self.wizard_status.winfo_exists():
            self.wizard_status.configure(text=text, fg=self.RED if error else self.GREEN)

    def _check_and_save(self) -> None:
        try:
            database = self._database_from_form()
            source_path = self.source_var.get().strip()
            if not source_path:
                raise ValueError("Укажите путь к JSONL-файлу.")
            updated_config = GatewayConfig(
                source_jsonl_path=source_path,
                database=database,
                statistics=self.config.statistics,
            )
        except ValueError as error:
            self._set_wizard_status(str(error), error=True)
            return

        self._set_wizard_status("Проверяем подключение…")

        def on_success(_: object) -> None:
            try:
                save_user_config(updated_config)
            except OSError as error:
                self._show_error(f"Не удалось сохранить настройки: {error}")
                return
            self.config = updated_config
            ConfigProvider.reset()
            self.load_error = None
            self.show_dashboard()

        self._run_async(lambda: test_connection(database), on_success)

    def _settings_database(self) -> DatabaseConfig:
        try:
            database = DatabaseConfig(
                db_user=self.user_var.get().strip(),
                db_password=self.password_var.get(),
                db_host=self.host_var.get().strip(),
                db_port=int(self.port_var.get().strip()),
                db_name=self.database_var.get().strip(),
                db_ssl=self.ssl_var.get(),
            )
        except (ValueError, TypeError) as error:
            raise ValueError("Проверьте номер порта.") from error
        if not all((database.db_user, database.db_password, database.db_host, database.db_name)):
            raise ValueError("Заполните все параметры PostgreSQL.")
        if not 1 <= database.db_port <= 65535:
            raise ValueError("Порт должен быть в диапазоне от 1 до 65535.")
        return database

    def _test_settings_connection(self) -> None:
        try:
            database = self._settings_database()
        except ValueError as error:
            self.settings_status.configure(text=str(error), fg=self.RED)
            return
        self.settings_status.configure(text="Проверяем подключение…", fg=self.MUTED)

        def on_success(_: object) -> None:
            if self.settings_status and self.settings_status.winfo_exists():
                self.settings_status.configure(text="Подключение успешно проверено.", fg=self.GREEN)

        self._run_async(lambda: test_connection(database), on_success)

    def _save_settings_form(self) -> None:
        try:
            database = self._settings_database()
            source_path = self.source_var.get().strip()
            if not source_path:
                raise ValueError("Укажите путь к JSONL-файлу.")
            updated_config = self.config.model_copy(
                update={"source_jsonl_path": source_path, "database": database}
            )
            save_user_config(updated_config)
        except (OSError, ValueError) as error:
            self.settings_status.configure(text=str(error), fg=self.RED)
            return

        self.config = updated_config
        ConfigProvider.reset()
        self.show_dashboard()
        if self.dashboard_status:
            self.dashboard_status.configure(text="Настройки сохранены.", fg=self.GREEN)

    def _test_saved_connection(self) -> None:
        if self.dashboard_status:
            self.dashboard_status.configure(text="Проверяем подключение…", fg=self.MUTED)

        def on_success(_: object) -> None:
            if self.dashboard_status:
                self.dashboard_status.configure(text="Подключение успешно проверено.", fg=self.GREEN)

        self._run_async(lambda: test_connection(self.config.database), on_success)

    def _start_import(self) -> None:
        source = Path(self.config.source_jsonl_path)
        if not source.is_file():
            self._show_error(f"Файл данных не найден: {source}")
            return
        if self.dashboard_status:
            self.dashboard_status.configure(text="Читаем файл и отправляем новые записи…", fg=self.MUTED)

        def on_success(result: object) -> None:
            if not isinstance(result, ImportResult):
                self._show_error("Импорт вернул неизвестный результат.")
                return
            old = self.config.statistics
            statistics = RunStatistics(
                runs=old.runs + 1,
                snapshots_processed=old.snapshots_processed + result.snapshots_processed,
                orders_sent=old.orders_sent + result.orders_sent,
                events_sent=old.events_sent + result.events_sent,
                last_run_at=datetime.now().astimezone().isoformat(timespec="minutes"),
            )
            self.config = self.config.model_copy(update={"statistics": statistics})
            try:
                save_user_config(self.config)
            except OSError as error:
                self._show_error(f"Импорт завершён, но статистику сохранить не удалось: {error}")
                self.show_dashboard()
                return
            self.show_dashboard()
            if self.dashboard_status:
                self.dashboard_status.configure(
                    text=(
                        f"Готово: обработано снимков {result.snapshots_processed}, "
                        f"добавлено заказов {result.orders_sent}, событий {result.events_sent}."
                    ),
                    fg=self.GREEN,
                )

        self._run_async(import_jsonl_data, on_success)
