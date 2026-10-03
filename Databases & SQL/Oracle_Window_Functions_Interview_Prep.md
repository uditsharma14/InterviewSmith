# Oracle Analytic (Window) Functions — Interview Prep (Intermediate → Senior, with Code & Sources)

> **Target level:** Intermediate → Senior · **Baseline:** Oracle Database 19c–23ai (version-specific features flagged inline: `FETCH FIRST` 12c+, `LISTAGG … ON OVERFLOW` 12.2+, `LISTAGG(DISTINCT)` 19c+, `WINDOW` clause 21c+, `BOOLEAN`/`FROM`-less `SELECT` 23ai); standard-SQL outputs executed on PostgreSQL 16 · **Last verified:** 2026-10-03 · **Prerequisites:** basic SQL (`GROUP BY`, subqueries)

A focused guide for Oracle SQL rounds. It covers the core analytic functions with the tie and frame fixes, then the Oracle-only features interviewers like to check (`ROWNUM`, `KEEP`, `RATIO_TO_REPORT`, `LISTAGG`, `IGNORE NULLS`).

Companion to [SQL Query Practice](SQL_Query_Practice_Interview_Prep.md) (patterns, traps, dialects) and [SQL & Data Modeling](SQL_Data_Modeling_Interview_Prep.md) (concepts).

> **How the outputs were produced.** Oracle itself was **not** run for this guide.
> - **Sections 1–7** use standard SQL that behaves the same in Oracle and Postgres. Those queries were run on PostgreSQL 16 against the seed data below, and the outputs are real.
> - **Section 8** (Oracle-only syntax) shows the *expected* output, computed with an equivalent Postgres query. Run it once on Oracle (Oracle Live SQL, or the `gvenzl/oracle-free` Docker image) before relying on exact formatting.

---

## The one idea to lead with

> "Window functions compute across a set of related rows **without collapsing them**. `GROUP BY` returns one row per group. `… OVER (PARTITION BY …)` returns every original row, with the group-level value attached."

```text
function(...) OVER (
    PARTITION BY ...    -- which rows form the group     (like GROUP BY, but rows are kept)
    ORDER BY ...        -- order inside the group         (needed for LAG/LEAD/RANK/running totals)
    ROWS BETWEEN ...    -- which rows around the current one to include (the "frame")
)
```

