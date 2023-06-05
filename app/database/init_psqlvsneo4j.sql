-- YCSB benchmark default table
CREATE TABLE IF NOT EXISTS usertable (
    YCSB_KEY varchar(255) PRIMARY KEY,
    FIELD0 text,
    FIELD1 text,
    FIELD2 text,
    FIELD3 text,
    FIELD4 text,
    FIELD5 text,
    FIELD6 text,
    FIELD7 text,
    FIELD8 text,
    FIELD9 text
);

CREATE TABLE IF NOT EXISTS benchmark_log (
    benchmark_log_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    iteration_count integer NOT NULL DEFAULT 3,
    psql_query text NOT NULL,
    psql_runtimes integer[] NOT NULL,
    psql_nrows integer[] NOT NULL,
    neo4j_query text NOT NULL,
    neo4j_runtimes integer[] NOT NULL,
    neo4j_nrows integer[] NOT NULL
);

