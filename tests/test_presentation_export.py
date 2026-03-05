import io
import unittest
import zipfile

import pandas as pd

from analytics import build_event_frame, build_user_registry
from presentation_export import build_presentation_bytes


class PresentationExportTestCase(unittest.TestCase):
    def test_build_presentation_bytes_returns_valid_pptx(self) -> None:
        events_raw = [
            [101, "Consulta JurisBrasil Concluida", "2026/01/01 10:00:00"],
            [101, "Consulta Doutrina utilizada", "2026/01/01 10:05:00"],
            [101, "Consulta JurisBrasil falhou", "2026/02/02 11:00:00"],
            [102, "Papo utilizado", "2026/02/01 09:00:00"],
            [102, "Consulta Leis utilizada", "2026/02/01 09:20:00"],
            [103, "Consulta PDF utilizada", "2026/02/03 15:00:00"],
        ]
        users_raw = [
            [101, "2026/01/01 10:00:00", "api", "", 12, 8],
            [101, "2026/02/02 11:00:00", "api", "", 10, 5],
            [102, "2026/02/01 09:00:00", "api", "", 20, 3],
            [103, "2026/02/03 15:00:00", "api", "", 15, 7],
        ]

        event_df = build_event_frame(events_raw)
        user_df = build_user_registry(users_raw)
        pptx_bytes = build_presentation_bytes(
            event_df,
            user_df,
            pd.Timestamp("2026-01-01"),
            pd.Timestamp("2026-02-28"),
        )

        self.assertTrue(pptx_bytes.startswith(b"PK"))
        self.assertGreater(len(pptx_bytes), 10_000)

        archive = zipfile.ZipFile(io.BytesIO(pptx_bytes))
        members = set(archive.namelist())
        self.assertIn("[Content_Types].xml", members)
        self.assertIn("ppt/presentation.xml", members)

        slide_members = [name for name in members if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
        self.assertEqual(len(slide_members), 5)


if __name__ == "__main__":
    unittest.main()
