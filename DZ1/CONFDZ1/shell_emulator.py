import os
import sys
import zipfile
import configparser
import json
import shutil
from pathlib import Path


class ShellEmulator:
    def __init__(self, config_path):
        self.load_config(config_path)
        self.current_dir = Path(self.vfs_root)
        self.log = []

        if not self.current_dir.exists():
            raise FileNotFoundError("Virtual filesystem root does not exist!")

        self.load_startup_script()

    def load_config(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path)

        self.hostname = config['DEFAULT'].get('hostname', 'shell-emulator')
        self.vfs_zip_path = config['DEFAULT'].get('vfs_zip_path', 'vfs.zip')
        self.log_file = config['DEFAULT'].get('log_file', 'log.json')
        self.startup_script = config['DEFAULT'].get('startup_script', None)

        self.vfs_root = Path('vfs_root')
        self.extract_vfs()

    def extract_vfs(self):
        if self.vfs_root.exists():
            shutil.rmtree(self.vfs_root)

        with zipfile.ZipFile(self.vfs_zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.vfs_root)

    def load_startup_script(self):
        if self.startup_script and Path(self.startup_script).exists():
            with open(self.startup_script, 'r') as f:
                for line in f:
                    self.execute_command(line.strip())

    def log_action(self, command, result):
        self.log.append({"command": command, "result": result})

    def save_log(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.log, f, indent=4)

    def execute_command(self, command):
        parts = command.split()
        if not parts:
            return

        cmd = parts[0]
        args = parts[1:]

        if cmd == "ls":
            self.cmd_ls()
        elif cmd == "cd":
            self.cmd_cd(args)
        elif cmd == "pwd":
            self.cmd_pwd()
        elif cmd == "uniq":
            self.cmd_uniq(args)
        elif cmd == "exit":
            self.save_log()
            sys.exit(0)
        else:
            print(f"Unknown command: {cmd}")

    def cmd_ls(self):
        try:
            entries = os.listdir(self.current_dir)
            print("\n".join(entries))
            self.log_action("ls", entries)
        except Exception as e:
            print(f"Error: {e}")
            self.log_action("ls", str(e))

    def cmd_cd(self, args):
        if len(args) != 1:
            print("Usage: cd <directory>")
            return

        target_dir = self.current_dir / args[0]
        if target_dir.exists() and target_dir.is_dir():
            self.current_dir = target_dir.resolve()
            self.log_action("cd", str(target_dir))
        else:
            print("Directory not found")
            self.log_action("cd", "Directory not found")

    def cmd_pwd(self):
        print(self.current_dir)
        self.log_action("pwd", str(self.current_dir))

    def cmd_uniq(self, args):
        if len(args) != 1:
            print("Usage: uniq <file>")
            return

        file_path = self.current_dir / args[0]
        if not file_path.exists() or not file_path.is_file():
            print("File not found")
            self.log_action("uniq", "File not found")
            return

        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            unique_lines = list(dict.fromkeys(lines))
            print("".join(unique_lines))
            self.log_action("uniq", unique_lines)
        except Exception as e:
            print(f"Error: {e}")
            self.log_action("uniq", str(e))

    def start(self):
        while True:
            try:
                command = input(f"{self.hostname}:{self.current_dir}$ ")
                self.execute_command(command)
            except KeyboardInterrupt:
                print("\nExiting...")
                self.save_log()
                break


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python shell_emulator.py <config_path>")
        sys.exit(1)

    config_path = sys.argv[1]
    shell = ShellEmulator(config_path)
    shell.start()