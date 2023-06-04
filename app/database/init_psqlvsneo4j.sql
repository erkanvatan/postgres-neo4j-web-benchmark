-- YCSB benchmark default table
CREATE TABLE IF NOT EXISTS usertable (
	YCSB_KEY VARCHAR(255) PRIMARY KEY,
	FIELD0 TEXT, FIELD1 TEXT,
	FIELD2 TEXT, FIELD3 TEXT,
	FIELD4 TEXT, FIELD5 TEXT,
	FIELD6 TEXT, FIELD7 TEXT,
	FIELD8 TEXT, FIELD9 TEXT
);

CREATE TABLE IF NOT EXISTS benchmark_log (
    benchmark_log_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    iteration_count integer NOT NULL DEFAULT 1,
    psql_query text NOT NULL,
    psql_runtimes integer[] NOT NULL,
    neo4j_query text NOT NULL,
    neo4j_runtimes integer[] NOT NULL
);
