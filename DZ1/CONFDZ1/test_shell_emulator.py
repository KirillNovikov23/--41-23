import unittest
import os
import zipfile
import shutil
from pathlib import Path
from shell_emulator import ShellEmulator

class test_shell_emulator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Создаем тестовую виртуальную файловую систему
        cls.test_vfs_zip = 'test_vfs.zip'
        cls.test_vfs_root = 'test_vfs_root'

        os.makedirs(cls.test_vfs_root, exist_ok=True)
        with open(os.path.join(cls.test_vfs_root, 'file1.txt'), 'w') as f:
            f.write("line1\nline2\nline1\n")

        os.makedirs(os.path.join(cls.test_vfs_root, 'folder1'), exist_ok=True)
        with open(os.path.join(cls.test_vfs_root, 'folder1', 'file2.txt'), 'w') as f:
            f.write("file2 content\n")

        with zipfile.ZipFile(cls.test_vfs_zip, 'w') as zipf:
            for root, _, files in os.walk(cls.test_vfs_root):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, cls.test_vfs_root)
                    zipf.write(full_path, arcname)

        # Создаем конфигурационный файл
        cls.config_path = 'test_config.ini'
        with open(cls.config_path, 'w') as f:
            f.write(f"""[DEFAULT]
hostname = test-shell
vfs_zip_path = {cls.test_vfs_zip}
log_file = test_log.json
startup_script = test_startup.sh
""")

    @classmethod
    def tearDownClass(cls):
        # Удаляем временные файлы и директории
        if os.path.exists(cls.test_vfs_zip):
            os.remove(cls.test_vfs_zip)
        if os.path.exists(cls.config_path):
            os.remove(cls.config_path)
        if os.path.exists(cls.test_vfs_root):
            shutil.rmtree(cls.test_vfs_root)
        if os.path.exists('test_log.json'):
            os.remove('test_log.json')

    def setUp(self):
        # Создаем экземпляр эмулятора для каждого теста
        self.emulator = ShellEmulator(self.config_path)

    def tearDown(self):
        if Path(self.emulator.vfs_root).exists():
            shutil.rmtree(self.emulator.vfs_root)

    def test_ls_root(self):
        result = self.capture_output(self.emulator.cmd_ls)
        self.assertIn('file1.txt', result)
        self.assertIn('folder1', result)

    def test_cd_and_pwd(self):
        self.emulator.cmd_cd(['folder1'])
        result = self.capture_output(self.emulator.cmd_pwd)
        self.assertTrue(Path(result).as_posix().endswith('/folder1'))

    def test_cd_invalid_directory(self):
        result = self.capture_output(lambda: self.emulator.cmd_cd(['nonexistent']))
        self.assertIn('Directory not found', result)

    def test_uniq(self):
        result = self.capture_output(lambda: self.emulator.cmd_uniq(['file1.txt']))
        expected_result = 'line1\nline2\n'
        self.assertEqual(result, expected_result.strip())

    def test_uniq_file_not_found(self):
        result = self.capture_output(lambda: self.emulator.cmd_uniq(['nonexistent.txt']))
        self.assertIn('File not found', result)

    def capture_output(self, func):
        """Перехватывает вывод функции для проверки результатов."""
        from io import StringIO
        import sys

        output = StringIO()
        sys.stdout = output

        try:
            func()
        finally:
            sys.stdout = sys.__stdout__

        return output.getvalue().strip()

if __name__ == "__main__":
    unittest.main()
