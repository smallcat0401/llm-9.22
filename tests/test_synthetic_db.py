import unittest

from verifiable_posttraining.synthetic_db import SALES_ROWS, SALES_SCHEMA, create_sales_connection


class SyntheticDatabaseTests(unittest.TestCase):
    def test_fixture_is_deterministic(self) -> None:
        first = create_sales_connection()
        second = create_sales_connection()
        try:
            first_rows = first.execute("SELECT * FROM sales ORDER BY sale_id").fetchall()
            second_rows = second.execute("SELECT * FROM sales ORDER BY sale_id").fetchall()
        finally:
            first.close()
            second.close()
        self.assertEqual(first_rows, list(SALES_ROWS))
        self.assertEqual(first_rows, second_rows)

    def test_known_north_revenue_is_accepted_fixture_value(self) -> None:
        connection = create_sales_connection()
        try:
            value = connection.execute(
                "SELECT SUM(units * unit_price) FROM sales WHERE region = 'north'"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(value, 97.5)

    def test_schema_documentation_matches_table(self) -> None:
        self.assertIn("sale_id INTEGER PRIMARY KEY", SALES_SCHEMA)
        self.assertIn("unit_price REAL", SALES_SCHEMA)


if __name__ == "__main__":
    unittest.main()
