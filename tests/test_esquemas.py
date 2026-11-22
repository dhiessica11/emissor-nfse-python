import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from baixar_esquemas_restritos import extrair_seguro


class EsquemasTests(unittest.TestCase):
    def test_extrai_apenas_xsd_e_mantem_subpastas(self):
        memory = io.BytesIO()
        with ZipFile(memory, "w") as z:
            z.writestr("schemas/DPS_v1.01.xsd", b"<schema/>")
            z.writestr("schemas/tipos.xsd", b"<schema/>")
            z.writestr("leiaute.pdf", b"nao publicar")
        with tempfile.TemporaryDirectory() as temp:
            files = extrair_seguro(memory.getvalue(), temp)
            self.assertEqual(len(files), 2)
            self.assertTrue((Path(temp) / "schemas" / "DPS_v1.01.xsd").exists())
            self.assertFalse((Path(temp) / "leiaute.pdf").exists())

    def test_bloqueia_sobrescrita(self):
        memory = io.BytesIO()
        with ZipFile(memory, "w") as z:
            z.writestr("DPS_v1.01.xsd", b"<schema/>")
        with tempfile.TemporaryDirectory() as temp:
            extrair_seguro(memory.getvalue(), temp)
            with self.assertRaises(FileExistsError):
                extrair_seguro(memory.getvalue(), temp)

    def test_bloqueia_escapada_da_pasta(self):
        memory = io.BytesIO()
        with ZipFile(memory, "w") as z:
            z.writestr("../fora.xsd", b"ruim")
            z.writestr("DPS_v1.01.xsd", b"bom")
        with tempfile.TemporaryDirectory() as temp:
            files = extrair_seguro(memory.getvalue(), temp)
            self.assertEqual(len(files), 1)
            self.assertFalse((Path(temp).parent / "fora.xsd").exists())


if __name__ == "__main__":
    unittest.main()
