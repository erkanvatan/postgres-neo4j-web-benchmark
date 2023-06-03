CREATE TABLE IF NOT EXISTS benchmark_log (
    benchmark_log_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    iteration_count integer NOT NULL DEFAULT 1,
    psql_query text NOT NULL,
    psql_runtimes integer[] NOT NULL,
    neo4j_query text NOT NULL,
    neo4j_runtimes integer[] NOT NULL
);

