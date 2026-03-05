import unittest

from analytics import (
    build_event_frame,
    build_user_registry,
    cohort_retention_matrix,
    credit_views,
    failure_by_feature,
    growth_from_events,
    transition_summary,
    uncategorized_events,
)


class AnalyticsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.events_raw = [
            [101, "Consulta JurisBrasil Concluida", "2026/01/01 10:00:00"],
            [101, "Consulta Doutrina utilizada", "2026/01/01 10:05:00"],
            [101, "Consulta JurisBrasil falhou", "2026/02/02 11:00:00"],
            [102, "Papo utilizado", "2026/02/01 09:00:00"],
            [102, "Consulta Leis utilizada", "2026/02/01 09:40:00"],
        ]
        self.users_raw = [
            [101, "2026/01/01 10:00:00", "api", "", 12, 8],
            [101, "2026/02/02 11:00:00", "api", "", 10, 5],
            [102, "2026/02/01 09:00:00", "api", "", 20, 3],
        ]
        self.event_df = build_event_frame(self.events_raw)
        self.user_df = build_user_registry(self.users_raw)

    def test_event_frame_adds_status_and_sessions(self) -> None:
        self.assertEqual(self.event_df.iloc[0]["Feature"], "Consulta JurisBrasil")
        self.assertEqual(self.event_df.iloc[0]["Status"], "Sucesso")
        self.assertEqual(self.event_df.iloc[2]["Status"], "Falha")
        self.assertEqual(self.event_df.iloc[0]["SessaoId"], self.event_df.iloc[1]["SessaoId"])
        self.assertNotEqual(self.event_df.iloc[3]["SessaoId"], self.event_df.iloc[4]["SessaoId"])

    def test_cohort_retention_matrix_tracks_monthly_return(self) -> None:
        matrix = cohort_retention_matrix(self.event_df)
        self.assertAlmostEqual(matrix.loc["2026-01", 0], 1.0)
        self.assertAlmostEqual(matrix.loc["2026-01", 1], 1.0)
        self.assertAlmostEqual(matrix.loc["2026-02", 0], 1.0)

    def test_failure_by_feature_aggregates_success_and_failure(self) -> None:
        failures = failure_by_feature(self.event_df).set_index("Feature")
        self.assertEqual(int(failures.loc["Consulta JurisBrasil", "Tentativas"]), 2)
        self.assertAlmostEqual(float(failures.loc["Consulta JurisBrasil", "TaxaFalha"]), 0.5)

    def test_transition_summary_uses_same_session_next_feature(self) -> None:
        transitions = transition_summary(self.event_df, top_n=10)
        row = transitions.iloc[0]
        self.assertEqual(row["FeatureOrigem"], "Consulta JurisBrasil")
        self.assertEqual(row["FeatureDestino"], "Consulta Doutrina")
        self.assertEqual(int(row["Transicoes"]), 1)

    def test_growth_and_credit_views_return_expected_shapes(self) -> None:
        growth = growth_from_events(self.event_df, days=5)
        self.assertFalse(growth["novos_mes"].empty)
        views = credit_views(self.user_df, self.event_df)
        self.assertEqual(len(views["latest"]), 2)
        self.assertFalse(views["por_segmento"].empty)

    def test_uncategorized_events_lists_exact_unmapped_actions(self) -> None:
        events_raw = self.events_raw + [[104, "Login realizado", "2026/02/04 08:00:00"]]
        event_df = build_event_frame(events_raw)
        outros = uncategorized_events(event_df)
        self.assertEqual(len(outros), 1)
        self.assertEqual(outros.iloc[0]["AcaoOriginal"], "Login realizado")
        self.assertEqual(int(outros.iloc[0]["Eventos"]), 1)


if __name__ == "__main__":
    unittest.main()
