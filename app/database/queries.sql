--  executeQueryWithDefinedKeySQL
SELECT
    q1.customerId,
    q2.invoiceId,
    SUM(q3.price) AS invoicePrice
FROM (
    SELECT
        customer.id AS customerId,
        invoice.id AS invoiceId
    FROM
        invoice
        INNER JOIN customer ON invoice.customerId = customer.id) AS q1
    INNER JOIN (
        SELECT
            workinvoice.invoiceId,
            workinvoice.workId
        FROM
            workinvoice
            INNER JOIN invoice ON workinvoice.invoiceId = invoice.id) AS q2 USING (invoiceId)
    INNER JOIN (
        SELECT
            workhours.workid AS workId,
            SUM((worktype.price * workhours.hours * workhours.discount) + (item.purchaseprice * useditem.amount * useditem.discount)) AS price
        FROM
            workhours
            INNER JOIN worktype ON workhours.worktypeid = worktype.id
            INNER JOIN useditem ON workhours.workid = useditem.workid
            INNER JOIN item ON useditem.itemid = item.id
        GROUP BY
            workhours.workid) AS q3 USING (workId)
WHERE
    q1.customerId = 0
GROUP BY
    q2.invoiceId,
    q1.customerId;

-- Query Number of Rows in "warehouse" Tables
WITH customer_count(id, customer_count) AS (SELECT 0, count(*) FROM customer),
invoice_count(id, invoice_count) AS (SELECT 0, count(*) FROM invoice),
item_count(id, item_count) AS (SELECT 0, count(*) FROM item),
target_count(id, target_count) AS (SELECT 0, count(*) FROM target),
useditem_count(id, useditem_count) AS (SELECT 0, count(*) FROM useditem),
work_count(id, work_count) AS (SELECT 0, count(*) FROM work),
workhours_count(id, workhours_count) AS (SELECT 0, count(*) FROM workhours),
workinvoice_count(id, workinvoice_count) AS (SELECT 0, count(*) FROM workinvoice),
worktarget_count(id, worktarget_count) AS (SELECT 0, count(*) FROM worktarget),
worktype_count(id, worktype_count) AS (SELECT 0, count(*) FROM worktype)
SELECT t1.customer_count, t2.invoice_count, t3.item_count, t4.target_count, t5.useditem_count, t6.work_count, 
t7.workhours_count, t8.workinvoice_count, t9.worktarget_count, t10.worktype_count FROM customer_count AS t1 
INNER JOIN invoice_count AS t2 USING(id)
INNER JOIN item_count AS t3 USING(id) 
INNER JOIN target_count AS t4 USING(id)
INNER JOIN useditem_count AS t5 USING(id)
INNER JOIN work_count AS t6 USING(id)
INNER JOIN workhours_count AS t7 USING(id)
INNER JOIN workinvoice_count AS t8 USING(id) 
INNER JOIN worktarget_count AS t9 USING(id)
INNER JOIN worktype_count AS t10 USING(id);
