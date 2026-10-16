import unittest
from collections import Counter

from verifiable_posttraining.public_seed_expansion import (
    PUBLIC_SEED_PARENT_TASKS,
    build_approved_public_seed_expansion,
    build_public_seed_expansion,
    build_public_seed_expansion_records,
)
from verifiable_posttraining.dataset import validate_task_dataset
from verifiable_posttraining.schemas import Split
from verifiable_posttraining.seed_expansion import (
    build_approved_self_written_seed_expansion,
)
from verifiable_posttraining.tools.calculator import calculator
from verifiable_posttraining.verifier import verify_numeric_answer


class PublicSeedExpansionTests(unittest.TestCase):
    def test_expected_family_counts_and_review_state(self) -> None:
        tasks = build_public_seed_expansion()
        self.assertEqual(len(tasks), 78)
        self.assertEqual(
            Counter(task.family_id for task in tasks),
            Counter({family: 6 for family in PUBLIC_SEED_PARENT_TASKS}),
        )
        self.assertTrue(all(task.split is Split.TRAIN for task in tasks))
        self.assertTrue(all(task.metadata["review_status"] == "pending" for task in tasks))
        self.assertFalse(any(task.metadata["training_eligible"] for task in tasks))

    def test_all_reference_expressions_replay(self) -> None:
        for task in build_public_seed_expansion():
            result = calculator(task.metadata["reference_expression"])
            self.assertTrue(verify_numeric_answer(result, task.ground_truth).passed)

    def test_ground_truth_matches_independent_relation_oracle(self) -> None:
        """Recompute every target from parameters, without using the stored expression."""

        for task in build_public_seed_expansion():
            family = task.family_id
            params = task.metadata["parameters"]
            if family == "v3-public-weighted_average-v1":
                units = params["units"]
                prices = params["prices"]
                selected = params["selected_indices"]
                expected = sum(units[i] * prices[i] for i in selected) / sum(
                    units[i] for i in selected
                )
            elif family == "v3-public-aggregate_percent_change-v1":
                selected = params["selected_indices"]
                old = sum(params["old"][i] for i in selected)
                new = sum(params["new"][i] for i in selected)
                expected = (new - old) / old * 100
            elif family == "v3-public-aggregate_percent_change_with_loss-v1":
                old = sum(params["old"])
                new = sum(params["new"])
                expected = (new - old) / old * 100
            elif family == "v3-public-average_growth_rate-v1":
                first, second, third = params["values"]
                expected = (((second - first) / first) + ((third - second) / second)) / 2 * 100
            elif family == "v3-public-derived_value_percent_change-v1":
                quantities = params["quantities"]
                prices = params["prices"]
                old = quantities[0] * prices[0]
                new = quantities[1] * prices[1]
                expected = (new - old) / old * 100
            elif family == "v3-public-difference_of_averages-v1":
                if "values" in params:
                    first, second, third = params["values"]
                    expected = (second + third) / 2 - (first + second) / 2
                elif "processing" in params:
                    expected = sum(params["processing"]) / 2 - sum(params["cloud"]) / 2
                else:
                    expected = sum(params["later"]) / 2 - sum(params["earlier"]) / 2
            elif family == "v3-public-midpoint_rate_application-v1":
                expected = params["notional"] * (params["low"] + params["high"]) / 2 / 100
            elif family == "v3-public-multi_period_interest-v1":
                expected = params["payment"] * params["frequency"] * params["years"]
            elif family == "v3-public-payout_ratio-v1":
                expected = params["shares"] * params["dividend"] / params["net_income"] * 100
            elif family == "v3-public-ratio_of_aggregates-v1":
                expected = (
                    sum(params["numerator"]) / sum(params["denominator"]) * 100
                )
            elif family == "v3-public-ratio_of_derived_values-v1":
                expected = (
                    params["granted"] * params["grant_price"]
                    / (params["settled"] * params["settle_price"])
                )
            elif family == "v3-public-signed_multi_value_average-v1":
                expected = sum(params["values"]) / 4
            elif family == "v3-public-signed_percent_change-v1":
                expected = (params["new"] - params["old"]) / params["old"] * 100
            else:  # pragma: no cover - protects the audit when a family is added
                self.fail(f"missing independent oracle for {family}")

            self.assertTrue(
                verify_numeric_answer(expected, task.ground_truth).passed,
                task.task_id,
            )

    def test_generation_is_deterministic_unique_and_synthetic(self) -> None:
        first = build_public_seed_expansion()
        second = build_public_seed_expansion()
        self.assertEqual(first, second)
        self.assertEqual(len({task.prompt for task in first}), len(first))
        self.assertTrue(all("Synthetic table:" in task.prompt for task in first))
        self.assertTrue(all(task.metadata["source_table_reproduction"] is False for task in first))
        self.assertTrue(all(task.metadata["parent_seed_task_ids"] for task in first))

    def test_chinese_audit_views_are_separate_from_model_prompts(self) -> None:
        records = build_public_seed_expansion_records()
        self.assertEqual(len(records), 78)
        self.assertTrue(all(record.question_zh for record in records))
        self.assertTrue(all(record.table_zh for record in records))
        self.assertTrue(all(record.question_zh not in record.task.prompt for record in records))

    def test_signed_and_loss_families_expose_notation(self) -> None:
        by_family = {
            family: [task for task in build_public_seed_expansion() if task.family_id == family]
            for family in PUBLIC_SEED_PARENT_TASKS
        }
        loss_prompts = by_family["v3-public-aggregate_percent_change_with_loss-v1"]
        self.assertTrue(all(
            ("Parentheses" in task.prompt or "parenthesized" in task.prompt)
            and "dash" in task.prompt
            for task in loss_prompts
        ))
        signed_prompts = by_family["v3-public-signed_percent_change-v1"]
        self.assertTrue(all("absolute" in task.prompt for task in signed_prompts))
        derived_ratio_prompts = by_family["v3-public-ratio_of_derived_values-v1"]
        self.assertTrue(all(
            "parenthes" in task.prompt.lower() and "absolute" in task.prompt.lower()
            for task in derived_ratio_prompts
        ))

    def test_prompts_do_not_spell_out_hidden_calculation_steps(self) -> None:
        forbidden_fragments = (
            "first combine the north and south",
            "calculate each of the two adjacent",
            "using quantity multiplied by",
            "derive the value of unvested awards",
            "derive total common dividends",
            "add long-term debt across both years",
            "multiply the count by fair value per unit",
            "sum every division for each year",
        )
        for task in build_public_seed_expansion():
            prompt = task.prompt.lower()
            self.assertFalse(
                any(fragment in prompt for fragment in forbidden_fragments),
                task.task_id,
            )

    def test_numeric_coverage_and_display_quality(self) -> None:
        tasks = build_public_seed_expansion()
        growth = [
            task.ground_truth["value"]
            for task in tasks
            if task.family_id == "v3-public-average_growth_rate-v1"
        ]
        self.assertTrue(any(value < 0 for value in growth))
        self.assertTrue(any(value > 0 for value in growth))
        weighted = [
            task for task in tasks if task.family_id == "v3-public-weighted_average-v1"
        ]
        for task in weighted:
            price1, price2, _ = task.metadata["parameters"]["prices"]
            self.assertLessEqual(max(price1, price2) / min(price1, price2), 1.34)
        self.assertFalse(any(
            "0000000000" in task.metadata["reference_expression"]
            or "9999999999" in task.metadata["reference_expression"]
            for task in tasks
        ))

    def test_structural_variation_is_not_just_number_substitution(self) -> None:
        tasks = build_public_seed_expansion()
        by_family = {
            family: [task for task in tasks if task.family_id == family]
            for family in PUBLIC_SEED_PARENT_TASKS
        }

        weighted_selections = {
            tuple(task.metadata["parameters"]["selected_indices"])
            for task in by_family["v3-public-weighted_average-v1"]
        }
        self.assertEqual(
            weighted_selections,
            {(0, 1), (0, 2), (1, 2), (0, 1, 2)},
        )

        aggregate_selections = {
            tuple(task.metadata["parameters"]["selected_indices"])
            for task in by_family["v3-public-aggregate_percent_change-v1"]
        }
        self.assertEqual(
            aggregate_selections,
            {(0, 1), (0, 2), (1, 2), (0, 1, 2)},
        )

        loss_parameters = [
            task.metadata["parameters"]
            for task in by_family["v3-public-aggregate_percent_change_with_loss-v1"]
        ]
        self.assertEqual({params["loss_index"] for params in loss_parameters}, {0, 1, 2, 3})
        self.assertEqual({params["zero_index"] for params in loss_parameters}, {0, 1, 2, 3})

        diversity_fields = {
            "v3-public-average_growth_rate-v1": "metric",
            "v3-public-midpoint_rate_application-v1": "instrument",
            "v3-public-multi_period_interest-v1": "instrument",
            "v3-public-ratio_of_aggregates-v1": "metric",
            "v3-public-signed_percent_change-v1": "metric",
            "v3-public-signed_multi_value_average-v1": "negative_count",
        }
        for family, field in diversity_fields.items():
            values = {
                task.metadata["parameters"][field]
                for task in by_family[family]
            }
            self.assertGreaterEqual(len(values), 3, family)

        average_difference_subtypes = {
            task.metadata["relation_subtype"]
            for task in by_family["v3-public-difference_of_averages-v1"]
        }
        self.assertEqual(len(average_difference_subtypes), 3)

        for task in by_family["v3-public-multi_period_interest-v1"]:
            question = task.prompt.split("\n\nSynthetic table:", maxsplit=1)[0]
            self.assertNotIn("$", question, task.task_id)

    def test_invalid_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "variants_per_family"):
            build_public_seed_expansion(variants_per_family=0)

    def test_owner_approved_copy_can_merge_without_becoming_sft(self) -> None:
        public = build_approved_public_seed_expansion()
        self_written = build_approved_self_written_seed_expansion()
        combined = (*self_written, *public)
        validate_task_dataset(combined)

        self.assertEqual(len(public), 78)
        self.assertEqual(len(combined), 162)
        self.assertEqual(len({task.family_id for task in combined}), 19)
        self.assertTrue(all(task.metadata["review_status"] == "approved" for task in public))
        self.assertTrue(all(task.metadata["training_eligible"] for task in public))
        self.assertTrue(all(
            task.metadata["owner_approval_date"] == "2026-10-06"
            for task in public
        ))
        self.assertEqual(len({task.task_id for task in combined}), 162)

    def test_empty_approval_date_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "approved_on"):
            build_approved_public_seed_expansion(approved_on=" ")


if __name__ == "__main__":
    unittest.main()
