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
    q1.customerId
