"""
db_connect.py  –  Shared connection helpers for PostgreSQL and Neo4j.
Edit the constants below to match your local settings before running.
"""

import psycopg
from neo4j import GraphDatabase

# ── PostgreSQL settings ──────────────────────────────────────────────────────
PG_DSN = "dbname=mobile_money user=postgres host=localhost port=5432"
# Override via environment variable MOBILE_PG_DSN if preferred.

# ── Neo4j settings ───────────────────────────────────────────────────────────
NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "Mobile2026!"


def pg_connect():
    """Return a persistent psycopg connection (autocommit for reads)."""
    import os
    dsn = os.environ.get('MOBILE_PG_DSN', PG_DSN)
    conn = psycopg.connect(dsn)
    conn.autocommit = True
    return conn


def neo_driver():
    """Return a Neo4j GraphDatabase.driver instance."""
    import os
    uri  = os.environ.get('MOBILE_NEO_URI',  NEO4J_URI)
    user = os.environ.get('MOBILE_NEO_USER', NEO4J_USER)
    pwd  = os.environ.get('MOBILE_NEO_PASS', NEO4J_PASSWORD)
    return GraphDatabase.driver(uri, auth=(user, pwd))


def run_pg(query, params=None, conn=None):
    """Execute a PostgreSQL query and return all result rows as a list of tuples."""
    _close = conn is None
    if conn is None:
        conn = pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or {})
            return cur.fetchall()
    finally:
        if _close:
            conn.close()


def run_neo(query, params=None, driver=None):
    """Execute a Cypher query and return all result rows as a list of dicts."""
    _close = driver is None
    if driver is None:
        driver = neo_driver()
    try:
        with driver.session(database='neo4j') as session:
            actual_params = dict(params) if params else {}
            actual_query = query
            if '$depth' in actual_query and 'depth' in actual_params:
                actual_query = actual_query.replace('$depth', str(actual_params.pop('depth')))
            if '$bound' in actual_query and 'bound' in actual_params:
                actual_query = actual_query.replace('$bound', str(actual_params.pop('bound')))
            result = session.run(actual_query, parameters=actual_params)
            return [dict(record) for record in result]
    finally:
        if _close:
            driver.close()
