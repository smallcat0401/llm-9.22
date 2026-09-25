import sqlite3
import unittest

from verifiable_posttraining.schemas import ToolCall
from verifiable_posttraining.tools import ReadOnlySQLiteTool, SQLToolLimits


class ReadOnlySQLiteToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute(
            "CREATE TABLE sales (region TEXT NOT NULL, units INTEGER NOT NULL, revenue REAL NOT NULL)"
        )
        self.connection.executemany(
            "INSERT INTO sales VALUES (?, ?, ?)",
            [
                ("north", 4, 40.0),
                ("south", 3, 37.5),
                ("north", 2, 25.0),
            ],
        )
        self.connection.execute("CREATE TABLE secrets (value TEXT NOT NULL)")
        self.connection.execute("INSERT INTO secrets VALUES ('hidden')")
        self.connection.commit()
        self.tool = ReadOnlySQLiteTool(
            self.connection,
            allowed_tables={"sales"},
            limits=SQLToolLimits(max_rows=3, max_vm_steps=10_000),
        )

    def tearDown(self) -> None:
        self.connection.close()

    @staticmethod
    def call(query: str, *, call_id: str = "call-1") -> ToolCall:
        return ToolCall(call_id=call_id, name="sql", arguments={"query": query})

    def test_aggregate_select_succeeds(self) -> None:
        observation = self.tool(
            self.call(
                "SELECT region, SUM(revenue) AS total "
                "FROM sales GROUP BY region ORDER BY region"
            )
        )
        self.assertTrue(observation.ok)
        self.assertEqual(observation.content["columns"], ["region", "total"])
        self.assertEqual(
            observation.content["rows"],
            [["north", 65.0], ["south", 37.5]],
        )

    def test_update_is_denied_and_data_is_unchanged(self) -> None:
        observation = self.tool(self.call("UPDATE sales SET revenue = 0"))
        self.assertFalse(observation.ok)
        self.assertEqual(observation.error_code, "unsafe_query")
        total = self.connection.execute("SELECT SUM(revenue) FROM sales").fetchone()[0]
        self.assertEqual(total, 102.5)

    def test_pragma_is_denied(self) -> None:
        observation = self.tool(self.call("PRAGMA table_info(sales)"))
        self.assertEqual(observation.error_code, "unsafe_query")

    def test_unlisted_table_is_denied(self) -> None:
        observation = self.tool(self.call("SELECT value FROM secrets"))
        self.assertEqual(observation.error_code, "unsafe_query")

    def test_unlisted_function_is_denied(self) -> None:
        observation = self.tool(self.call("SELECT random() FROM sales LIMIT 1"))
        self.assertEqual(observation.error_code, "unsafe_query")

    def test_invalid_syntax_is_a_query_error(self) -> None:
        observation = self.tool(self.call("SELECT FROM sales"))
        self.assertEqual(observation.error_code, "query_error")

    def test_multiple_statements_are_denied(self) -> None:
        observation = self.tool(
            self.call("SELECT * FROM sales; DELETE FROM sales")
        )
        self.assertEqual(observation.error_code, "unsafe_query")

    def test_row_limit_is_enforced(self) -> None:
        observation = self.tool(
            self.call(
                "SELECT a.units FROM sales AS a CROSS JOIN sales AS b ORDER BY a.units"
            )
        )
        self.assertEqual(observation.error_code, "row_limit_exceeded")

    def test_recursive_cte_is_denied(self) -> None:
        observation = self.tool(
            self.call(
                "WITH RECURSIVE counter(x) AS ("
                "SELECT 1 UNION ALL SELECT x + 1 FROM counter WHERE x < 10"
                ") SELECT x FROM counter"
            )
        )
        self.assertEqual(observation.error_code, "unsafe_query")

    def test_arguments_must_contain_only_query(self) -> None:
        call = ToolCall(
            call_id="call-1",
            name="sql",
            arguments={"query": "SELECT 1", "database": "other.db"},
        )
        observation = self.tool(call)
        self.assertEqual(observation.error_code, "invalid_arguments")


if __name__ == "__main__":
    unittest.main()