**Logical order of evaluation:** `FROM` → `WHERE` → `GROUP BY` → `HAVING` → **window functions** → `SELECT` → `ORDER BY`.
So **you cannot use a window function in `WHERE`**. Wrap the query and filter outside it (see [§5](#5-filter-on-a-window-result-latest-order-per-customer)).

---

## Seed data (Oracle syntax)

```sql
CREATE TABLE orders (
  order_id     NUMBER PRIMARY KEY,
  customer_id  NUMBER NOT NULL,
  order_date   DATE   NOT NULL,
  amount       NUMBER(10,2) NOT NULL
);

INSERT INTO orders VALUES (1, 101, DATE '2026-01-05', 100);
INSERT INTO orders VALUES (2, 101, DATE '2026-01-10', 250);
INSERT INTO orders VALUES (3, 101, DATE '2026-01-10',  50);   -- same date as order 2
INSERT INTO orders VALUES (4, 101, DATE '2026-02-01', 300);
INSERT INTO orders VALUES (5, 102, DATE '2026-01-07',  80);
INSERT INTO orders VALUES (6, 102, DATE '2026-01-20',  80);   -- same amount as order 5
INSERT INTO orders VALUES (7, 102, DATE '2026-03-02',  40);
INSERT INTO orders VALUES (8, 103, DATE '2026-02-14', 500);   -- customer with one order
COMMIT;
```

**Built-in edge cases:** a date tie (orders 2 and 3), an amount tie (5 and 6), and a customer with a single order (103). Most bugs in window queries show up on exactly these cases.

---

## 1. Group-level analytics without collapsing rows (MIN / MAX / AVG / COUNT)

```sql
SELECT customer_id, order_id, amount,
       MIN(amount)                                  OVER (PARTITION BY customer_id) AS min_amount,
       MAX(amount)                                  OVER (PARTITION BY customer_id) AS max_amount,
       ROUND(AVG(amount) OVER (PARTITION BY customer_id), 2)                         AS avg_amount,
       COUNT(*)                                     OVER (PARTITION BY customer_id) AS order_count
FROM   orders
ORDER  BY customer_id, order_id;
```

```text
 customer_id | order_id | amount | min_amount | max_amount | avg_amount | order_count
-------------+----------+--------+------------+------------+------------+-------------
         101 |        1 | 100.00 |      50.00 |     300.00 |     175.00 |           4
         101 |        2 | 250.00 |      50.00 |     300.00 |     175.00 |           4
         101 |        3 |  50.00 |      50.00 |     300.00 |     175.00 |           4
         101 |        4 | 300.00 |      50.00 |     300.00 |     175.00 |           4
         102 |        5 |  80.00 |      40.00 |      80.00 |      66.67 |           3
         102 |        6 |  80.00 |      40.00 |      80.00 |      66.67 |           3
         102 |        7 |  40.00 |      40.00 |      80.00 |      66.67 |           3
         103 |        8 | 500.00 |     500.00 |     500.00 |     500.00 |           1
```

- With `GROUP BY customer_id` you'd get 3 rows. Here all 8 rows remain, each carrying its customer's statistics. That's what makes "compare each order to the customer's average" a single query.
- `ROUND` the `AVG`. In Oracle, 200/3 comes back as `66.6666666666666666666666666666666666667`.
- No `ORDER BY` inside `OVER` means the frame is the **whole partition**. That's what you want for group totals.

---

## 2. Running total (and the tie trap)

```sql
SELECT customer_id, order_id, order_date, amount,
       SUM(amount) OVER (PARTITION BY customer_id
                         ORDER BY order_date)                           AS default_frame,
       SUM(amount) OVER (PARTITION BY customer_id
                         ORDER BY order_date, order_id
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM   orders
WHERE  customer_id = 101
ORDER  BY order_date, order_id;
```

```text
 customer_id | order_id | order_date | amount | default_frame | running_total
-------------+----------+------------+--------+---------------+---------------
         101 |        1 | 2026-01-05 | 100.00 |        100.00 |        100.00
         101 |        2 | 2026-01-10 | 250.00 |        400.00 |        350.00   ← default jumps ahead
         101 |        3 | 2026-01-10 |  50.00 |        400.00 |        400.00
         101 |        4 | 2026-02-01 | 300.00 |        700.00 |        700.00
```

- **Why:** when you specify `ORDER BY` with no frame, the default is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. `RANGE` includes every row whose `order_date` *equals* the current one, so orders 2 and 3 both show 400.
- **Fix:** `ROWS` plus a unique tie-breaker (`order_id`).
- **Oracle note:** `DATE` always includes the time of day. If the data was loaded as date-only (time = midnight), same-day ties are common.

---

## 3. LAG / LEAD: previous and next row

```sql
SELECT customer_id, order_id, order_date, amount,
       LAG(amount)  OVER w                                   AS prev_amount,
       LEAD(amount) OVER w                                   AS next_amount,
       amount - LAG(amount) OVER w                           AS diff_from_prev,
       ROUND(100 * (amount - LAG(amount) OVER w)
                 / NULLIF(LAG(amount) OVER w, 0), 1)         AS pct_change,
       order_date - LAG(order_date) OVER w                   AS days_since_prev
FROM   orders
WINDOW w AS (PARTITION BY customer_id ORDER BY order_date, order_id)   -- WINDOW clause: Oracle 21c+
ORDER  BY customer_id, order_date, order_id;
```

```text
 customer_id | order_id | order_date | amount | prev_amount | next_amount | diff_from_prev | pct_change | days_since_prev
-------------+----------+------------+--------+-------------+-------------+----------------+------------+-----------------
         101 |        1 | 2026-01-05 | 100.00 |             |      250.00 |                |            |
         101 |        2 | 2026-01-10 | 250.00 |      100.00 |       50.00 |         150.00 |      150.0 |               5
         101 |        3 | 2026-01-10 |  50.00 |      250.00 |      300.00 |        -200.00 |      -80.0 |               0
         101 |        4 | 2026-02-01 | 300.00 |       50.00 |             |         250.00 |      500.0 |              22
         102 |        5 | 2026-01-07 |  80.00 |             |       80.00 |                |            |
         102 |        6 | 2026-01-20 |  80.00 |       80.00 |       40.00 |           0.00 |        0.0 |              13
         102 |        7 | 2026-03-02 |  40.00 |       80.00 |             |         -40.00 |      -50.0 |              41
         103 |        8 | 2026-02-14 | 500.00 |             |             |                |            |
```

- **The first row in each partition gets NULL** from `LAG`, and the last gets NULL from `LEAD`. Customer 103 gets NULL from both. To supply a default, use `LAG(amount, 1, 0)` (offset, default), but only when 0 makes sense for the business.
- **Tie-breaker:** without `order_id`, which of orders 2 and 3 counts as "previous" is arbitrary, and the diff could be `+150` or `-50` between runs.
- `NULLIF(…, 0)` prevents a divide-by-zero error (`ORA-01476`) when the previous amount is 0.
- In Oracle, `DATE - DATE` returns a **number of days** (fractional if times differ). For `TIMESTAMP`s, the result is an `INTERVAL DAY TO SECOND`.
- **Before Oracle 21c** there's no `WINDOW` clause: repeat the `OVER (PARTITION BY customer_id ORDER BY order_date, order_id)` in each column.

---

## 4. RANK vs DENSE_RANK vs ROW_NUMBER within a group

```sql
SELECT customer_id, order_id, amount,
       ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS rn,
       RANK()       OVER (PARTITION BY customer_id ORDER BY amount DESC) AS rnk,
       DENSE_RANK() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS drnk
FROM   orders
WHERE  customer_id = 102
ORDER  BY amount DESC, order_id;
```

```text
 customer_id | order_id | amount | rn | rnk | drnk
-------------+----------+--------+----+-----+------
         102 |        5 |  80.00 |  1 |   1 |    1
         102 |        6 |  80.00 |  2 |   1 |    1
         102 |        7 |  40.00 |  3 |   3 |    2
```

| Function | On a tie | Use it for |
|---|---|---|
| `ROW_NUMBER` | Always unique; ties broken arbitrarily (add a tie-breaker) | Exactly one row: "latest order", dedup |
| `RANK` | Same rank, then **skips** (1, 1, 3) | Competition-style ranking |
| `DENSE_RANK` | Same rank, **no gaps** (1, 1, 2) | "Nth highest value", top N distinct values |

---

## 5. Filter on a window result: latest order per customer

```sql
-- ❌ ORA-30483: window functions are not allowed here
SELECT * FROM orders
WHERE  ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1;

-- ✅ Compute in a subquery, filter outside
SELECT customer_id, order_id, order_date, amount
FROM (
  SELECT o.*,
         ROW_NUMBER() OVER (PARTITION BY customer_id
                            ORDER BY order_date DESC, order_id DESC) AS rn
  FROM   orders o
)
WHERE  rn = 1
ORDER  BY customer_id;
```

```text
 customer_id | order_id | order_date | amount
-------------+----------+------------+--------
         101 |        4 | 2026-02-01 | 300.00
         102 |        7 | 2026-03-02 |  40.00
         103 |        8 | 2026-02-14 | 500.00
```

Oracle doesn't require an alias on the inline view. Neither does PostgreSQL from version 16 (earlier versions, and MySQL, do). Adding one is harmless. For the one-step Oracle alternative, see `KEEP` in [§8.2](#82-keep-dense_rank-firstlast-latest-per-group-in-one-group-by).

---

## 6. Moving average (sliding frame)

```sql
SELECT customer_id, order_id, order_date, amount,
       ROUND(AVG(amount) OVER (PARTITION BY customer_id
                               ORDER BY order_date, order_id
                               ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3
FROM   orders
WHERE  customer_id = 101
ORDER  BY order_date, order_id;
```

```text
 customer_id | order_id | order_date | amount | moving_avg_3
-------------+----------+------------+--------+--------------
         101 |        1 | 2026-01-05 | 100.00 |       100.00
         101 |        2 | 2026-01-10 | 250.00 |       175.00
         101 |        3 | 2026-01-10 |  50.00 |       133.33
         101 |        4 | 2026-02-01 | 300.00 |       200.00
```

- `ROWS BETWEEN 2 PRECEDING` means the last 3 **orders**. For the last 30 **days**, use a range on the date: `RANGE BETWEEN INTERVAL '30' DAY PRECEDING AND CURRENT ROW` (Oracle), or `RANGE BETWEEN 30 PRECEDING AND CURRENT ROW` on a `DATE`.
- The first rows average over fewer than 3 values. Say whether that's acceptable, or blank them out until `COUNT(*) OVER (same frame) = 3`.

---

## 7. NTILE: bucket rows into quartiles

```sql
SELECT order_id, amount,
       NTILE(4) OVER (ORDER BY amount DESC, order_id) AS quartile
FROM   orders
ORDER  BY amount DESC, order_id;
```

```text
 order_id | amount | quartile
----------+--------+----------
        8 | 500.00 |        1
        4 | 300.00 |        1
        2 | 250.00 |        2
        1 | 100.00 |        2
        5 |  80.00 |        3
        6 |  80.00 |        3
        3 |  50.00 |        4
        7 |  40.00 |        4
```

`NTILE` splits by **row count**, not by value: equal amounts can land in different buckets if they fall on a boundary. For value-based percentiles, use `PERCENT_RANK()` or `PERCENTILE_CONT`.

---

## 8. Oracle-only features

*Expected outputs below were computed with an equivalent Postgres query; Oracle was not run.*

### 8.1 The `ROWNUM` trap and `FETCH FIRST`

```sql
-- ❌ ROWNUM is assigned BEFORE ORDER BY: picks 3 arbitrary rows, then sorts them
SELECT order_id, amount FROM orders
WHERE  ROWNUM <= 3
ORDER  BY amount DESC;

-- ✅ Oracle 12c+
SELECT order_id, amount FROM orders
ORDER  BY amount DESC, order_id
FETCH FIRST 3 ROWS ONLY;            -- or FETCH FIRST 3 ROWS WITH TIES

-- ✅ Pre-12c: sort in an inline view, apply ROWNUM outside
SELECT * FROM (
  SELECT order_id, amount FROM orders ORDER BY amount DESC, order_id
) WHERE ROWNUM <= 3;
```

```text
 ORDER_ID | AMOUNT
----------+--------
        8 |    500
        4 |    300
        2 |    250
```

- `WHERE ROWNUM = 2` or `ROWNUM > 1` **always returns no rows**. A row only gets ROWNUM 2 once a row 1 has been accepted, and that filter rejects row 1. For pagination, use `OFFSET 10 ROWS FETCH NEXT 10 ROWS ONLY` (12c+), or `ROW_NUMBER()` in a subquery.

### 8.2 `KEEP (DENSE_RANK FIRST/LAST)`: latest per group in one `GROUP BY`

```sql
SELECT customer_id,
       MAX(amount) KEEP (DENSE_RANK LAST  ORDER BY order_date, order_id) AS latest_amount,
       MAX(amount) KEEP (DENSE_RANK FIRST ORDER BY order_date, order_id) AS first_amount,
       COUNT(*)                                                          AS orders
FROM   orders
GROUP  BY customer_id
ORDER  BY customer_id;
```

```text
 CUSTOMER_ID | LATEST_AMOUNT | FIRST_AMOUNT | ORDERS
-------------+---------------+--------------+--------
         101 |           300 |          100 |      4
         102 |            40 |           80 |      3
         103 |           500 |          500 |      1
```

- Read it as: "Among the rows that rank **last** by `order_date, order_id`, take the `MAX(amount)`." The `MAX` only matters as a tie-breaker when several rows share that last position.
- You can mix it with ordinary aggregates in the same `GROUP BY`. A `ROW_NUMBER` subquery can't do that without an extra join.
- It can also be used as an analytic function: `… KEEP (…) OVER (PARTITION BY customer_id)`.

### 8.3 `RATIO_TO_REPORT`: share of the total

```sql
SELECT customer_id, order_id, amount,
       ROUND(RATIO_TO_REPORT(amount) OVER (PARTITION BY customer_id), 4) AS share
FROM   orders
ORDER  BY customer_id, order_id;
```

```text
 CUSTOMER_ID | ORDER_ID | AMOUNT |  SHARE
-------------+----------+--------+--------
         101 |        1 |    100 |  .1429
         101 |        2 |    250 |  .3571
         101 |        3 |     50 |  .0714
         101 |        4 |    300 |  .4286
         102 |        5 |     80 |     .4
         102 |        6 |     80 |     .4
         102 |        7 |     40 |     .2
         103 |        8 |    500 |      1
```

Equivalent portable form: `amount / SUM(amount) OVER (PARTITION BY customer_id)`. Drop the `PARTITION BY` for share of the grand total. (SQL*Plus prints decimals without the leading zero, as shown.)

### 8.4 `LISTAGG`: string aggregation

```sql
SELECT customer_id,
       LISTAGG(order_id, ',') WITHIN GROUP (ORDER BY order_date, order_id) AS order_ids
FROM   orders
GROUP  BY customer_id
ORDER  BY customer_id;
```

```text
 CUSTOMER_ID | ORDER_IDS
-------------+-----------
         101 | 1,2,3,4
         102 | 5,6,7
         103 | 8
```

- The result is limited to `VARCHAR2` size (4000 bytes by default). Past that, it fails with `ORA-01489`. Since 12.2 you can write `LISTAGG(… ON OVERFLOW TRUNCATE '…' WITH COUNT)`.
- `LISTAGG(DISTINCT …)` is available from 19c.

### 8.5 `IGNORE NULLS`: carry the last known value forward

```sql
-- Fill gaps in a reading with the most recent non-NULL value
SELECT reading_time, value,
       LAST_VALUE(value IGNORE NULLS) OVER (ORDER BY reading_time
                                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS filled
FROM   sensor_readings;

-- Previous non-NULL value
LAG(value IGNORE NULLS) OVER (ORDER BY reading_time)
```

Example: values `10, NULL, NULL, 25, NULL` → `filled` = `10, 10, 10, 25, 25`. Postgres 16 has no `IGNORE NULLS`. There you'd use the "flag and cumulative count" trick ([SQL Query Practice B7](SQL_Query_Practice_Interview_Prep.md#b7-sessionization)) to group each value with the NULLs that follow it.

### 8.6 Oracle gotchas worth mentioning

| Gotcha | Detail |
|---|---|
| `''` is NULL | In Oracle, an empty string *is* NULL: `WHERE name = ''` matches nothing, and `'' IS NULL` is true. Other databases treat them as different. |
| `DATE` has a time part | `WHERE order_date = DATE '2026-01-10'` misses rows at 14:30. Use `>= DATE '2026-01-10' AND < DATE '2026-01-11'`, or `TRUNC(order_date)`, which prevents a plain index on `order_date` from being used unless you create a function-based index. |
| No `LIMIT` | Use `FETCH FIRST n ROWS ONLY` (12c+) or `ROWNUM` in an outer query. |
| `DUAL` | `SELECT SYSDATE FROM dual`. Before 23ai, every `SELECT` needs a `FROM`. |
| No `BOOLEAN` column before 23ai | Usually `CHAR(1)` with 'Y'/'N', or `NUMBER(1)`. |
| Identifiers are uppercased | `orders` and `ORDERS` are the same table. A quoted `"orders"` is a different one. |
| `MERGE` for upsert | Oracle has no `ON CONFLICT`. Use `MERGE INTO … USING … ON (…) WHEN MATCHED THEN UPDATE … WHEN NOT MATCHED THEN INSERT …`. |

---

## Memory sheet

```text
Window function      → analytics per row, rows NOT collapsed (vs GROUP BY)
OVER ()              → whole result set     | PARTITION BY → per group
ORDER BY in OVER     → enables LAG/LEAD/RANK/running totals; default frame = RANGE … CURRENT ROW
Running total        → ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW + unique tie-breaker
LAG / LEAD           → previous / next row; NULL at the edges; LAG(x, 1, default)
ROW_NUMBER           → unique; latest-per-group, dedup
RANK / DENSE_RANK    → ties share a rank; RANK skips (1,1,3), DENSE_RANK doesn't (1,1,2)
Moving average       → ROWS BETWEEN n PRECEDING AND CURRENT ROW
Filter on a window   → subquery/CTE, then WHERE (no window functions in WHERE: ORA-30483)
Oracle extras        → FETCH FIRST (not ROWNUM + ORDER BY), KEEP DENSE_RANK LAST,
                       RATIO_TO_REPORT, LISTAGG, IGNORE NULLS, '' IS NULL
```

---

## Sources

- Oracle Database 19c SQL Language Reference: [Analytic Functions](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Analytic-Functions.html) (windowing clause and default frame), [`FIRST`/`LAST` (`KEEP`)](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/FIRST.html), [`RATIO_TO_REPORT`](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/RATIO_TO_REPORT.html), [`LISTAGG`](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/LISTAGG.html), [`LAST_VALUE` (`IGNORE NULLS`)](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/LAST_VALUE.html), [`NTILE`](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/NTILE.html), [`ROWNUM` pseudocolumn](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/ROWNUM-Pseudocolumn.html), [`SELECT` row-limiting clause (`FETCH FIRST`)](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/SELECT.html), [`MERGE`](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/MERGE.html), [Nulls (empty string is NULL)](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Nulls.html)
- Oracle Database 21c SQL Language Reference: [`SELECT` (`window_clause`)](https://docs.oracle.com/en/database/oracle/oracle-database/21/sqlrf/SELECT.html)
- Oracle Database 23ai SQL Language Reference: [Data Types (`BOOLEAN`)](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/Data-Types.html), [`SELECT` (`FROM` clause optional)](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/SELECT.html)
- PostgreSQL 16 documentation: [Window Functions](https://www.postgresql.org/docs/16/functions-window.html) (used to execute the standard-SQL sections)
