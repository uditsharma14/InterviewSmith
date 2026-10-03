# SQL Query Practice — Interview Prep (Senior → Staff, with Real Outputs & Sources)

> **Target level:** Senior → Staff · **Baseline:** PostgreSQL 16.2 (every query and output executed); MySQL 9.3 for the MySQL claims; SQL Server syntax is reference only, not executed · **Last verified:** 2026-10-03 · **Prerequisites:** [SQL & Data Modeling](SQL_Data_Modeling_Interview_Prep.md) Part B, or comfort with joins, `GROUP BY` and basic window functions

The second SQL guide. [SQL & Data Modeling](SQL_Data_Modeling_Interview_Prep.md) covers the concepts (modeling, indexing, isolation) and the eight core practice problems. This one is the **query-writing workout**:

- 10 rapid-fire classics with the edge cases fixed
- 14 harder patterns that come up in Lead/Senior rounds
- the SQL traps interviewers probe
- a Postgres / MySQL / SQL Server dialect table

**Every query and output here was actually run.** Postgres queries ran on PostgreSQL 16.2 against the seed data below, and the result tables are copied from that run. The MySQL claims were checked on MySQL 9.3. SQL Server syntax was **not** executed; treat it as reference.

**How to answer any SQL question (say this out loud):**
1. **Clarify** the grain and the edge cases: "One row per what? What about ties, NULLs, duplicates, empty groups?"
2. **State the approach** in one sentence before typing.
3. **Write** the query, using CTEs to name each step.
4. **Check** it against a tiny example, especially ties and NULLs.
5. **Scale:** "On a big table I'd want an index on X. Here's what the plan would do."

---

## Contents

