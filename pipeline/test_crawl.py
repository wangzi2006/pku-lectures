from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import crawl
import policy


class CrawlPolicyTests(unittest.TestCase):
    def test_confidence_is_normalized_to_zero_one(self) -> None:
        self.assertEqual(crawl.normalize_confidence(5), 1.0)
        self.assertEqual(crawl.normalize_confidence(4), 0.8)
        self.assertEqual(crawl.normalize_confidence(0.86), 0.86)

    def test_sources_are_interleaved(self) -> None:
        first = {"name": "数学"}
        second = {"name": "人文"}
        order = list(crawl.round_robin([(first, ["m1", "m2"]), (second, ["h1", "h2"])]))
        self.assertEqual([url for _, url in order], ["m1", "h1", "m2", "h2"])

    def test_next_id_ignores_legacy_hashes(self) -> None:
        number = crawl.next_lecture_number(
            [], [{"id": "L006"}, {"id": "LABC123"}], [{"lectureId": "L005"}]
        )
        self.assertEqual(number, 7)

    def test_policy_never_treats_confidence_as_five_point_score(self) -> None:
        item = {
            "relevanceScore": 4,
            "qualityScore": 4,
            "undergradScore": 4,
            "prominenceScore": 4,
            "confidence": 5,
        }
        source = {"tier": 1}
        score_with_five = policy.deterministic_score(item, source)
        item["confidence"] = 1
        self.assertEqual(score_with_five, policy.deterministic_score(item, source))

    def test_issue_only_contains_current_batch(self) -> None:
        old_data = crawl.DATA
        with tempfile.TemporaryDirectory() as directory:
            crawl.DATA = Path(directory)
            try:
                crawl.write_review_issue(
                    [
                        {
                            "id": "L007",
                            "status": "pending",
                            "discoveredOn": "2026-09-02",
                            "title": "new",
                            "confidence": 4,
                            "sourceUrl": "https://example.com/new",
                        },
                        {
                            "id": "L008",
                            "status": "pending",
                            "discoveredOn": "2026-09-01",
                            "title": "old",
                            "confidence": 0.9,
                            "sourceUrl": "https://example.com/old",
                        },
                    ],
                    10,
                    "2026-09-02",
                )
                body = (Path(directory) / "review-issue.md").read_text(encoding="utf-8")
            finally:
                crawl.DATA = old_data
        self.assertIn("### L007", body)
        self.assertNotIn("### L008", body)
        self.assertIn("置信度 0.80", body)


if __name__ == "__main__":
    unittest.main()
