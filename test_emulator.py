import unittest
from emulator import Emulator

class TestEmulator(unittest.TestCase):
    def setUp(self):
        self.emulator = Emulator("config.json")

    def test_ls(self):
        output = self.emulator.ls()
        self.assertIn("folder1", output)

    def test_cd(self):
        output = self.emulator.cd("folder1")
        self.assertIn("Текущая директория", output)

    def test_rev(self):
        output = self.emulator.rev("file1.txt")
        self.assertEqual(output, "txetelpmas")  # Замените на содержимое файла

    def test_du(self):
        output = self.emulator.du()
        self.assertIn("Размер текущей директории", output)

    def test_rmdir(self):
        self.emulator.cd("..")
        output = self.emulator.rmdir("folder2")
        self.assertIn("удалена", output)

if __name__ == "__main__":
    unittest.main()