- [Setup: seed data](#setup-seed-data)
- [Part A — 10 rapid-fire classics](#part-a--10-rapid-fire-classics)
- [Part B — Advanced patterns](#part-b--advanced-patterns)
  - [B1. Earning more than their manager](#b1-earning-more-than-their-manager-self-join) · [B2. Org chart](#b2-org-chart-with-depth-recursive-cte) · [B3. Pivot](#b3-pivot-rows-into-columns) · [B4. Percent of total](#b4-percent-of-total)
  - [B5. Median and p90](#b5-median-and-percentiles) · [B6. Fill missing days](#b6-fill-missing-days-date-spine) · [B7. Sessionization](#b7-sessionization) · [B8. Streaks](#b8-streaks-of-the-same-status-gaps-and-islands)
  - [B9. Retention](#b9-month-over-month-retention) · [B10. Relational division](#b10-relational-division-has-all-of) · [B11. Mode with ties](#b11-most-frequent-value-per-group-with-ties) · [B12. Overlapping intervals](#b12-overlapping-intervals)
  - [B13. FIRST_VALUE / LAST_VALUE trap](#b13-first_value--last_value-and-the-frame-trap) · [B14. Idempotent upsert](#b14-idempotent-upsert-for-out-of-order-events)
- [Part C — Traps interviewers probe](#part-c--traps-interviewers-probe)
- [Part D — Dialect differences](#part-d--dialect-differences)
- [Part E — Pattern picker](#part-e--pattern-picker)
- [Sources](#sources)

---

## Setup: seed data

Paste this into any Postgres (`docker run -e POSTGRES_PASSWORD=x -p 5432:5432 postgres:16`, or an online sandbox) to reproduce every output below. It uses the same `customers` / `accounts` / `transactions` shape as the first guide, plus `employees`.

```sql
CREATE TABLE employees (
  emp_id      INT PRIMARY KEY,
  name        TEXT NOT NULL,
  dept        TEXT NOT NULL,
  manager_id  INT REFERENCES employees(emp_id),
  salary      INT NOT NULL
);
INSERT INTO employees VALUES
 (1,'Asha','Eng',  NULL,250),
 (2,'Ben', 'Eng',  1,   180),
 (3,'Chen','Eng',  1,   180),
 (4,'Dev', 'Eng',  2,   150),
 (5,'Eli', 'Eng',  2,   190),
 (6,'Fay', 'Sales',1,   120),
 (7,'Gus', 'Sales',6,   130),
 (8,'Hana','Sales',6,    90),
 (9,'Ivy', 'Ops',  1,   100);

CREATE TABLE customers (
  customer_id BIGINT PRIMARY KEY,
  name        TEXT NOT NULL,
  email       TEXT UNIQUE,
  country     TEXT,
  created_at  TIMESTAMP NOT NULL
);
INSERT INTO customers VALUES
 (1,'Ana', 'ana@x.com', 'US','2026-01-01'),
 (2,'Raj', 'raj@x.com', 'US','2026-01-05'),
 (3,'Mei', 'mei@x.com', 'IN','2026-01-10'),
 (4,'Tom', NULL,        'UK','2026-02-01'),
 (5,'Zoe', NULL,        'US','2026-02-15'),
 (6,'Ana2','ANA@x.com', 'US','2026-03-01');

CREATE TABLE accounts (
  account_id   BIGINT PRIMARY KEY,
  customer_id  BIGINT NOT NULL REFERENCES customers(customer_id),
  account_type TEXT NOT NULL,
  opened_at    TIMESTAMP NOT NULL
);
INSERT INTO accounts VALUES
 (10,1,'CHECKING','2026-01-01'),
 (11,1,'CREDIT',  '2026-01-02'),
 (20,2,'CHECKING','2026-01-05'),
 (30,3,'CREDIT',  '2026-01-10'),
 (40,4,'CHECKING','2026-02-01');

CREATE TABLE transactions (
  txn_id      BIGINT PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES accounts(account_id),
  amount      NUMERIC(12,2) NOT NULL,
  status      TEXT NOT NULL,
  merchant    TEXT,
  created_at  TIMESTAMP NOT NULL
);
INSERT INTO transactions VALUES
 (101,10, 50.00,'APPROVED','Cafe',   '2026-01-03 09:00'),
 (102,10, 20.00,'APPROVED','Cafe',   '2026-01-03 09:20'),
 (103,10,200.00,'APPROVED','Grocer', '2026-01-03 11:00'),
 (104,10, 30.00,'APPROVED','Cafe',   '2026-01-04 08:00'),
 (105,10, 30.00,'APPROVED','Grocer', '2026-01-04 08:00'),
 (106,10, 75.00,'APPROVED','Fuel',   '2026-01-05 18:00'),
 (107,10, 40.00,'APPROVED','Cafe',   '2026-02-02 09:00'),
 (111,11,500.00,'APPROVED','Airline','2026-01-15 10:00'),
 (112,11, 60.00,'DECLINED','Hotel',  '2026-02-10 10:00'),
 (113,11, 60.00,'DECLINED','Hotel',  '2026-02-10 10:01'),
 (114,11, 60.00,'DECLINED','Hotel',  '2026-02-10 10:02'),
 (115,11, 60.00,'APPROVED','Hotel',  '2026-02-10 10:05'),
 (201,20, 10.00,'APPROVED','Cafe',   '2026-01-06 07:00'),
 (202,20, 10.00,'APPROVED','Fuel',   '2026-01-20 07:00'),
 (203,20, 90.00,'APPROVED','Grocer', '2026-02-20 07:00'),
 (204,20, 15.00,'DECLINED','Cafe',   '2026-03-01 07:00'),
 (301,30,500.00,'APPROVED','Airline','2026-01-12 12:00'),
 (302,30,120.00,'APPROVED','Grocer', '2026-03-05 12:00');

CREATE TABLE card_holds (
  hold_id     INT PRIMARY KEY,
  account_id  BIGINT NOT NULL,
  starts_at   TIMESTAMP NOT NULL,
  ends_at     TIMESTAMP NOT NULL
);
INSERT INTO card_holds VALUES
 (1,10,'2026-01-03 09:00','2026-01-03 12:00'),
 (2,10,'2026-01-03 11:00','2026-01-03 13:00'),
 (3,10,'2026-01-03 13:00','2026-01-03 14:00'),
 (4,20,'2026-01-06 07:00','2026-01-06 08:00');

CREATE TABLE account_balance (
  account_id  BIGINT PRIMARY KEY,
  balance     NUMERIC(12,2) NOT NULL,
  as_of       TIMESTAMP NOT NULL
);
INSERT INTO account_balance VALUES (10, 500.00, '2026-02-01 00:00');
```

**Built-in edge cases:** Ben and Chen tie at 180; two customers have NULL emails; `ana@x.com` and `ANA@x.com` differ only by case; txns 104 and 105 share a timestamp; account 11 has three declines in a row; customers 5 and 6 have no accounts.

---

## Part A — 10 Rapid-Fire Classics

Short answers you should be able to write without thinking. Each one includes the edge case that separates a Senior answer from a Lead answer.

### A1. Second-highest salary

```sql
SELECT MAX(salary) AS second_highest
FROM   employees
WHERE  salary < (SELECT MAX(salary) FROM employees);
```

```text
 second_highest
----------------
            190
```

- Handles ties at the top. Returns NULL (not zero rows) if there's no second value.
- **Generalize to Nth:** `DENSE_RANK() OVER (ORDER BY salary DESC)` and filter `rnk = N`. `DENSE_RANK`, not `ROW_NUMBER`, because "Nth highest *salary*" means the Nth distinct value.

### A2. Top 3 salaries per department

```sql
SELECT dept, name, salary, rnk
FROM (
  SELECT dept, name, salary,
         DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rnk
  FROM   employees
) t
WHERE  rnk <= 3
ORDER  BY dept, rnk, name;
```

```text
 dept  | name | salary | rnk
-------+------+--------+-----
 Eng   | Asha |    250 |   1
 Eng   | Eli  |    190 |   2
 Eng   | Ben  |    180 |   3
 Eng   | Chen |    180 |   3
 Ops   | Ivy  |    100 |   1
 Sales | Gus  |    130 |   1
 Sales | Fay  |    120 |   2
 Sales | Hana |     90 |   3
```

- **Say this:** "Eng returns 4 rows because Ben and Chen tie. If the requirement is *exactly* 3 people, I'd use `ROW_NUMBER` with a tie-breaker. If it's the top 3 *pay levels*, `DENSE_RANK`." Always ask which one they want.

### A3. Find duplicates

```sql
-- ❌ Naive: groups NULLs together and misses case variants
SELECT email, COUNT(*) FROM customers GROUP BY email HAVING COUNT(*) > 1;
```

```text
 email | count
-------+-------
       |     2        ← the two NULL emails, not a real duplicate
```

```sql
-- ✅ Normalize and exclude NULLs
SELECT LOWER(TRIM(email)) AS email, COUNT(*) AS cnt
FROM   customers
WHERE  email IS NOT NULL
GROUP  BY LOWER(TRIM(email))
HAVING COUNT(*) > 1;
```

```text
   email   | cnt
-----------+-----
 ana@x.com |   2
```

The naive version returned the wrong row *and* missed the real duplicate.

### A4. Customers with no accounts (anti-join)

```sql
SELECT c.customer_id, c.name
FROM   customers c
WHERE  NOT EXISTS (SELECT 1 FROM accounts a WHERE a.customer_id = c.customer_id)
ORDER  BY 1;
```

```text
 customer_id | name
-------------+------
           5 | Zoe
           6 | Ana2
```

`LEFT JOIN … WHERE a.customer_id IS NULL` gives the same result. **Never `NOT IN (subquery)`**: see [Part C](#part-c--traps-interviewers-probe).

### A5. Latest row per group

```sql
SELECT account_id, txn_id, created_at
FROM (
  SELECT t.*,
         ROW_NUMBER() OVER (PARTITION BY account_id
                            ORDER BY created_at DESC, txn_id DESC) AS rn
  FROM   transactions t
) x
WHERE  rn = 1
ORDER  BY account_id;

-- Postgres shorthand, same result
SELECT DISTINCT ON (account_id) account_id, txn_id, created_at
FROM   transactions
ORDER  BY account_id, created_at DESC, txn_id DESC;
```

```text
 account_id | txn_id |     created_at
------------+--------+---------------------
         10 |    107 | 2026-02-02 09:00:00
         11 |    115 | 2026-02-10 10:05:00
         20 |    204 | 2026-03-01 07:00:00
         30 |    302 | 2026-03-05 12:00:00
```

- The `txn_id DESC` tie-breaker makes the result deterministic when two rows share a timestamp (like 104/105). Without it, which row you get can change between runs.
- **Scale:** an index on `(account_id, created_at DESC, txn_id DESC)` lets each group be found with an index seek.

### A6. `WHERE` vs `HAVING`

```sql
SELECT dept, COUNT(*) AS headcount
FROM   employees
WHERE  salary >= 100          -- filters ROWS, before grouping
GROUP  BY dept
HAVING COUNT(*) >= 2          -- filters GROUPS, after aggregation
ORDER  BY dept;
```

```text
 dept  | headcount
-------+-----------
 Eng   |         5
 Sales |         2
```

Hana (90) is removed by `WHERE`, so Sales keeps 2 people. Ops (1 person) is removed by `HAVING`. **Performance point:** put row filters in `WHERE` so less data is grouped. Use `HAVING` only for conditions on aggregates.

### A7. `ROW_NUMBER` vs `RANK` vs `DENSE_RANK`

```sql
SELECT v,
       ROW_NUMBER() OVER w AS row_number,
       RANK()       OVER w AS rank,
       DENSE_RANK() OVER w AS dense_rank
FROM   (VALUES (100),(90),(90),(80)) t(v)
WINDOW w AS (ORDER BY v DESC);
```

```text
  v  | row_number | rank | dense_rank
-----+------------+------+------------
 100 |          1 |    1 |          1
  90 |          2 |    2 |          2
  90 |          3 |    2 |          2
  80 |          4 |    4 |          3
```

One line: **ROW_NUMBER** is always unique, **RANK** gives ties the same rank and then skips numbers, and **DENSE_RANK** gives ties the same rank with no gaps.

### A8. Running total (and the default-frame bug)

```sql
SELECT txn_id, created_at, amount,
       SUM(amount) OVER (ORDER BY created_at) AS default_frame,
       SUM(amount) OVER (ORDER BY created_at, txn_id
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rows_frame
FROM   transactions
WHERE  account_id = 10 AND created_at < '2026-01-05'
ORDER  BY created_at, txn_id;
```

```text
 txn_id |     created_at      | amount | default_frame | rows_frame
--------+---------------------+--------+---------------+------------
    101 | 2026-01-03 09:00:00 |  50.00 |         50.00 |      50.00
    102 | 2026-01-03 09:20:00 |  20.00 |         70.00 |      70.00
    103 | 2026-01-03 11:00:00 | 200.00 |        270.00 |     270.00
    104 | 2026-01-04 08:00:00 |  30.00 |        330.00 |     300.00   ← default jumps ahead
    105 | 2026-01-04 08:00:00 |  30.00 |        330.00 |     330.00
```

The default frame is `RANGE UNBOUNDED PRECEDING`, which includes every row *tied* with the current one. Txns 104 and 105 share a timestamp, so both show 330. Use `ROWS` plus a unique tie-breaker for a true row-by-row total. The same thing happens in MySQL.

### A9. Employees earning more than their department average

```sql
SELECT dept, name, salary, ROUND(dept_avg, 1) AS dept_avg
FROM (
  SELECT e.*, AVG(salary) OVER (PARTITION BY dept) AS dept_avg
  FROM   employees e
) t
WHERE  salary > dept_avg
ORDER  BY dept, name;
```

```text
 dept  | name | salary | dept_avg
-------+------+--------+----------
 Eng   | Asha |    250 |    190.0
 Sales | Fay  |    120 |    113.3
 Sales | Gus  |    130 |    113.3
```

The window version reads the table once. The classic version, a join to a `GROUP BY` subquery, reads it twice. Both are correct; mention both.

### A10. Delete duplicates, keep one

```sql
-- Postgres: self-join delete (keeps the lowest id)
DELETE FROM customers c
USING  customers d
WHERE  LOWER(c.email) = LOWER(d.email)
  AND  c.customer_id > d.customer_id
RETURNING c.customer_id, c.email;
```

```text
 customer_id |   email
-------------+-----------
           6 | ANA@x.com
```

**Dialect notes (MySQL ones verified on 9.3):**
- **MySQL:** `DELETE FROM users WHERE id IN (SELECT id FROM users …)` fails with **ERROR 1093** ("can't specify target table for update in FROM clause"). Wrapping the subquery in a **CTE or derived table** works, because MySQL materializes it first, so the `WITH cte AS (… ROW_NUMBER …) DELETE … WHERE id IN (SELECT id FROM cte WHERE rn > 1)` pattern runs fine. The multi-table form `DELETE u FROM users u JOIN users d ON u.email = d.email AND u.id > d.id` also works.
- **MySQL collation:** the default `utf8mb4_0900_ai_ci` collation is case-insensitive, so `'a@x.com' = 'A@X.com'` is true. That delete removes case variants that Postgres would keep unless you add `LOWER()`.
- **SQL Server:** you can delete through the CTE directly: `WITH cte AS (…) DELETE FROM cte WHERE rn > 1;`.
- **Say this:** "Before deleting, I'd re-point foreign keys to the surviving row, run it in batches on a big table, and add a unique index on `LOWER(email)` so it can't happen again."

---

## Part B — Advanced Patterns

### B1. Earning more than their manager (self-join)

> **Approach:** "Join the table to itself: one alias for the employee, one for the manager."

```sql
SELECT e.name AS employee, e.salary, m.name AS manager, m.salary AS manager_salary
FROM   employees e
JOIN   employees m ON m.emp_id = e.manager_id
WHERE  e.salary > m.salary
ORDER  BY e.name;
```

```text
 employee | salary | manager | manager_salary
----------+--------+---------+----------------
 Eli      |    190 | Ben     |            180
 Gus      |    130 | Fay     |            120
```

An inner join drops the CEO (no manager), which is correct here. Use `LEFT JOIN` if the question asks you to list everyone.

### B2. Org chart with depth (recursive CTE)

> **Approach:** "Anchor on the root, then repeatedly join children to the rows found so far. Track the path, both to sort and to stop cycles."

```sql
WITH RECURSIVE org AS (
  SELECT emp_id, name, manager_id, 0 AS depth,
         ARRAY[emp_id] AS path, name::text AS chain
  FROM   employees
  WHERE  manager_id IS NULL                      -- anchor
  UNION ALL
  SELECT e.emp_id, e.name, e.manager_id, o.depth + 1,
         o.path || e.emp_id, o.chain || ' > ' || e.name
  FROM   employees e
  JOIN   org o ON e.manager_id = o.emp_id         -- recursive step
  WHERE  NOT e.emp_id = ANY(o.path)               -- cycle guard
)
SELECT depth, chain FROM org ORDER BY path;
```

```text
 depth |       chain
-------+-------------------
     0 | Asha
     1 | Asha > Ben
     2 | Asha > Ben > Dev
     2 | Asha > Ben > Eli
     1 | Asha > Chen
     1 | Asha > Fay
     2 | Asha > Fay > Gus
     2 | Asha > Fay > Hana
     1 | Asha > Ivy
```

- **Follow-ups:** "What if the data has a cycle?" The path check stops it. Postgres 14+ also has a `CYCLE` clause. "Bottom-up instead?" Anchor on an employee and join on `o.manager_id = e.emp_id`.
- MySQL 8+ supports `WITH RECURSIVE`, but has no arrays. Build the path as a string with `CONCAT` and check it with `FIND_IN_SET`.

### B3. Pivot rows into columns

> **Approach:** "Conditional aggregation: one aggregate per output column, each filtered to its value."

```sql
SELECT a.account_type,
       SUM(t.amount) FILTER (WHERE date_trunc('month', t.created_at) = DATE '2026-01-01') AS jan,
       SUM(t.amount) FILTER (WHERE date_trunc('month', t.created_at) = DATE '2026-02-01') AS feb,
       SUM(t.amount) FILTER (WHERE date_trunc('month', t.created_at) = DATE '2026-03-01') AS mar
FROM   transactions t
JOIN   accounts a USING (account_id)
WHERE  t.status = 'APPROVED'
GROUP  BY a.account_type
ORDER  BY 1;
```

```text
 account_type |   jan   |  feb   |  mar
--------------+---------+--------+--------
 CHECKING     |  425.00 | 130.00 |
 CREDIT       | 1000.00 |  60.00 | 120.00
```

- `FILTER` is Postgres-only. The portable form is `SUM(CASE WHEN … THEN t.amount END)`, which works everywhere, including MySQL.
- An empty cell is NULL. Wrap it in `COALESCE(…, 0)` if the report needs zeros.
- Dynamic columns (an unknown list of months) need dynamic SQL. Say that, and suggest pivoting in the BI layer instead.

### B4. Percent of total

> **Approach:** "Aggregate, then divide by a window SUM over the aggregate."

```sql
SELECT merchant,
       SUM(amount) AS volume,
       ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 1) AS pct_of_total
FROM   transactions
WHERE  status = 'APPROVED'
GROUP  BY merchant
ORDER  BY volume DESC;
```

```text
 merchant | volume  | pct_of_total
----------+---------+--------------
 Airline  | 1000.00 |         57.6
 Grocer   |  440.00 |         25.4
 Cafe     |  150.00 |          8.6
 Fuel     |   85.00 |          4.9
 Hotel    |   60.00 |          3.5
```

`SUM(SUM(amount)) OVER ()` looks odd but is legal: the window runs *after* `GROUP BY`, over the grouped rows. For a share within a group, use `OVER (PARTITION BY region)`. Use `100.0`, not `100`, to avoid integer division.

### B5. Median and percentiles

```sql
SELECT account_id, COUNT(*) AS n,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount)                    AS median,
       ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY amount)::numeric, 2) AS p90,
       ROUND(AVG(amount), 2)                                                  AS mean
FROM   transactions
WHERE  status = 'APPROVED'
GROUP  BY account_id
ORDER  BY account_id;
```

```text
 account_id | n | median |  p90   |  mean
------------+---+--------+--------+--------
         10 | 7 |     40 | 125.00 |  63.57
         11 | 2 |    280 | 456.00 | 280.00
         20 | 3 |     10 |  74.00 |  36.67
         30 | 2 |    310 | 462.00 | 310.00
```

- `PERCENTILE_CONT` interpolates between values (the median of 10, 10, 90 is 10; of 60, 500 it's 280). `PERCENTILE_DISC` returns an actual value from the data.
- Account 10's mean (63.57) is well above its median (40) because one 200 purchase skews it. That's the reason to report p50/p90 for latency and amounts.
- **MySQL has no `PERCENTILE_CONT`.** Use `ROW_NUMBER` with `COUNT(*) OVER`, then pick the middle row or rows. SQL Server has it only as a window function (`… OVER (PARTITION BY …)`).

### B6. Fill missing days (date spine)

> **Approach:** "Generate every date, then LEFT JOIN the facts to it so empty days show as 0 instead of disappearing."

```sql
SELECT d::date AS day, COALESCE(SUM(t.amount), 0) AS volume
FROM   generate_series(DATE '2026-01-03', DATE '2026-01-07', INTERVAL '1 day') AS d
LEFT JOIN transactions t
       ON t.created_at >= d
      AND t.created_at <  d + INTERVAL '1 day'
      AND t.status = 'APPROVED'               -- filter in ON, not WHERE (see Part C)
GROUP  BY d
ORDER  BY d;
```

```text
    day     | volume
------------+--------
 2026-01-03 | 270.00
 2026-01-04 |  60.00
 2026-01-05 |  75.00
 2026-01-06 |  10.00
 2026-01-07 |      0
```

- This is a prerequisite for correct moving averages. Without it, a "7-row" window can cover 30 days.
- The half-open range (`>= d AND < d + 1 day`) still lets an index on `created_at` be used. `t.created_at::date = d` would prevent that.
- In MySQL, build the date list with a recursive CTE. Warehouses usually have a `dim_date` table.

### B7. Sessionization

*Group each account's activity into sessions. A new session starts after a gap of more than 30 minutes.*

> **Approach:** "Use `LAG` to flag each row that starts a new session, then take a running `SUM` of the flags to get a session number."

```sql
WITH flagged AS (
  SELECT account_id, txn_id, created_at,
         CASE WHEN created_at - LAG(created_at) OVER (PARTITION BY account_id
                                                      ORDER BY created_at, txn_id)
                   <= INTERVAL '30 minutes'
              THEN 0 ELSE 1 END AS new_session      -- first row: LAG is NULL → 1
  FROM   transactions
  WHERE  account_id = 10
)
SELECT account_id, txn_id, created_at,
       SUM(new_session) OVER (PARTITION BY account_id ORDER BY created_at, txn_id) AS session_id
FROM   flagged
ORDER  BY created_at, txn_id;
```

```text
 account_id | txn_id |     created_at      | session_id
------------+--------+---------------------+------------
         10 |    101 | 2026-01-03 09:00:00 |          1
         10 |    102 | 2026-01-03 09:20:00 |          1
         10 |    103 | 2026-01-03 11:00:00 |          2
         10 |    104 | 2026-01-04 08:00:00 |          3
         10 |    105 | 2026-01-04 08:00:00 |          3
         10 |    106 | 2026-01-05 18:00:00 |          4
         10 |    107 | 2026-02-02 09:00:00 |          5
```

This "flag, then cumulative sum" trick is the most reusable window pattern there is. It works for sessions, status changes and resets.

### B8. Streaks of the same status (gaps and islands)

*Find runs of 3 or more consecutive declines on the same account. That's a fraud signal.*

> **Approach:** "Take the difference of two `ROW_NUMBER`s: one over the whole account and one per status. Within an unbroken run of one status, both increase together, so the difference stays constant and labels the island."

```sql
WITH s AS (
  SELECT account_id, txn_id, status, created_at,
         ROW_NUMBER() OVER (PARTITION BY account_id         ORDER BY created_at, txn_id)
       - ROW_NUMBER() OVER (PARTITION BY account_id, status ORDER BY created_at, txn_id) AS grp
  FROM   transactions
)
SELECT account_id, MIN(created_at) AS streak_start, MAX(created_at) AS streak_end,
       COUNT(*) AS declines
FROM   s
WHERE  status = 'DECLINED'
GROUP  BY account_id, grp
HAVING COUNT(*) >= 3;
```

```text
 account_id |    streak_start     |     streak_end      | declines
------------+---------------------+---------------------+----------
         11 | 2026-02-10 10:00:00 | 2026-02-10 10:02:00 |        3
```

The first guide's [consecutive-days version](SQL_Data_Modeling_Interview_Prep.md#bonus-problems-commonly-asked) uses `date - ROW_NUMBER` instead. That works for dates; this version works for any categorical value.

### B9. Month-over-month retention

*Of the customers active in month M, how many were also active in M+1?*

```sql
WITH active AS (
  SELECT DISTINCT a.customer_id, date_trunc('month', t.created_at)::date AS month
  FROM   transactions t
  JOIN   accounts a USING (account_id)
  WHERE  t.status = 'APPROVED'
)
SELECT cur.month,
       COUNT(*)                                            AS active,
       COUNT(nxt.customer_id)                              AS retained_next_month,
       ROUND(100.0 * COUNT(nxt.customer_id) / COUNT(*), 1) AS retention_pct
FROM   active cur
LEFT JOIN active nxt
       ON nxt.customer_id = cur.customer_id
      AND nxt.month = (cur.month + INTERVAL '1 month')::date
GROUP  BY cur.month
ORDER  BY cur.month;
```

```text
   month    | active | retained_next_month | retention_pct
------------+--------+---------------------+---------------
 2026-01-01 |      3 |                   2 |          66.7
 2026-02-01 |      2 |                   0 |           0.0
 2026-03-01 |      1 |                   0 |           0.0
```

- `COUNT(nxt.customer_id)` counts only matches. `COUNT(*)` would count every row. That difference is the whole query.
- `DISTINCT` in the CTE matters: without it, a customer with 5 transactions in a month counts 5 times.
- Mar shows 0% only because April isn't in the data yet. Say that the last period is always incomplete.
- **Cohort version:** replace `cur.month` with each customer's *first* active month (`MIN(month) OVER (PARTITION BY customer_id)`) and pivot by months since signup.

### B10. Relational division ("has all of")

*Customers who hold every account type.*

> **Approach:** "Count the distinct types each customer has and compare that to the total number of types."

```sql
SELECT c.customer_id, c.name
FROM   customers c
JOIN   accounts a USING (customer_id)
GROUP  BY c.customer_id, c.name
HAVING COUNT(DISTINCT a.account_type) = (SELECT COUNT(DISTINCT account_type) FROM accounts);
```

```text
 customer_id | name
-------------+------
           1 | Ana
```

The double-`NOT EXISTS` form ("no type exists that this customer lacks") is the textbook alternative. Mention it. For "has *both* CHECKING and CREDIT" specifically, use `WHERE account_type IN (…) … HAVING COUNT(DISTINCT account_type) = 2`.

### B11. Most frequent value per group, with ties

*Each customer's favorite merchant.*

```sql
SELECT customer_id, merchant, txns
FROM (
  SELECT a.customer_id, t.merchant, COUNT(*) AS txns,
         RANK() OVER (PARTITION BY a.customer_id ORDER BY COUNT(*) DESC) AS rnk
  FROM   transactions t
  JOIN   accounts a USING (account_id)
  GROUP  BY a.customer_id, t.merchant
) x
WHERE  rnk = 1
ORDER  BY customer_id, merchant;
```

```text
 customer_id | merchant | txns
-------------+----------+------
           1 | Cafe     |    4
           1 | Hotel    |    4
           2 | Cafe     |    2
           3 | Airline  |    1
           3 | Grocer   |    1
```

- A window function over an aggregate (`ORDER BY COUNT(*)`) is legal, because windows run after `GROUP BY`.
- `RANK` keeps ties (customer 1 has two favorites). If they want exactly one, use `ROW_NUMBER` with a tie-breaker, and ask which tie-breaker. Postgres also has `mode() WITHIN GROUP (ORDER BY merchant)`, which silently picks one value.

### B12. Overlapping intervals

*Find pre-authorization holds on the same account whose time windows overlap.*

> **Approach:** "Two intervals overlap when each one starts before the other ends: `a.start < b.end AND b.start < a.end`."

```sql
SELECT a.hold_id AS hold_a, b.hold_id AS hold_b, a.account_id
FROM   card_holds a
JOIN   card_holds b
  ON   a.account_id = b.account_id
 AND   a.hold_id < b.hold_id                 -- each pair once, no self-match
 AND   a.starts_at < b.ends_at
 AND   b.starts_at < a.ends_at;
```

```text
 hold_a | hold_b | account_id
--------+--------+------------
      1 |      2 |         10
```

- Holds 2 (11:00–13:00) and 3 (13:00–14:00) only *touch*, so they don't overlap. Strict `<` treats intervals as half-open `[start, end)`, which is usually what you want.
- **Prevent overlaps instead of detecting them (Postgres):** an exclusion constraint.

  ```sql
  CREATE EXTENSION IF NOT EXISTS btree_gist;   -- needed for the "account_id WITH =" part
  CREATE TABLE holds_guarded (
    account_id BIGINT,
    during     TSRANGE,
    EXCLUDE USING gist (account_id WITH =, during WITH &&)
  );
  ```

  Verified with a single-column version (`EXCLUDE USING gist (during WITH &&)`): `[09:00,12:00)` followed by `[12:00,13:00)` is accepted, and `[11:00,13:00)` is rejected with *"conflicting key value violates exclusion constraint"*. That's the database-level answer to "how do you stop double-booking?"

### B13. FIRST_VALUE / LAST_VALUE and the frame trap

```sql
SELECT txn_id, created_at, amount,
       FIRST_VALUE(amount) OVER w AS first_amt,
       LAST_VALUE(amount)  OVER w AS last_amt_wrong,
       LAST_VALUE(amount)  OVER (w ROWS BETWEEN UNBOUNDED PRECEDING
                                           AND UNBOUNDED FOLLOWING) AS last_amt
FROM   transactions
WHERE  account_id = 20
WINDOW w AS (PARTITION BY account_id ORDER BY created_at)
ORDER  BY created_at;
```

```text
 txn_id |     created_at      | amount | first_amt | last_amt_wrong | last_amt
--------+---------------------+--------+-----------+----------------+----------
    201 | 2026-01-06 07:00:00 |  10.00 |     10.00 |          10.00 |    15.00
    202 | 2026-01-20 07:00:00 |  10.00 |     10.00 |          10.00 |    15.00
    203 | 2026-02-20 07:00:00 |  90.00 |     10.00 |          90.00 |    15.00
    204 | 2026-03-01 07:00:00 |  15.00 |     10.00 |          15.00 |    15.00
```

`LAST_VALUE` with the default frame stops at the current row, so it just returns the current row's value. Extend the frame to `UNBOUNDED FOLLOWING`. Simpler still: use `FIRST_VALUE` with `ORDER BY created_at DESC`. Same root cause as [A8](#a8-running-total-and-the-default-frame-bug).

### B14. Idempotent upsert for out-of-order events

*A Kafka consumer writes the latest balance per account. Events can be redelivered or arrive out of order.*

> **Approach:** "Upsert keyed on the account, and only overwrite when the incoming event is newer. A replay or a late event becomes a no-op."

```sql
-- Newer events: account 10 is updated, account 20 is inserted
INSERT INTO account_balance AS b (account_id, balance, as_of) VALUES
  (10, 450.00, '2026-02-02 09:00'),
  (20, 100.00, '2026-02-20 07:00')
ON CONFLICT (account_id) DO UPDATE
  SET   balance = EXCLUDED.balance, as_of = EXCLUDED.as_of
  WHERE EXCLUDED.as_of > b.as_of;              -- INSERT 0 2

-- A stale event for account 10 arrives late → ignored
INSERT INTO account_balance AS b (account_id, balance, as_of) VALUES
  (10, 999.00, '2026-01-20 00:00')
ON CONFLICT (account_id) DO UPDATE
  SET   balance = EXCLUDED.balance, as_of = EXCLUDED.as_of
  WHERE EXCLUDED.as_of > b.as_of;              -- INSERT 0 0

SELECT * FROM account_balance ORDER BY account_id;
```

```text
 account_id | balance |        as_of
------------+---------+---------------------
         10 |  450.00 | 2026-02-02 09:00:00
         20 |  100.00 | 2026-02-20 07:00:00
```

- The point to say out loud: *idempotency plus ordering, enforced in the database rather than trusted to the consumer.* The consumer-side half of the same problem is covered in [Transactions Q25](../System%20Design/Transactions_Interview_Prep.md#25-how-would-you-design-idempotency-for-a-transactional-consumer) and [Kafka](../System%20Design/Kafka_Interview_Prep.md).
- Timestamps can collide or skew between producers. A per-account **sequence number or version** from the source is stronger than `as_of`.
- MySQL: `INSERT … AS new ON DUPLICATE KEY UPDATE balance = IF(new.as_of > as_of, new.balance, balance), as_of = GREATEST(as_of, new.as_of)`. The row alias (`AS new`) replaces the `VALUES()` function, which is deprecated since MySQL 8.0.20. Watch the column order, because each assignment sees the values already updated earlier in the same clause. SQL Server: `MERGE`, or `UPDATE` then `INSERT` under the right locking.

---

## Part C — Traps Interviewers Probe

All results below are from the seed data.

| Trap | Demonstration | Result | Fix |
|---|---|---|---|
| **`COUNT(*)` vs `COUNT(col)`** | `SELECT COUNT(*), COUNT(email) FROM customers` | `6`, `4` | `COUNT(col)` skips NULLs. Choose on purpose. |
| **NULL never equals NULL** | `SELECT NULL = NULL` | `NULL` (not true) | `IS NULL`, `IS NOT DISTINCT FROM` (Postgres), `<=>` (MySQL) |
| **`NOT IN` with a NULL** | `WHERE country NOT IN ('UK', NULL)` | `0` rows | `NOT EXISTS`, or filter NULLs out of the subquery |
| **LEFT JOIN, filter in `WHERE`** | `LEFT JOIN accounts a … WHERE a.account_type = 'CREDIT'` | 2 customers | Move the filter into `ON`: 6 customers, 4 with `0` |
| **`BETWEEN` on timestamps** | `created_at BETWEEN '2026-01-03' AND '2026-01-04'` | `3` rows (misses Jan 4 after midnight) | Half-open: `>= '2026-01-03' AND < '2026-01-05'` → `5` |
| **`AVG` ignores NULLs** | `AVG(x)` over `10, 20, NULL` | `15` | `AVG(COALESCE(x, 0))` → `10`, if NULL means zero |
| **Integer division** | `SELECT 7/2` (Postgres, SQL Server) | `3` | `7/2.0` or a `CAST`. MySQL's `/` already returns `3.5`. |
| **Default window frame** | `SUM() OVER (ORDER BY ts)` with tied `ts` | Tied rows share a total | `ROWS BETWEEN …` plus a tie-breaker (see [A8](#a8-running-total-and-the-default-frame-bug)) |
| **Non-deterministic "latest"** | `ROW_NUMBER() OVER (ORDER BY created_at)` with ties | Arbitrary winner | Add a unique tie-breaker column |
| **Function on an indexed column** | `WHERE created_at::date = '2026-01-03'` | Index not used | Rewrite as a range, or create an expression index |

**The LEFT JOIN trap, in full** (the most common one):

```sql
-- ❌ The WHERE clause throws away the NULL rows the LEFT JOIN kept → it's now an INNER JOIN
SELECT c.customer_id, COUNT(a.account_id) AS credit_accts
FROM   customers c LEFT JOIN accounts a ON a.customer_id = c.customer_id
WHERE  a.account_type = 'CREDIT'
GROUP  BY c.customer_id ORDER BY 1;          -- 2 rows: customers 1 and 3

-- ✅ Filter the right-hand table in ON
SELECT c.customer_id, COUNT(a.account_id) AS credit_accts
FROM   customers c LEFT JOIN accounts a
       ON a.customer_id = c.customer_id AND a.account_type = 'CREDIT'
GROUP  BY c.customer_id ORDER BY 1;          -- 6 rows: 1→1, 3→1, everyone else→0
```

---

## Part D — Dialect Differences

The Postgres and MySQL columns were checked on PostgreSQL 16.2 and MySQL 9.3. The SQL Server column is reference syntax that was not executed. For Oracle (`ROWNUM`, `FETCH FIRST`, `KEEP`, `LISTAGG`, `MERGE`), see [Oracle Window Functions](Oracle_Window_Functions_Interview_Prep.md).

| Need | PostgreSQL | MySQL 8+ | SQL Server |
|---|---|---|---|
| First N rows | `LIMIT n` | `LIMIT n` | `TOP (n)` / `OFFSET … FETCH` |
| Latest row per group | `DISTINCT ON`, or `ROW_NUMBER` | `ROW_NUMBER` only | `ROW_NUMBER`, or `TOP 1 WITH TIES` |
| Conditional aggregate | `FILTER (WHERE …)` or `CASE` | `CASE` only (`FILTER` is a syntax error) | `CASE` only |
| Median | `PERCENTILE_CONT … WITHIN GROUP` | Not available, use `ROW_NUMBER` math | `PERCENTILE_CONT … OVER ()` |
| Date series | `generate_series` | Recursive CTE | Recursive CTE / `GENERATE_SERIES` (2022+) |
| Upsert | `ON CONFLICT … DO UPDATE` | `ON DUPLICATE KEY UPDATE` | `MERGE` |
| Delete duplicates | `DELETE … USING` | `DELETE u FROM u JOIN …`, or a CTE/derived table (avoid error 1093) | `DELETE FROM cte WHERE rn > 1` |
| NULL-safe equality | `IS NOT DISTINCT FROM` | `<=>` | `IS NOT DISTINCT FROM` (2022+) |
| String aggregation | `string_agg(x, ',')` | `GROUP_CONCAT(x)` | `STRING_AGG(x, ',')` |
| Truncate to month | `date_trunc('month', ts)` | `DATE_FORMAT(ts, '%Y-%m-01')` | `DATETRUNC(month, ts)` (2022+) |
| Return changed rows | `RETURNING` | Not available | `OUTPUT` |
| Case sensitivity of `=` | Case-sensitive | Case-insensitive by default collation | Depends on collation (default insensitive) |

---

## Part E — Pattern Picker

| If the question says… | Reach for |
|---|---|
| "top N per", "latest per", "first per" | `ROW_NUMBER` / `DENSE_RANK` in a subquery ([A2](#a2-top-3-salaries-per-department), [A5](#a5-latest-row-per-group)) |
| "never", "without any", "missing" | `NOT EXISTS` anti-join ([A4](#a4-customers-with-no-accounts-anti-join)) |
| "running", "cumulative", "moving" | `SUM/AVG OVER (… ROWS BETWEEN …)` ([A8](#a8-running-total-and-the-default-frame-bug)) |
| "compared to previous", "change since" | `LAG` / `LEAD` |
| "consecutive", "streak", "in a row" | Gaps and islands ([B8](#b8-streaks-of-the-same-status-gaps-and-islands)) |
| "session", "gap of more than" | `LAG` flag + cumulative `SUM` ([B7](#b7-sessionization)) |
| "hierarchy", "reports to", "chain" | Recursive CTE ([B2](#b2-org-chart-with-depth-recursive-cte)) |
| "share of", "% of total" | `x / SUM(x) OVER ()` ([B4](#b4-percent-of-total)) |
| "as columns", "per month side by side" | Conditional aggregation ([B3](#b3-pivot-rows-into-columns)) |
| "every day, even with no data" | Date spine + `LEFT JOIN` ([B6](#b6-fill-missing-days-date-spine)) |
| "has all of" | `HAVING COUNT(DISTINCT …) = (…)` ([B10](#b10-relational-division-has-all-of)) |
| "overlap", "double-booked" | `a.start < b.end AND b.start < a.end` ([B12](#b12-overlapping-intervals)) |
| "retained", "came back" | Self-`LEFT JOIN` on period + 1 ([B9](#b9-month-over-month-retention)) |
| "duplicate events", "replayed", "out of order" | Upsert with a version/timestamp guard ([B14](#b14-idempotent-upsert-for-out-of-order-events)) |

---

## Sources

- PostgreSQL 16 documentation: [Window Functions](https://www.postgresql.org/docs/16/functions-window.html) and [window-call syntax and frames](https://www.postgresql.org/docs/16/sql-expressions.html#SYNTAX-WINDOW-FUNCTIONS) (default `RANGE … CURRENT ROW` frame, peers), [Aggregate Functions](https://www.postgresql.org/docs/16/functions-aggregate.html) (`FILTER`, `PERCENTILE_CONT`/`PERCENTILE_DISC`, `mode()`), [`WITH RECURSIVE` and the `CYCLE` clause](https://www.postgresql.org/docs/16/queries-with.html), [`generate_series`](https://www.postgresql.org/docs/16/functions-srf.html), [`INSERT … ON CONFLICT`](https://www.postgresql.org/docs/16/sql-insert.html), [`DELETE … USING`](https://www.postgresql.org/docs/16/sql-delete.html), [Exclusion constraints](https://www.postgresql.org/docs/16/ddl-constraints.html#DDL-CONSTRAINTS-EXCLUSION), [`btree_gist`](https://www.postgresql.org/docs/16/btree-gist.html)
- MySQL 8.0 Reference Manual: [`INSERT … ON DUPLICATE KEY UPDATE` (row alias; `VALUES()` deprecation)](https://dev.mysql.com/doc/refman/8.0/en/insert-on-duplicate.html), [`DELETE` restrictions (error 1093)](https://dev.mysql.com/doc/refman/8.0/en/delete.html), [Recursive CTEs](https://dev.mysql.com/doc/refman/8.0/en/with.html), [Character set and collation defaults (`utf8mb4_0900_ai_ci`)](https://dev.mysql.com/doc/refman/8.0/en/charset-server.html)
- Microsoft SQL Server documentation: [`PERCENTILE_CONT`](https://learn.microsoft.com/en-us/sql/t-sql/functions/percentile-cont-transact-sql), [`GENERATE_SERIES`](https://learn.microsoft.com/en-us/sql/t-sql/functions/generate-series-transact-sql), [`IS [NOT] DISTINCT FROM`](https://learn.microsoft.com/en-us/sql/t-sql/queries/is-distinct-from-transact-sql), [`DATETRUNC`](https://learn.microsoft.com/en-us/sql/t-sql/functions/datetrunc-transact-sql)
