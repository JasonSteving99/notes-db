import base64
import click as hide_from_click_clack
import csv
import duckdb
import os
from pathlib import Path
import re
from typing import Any


def __base64encode_row(row: list[str]) -> str:
    encoded_row = [
        base64.b64encode(v.encode("utf-8")) for v in row
    ]
    return "(" + ",".join(f'"{str(v, "utf-8")}"' for v in encoded_row) + ")"


def __extract_table_name(create_statement: str) -> str:
    """
    Extract the table name from a CREATE TABLE statement.
    
    Args:
        create_statement: A SQL CREATE TABLE statement
        
    Returns:
        The extracted table name
    """
    # Match "CREATE TABLE [schema_name.]table_name" pattern
    pattern = r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\"?(\w+)\"?\.)?\"?(\w+)\"?"
    match = re.search(pattern, create_statement, re.IGNORECASE)
    
    if match:
        # If there's a schema name, use the second group (table name)
        # Otherwise use the first non-None group
        schema_name, table_name = match.groups()
        if schema_name and table_name:
            return table_name
        return next(name for name in match.groups() if name is not None)
    
    return None


def generate_python_import_duckdb(export_dir: Path, extensions: list[str]) -> str:
    export_path = Path(export_dir)

    extensions_codegen = [
        f"""
    # Install/Load {extension} extension.
    conn.execute("INSTALL {extension};")
    conn.execute("LOAD {extension};")
""" 
        for extension in extensions
    ]

    schema_ddl_statements: list[duckdb.Statement]
    with (export_path / "schema.sql").open("r") as f:
        schema_ddl_statements = duckdb.extract_statements(f.read())
    schema_ddl_stmts_codegen = [
        f"conn.execute(\"\"\"{schema_ddl_statement.query.strip()}\"\"\")"
        for schema_ddl_statement in schema_ddl_statements
    ]
    tables_in_creation_order: list[duckdb.Statement] = []
    for ddl_stmt in schema_ddl_statements:
        match ddl_stmt.type:
            case duckdb.StatementType.CREATE:
                # Check that this is actually a CREATE TABLE stmt, not a CREATE INDEX or smth like that.
                if table_name := __extract_table_name(ddl_stmt.query): 
                    tables_in_creation_order.append(table_name)
                

     # Find all CSV files (assuming they correspond to table names)
    csv_files = list(export_path.glob("*.csv"))
    # Generate INSERTs for all tables from their CSVs.
    tables_codegen: dict[str, str] = {}
    for csv_file in csv_files:
        table_name = os.path.splitext(csv_file.name)[0]
        table_columns: list[str]
        table_rows: list[list[str]]
        with open(csv_file, "r", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            table_columns = header
            table_rows = [row for row in reader]
        tables_codegen[table_name] = f"""
    # Loading {table_name}.
    conn.executemany(
        "INSERT INTO {table_name} ({", ".join(table_columns)}) VALUES ({", ".join("?" for _ in table_columns)})", 
        [
            {",\n            ".join(f"__base64decode_row({__base64encode_row(row)})" for row in table_rows)}
        ],
    )
"""

    codegen = f"""
import base64
import duckdb

def load_connection() -> duckdb.DuckDBPyConnection:
    def __base64decode_row(row: tuple[str]) -> tuple[str]:
        return tuple(base64.b64decode(v).decode("utf-8") for v in row)

    conn = duckdb.connect()

    # Load all the extensions.
    {"\n    ".join(extensions_codegen)}
    
    # Load all the schemas.
    {"\n    ".join(schema_ddl_stmts_codegen)}

    # Load data into all tables ensuring to load them in the same order the tables were created (so that foreign keys work).
    {"\n    ".join(tables_codegen[table_name] for table_name in tables_in_creation_order)}

    return conn
"""

    return codegen


@hide_from_click_clack.command()
@hide_from_click_clack.option("--export-dir", type=hide_from_click_clack.Path(exists=True, file_okay=False, dir_okay=True, readable=True), required=True)
@hide_from_click_clack.option("--extensions", type=str, required=True, multiple=True)
def generate_python_import_duckdb_script(export_dir: Path, extensions: list[str]) -> str:
    hide_from_click_clack.echo(
        generate_python_import_duckdb(export_dir=export_dir, extensions=extensions)
    )


if __name__ == "__main__":
    generate_python_import_duckdb_script()