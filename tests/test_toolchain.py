"""Phase 0: the local execution toolchain used by later phases is available.

This is not a feature test: it only checks that sqlglot (databricks dialect)
works and that a local SparkSession can run SQL (requires Java 17+). The Spark
test is skipped, with an explicit reason, when no JVM is installed.
"""

from __future__ import annotations

import os
import shutil

import pytest
import sqlglot
from pyspark.sql import SparkSession  # importing does not start a JVM


def test_sqlglot_databricks_dialect() -> None:
    sql = sqlglot.transpile("select 1 as x", read="databricks", write="databricks")[0]
    assert sql == "SELECT 1 AS x"


_HAS_JAVA = shutil.which("java") is not None or bool(os.environ.get("JAVA_HOME"))


@pytest.mark.spark
@pytest.mark.skipif(not _HAS_JAVA, reason="Java (JVM 17+) absente : PySpark local indisponible")
def test_local_spark_runs_sql() -> None:
    spark = (
        SparkSession.builder.master("local[1]")
        .appName("dku2dbx-toolchain")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    try:
        assert spark.sql("SELECT 1 + 1 AS two").collect()[0]["two"] == 2
    finally:
        spark.stop()
