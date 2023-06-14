-- Sample benchmark queries, shown in the "Select Query" dropdown of the Run Benchmark page.
-- Each pair returns the same rows from PostgreSQL and Neo4j.
INSERT INTO saved_query (selected_database, psql_query, neo4j_query, iteration_count)
SELECT * FROM (VALUES
-- Work price from work hours (2 joins)
('warehouse',
$$SELECT work.id AS workid, SUM(worktype.price * workhours.hours * workhours.discount) AS price
FROM work
INNER JOIN workhours ON work.id = workhours.workid
INNER JOIN worktype ON worktype.id = workhours.worktypeid
GROUP BY work.id$$,
$$MATCH (w:work)-[h:WORKHOURS]->(wt:worktype)
RETURN w.id AS workid, SUM(h.hours * h.discount * wt.price) AS price$$,
10),

-- Work price from work hours and used items (4 joins)
('warehouse',
$$SELECT work.id AS workid,
SUM((worktype.price * workhours.hours * workhours.discount) + (item.purchaseprice * useditem.amount * useditem.discount)) AS price
FROM work
INNER JOIN workhours ON work.id = workhours.workid
INNER JOIN worktype ON worktype.id = workhours.worktypeid
INNER JOIN useditem ON work.id = useditem.workid
INNER JOIN item ON useditem.itemid = item.id
GROUP BY work.id$$,
$$MATCH (wt:worktype)<-[h:WORKHOURS]-(w:work)-[u:USED_ITEM]->(i:item)
RETURN w.id AS workid, SUM((h.hours * h.discount * wt.price) + (u.amount * u.discount * i.purchaseprice)) AS price$$,
10),

-- All prerequisites of the "*-200" courses, found recursively (100 levels deep)
('university',
$$WITH RECURSIVE rec_prereq(course_id, prereq_id) AS (
    SELECT course_id, prereq_id FROM prereq WHERE course_id LIKE '%200%'
    UNION
    SELECT rec_prereq.course_id, prereq.prereq_id
    FROM rec_prereq
    INNER JOIN prereq ON rec_prereq.prereq_id = prereq.course_id
)
SELECT course_id, prereq_id FROM rec_prereq$$,
$$MATCH (c:course)-[:PREREQ*1..]->(p:course)
WHERE c.course_id CONTAINS '200'
RETURN c.course_id AS course_id, p.course_id AS prereq_id$$,
10),

-- Sum of grades per year for students named "A*" in "*engineer*" courses
('university',
$$SELECT year, SUM(grade) FROM takes
INNER JOIN student USING (student_id)
INNER JOIN course USING (course_id)
WHERE name LIKE 'A%' AND title LIKE '%engineer%'
GROUP BY year$$,
$$MATCH (st:student)-[t:TAKES]->(co:course)
WHERE st.name STARTS WITH 'A' AND co.title CONTAINS 'engineer'
RETURN t.year AS year, SUM(t.grade)$$,
10),

-- Students who took a "*-110" course and completed all of its direct prerequisites
('university',
$$SELECT s.name FROM student s
INNER JOIN takes t ON s.student_id = t.student_id
WHERE t.course_id LIKE '%110%'
AND NOT EXISTS (
    SELECT 1 FROM prereq p
    WHERE p.course_id = t.course_id
    AND NOT EXISTS (SELECT 1 FROM takes t2 WHERE t2.student_id = s.student_id AND t2.course_id = p.prereq_id)
)$$,
$$MATCH (s:student)-[:TAKES]->(c:course)
WHERE c.course_id CONTAINS '110'
AND NOT EXISTS {
    MATCH (c)-[:PREREQ]->(p:course)
    WHERE NOT EXISTS { MATCH (s)-[:TAKES]->(p) }
}
RETURN s.name$$,
10)
) AS samples
WHERE NOT EXISTS (SELECT 1 FROM saved_query);
