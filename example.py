#!/usr/bin/env python

import logging

log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

KEYSPACE = "testkeyspace"

def main():
    c = Cluster(['127.0.0.1', '127.0.0.2'])
    s = c.connect()

    rows = s.execute("SELECT keyspace_name FROM system.schema_keyspaces")
    if KEYSPACE in [row[0] for row in rows]:
        log.info("dropping existing keyspace...")
        s.execute("DROP KEYSPACE " + KEYSPACE)

    log.info("creating keyspace...")
    s.execute("""
        CREATE KEYSPACE %s
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '1' }
        """ % KEYSPACE)

    log.info("setting keyspace...")
    s.set_keyspace(KEYSPACE)

    log.info("creating table...")
    s.execute("""
        CREATE TABLE mytable (
            thekey text,
            col1 text,
            col2 text,
            PRIMARY KEY (thekey, col1)
        )
        """)

    query = SimpleStatement("""
                  INSERT INTO mytable (thekey, col1, col2)
                  VALUES (%(key)s, %(a)s, %(b)s)
                  """, consistency_level=ConsistencyLevel.ONE)
    for i in range(10):
        log.info("inserting row %d" % i)
        s.execute(query, dict(key="key%d" % i, a='a', b='b'))

    future = s.execute_async("SELECT * FROM mytable")
    log.info("key\tcol1\tcol2")
    log.info("---\t----\t----")

    try:
        rows = future.result()
    except:
        log.exeception()

    for row in rows:
        log.info('\t'.join(row))

    s.execute("DROP KEYSPACE " + KEYSPACE)

if __name__ == "__main__":
    main()