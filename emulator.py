import os
import zipfile
import json
import sys
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox


class Emulator:
    def __init__(self, config_file):
        self.config = self._load_config(config_file)
        self.vfs_root = "/tmp/vfs"
        self.current_path = self.vfs_root
        self._load_vfs()
        self.log_file = self.config["log_file"]
        self._initialize_log()
        self._execute_startup_script()

    def _load_config(self, config_file):
        """Загрузка конфигурации из JSON файла."""
        try:
            with open(config_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Ошибка: Конфигурационный файл не найден.")
            sys.exit(1)
        except json.JSONDecodeError:
            print("Ошибка: Некорректный формат JSON.")
            sys.exit(1)

    def _load_vfs(self):
        """Распаковать виртуальную файловую систему."""
        try:
            if os.path.exists(self.vfs_root):
                os.system(f"rm -rf {self.vfs_root}")  # Очистка старой VFS
            with zipfile.ZipFile(self.config["vfs_archive"], 'r') as zip_ref:
                zip_ref.extractall(self.vfs_root)
        except Exception as e:
            print(f"Ошибка при загрузке VFS: {e}")
            sys.exit(1)

    def _initialize_log(self):
        """Инициализация файла логов."""
        with open(self.log_file, 'w') as log:
            log.write("Логи эмулятора:\n")

    def _execute_startup_script(self, gui=None):
        """Выполняет команды из startup_script, если он указан в конфигурации."""
        startup_script = self.config.get("startup_script")
        if startup_script and os.path.exists(startup_script):
            try:
                with open(startup_script, 'r') as script:
                    for line in script:
                        command = line.strip()
                        if command:  # Игнорировать пустые строки
                            print(f"Выполнение команды из startup_script: {command}")
                            result = self.execute_command(command)
                            print(result)  # Выводить результат выполнения
            except Exception as e:
                print(f"Ошибка при выполнении startup_script: {e}")
        else:
            print("startup_script не указан или файл отсутствует.")

    def _log_action(self, action):
        """Записать действие в лог с датой и временем."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {"timestamp": timestamp, "action": action, "path": self.current_path}
        with open(self.log_file, 'a') as log:
            log.write(json.dumps(log_entry) + "\n")

    def prompt(self):
        """Возвращает строку приглашения."""
        user = self.config.get("user", "user")
        computer = self.config.get("computer", "computer")
        return f"{user}@{computer}:{self.current_path}$ "

    def ls(self):
        """Список содержимого текущей директории."""
        try:
            contents = os.listdir(self.current_path)
            self._log_action("ls")
            return "\n".join(contents) if contents else "(Пусто)"
        except Exception as e:
            return f"Ошибка: {e}"

    def cd(self, path):
        """Переместиться в указанную директорию."""
        new_path = os.path.join(self.current_path, path)
        if os.path.exists(new_path) and os.path.isdir(new_path):
            self.current_path = new_path
            self._log_action(f"cd {path}")
            return f"Текущая директория: {self.current_path}"
        return f"Ошибка: {path} не существует или не является директорией."

    def rev(self, filename):
        """Переворачивает строки файла."""
        file_path = os.path.join(self.current_path, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                reversed_lines = [line.strip()[::-1] for line in lines]
                self._log_action(f"rev {filename}")
                return "\n".join(reversed_lines)
            except Exception as e:
                return f"Ошибка: {e}"
        return f"Ошибка: {filename} не найден или не является файлом."

    def du(self):
        """Подсчитывает размер текущей директории и вложенных."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.current_path):
                for file in filenames:
                    file_path = os.path.join(dirpath, file)
                    total_size += os.path.getsize(file_path)
            self._log_action("du")
            return f"Размер текущей директории: {total_size} байт"
        except Exception as e:
            return f"Ошибка: {e}"

    def rmdir(self, directory):
        """Удаляет директорию, если она пуста."""
        dir_path = os.path.join(self.current_path, directory)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            try:
                os.rmdir(dir_path)  # Удаляет только пустую директорию
                self._log_action(f"rmdir {directory}")
                return f"Директория {directory} удалена."
            except OSError:
                return f"Ошибка: Директория {directory} не пуста."
            except Exception as e:
                return f"Ошибка: {e}"
        return f"Ошибка: {directory} не существует или не является директорией."

    def execute_command(self, command):
        """Выполнить команду."""
        if command.startswith("ls"):
            return self.ls()
        elif command.startswith("cd "):
            path = command[3:]
            return self.cd(path)
        elif command.startswith("rev "):
            filename = command[4:]
            return self.rev(filename)
        elif command.startswith("du"):
            return self.du()
        elif command.startswith("rmdir "):
            directory = command[6:]
            return self.rmdir(directory)
        elif command == "exit":
            self._log_action("exit")
            return "Выход из эмулятора."
        else:
            return f"Неизвестная команда: {command}"


class EmulatorGUI:
    def __init__(self, emulator):
        self.emulator = emulator
        self.root = tk.Tk()
        self.root.title("Эмулятор командной строки")

        # Поле вывода
        self.output_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=20, width=80)
        self.output_area.pack(padx=10, pady=10)

        # Поле ввода команды
        self.command_entry = tk.Entry(self.root, width=80)
        self.command_entry.pack(padx=10, pady=5)
        self.command_entry.bind("<Return>", self.execute_command)

        # Кнопка выполнения команды
        self.execute_button = tk.Button(self.root, text="Выполнить", command=self.execute_command)
        self.execute_button.pack(padx=10, pady=5)

        self.output_area.insert(tk.END, self.emulator.prompt())

    def execute_command(self, event=None):
        command = self.command_entry.get().strip()
        if command:
            self.output_area.insert(tk.END, f"\n{self.emulator.prompt()} {command}\n")
            result = self.emulator.execute_command(command)
            self.output_area.insert(tk.END, f"{result}\n")
            self.output_area.see(tk.END)
            self.command_entry.delete(0, tk.END)
            if command == "exit":  # Закрытие GUI при выходе
                self.root.quit()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 emulator.py config.json")
        sys.exit(1)

    config_file = sys.argv[1]
    emulator = Emulator(config_file)
    gui = EmulatorGUI(emulator)
    gui.run()
