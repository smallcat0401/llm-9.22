"""Deterministic, entirely synthetic SQLite fixtures for pilot tasks."""

from __future__ import annotations

import sqlite3

SALES_SCHEMA = """sales(
  sale_id INTEGER PRIMARY KEY,
  month TEXT,
  region TEXT,
  product TEXT,
  units INTEGER,
  unit_price REAL
)"""

SALES_ROWS = (
    (1, "2026-01", "north", "widget", 3, 20.0),
    (2, "2026-02", "north", "gadget", 5, 7.5),
    (3, "2026-01", "south", "widget", 4, 18.0),
    (4, "2026-02", "south", "gadget", 2, 30.0),
    (5, "2026-03", "east", "widget", 6, 12.5),
)

PILOT_REGIONS = ("north", "south", "east", "west")
PILOT_PRODUCTS = ("widget", "gadget", "doodad")


def _build_pilot_sales_rows() -> tuple[tuple[int, str, str, str, int, float], ...]:
    rows = []
    sale_id = 1
    for month_number in range(1, 13):
        month = f"2026-{month_number:02d}"
        for region_index, region in enumerate(PILOT_REGIONS):
            for product_index, product in enumerate(PILOT_PRODUCTS):
                units = (month_number * 3 + region_index * 5 + product_index * 7) % 20 + 1
                unit_price = round(
                    5 + region_index * 2.5 + product_index * 3.25 + month_number * 0.4,
                    2,
                )
                rows.append((sale_id, month, region, product, units, unit_price))
                sale_id += 1
    return tuple(rows)


PILOT_SALES_ROWS = _build_pilot_sales_rows()


def create_sales_connection() -> sqlite3.Connection:
    """Return a fresh in-memory database with fixed public synthetic rows."""

    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY,
            month TEXT NOT NULL,
            region TEXT NOT NULL,
            product TEXT NOT NULL,
            units INTEGER NOT NULL CHECK (units >= 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0)
        )
        """
    )
    connection.executemany(
        "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)",
        SALES_ROWS,
    )
    connection.commit()
    return connection


def create_pilot_sales_connection() -> sqlite3.Connection:
    """Return the larger deterministic database used by generated SQL tasks."""

    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY,
            month TEXT NOT NULL,
            region TEXT NOT NULL,
            product TEXT NOT NULL,
            units INTEGER NOT NULL CHECK (units >= 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0)
        )
        """
    )
    connection.executemany(
        "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)",
        PILOT_SALES_ROWS,
    )
    connection.commit()
    return connection
