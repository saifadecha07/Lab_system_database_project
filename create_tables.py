import os
from pathlib import Path

import psycopg2


PROJECT_ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    if not SCHEMA_PATH.exists():
        raise RuntimeError(f"Schema file not found: {SCHEMA_PATH}")

    sql_commands = SCHEMA_PATH.read_text(encoding="utf-8")

    print("Connecting to database...")
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            print("Applying schema from sql/schema.sql ...")
            cur.execute(sql_commands)
        conn.commit()
    print("Schema applied successfully.")


if __name__ == "__main__":
    main()
