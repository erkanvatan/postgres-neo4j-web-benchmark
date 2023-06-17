-- Sample benchmark queries, shown in the "Select Query" dropdown of the Run Benchmark page.
-- Each pair returns the same rows from PostgreSQL and Neo4j. Fixed ids refer to the seeded
-- university generator and to the sequential ids of the warehouse generator.
INSERT INTO saved_query (selected_database, psql_query, neo4j_query, iteration_count)
SELECT * FROM (VALUES
('warehouse',
$$-- Work price for every work (2 joins)
SELECT work.id AS workid, SUM(worktype.price * workhours.hours * workhours.discount) AS price
FROM work
INNER JOIN workhours ON work.id = workhours.workid
INNER JOIN worktype ON worktype.id = workhours.worktypeid
GROUP BY work.id$$,
$$MATCH (w:work)-[h:WORKHOURS]->(wt:worktype)
RETURN w.id AS workid, SUM(h.hours * h.discount * wt.price) AS price$$,
10),

('warehouse',
$$-- Top 10 customers by revenue (4 joins over 1M invoice links)
SELECT i.customerid, SUM(wt.price * wh.hours * wh.discount) AS revenue
FROM invoice i
INNER JOIN workinvoice wi ON wi.invoiceid = i.id
INNER JOIN workhours wh ON wh.workid = wi.workid
INNER JOIN worktype wt ON wt.id = wh.worktypeid
GROUP BY i.customerid
ORDER BY revenue DESC, i.customerid
LIMIT 10$$,
$$MATCH (c:customer)-[:PAYS]->(:invoice)<-[:WORK_INVOICE]-(:work)-[h:WORKHOURS]->(wt:worktype)
RETURN c.id AS customerid, SUM(wt.price * h.hours * h.discount) AS revenue
ORDER BY revenue DESC, customerid
LIMIT 10$$,
10),

('warehouse',
$$-- One customer by id
SELECT id, name, address FROM customer WHERE id = 4000$$,
$$MATCH (c:customer {id: 4000})
RETURN c.id AS id, c.name AS name, c.address AS address$$,
10),

('warehouse',
$$-- Distinct items used for one customer (customer > targets > works > items)
SELECT count(DISTINCT u.itemid)
FROM target t
INNER JOIN worktarget wt ON wt.targetid = t.id
INNER JOIN useditem u ON u.workid = wt.workid
WHERE t.customerid = 4000$$,
$$MATCH (:customer {id: 4000})-[:CUSTOMER_TARGET]->(:target)<-[:WORK_TARGET]-(:work)-[:USED_ITEM]->(i:item)
RETURN count(DISTINCT i)$$,
10),

('university',
$$-- Prerequisites of AAS-200 within 5 levels
WITH RECURSIVE reachable(course_id, depth) AS (
    SELECT prereq_id, 1 FROM prereq WHERE course_id = 'AAS-200'
    UNION
    SELECT prereq.prereq_id, reachable.depth + 1
    FROM reachable
    INNER JOIN prereq ON prereq.course_id = reachable.course_id
    WHERE reachable.depth < 5
)
SELECT count(DISTINCT course_id) FROM reachable$$,
$$MATCH (:course {course_id: 'AAS-200'})-[:PREREQ*1..5]->(p:course)
RETURN count(DISTINCT p)$$,
10),

('university',
$$-- Prerequisites of AAS-200 within 10 levels
WITH RECURSIVE reachable(course_id, depth) AS (
    SELECT prereq_id, 1 FROM prereq WHERE course_id = 'AAS-200'
    UNION
    SELECT prereq.prereq_id, reachable.depth + 1
    FROM reachable
    INNER JOIN prereq ON prereq.course_id = reachable.course_id
    WHERE reachable.depth < 10
)
SELECT count(DISTINCT course_id) FROM reachable$$,
$$MATCH (:course {course_id: 'AAS-200'})-[:PREREQ*1..10]->(p:course)
RETURN count(DISTINCT p)$$,
10),

('university',
$$-- Prerequisites of AAS-200 within 20 levels
WITH RECURSIVE reachable(course_id, depth) AS (
    SELECT prereq_id, 1 FROM prereq WHERE course_id = 'AAS-200'
    UNION
    SELECT prereq.prereq_id, reachable.depth + 1
    FROM reachable
    INNER JOIN prereq ON prereq.course_id = reachable.course_id
    WHERE reachable.depth < 20
)
SELECT count(DISTINCT course_id) FROM reachable$$,
$$MATCH (:course {course_id: 'AAS-200'})-[:PREREQ*1..20]->(p:course)
RETURN count(DISTINCT p)$$,
10),

('university',
$$-- Prerequisites of AAS-200 within 30 levels
WITH RECURSIVE reachable(course_id, depth) AS (
    SELECT prereq_id, 1 FROM prereq WHERE course_id = 'AAS-200'
    UNION
    SELECT prereq.prereq_id, reachable.depth + 1
    FROM reachable
    INNER JOIN prereq ON prereq.course_id = reachable.course_id
    WHERE reachable.depth < 30
)
SELECT count(DISTINCT course_id) FROM reachable$$,
$$MATCH (:course {course_id: 'AAS-200'})-[:PREREQ*1..30]->(p:course)
RETURN count(DISTINCT p)$$,
10),

('university',
$$-- Shortest prerequisite path length from AAS-200 to VGD-115
WITH RECURSIVE reachable(course_id, depth) AS (
    SELECT 'AAS-200'::varchar, 0
    UNION
    SELECT prereq.prereq_id, reachable.depth + 1
    FROM reachable
    INNER JOIN prereq ON prereq.course_id = reachable.course_id
    WHERE reachable.depth < 30
)
SELECT min(depth) FROM reachable WHERE course_id = 'VGD-115'$$,
$$MATCH path = shortestPath((:course {course_id: 'AAS-200'})-[:PREREQ*..30]->(:course {course_id: 'VGD-115'}))
RETURN length(path)$$,
10),

('university',
$$-- Top 10 course recommendations for student 19061384 (courses taken by classmates)
SELECT t3.course_id, count(*) AS score
FROM takes t1
INNER JOIN takes t2 ON t2.course_id = t1.course_id AND t2.student_id <> t1.student_id
INNER JOIN takes t3 ON t3.student_id = t2.student_id
WHERE t1.student_id = '19061384'
AND NOT EXISTS (SELECT 1 FROM takes t4 WHERE t4.student_id = t1.student_id AND t4.course_id = t3.course_id)
GROUP BY t3.course_id
ORDER BY score DESC, t3.course_id
LIMIT 10$$,
$$// Collect my courses once: a NOT EXISTS { (me)-[:TAKES]->(rec) } check per row is about 5x slower
MATCH (me:student {student_id: '19061384'})-[:TAKES]->(c:course)
WITH me, collect(c) AS mine
UNWIND mine AS c
MATCH (c)<-[:TAKES]-(peer:student)-[:TAKES]->(rec:course)
WHERE peer <> me AND NOT rec IN mine
WITH rec, count(*) AS score
RETURN rec.course_id AS course_id, score
ORDER BY score DESC, course_id
LIMIT 10$$,
10),

('university',
$$-- Level-110 enrollments with every direct prerequisite completed
SELECT count(*)
FROM takes t
WHERE t.course_id LIKE '%-110'
AND NOT EXISTS (
    SELECT 1 FROM prereq p
    WHERE p.course_id = t.course_id
    AND NOT EXISTS (SELECT 1 FROM takes t2 WHERE t2.student_id = t.student_id AND t2.course_id = p.prereq_id)
)$$,
$$MATCH (s:student)-[:TAKES]->(c:course)
WHERE c.course_id ENDS WITH '-110'
AND NOT EXISTS {
    MATCH (c)-[:PREREQ]->(p:course)
    WHERE NOT EXISTS { (s)-[:TAKES]->(p) }
}
RETURN count(*)$$,
10)
) AS samples
WHERE NOT EXISTS (SELECT 1 FROM saved_query);
