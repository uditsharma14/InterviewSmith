# SQL & Data Modeling — Interview Prep (Intermediate → Staff, with Code & Sources)

> **Target level:** Intermediate → Staff · **Baseline:** PostgreSQL 16 as the reference RDBMS for all SQL unless noted; MySQL 8+/InnoDB and SQL Server differences called out where they matter; Kimball dimensional-modeling terminology for Parts A (§3–§5) and C · **Last verified:** 2026-10-03 · **Prerequisites:** basic SQL (`SELECT`/`JOIN`/`GROUP BY`)

SQL and data-modeling rounds test whether you can design a clean data model and explain *why*, more than whether you remember unusual syntax.

**How to use this guide.** Each topic starts with a **20-second answer** to say first (answer-first), then the **details** for follow-ups, an **example**, and **likely follow-ups**. Differences in MySQL or SQL Server are called out where they matter. For hands-on query drills with real outputs, continue with [SQL Query Practice](SQL_Query_Practice_Interview_Prep.md); for Oracle's analytic functions, see [Oracle Window Functions](Oracle_Window_Functions_Interview_Prep.md). Transactions, isolation and locking get deeper, Spring-aware coverage in [Transactions](../System%20Design/Transactions_Interview_Prep.md).

---

## Contents

**[Part A — 15 must-know concepts](#part-a--15-must-know-concepts)**
- Data modeling: [1. Normalization vs denormalization](#1-normalization-vs-denormalization) · [2. 3NF](#2-third-normal-form-3nf) · [3. Star vs snowflake](#3-star-vs-snowflake-schema) · [4. Fact vs dimension](#4-fact-vs-dimension-tables) · [5. SCD Type 1 vs 2](#5-scd-type-1-vs-type-2)
- Querying and performance: [6. INNER vs LEFT JOIN](#6-inner-vs-left-join) · [7. Indexing](#7-indexing) · [8. Composite indexes](#8-composite-indexes) · [9. Query optimization](#9-sql-query-optimization) · [10. Execution plans](#10-execution-plans)
- Transactions and scale: [11. ACID](#11-transactions-and-acid) · [12. Isolation levels](#12-isolation-levels) · [13. Optimistic vs pessimistic locking](#13-optimistic-vs-pessimistic-locking) · [14. Partitioning vs sharding](#14-partitioning-vs-sharding) · [15. SQL vs NoSQL](#15-sql-vs-nosql)

**[Part B — Practice problems](#part-b--practice-problems)** (with solutions)

**[Part C — Data modeling walkthrough](#part-c--data-modeling-walkthrough)**

**[Part D — One-page cheat sheet](#part-d--one-page-cheat-sheet)**

**[Sources](#sources)**

---

## Sample schema used throughout

```sql
CREATE TABLE customers (
  customer_id   BIGINT PRIMARY KEY,
  name          TEXT NOT NULL,
  email         TEXT UNIQUE,
  country       TEXT,
  created_at    TIMESTAMP NOT NULL
);

CREATE TABLE accounts (
  account_id    BIGINT PRIMARY KEY,
  customer_id   BIGINT NOT NULL REFERENCES customers(customer_id),
  account_type  TEXT NOT NULL,          -- 'CHECKING', 'CREDIT'
  opened_at     TIMESTAMP NOT NULL
);

CREATE TABLE transactions (
  txn_id        BIGINT PRIMARY KEY,
  account_id    BIGINT NOT NULL REFERENCES accounts(account_id),
  amount        NUMERIC(12,2) NOT NULL,
  status        TEXT NOT NULL,          -- 'APPROVED', 'DECLINED'
  merchant      TEXT,
  created_at    TIMESTAMP NOT NULL
);
```

---

## Part A — 15 Must-Know Concepts

## 1. Normalization vs denormalization

**20-second answer:**
> "Normalization splits data so each fact is stored once. That keeps writes consistent and prevents update anomalies. Denormalization deliberately duplicates data to make reads faster by avoiding joins. I normalize transactional (OLTP) systems by default and denormalize for read-heavy analytics or hot query paths, but only where I can keep the copies in sync."

**Details**

| | Normalized | Denormalized |
|---|---|---|
| Goal | Integrity, no redundancy | Read speed, fewer joins |
| Writes | Cheap, one place to update | Expensive, must update every copy |
| Reads | More joins | Fewer joins, faster |
| Risk | Slow complex reads | Copies drift out of sync |
| Typical use | OLTP: payments, orders, user accounts | OLAP/warehouse, reporting, caches, search indexes |

**The three anomalies normalization prevents:**
- **Update anomaly:** a customer's email is stored on every order. You change it in one row and miss the others.
- **Insert anomaly:** you can't record a new product until someone orders it.
- **Delete anomaly:** deleting the last order for a product also deletes everything you knew about that product.

**Example.** `transactions(txn_id, account_id, customer_name, customer_email, …)` is denormalized. If a customer changes their email, you have to update millions of rows. Normalized, the name and email live in `customers`, and transactions reach them through `account_id → customer_id`.

**Ways to denormalize safely:**
- **Materialized views** (`REFRESH MATERIALIZED VIEW CONCURRENTLY`)
- **Summary tables** maintained by triggers or batch jobs
- **CDC into a read model** such as Elasticsearch or a warehouse
- **Copying immutable facts.** Storing the `merchant_name` *at the time of the transaction* is correct, not redundant, because it's a historical fact.

**Likely follow-ups**
- *"When did you denormalize in practice?"* Typical shapes: a read model for a status screen, a reporting table, or a search index fed from the OLTP database.

  > Personal example to add: describe a real case where you denormalized, including what was duplicated, how the copy was kept in sync, and what it cost.
- *"How do you keep denormalized data consistent?"* A single writer, CDC/outbox events, reconciliation jobs, and accepting eventual consistency with a known lag.

---

## 2. Third Normal Form (3NF)

**20-second answer:**
> "3NF means every non-key column depends on the key, the whole key, and nothing but the key. 1NF removes repeating groups, 2NF removes dependencies on part of a composite key, and 3NF removes dependencies between non-key columns. In practice, if a column describes something other than the row's entity, it belongs in its own table."

**The normal forms, step by step**

| Form | Rule | Violation example | Fix |
|---|---|---|---|
| **1NF** | Atomic values, no repeating groups | `phones = '555-1234, 555-9876'` | Separate `customer_phones` table |
| **2NF** | 1NF + no **partial** dependency on a composite key | `order_items(order_id, product_id, qty, product_name)`: `product_name` depends only on `product_id` | Move `product_name` to `products` |
| **3NF** | 2NF + no **transitive** dependency (non-key → non-key) | `accounts(account_id, branch_id, branch_city)`: `branch_city` depends on `branch_id`, not `account_id` | Move `branch_city` to `branches` |
| **BCNF** | Every determinant is a candidate key (a stricter 3NF) | Rare edge cases with overlapping candidate keys | Decompose further |

**Worked decomposition**

Before (violates 2NF and 3NF):

```text
order_lines(order_id, product_id, customer_id, customer_city, product_name, qty, unit_price)
PK = (order_id, product_id)
```

- `product_name` depends only on `product_id`, which is part of the key (2NF violation).
- `customer_id` depends only on `order_id` (2NF violation).
- `customer_city` depends on `customer_id`, a non-key column (3NF violation).

After (3NF):

```text
customers(customer_id PK, customer_city)
products(product_id PK, product_name)
orders(order_id PK, customer_id FK)
order_lines(order_id FK, product_id FK, qty, unit_price,  PK(order_id, product_id))
```

`unit_price` stays on `order_lines` on purpose. It's the price *at the time of sale*, which is a historical fact and not a copy of `products.price`.

**Likely follow-ups**
- *"Is 3NF always the goal?"* For OLTP it's the default. Analytics uses star schemas, which are deliberately denormalized.
- *"What is a functional dependency?"* A → B means knowing A determines B exactly. For example, `customer_id → email`.

---

## 3. Star vs snowflake schema

**20-second answer:**
> "Both are warehouse designs with a central fact table surrounded by dimensions. In a star schema the dimensions are flat and denormalized, so queries need one join per dimension. That's simpler and faster for BI. A snowflake schema normalizes the dimensions into sub-tables. It saves a little storage but adds joins. I default to star, and snowflake only when a dimension is huge or shared hierarchies need one place to be maintained."

**Diagram**

```text
STAR                                     SNOWFLAKE
            dim_date                                 dim_date
               │                                        │
dim_customer ─ fact_txn ─ dim_merchant    dim_customer ─ fact_txn ─ dim_merchant
               │                              │                       │
           dim_card                       dim_country           dim_mcc_category
                                                                      │
                                                                dim_mcc_group
```

| | Star | Snowflake |
|---|---|---|
| Dimensions | Flat (denormalized) | Normalized into sub-dimensions |
| Joins per query | Fewer | More |
| Query simplicity | High, BI-tool friendly | Lower |
| Storage | Slightly more | Slightly less (rarely matters today) |
| Maintenance of hierarchies | Values repeated in rows | One place per level |
| Default choice | Yes | When a dimension is very large or a hierarchy is reused |

**Example.** `dim_merchant` in a star schema holds `merchant_name, mcc_code, mcc_description, mcc_group, city, country` in one row. In a snowflake schema, `mcc_code` → `dim_mcc` → `dim_mcc_group`.

**Likely follow-ups**
- *"Why does star perform well on columnar warehouses (Redshift, Snowflake, BigQuery)?"* Columnar compression handles the repeated dimension values, and fewer joins means simpler plans.
- *"What's a conformed dimension?"* One dimension, such as `dim_date` or `dim_customer`, shared by several fact tables, so reports from different facts agree.

---

## 4. Fact vs dimension tables

**20-second answer:**
> "A fact table records measurable events at a fixed grain, such as one row per transaction, holding numbers like amount and foreign keys to dimensions. Dimension tables hold the descriptive context you filter and group by: who, what, where, when. The most important design decision is the grain. You declare it first, and every fact in the table must match it."

**Details**

| | Fact | Dimension |
|---|---|---|
| Contains | Measures + FKs | Descriptive attributes |
| Example columns | `amount`, `fee`, `quantity` | `customer_name`, `segment`, `country` |
| Size | Very tall (billions of rows) | Short and wide |
| Changes | Append-mostly | Slowly changing (see SCD) |
| Key | Composite of dimension FKs or a surrogate key | **Surrogate key** (`customer_sk`) + natural/business key |

**Types of measures:**
- **Additive:** sums across every dimension (`amount`).
- **Semi-additive:** sums across some dimensions but not time (`account_balance`, where you'd average or take the last value).
- **Non-additive:** can't be summed (`ratio`, `percentage`). Store the numerator and denominator instead.

**Types of fact tables:**
- **Transaction:** one row per event (each card swipe).
- **Periodic snapshot:** one row per entity per period (daily account balance).
- **Accumulating snapshot:** one row per process instance, updated as milestones happen (a loan application from submitted → approved → funded).
- **Factless:** events with no measure (student attended class, or a document was viewed).

**Example**

```sql
CREATE TABLE fact_transaction (
  txn_id        BIGINT,
  date_sk       INT    REFERENCES dim_date(date_sk),
  customer_sk   BIGINT REFERENCES dim_customer(customer_sk),
  merchant_sk   BIGINT REFERENCES dim_merchant(merchant_sk),
  amount        NUMERIC(12,2),
  fee           NUMERIC(12,2)
);
-- Grain: one row per authorized card transaction.
```

**Likely follow-ups**
- *"Why surrogate keys instead of natural keys?"* They insulate the warehouse from changes to source keys, make SCD Type 2 possible (several versions of one customer), and make joins faster on integers.
- *"What if you get the grain wrong?"* Double counting. For example, mixing order-level shipping fees into a line-item fact inflates totals when you sum.

---

## 5. SCD Type 1 vs Type 2

**20-second answer:**
> "Slowly changing dimensions decide what happens when an attribute changes. Type 1 overwrites the old value, so there's no history. It's right for corrections like a typo. Type 2 adds a new row with effective dates and a current flag, so history is kept and old facts still join to the version that was true at the time. I use Type 2 for anything that drives reporting over time, like a customer's segment or address."

**Details**

| Type | What happens | History | Use for |
|---|---|---|---|
| **0** | Never changes | N/A | Date of birth, original signup date |
| **1** | Overwrite | None | Typo fixes, attributes nobody analyzes historically |
| **2** | New row + `valid_from` / `valid_to` / `is_current` | Full | Customer tier, address, risk segment |
| **3** | Extra column (`previous_value`) | One level | "Before/after reorg" comparisons |
| **4** | Current table + separate history table | Full, kept separately | Fast-changing attributes |
| **6** | 1 + 2 + 3 combined | Full + current value on every row | "As of then" and "as of now" reporting together |

**Type 2 table**

```sql
CREATE TABLE dim_customer (
  customer_sk   BIGSERIAL PRIMARY KEY,   -- surrogate key, one per version
  customer_id   BIGINT NOT NULL,         -- natural/business key
  name          TEXT,
  tier          TEXT,                    -- tracked attribute
  valid_from    TIMESTAMP NOT NULL,
  valid_to      TIMESTAMP NOT NULL DEFAULT '9999-12-31',
  is_current    BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX ux_dim_customer_current
  ON dim_customer(customer_id) WHERE is_current;   -- at most one current row
```

**Type 2 load from a staging table**

```sql
BEGIN;

-- 1. Close out current rows whose tracked attribute changed
UPDATE dim_customer d
SET    valid_to = now(), is_current = FALSE
FROM   stg_customer s
WHERE  d.customer_id = s.customer_id
  AND  d.is_current
  AND  d.tier IS DISTINCT FROM s.tier;

-- 2. Insert new versions (changed customers + brand-new customers)
INSERT INTO dim_customer (customer_id, name, tier, valid_from)
SELECT s.customer_id, s.name, s.tier, now()
FROM   stg_customer s
LEFT JOIN dim_customer d
       ON d.customer_id = s.customer_id AND d.is_current
WHERE  d.customer_id IS NULL;          -- no current row → new, or just closed above

COMMIT;
```

**Point-in-time join** (which tier was the customer in when they transacted?)

```sql
SELECT t.txn_id, d.tier
FROM   transactions t
JOIN   accounts a      ON a.account_id = t.account_id
JOIN   dim_customer d  ON d.customer_id = a.customer_id
                      AND t.created_at >= d.valid_from
                      AND t.created_at <  d.valid_to;
```

In a real warehouse, the fact row stores the `customer_sk` that was current at load time, so this join becomes a plain key lookup.

**Likely follow-ups**
- *"Type 1 and Type 2 in the same dimension?"* Yes. Overwrite the name (Type 1) but version the tier (Type 2). That's a hybrid.
- *"Why `IS DISTINCT FROM`?"* Because `NULL <> 'GOLD'` is NULL, not true, so a change from or to NULL would be missed.
- *"Why half-open ranges `[valid_from, valid_to)`?"* So no timestamp matches two versions.

---

## 6. INNER vs LEFT JOIN

**20-second answer:**
> "An INNER JOIN returns only rows that match on both sides. A LEFT JOIN returns every row from the left table, with NULLs where the right side has no match. The classic trap is filtering the right table in the WHERE clause, which silently turns a LEFT JOIN back into an INNER JOIN. That filter belongs in the ON clause."

**Details**

```sql
-- All customers, with account count (0 for customers without accounts)
SELECT c.customer_id, COUNT(a.account_id) AS accounts
FROM   customers c
LEFT JOIN accounts a ON a.customer_id = c.customer_id
GROUP BY c.customer_id;
```

Use `COUNT(a.account_id)`, not `COUNT(*)`. `COUNT(*)` counts the NULL-padded row as 1.

**The WHERE vs ON trap**

```sql
-- ❌ Becomes an INNER JOIN: customers with no CREDIT account disappear
SELECT c.name, a.account_id
FROM   customers c
LEFT JOIN accounts a ON a.customer_id = c.customer_id
WHERE  a.account_type = 'CREDIT';

-- ✅ Keeps every customer; account_id is NULL if they have no CREDIT account
SELECT c.name, a.account_id
FROM   customers c
LEFT JOIN accounts a ON a.customer_id = c.customer_id
                    AND a.account_type = 'CREDIT';
```

**Other joins to know**

| Join | Returns |
|---|---|
| `RIGHT JOIN` | Mirror of LEFT. Rarely used, rewrite as LEFT. |
| `FULL OUTER JOIN` | All rows from both sides. Useful for reconciliation (rows in A only, B only, or both). |
| `CROSS JOIN` | Cartesian product. Use it to generate grids, such as every date × every merchant. |
| **Self join** | A table joined to itself (employee → manager, case → cited case). |
| **Semi join** (`EXISTS`) | Left rows that have a match, without duplicating them. |
| **Anti join** (`NOT EXISTS`) | Left rows with no match (see Part B, problem 8). |

**Row multiplication.** Joining one customer to 3 accounts and 10 transactions per account produces 30 rows. Summing a customer-level column across that join overcounts. Aggregate in a subquery first, then join.

**Reconciliation with FULL OUTER JOIN** (the standard check when migrating data from a legacy system to a new one):

```sql
SELECT COALESCE(l.token_id, m.token_id) AS token_id,
       CASE WHEN l.token_id IS NULL THEN 'MISSING_IN_LEGACY'
            WHEN m.token_id IS NULL THEN 'MISSING_IN_MODERN'
            ELSE 'STATUS_MISMATCH' END AS issue
FROM   legacy_tokens l
FULL OUTER JOIN modern_tokens m ON m.token_id = l.token_id
WHERE  l.token_id IS NULL OR m.token_id IS NULL OR l.status <> m.status;
```

---

## 7. Indexing

**20-second answer:**
> "An index is a separate sorted structure, usually a B-tree, that lets the database find rows without scanning the whole table. It speeds up reads on filtered, joined and sorted columns, but every index slows writes and takes storage. So I index for the actual query patterns, check that the plan uses the index, and drop unused ones."

**Index types**

| Type | Good for | Notes |
|---|---|---|
| **B-tree** (default) | `=`, `<`, `>`, `BETWEEN`, `ORDER BY`, prefix `LIKE 'abc%'` | Works for 95% of cases |
| **Hash** | Equality only | Rarely better than B-tree in Postgres |
| **GIN** | Full-text search, JSONB, arrays | Inverted index. Relevant to document search. |
| **GiST / BRIN** | Geospatial / very large append-only tables ordered by time | BRIN is tiny and great for time-series data |
| **Unique** | Enforcing uniqueness | Also used for lookups |
| **Partial** | A subset: `WHERE status = 'PENDING'` | Small and fast for hot subsets |
| **Expression** | `LOWER(email)` | Needed when the query applies a function to the column |

**Clustered vs non-clustered**
- **Clustered:** the table rows are physically stored in index order, so there's at most one per table. MySQL InnoDB always clusters on the primary key. SQL Server makes the primary key the clustered index by default, but you can cluster on a different key or leave the table as a heap.
- **Non-clustered / secondary:** a separate structure pointing to the rows. Postgres tables are heaps, so every index is secondary (`CLUSTER` is only a one-time reorder).
- **Covering index:** contains every column the query needs, so the table isn't touched at all (an index-only scan).

**When an index is NOT used**
- A function is applied to the column: `WHERE DATE(created_at) = '2026-10-01'`. Rewrite it as a range: `created_at >= '2026-10-01' AND created_at < '2026-10-02'`.
- A leading wildcard: `LIKE '%smith'`. Use a trigram (`pg_trgm`) or full-text index instead.
- An implicit type cast: comparing a `VARCHAR` column to a number.
- Low selectivity: `WHERE status = 'APPROVED'` when 95% of rows are approved. A full scan is cheaper, and the optimizer is right to choose it.
- `OR` across different columns (sometimes fixed with `UNION ALL` or a bitmap OR).
- Stale statistics. Run `ANALYZE`.

**Costs of indexes**
- Every `INSERT`, `UPDATE` and `DELETE` must also update each index (write amplification).
- Storage and memory pressure.
- Find unused indexes in Postgres with `pg_stat_user_indexes` where `idx_scan = 0`.

```sql
CREATE INDEX idx_txn_account_created ON transactions(account_id, created_at);
CREATE INDEX idx_customers_email_lower ON customers (LOWER(email));
CREATE INDEX idx_txn_pending ON transactions(created_at) WHERE status = 'PENDING';
CREATE INDEX CONCURRENTLY idx_txn_merchant ON transactions(merchant); -- no write lock
```

**Likely follow-ups**
- *"How do you add an index to a huge production table?"* In Postgres, `CREATE INDEX CONCURRENTLY` (slower, but no table lock). In MySQL, online DDL or gh-ost/pt-osc. Do it off-peak and monitor replication lag.
- *"How many indexes are too many?"* There's no fixed number. Let the write rate and the actual query patterns decide.

---

## 8. Composite indexes

**20-second answer:**
> "A composite index covers several columns, sorted by the first column, then the second, and so on, like a phone book sorted by last name then first name. It only helps queries that filter on a **leftmost prefix** of those columns. For column order, I put equality filters first and range or sort columns last."

**Leftmost-prefix rule** for `INDEX (account_id, status, created_at)`:

| Query filter | Uses index? |
|---|---|
| `account_id = ?` | ✅ |
| `account_id = ? AND status = ?` | ✅ |
| `account_id = ? AND status = ? AND created_at > ?` | ✅ fully |
| `account_id = ? AND created_at > ?` | ⚠️ partly: seeks on `account_id`, then filters `created_at` within it |
| `status = ?` | ❌ (mostly; some engines can skip-scan) |
| `created_at > ?` | ❌ |

**Ordering rules**
1. **Equality columns first**, then **range or `ORDER BY`** columns.
   - Query: `WHERE account_id = ? AND created_at > ? ORDER BY created_at` → `INDEX(account_id, created_at)`. This seeks to the account, then reads already sorted by date, with no sort step.
   - Reversing it, `(created_at, account_id)`, scans the whole date range across all accounts.
2. After a range column, later columns can't be used for seeking.
3. Among equality columns, order by which **combinations of queries** you need to serve. Selectivity is a weaker tie-breaker than people think.

**Covering with INCLUDE** (Postgres 11+, SQL Server):

```sql
-- "Latest 20 transactions for an account" served entirely from the index
CREATE INDEX idx_txn_acct_time
  ON transactions (account_id, created_at DESC)
  INCLUDE (amount, status);

SELECT created_at, amount, status
FROM   transactions
WHERE  account_id = 42
ORDER  BY created_at DESC
LIMIT  20;
```

**Likely follow-ups**
- *"Do you need an index on `(a)` if you have `(a, b)`?"* Usually not, because `(a, b)` serves `a` queries. You'd keep `(a)` only if the composite is much wider and `a` lookups are very hot.
- *"Index on `(a, b)` and the query is `WHERE b = ? AND a = ?`?"* That's fine. The order of the WHERE clause doesn't matter, only which columns are filtered.

---

## 9. SQL query optimization

**20-second answer:**
> "I start from the execution plan, not guesses. I look for full scans on large tables, row estimates that are far off, and expensive sorts or joins. Then I fix them in order: make the filters able to use an index, add the right composite index, return fewer rows and columns, rewrite inefficient patterns, and only then consider bigger changes like partitioning, caching or denormalization."

**Checklist, roughly in order**

1. **Measure.** `EXPLAIN (ANALYZE, BUFFERS)`, slow query log, `pg_stat_statements` to find the queries that cost the most *in total* (frequency × time).
2. **Make filters index-friendly.** Don't wrap indexed columns in functions, avoid leading wildcards, and match types.
3. **Index for the access pattern.** Use composite indexes (equality → range), covering indexes, and partial indexes.
4. **Fetch less.**
   - Use explicit columns, not `SELECT *`. `SELECT *` defeats index-only scans and moves more data.
   - Paginate with **keyset pagination** instead of a large `OFFSET`:

     ```sql
     -- ❌ OFFSET 100000 reads and throws away 100k rows
     -- ✅ keyset: seek straight to the next page
     SELECT * FROM transactions
     WHERE  account_id = 42 AND (created_at, txn_id) < (:last_created, :last_id)
     ORDER  BY created_at DESC, txn_id DESC
     LIMIT  50;
     ```

5. **Rewrite inefficient patterns.**
   - Correlated subqueries that run once per row → a JOIN or window function.
   - `NOT IN (subquery)` → `NOT EXISTS`. NULL-safe, and often a better plan.
   - `OR` on different columns → `UNION ALL` of two indexed queries.
   - `DISTINCT` used to hide join duplication → fix the join, or use `EXISTS`.
   - Aggregate **before** joining, to avoid row multiplication.
6. **Keep statistics fresh.** `ANALYZE`, autovacuum tuning, and extended statistics for correlated columns.
7. **Batch.** Avoid N+1 query patterns from the ORM. Use bulk `INSERT`/`COPY`, and batched updates on large tables.
8. **Bigger changes:** partitioning (pruning), materialized views or summary tables, read replicas, caching (Redis), and denormalization.

**Example rewrite**

```sql
-- ❌ Correlated subquery: runs once per customer
SELECT c.customer_id,
       (SELECT MAX(t.created_at)
        FROM   accounts a JOIN transactions t ON t.account_id = a.account_id
        WHERE  a.customer_id = c.customer_id) AS last_txn
FROM customers c;

-- ✅ One pass with aggregation
SELECT a.customer_id, MAX(t.created_at) AS last_txn
FROM   accounts a
JOIN   transactions t ON t.account_id = a.account_id
GROUP  BY a.customer_id;
```

Modern optimizers sometimes rewrite the first form automatically, but don't rely on that. Check the plan.

**Likely follow-ups**
- *"A query was fast yesterday and slow today. Why?"* Stale statistics, data growth crossing a plan threshold, parameter sniffing (SQL Server) or a generic plan (Postgres prepared statements), lock contention, table bloat, or a dropped or invalid index.

---

## 10. Execution plans

**20-second answer:**
> "The execution plan shows how the database will run the query: which access path, which join algorithm, in what order, and with how many estimated rows. I use `EXPLAIN ANALYZE` to compare estimated rows with actual rows. A large mismatch usually means stale statistics or a non-sargable filter, and that's typically the root cause of a bad plan."

**How to read one**

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT t.*
FROM   transactions t
WHERE  t.account_id = 42 AND t.created_at >= now() - interval '30 days';
```

Illustrative output (representative numbers on a large table with `idx_txn_account_created` from §7, not a captured run; on a tiny table the planner will correctly pick a Seq Scan instead):

```text
Index Scan using idx_txn_account_created on transactions t
   (cost=0.43..85.12 rows=80 width=64) (actual time=0.03..0.41 rows=75 loops=1)
   Index Cond: ((account_id = 42) AND (created_at >= (now() - '30 days'::interval)))
   Buffers: shared hit=12
Planning Time: 0.2 ms
Execution Time: 0.5 ms
```

- **Read inside-out, bottom-up:** the innermost or most-indented nodes run first.
- `cost=startup..total` is in arbitrary planner units. Use it to compare plans, not as milliseconds.
- `rows` estimated vs `actual rows`: **the most important comparison.** A difference of 10× or more points to the problem.
- `loops`: multiply per-loop numbers by loops for the total.
- `Buffers: shared hit` means pages came from cache. `read` means they came from disk.

**Access methods**

| Node | Meaning | Good or bad? |
|---|---|---|
| Seq Scan | Reads the whole table | Fine for small tables or low selectivity. Bad on a large table with a selective filter. |
| Index Scan | Seeks in the index, then fetches rows | Good for selective filters |
| Index Only Scan | Answered entirely from the index | Best (needs a covering index and a fresh visibility map) |
| Bitmap Index/Heap Scan | Collects matching row locations, then reads pages in order | Good for medium selectivity and combining indexes |

**Join algorithms**

| Join | Best when | Watch out for |
|---|---|---|
| **Nested Loop** | Small outer side + indexed inner side | Terrible if the outer estimate is wrong and it's actually huge |
| **Hash Join** | Large unsorted inputs, equality joins | Memory: spills to disk if the hash exceeds `work_mem` |
| **Merge Join** | Both inputs already sorted on the join key | Cost of sorting if they aren't |

**Red flags**
- A Seq Scan on a large table with a selective WHERE clause → missing or unusable index.
- Estimated rows = 1, actual rows = 500,000 → stale or missing statistics → wrong join type.
- `Sort Method: external merge Disk` → the sort spilled to disk. Add an index for the order, or increase `work_mem`.
- `Rows Removed by Filter` is large → the index isn't selective enough, or the composite order is wrong.

**Equivalents:** MySQL `EXPLAIN ANALYZE` / `EXPLAIN FORMAT=JSON` (check `type`: `ALL` = full scan, `ref`/`range` = index). SQL Server actual execution plan (check key lookups and implicit conversions).

---

## 11. Transactions and ACID

**20-second answer:**
> "A transaction groups operations so they succeed or fail as a unit. ACID stands for Atomicity: all or nothing. Consistency: constraints hold before and after. Isolation: concurrent transactions don't see each other's partial work. Durability: once committed, it survives a crash, usually through a write-ahead log. In payments, a transfer that debits one account and credits another is the classic example."

**Details**

| Property | Guarantees | How databases implement it |
|---|---|---|
| **Atomicity** | All operations commit, or none do | Undo/rollback using the log |
| **Consistency** | Constraints (PK, FK, CHECK, UNIQUE) hold at commit | Constraint checks + application invariants |
| **Isolation** | Concurrent transactions behave as if isolated, to the chosen level | Locks and/or MVCC (multi-version concurrency control) |
| **Durability** | Committed data survives a crash | Write-ahead log (WAL) flushed with fsync before commit is acknowledged; replication |

**Example: money transfer**

```sql
BEGIN;
UPDATE accounts_balance SET balance = balance - 100
WHERE  account_id = 1 AND balance >= 100;      -- guard against overdraft
-- application checks: 1 row updated? otherwise ROLLBACK
UPDATE accounts_balance SET balance = balance + 100
WHERE  account_id = 2;
INSERT INTO ledger(txn_id, debit_acct, credit_acct, amount) VALUES (…);
COMMIT;
```

**Practical points**
- **Keep transactions short.** Long transactions hold locks, block vacuum in Postgres (bloat), and increase deadlocks.
- **Never call an external API inside a DB transaction.** If the remote service or the network is slow, you hold locks the whole time. Use the outbox pattern instead (see [Transactions Q11](../System%20Design/Transactions_Interview_Prep.md#11-why-is-holding-a-database-transaction-open-during-a-remote-call-dangerous)).
- **Deadlocks:** two transactions lock rows in opposite order. Prevent them by locking in a consistent order (for example, lower `account_id` first). Handle them by retrying the victim transaction.
- **Savepoints** allow partial rollback inside a transaction.

**Distributed transactions** (a likely follow-up):
- **2PC (two-phase commit):** a coordinator asks every participant to prepare, then to commit. It's consistent, but blocking and fragile, and you can't use it across HTTP APIs.
- **Saga:** a sequence of local transactions, each with a compensating action (refund, cancel). Eventually consistent.
- **Outbox:** write the business row and the event row in **one local transaction**. A relay publishes the event. No dual-write problem.
- Deeper treatment of all three: [Transactions Q19–Q24](../System%20Design/Transactions_Interview_Prep.md#19-explain-the-transactional-outbox-pattern).

---

## 12. Isolation levels

**20-second answer:**
> "Isolation levels trade correctness for concurrency. Read Committed, the Postgres default, only sees committed data but can see different results within one transaction. Repeatable Read gives a stable snapshot. Serializable behaves as if transactions ran one at a time. I use the default plus explicit row locks or optimistic checks for hot spots like balances, and Serializable with retries where invariants span many rows."

**Anomalies**
- **Dirty read:** reading another transaction's *uncommitted* change.
- **Non-repeatable read:** reading the same row twice and getting different values, because someone committed in between.
- **Phantom read:** re-running a range query and getting new rows.
- **Lost update:** two transactions read, modify and write the same row. One overwrites the other.
- **Write skew:** two transactions each read overlapping data, make decisions, and write *different* rows, which breaks an invariant together. Example: two doctors both go off-call because each saw the other was on call.

**Levels (ANSI standard vs. what engines actually do)**

| Level | Dirty read | Non-repeatable | Phantom | Notes |
|---|---|---|---|---|
| Read Uncommitted | Possible | Possible | Possible | Postgres treats it as Read Committed |
| **Read Committed** | ❌ | Possible | Possible | **Default in Postgres, Oracle, SQL Server** |
| **Repeatable Read** | ❌ | ❌ | Possible (ANSI) | **Default in MySQL InnoDB.** In Postgres it's snapshot isolation (no phantoms, but write skew is possible). |
| **Serializable** | ❌ | ❌ | ❌ | Postgres uses SSI and aborts conflicting transactions, so **the app must retry** (SQLSTATE 40001) |

**Fixing a lost update**

```sql
-- ❌ Read-modify-write in the app at Read Committed → lost update
SELECT balance FROM accounts_balance WHERE account_id = 1;   -- app computes new value
UPDATE accounts_balance SET balance = :new WHERE account_id = 1;

-- ✅ Option 1: atomic update in SQL
UPDATE accounts_balance SET balance = balance - 100 WHERE account_id = 1 AND balance >= 100;

-- ✅ Option 2: lock the row (pessimistic)
SELECT balance FROM accounts_balance WHERE account_id = 1 FOR UPDATE;

-- ✅ Option 3: version check (optimistic) — see §13
```

**Likely follow-ups**
- *"What is MVCC?"* Readers see a snapshot built from row versions, so readers don't block writers and writers don't block readers. The cost is old versions that must be cleaned up (`VACUUM` in Postgres, undo logs in MySQL and Oracle).
- *"Which level for a payment system?"* Read Committed plus atomic updates, row locks or optimistic versioning on the contended rows. Serializable for complex cross-row invariants, with retry logic.

---

## 13. Optimistic vs pessimistic locking

**20-second answer:**
> "Pessimistic locking takes a lock up front, with `SELECT … FOR UPDATE`, so nobody else can change the row. That's best when conflicts are frequent and the transaction is short. Optimistic locking takes no lock. It checks a version number when writing and retries if someone else changed the row first. That's best when conflicts are rare or when the 'transaction' spans user think-time or an HTTP round-trip."

**Pessimistic**

```sql
BEGIN;
SELECT * FROM accounts_balance WHERE account_id = 1 FOR UPDATE;   -- others wait
UPDATE accounts_balance SET balance = balance - 100 WHERE account_id = 1;
COMMIT;
```

- Variants: `FOR UPDATE NOWAIT` (fail immediately) and `FOR UPDATE SKIP LOCKED` (skip locked rows). **SKIP LOCKED is the standard way to build a job queue in SQL**, because many workers each grab different rows:

  ```sql
  SELECT * FROM jobs WHERE status = 'READY'
  ORDER BY created_at LIMIT 10
  FOR UPDATE SKIP LOCKED;
  ```

**Optimistic**

```sql
-- read: version = 7
UPDATE accounts_profile
SET    email = :new_email, version = version + 1
WHERE  account_id = 1 AND version = 7;
-- 0 rows updated → someone else won → reload and retry (or tell the user)
```

- JPA/Hibernate: the `@Version` annotation does this automatically and throws `OptimisticLockException` (see [JPA & Hibernate](../Frameworks/JPA_Hibernate_Interview_Prep.md)).
- An `updated_at` timestamp can serve as the version, but an integer is safer.
- HTTP equivalent: `ETag` + `If-Match`, returning `412 Precondition Failed`.

| | Optimistic | Pessimistic |
|---|---|---|
| Lock held | None | Until commit |
| Best when | Conflicts are rare, long or user-facing edits | Conflicts are frequent, short critical sections |
| Failure mode | Retry storms under high contention | Blocking, deadlocks, lower throughput |
| Payments example | Updating a customer profile | Decrementing a hot balance, claiming a job |

**Likely follow-ups**
- *"Which did you use, and where?"* A version or sequence check on an event consumer ("ignore anything older than the current version") is effectively optimistic concurrency, even without a `version` column.

  > Personal example to add: describe a real system where you chose optimistic or pessimistic locking, including the contention level and why that choice fit.

---

## 14. Partitioning vs sharding

**20-second answer:**
> "Partitioning splits one large table into pieces **inside one database**, usually by date, so queries skip irrelevant partitions and old data can be dropped instantly. Sharding splits data **across multiple database servers** by a shard key, so you scale writes and storage beyond one machine. Partitioning is a cheap, local optimization. Sharding is a big architectural step, because cross-shard joins, transactions and resharding all get hard."

**Partitioning (one database)**

| Strategy | Example | Good for |
|---|---|---|
| **Range** | By month on `created_at` | Time-series data, retention, archiving |
| **List** | By `region IN ('US','EU')` | Data residency, known categories |
| **Hash** | `hash(customer_id) % 8` | Spreading data evenly when there's no natural range |

```sql
CREATE TABLE transactions_p (
  txn_id BIGINT, account_id BIGINT, amount NUMERIC(12,2), created_at TIMESTAMP NOT NULL
) PARTITION BY RANGE (created_at);

CREATE TABLE transactions_2026_10 PARTITION OF transactions_p
  FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
```

- **Partition pruning:** `WHERE created_at >= '2026-10-01'` only reads matching partitions. The filter must be on the partition key.
- **Retention:** `DROP TABLE transactions_2025_01` is instant, while `DELETE` would create bloat.
- **Gotchas:** unique constraints must include the partition key. Too many partitions slow planning.

**Sharding (multiple databases)**
- **Choose the shard key carefully:**
  - High cardinality, even distribution, and present in most queries (for example `customer_id` or `tenant_id`).
  - Avoid monotonic keys such as timestamps, which send every write to one shard.
- **Routing:** the application or a proxy computes the shard (Vitess, Citus, or app-level hash).
- **Approaches:** hash sharding (even, but resharding is hard, so use consistent hashing), range sharding (easy ranges, but hot spots), directory/lookup table (flexible, but an extra lookup).
- **What gets hard:** cross-shard joins, cross-shard transactions (sagas instead), global unique IDs (Snowflake IDs/UUIDs), resharding, hot tenants, and operations (backups, schema changes ×N).
- **Before sharding,** try in this order: indexes and query tuning → read replicas → caching → partitioning → vertical scaling → archiving cold data. Then shard.

| | Partitioning | Sharding |
|---|---|---|
| Where | One database instance | Many database instances |
| Scales | Query performance and maintenance | Writes, storage and throughput |
| Transparent to the app? | Mostly yes | Usually no (routing, key in every query) |
| Cross-piece queries | Easy | Hard and slow |

---

## 15. SQL vs NoSQL

**20-second answer:**
> "I pick based on the access patterns and consistency needs, not hype. Relational databases are best when data is relational, you need ad-hoc queries, joins and strong ACID transactions, like a payments ledger. NoSQL fits when access patterns are known and simple, scale or flexibility matter more than joins, and eventual consistency is acceptable, like session data, event streams or high-volume key lookups. Many systems use both."

**Details**

| | Relational (Postgres, MySQL, Oracle) | NoSQL |
|---|---|---|
| Model | Tables, fixed schema | Key-value, document, wide-column, graph |
| Queries | Ad hoc, joins, aggregations | Designed around known access patterns |
| Consistency | Strong ACID | Often tunable or eventual (many now offer transactions) |
| Scaling | Vertical + replicas. Sharding takes effort. | Horizontal scaling built in |
| Schema change | Migrations | Flexible, but the schema just moves into the app |

**NoSQL families**

| Type | Examples | Use for |
|---|---|---|
| Key-value | Redis, DynamoDB | Sessions, caching, idempotency keys, rate limits |
| Document | MongoDB, DynamoDB, Couchbase | Flexible nested records, product catalogs, content |
| Wide-column | Cassandra, HBase, ScyllaDB | Massive write-heavy time-series and event logs |
| Graph | Neo4j, Neptune | Relationships: fraud rings, **citation networks** |
| Search | Elasticsearch, OpenSearch | Full-text search, relevance ranking, document retrieval |

**Payments examples**
- Ledger, balances, accounts → **Postgres/Oracle** (ACID, constraints, audit).
- Idempotency keys with TTL, rate limiting → **Redis/DynamoDB**.
- Token lifecycle events → **Kafka** + a relational or DynamoDB read model.
- Fraud ring detection → **Graph**.

**Legal-research and data-platform examples**
- Case and document metadata, subscriptions, billing → **relational**.
- Full-text search across millions of opinions → **Elasticsearch/OpenSearch**.
- Citation network ("which cases cite this one, and was it overturned?") → **graph**, or relational with recursive CTEs.
- Raw documents → **object storage (S3)** + metadata in the relational database.

**Likely follow-ups**
- *"CAP theorem?"* During a network partition, you choose consistency or availability. PACELC adds that even without a partition, you trade latency against consistency.
- *"DynamoDB single-table design?"* Model around access patterns, with composite partition and sort keys. Good at known queries, poor at ad-hoc ones.

---

## Part B — Practice Problems

For each problem: say the approach in one sentence first, then write the query. Mention edge cases such as ties, NULLs and duplicates. Interviewers listen for those.

### Problem 1 — Top-N per group

*Top 3 transactions by amount for each account.*

> **Approach:** "Number the rows within each account by amount descending using a window function, then keep rows 1 to 3."

```sql
SELECT account_id, txn_id, amount
FROM (
  SELECT t.*,
         ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY amount DESC, txn_id) AS rn
  FROM   transactions t
) x
WHERE rn <= 3;
```

- **Ties:** `ROW_NUMBER` picks exactly 3 (adding `txn_id` makes the result deterministic). `RANK` lets ties share a rank and skips the next numbers, so you might get more than 3. `DENSE_RANK` gives the top 3 *distinct amounts*.
- Postgres alternative for large tables: a `LATERAL` join using an index on `(account_id, amount DESC)`.

```sql
SELECT a.account_id, t.txn_id, t.amount
FROM   accounts a
CROSS JOIN LATERAL (
  SELECT txn_id, amount FROM transactions
  WHERE  account_id = a.account_id
  ORDER  BY amount DESC LIMIT 3
) t;
```

### Problem 2 — Duplicate detection (and removal)

*Find customers with duplicate emails, then delete duplicates and keep the oldest.*

> **Approach:** "Group by the duplicate key with `HAVING COUNT(*) > 1` to find them. Use `ROW_NUMBER` to choose which one to keep."

```sql
-- Find duplicates
SELECT LOWER(email) AS email, COUNT(*) AS cnt
FROM   customers
GROUP  BY LOWER(email)
HAVING COUNT(*) > 1;

-- Show every duplicate row with its rank
SELECT *
FROM (
  SELECT c.*,
         ROW_NUMBER() OVER (PARTITION BY LOWER(email) ORDER BY created_at, customer_id) AS rn
  FROM   customers c
) x
WHERE rn > 1;

-- Delete duplicates, keep the oldest
DELETE FROM customers
WHERE customer_id IN (
  SELECT customer_id FROM (
    SELECT customer_id,
           ROW_NUMBER() OVER (PARTITION BY LOWER(email) ORDER BY created_at, customer_id) AS rn
    FROM   customers
  ) x WHERE rn > 1
);
```

- **Say this:** "Before deleting, I'd check foreign keys pointing at those rows and re-point them to the survivor. Then I'd add a unique index on `LOWER(email)` so it can't happen again."
- Payments variant: duplicate transactions = same `account_id`, `amount` and `merchant` within 60 seconds. Use `LAG()` (problem 6).

### Problem 3 — Latest row per customer

*Each customer's most recent transaction.*

> **Approach:** "`ROW_NUMBER` partitioned by customer and ordered by time descending, keeping row 1. In Postgres, `DISTINCT ON` is the short form."

```sql
-- Portable (window function)
SELECT *
FROM (
  SELECT a.customer_id, t.*,
         ROW_NUMBER() OVER (PARTITION BY a.customer_id
                            ORDER BY t.created_at DESC, t.txn_id DESC) AS rn
  FROM   transactions t
  JOIN   accounts a ON a.account_id = t.account_id
) x
WHERE rn = 1;

-- Postgres shorthand
SELECT DISTINCT ON (a.customer_id) a.customer_id, t.*
FROM   transactions t
JOIN   accounts a ON a.account_id = t.account_id
ORDER  BY a.customer_id, t.created_at DESC, t.txn_id DESC;
```

- **Why not `MAX(created_at)` + a join back?** It works, but returns several rows on timestamp ties and needs two passes.
- The index that makes this fast: `(account_id, created_at DESC)`.

### Problem 4 — Joins

*Customer name, account type, and total approved spend per account, including accounts with no transactions.*

> **Approach:** "Aggregate transactions first so the join doesn't multiply rows, then LEFT JOIN so accounts with no transactions still appear."

```sql
SELECT c.name, a.account_id, a.account_type,
       COALESCE(t.total_spend, 0) AS total_spend
FROM   customers c
JOIN   accounts  a ON a.customer_id = c.customer_id
LEFT JOIN (
  SELECT account_id, SUM(amount) AS total_spend
  FROM   transactions
  WHERE  status = 'APPROVED'            -- filter inside the subquery, not in the outer WHERE
  GROUP  BY account_id
) t ON t.account_id = a.account_id
ORDER BY total_spend DESC;
```

### Problem 5 — GROUP BY / HAVING

*Merchants with more than 100 approved transactions and average amount above $50 in the last 30 days.*

> **Approach:** "WHERE filters rows before grouping, and HAVING filters groups after aggregation."

```sql
SELECT merchant,
       COUNT(*)            AS txn_count,
       ROUND(AVG(amount),2) AS avg_amount
FROM   transactions
WHERE  status = 'APPROVED'
  AND  created_at >= now() - interval '30 days'
GROUP  BY merchant
HAVING COUNT(*) > 100 AND AVG(amount) > 50
ORDER  BY txn_count DESC;
```

- **Logical order of execution:** `FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT`. This is why you can't use a SELECT alias in WHERE, but can in ORDER BY (Postgres also allows it in GROUP BY).
- **Conditional aggregation**, which interviewers like:

  ```sql
  SELECT merchant,
         COUNT(*) FILTER (WHERE status = 'DECLINED')::float / COUNT(*) AS decline_rate
  FROM   transactions GROUP BY merchant;
  -- Portable: SUM(CASE WHEN status='DECLINED' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
  ```

### Problem 6 — Window functions

*For each transaction: the previous transaction amount on the same account, the time since it, and the rank of its amount within the account.*

> **Approach:** "Window functions compute values across related rows without collapsing them like GROUP BY does. LAG looks back, and RANK orders within the partition."

```sql
SELECT txn_id, account_id, amount, created_at,
       LAG(amount)     OVER w                    AS prev_amount,
       created_at - LAG(created_at) OVER w       AS time_since_prev,
       RANK()          OVER (PARTITION BY account_id ORDER BY amount DESC) AS amount_rank,
       amount - AVG(amount) OVER (PARTITION BY account_id) AS diff_from_avg
FROM   transactions
WINDOW w AS (PARTITION BY account_id ORDER BY created_at);
```

**Window functions to know**

| Function | Use |
|---|---|
| `ROW_NUMBER()` | Unique sequence. Use for dedupe and top-N. |
| `RANK()` / `DENSE_RANK()` | Ties share a rank. RANK skips the following numbers, DENSE_RANK doesn't. |
| `LAG()` / `LEAD()` | Previous or next row's value |
| `FIRST_VALUE()` / `LAST_VALUE()` | First or last value in the window (LAST_VALUE needs an explicit frame) |
| `NTILE(n)` | Buckets: quartiles, deciles |
| `SUM/AVG/COUNT() OVER` | Running or partition-level aggregates |

**Fraud-style example:** a possible card-testing burst, meaning 3+ transactions on one account within 1 minute.

```sql
SELECT *
FROM (
  SELECT t.*,
         COUNT(*) OVER (PARTITION BY account_id ORDER BY created_at
                        RANGE BETWEEN interval '1 minute' PRECEDING AND CURRENT ROW) AS txns_last_min
  FROM transactions t
) x
WHERE txns_last_min >= 3;
```

### Problem 7 — Running total

*Running balance of each account's approved transactions over time, and a 7-day moving average of daily volume.*

> **Approach:** "`SUM() OVER` with an `ORDER BY` gives a cumulative total. Specify the frame explicitly so ties are handled correctly."

```sql
SELECT account_id, txn_id, created_at, amount,
       SUM(amount) OVER (PARTITION BY account_id
                         ORDER BY created_at, txn_id
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM   transactions
WHERE  status = 'APPROVED';
```

- **Why `ROWS` and the `txn_id` tie-breaker?** The default frame is `RANGE … CURRENT ROW`, which treats rows with the same timestamp as peers and gives them all the same total. `ROWS` gives a true row-by-row running total.

```sql
-- 7-day moving average of daily volume
WITH daily AS (
  SELECT created_at::date AS day, SUM(amount) AS volume
  FROM   transactions WHERE status = 'APPROVED'
  GROUP  BY created_at::date
)
SELECT day, volume,
       AVG(volume) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d
FROM daily;
```

- Edge case: days with no transactions are missing, so a 7-row window could span more than 7 days. Fix it by generating a date series (`generate_series`) and LEFT JOINing to it.

### Problem 8 — Customers with no matching records

*Customers who have never made a transaction.*

> **Approach:** "An anti-join. I prefer `NOT EXISTS` because it's NULL-safe and the optimizer handles it well. `LEFT JOIN … IS NULL` works too. I avoid `NOT IN` with a subquery because a single NULL makes it return nothing."

```sql
-- ✅ NOT EXISTS (preferred)
SELECT c.*
FROM   customers c
WHERE  NOT EXISTS (
  SELECT 1
  FROM   accounts a
  JOIN   transactions t ON t.account_id = a.account_id
  WHERE  a.customer_id = c.customer_id
);

-- ✅ LEFT JOIN + aggregate (handles customers with several accounts)
SELECT c.customer_id, c.name
FROM   customers c
LEFT JOIN accounts a     ON a.customer_id = c.customer_id
LEFT JOIN transactions t ON t.account_id  = a.account_id
GROUP  BY c.customer_id, c.name
HAVING COUNT(t.txn_id) = 0;

-- ✅ LEFT JOIN / IS NULL (the classic form, when there's only one hop)
SELECT a.*
FROM   accounts a
LEFT JOIN transactions t ON t.account_id = a.account_id
WHERE  t.txn_id IS NULL;            -- accounts with no transactions

-- ❌ NOT IN trap
SELECT * FROM customers
WHERE customer_id NOT IN (SELECT customer_id FROM accounts);
-- If any accounts.customer_id is NULL → returns ZERO rows, because x NOT IN (…, NULL) is never TRUE.
```

**Say this:** "The LEFT JOIN version needs care when there's a one-to-many in between. NOT EXISTS expresses the intent directly: no matching row exists."

### Bonus problems (commonly asked)

**Second-highest amount (handles ties and the no-result case)**

```sql
SELECT MAX(amount) FROM transactions
WHERE  amount < (SELECT MAX(amount) FROM transactions);
-- or: DENSE_RANK() = 2
```

**Month-over-month growth**

```sql
WITH m AS (
  SELECT date_trunc('month', created_at) AS month, SUM(amount) AS vol
  FROM transactions GROUP BY 1
)
SELECT month, vol,
       ROUND(100.0 * (vol - LAG(vol) OVER (ORDER BY month))
             / NULLIF(LAG(vol) OVER (ORDER BY month), 0), 2) AS pct_growth
FROM m;
```

`NULLIF` turns a zero previous month into NULL growth instead of a division-by-zero error. The first month is NULL too, because it has no previous month.

**Consecutive days active (gaps and islands)**

```sql
WITH d AS (
  SELECT DISTINCT a.customer_id, t.created_at::date AS day
  FROM transactions t JOIN accounts a USING (account_id)
),
g AS (
  SELECT customer_id, day,
         day - (ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY day))::int AS grp
  FROM d
)
SELECT customer_id, MIN(day) AS streak_start, MAX(day) AS streak_end, COUNT(*) AS days
FROM g GROUP BY customer_id, grp
HAVING COUNT(*) >= 3;
```

The trick: in a run of consecutive dates, `date − row_number` stays constant, so it identifies each "island".

**Recursive CTE: hierarchy or citation chain**

```sql
-- All cases that directly or indirectly cite case 100 (depth-limited)
WITH RECURSIVE chain AS (
  SELECT citing_case_id, cited_case_id, 1 AS depth
  FROM   case_citations WHERE cited_case_id = 100
  UNION ALL
  SELECT c.citing_case_id, c.cited_case_id, ch.depth + 1
  FROM   case_citations c
  JOIN   chain ch ON c.cited_case_id = ch.citing_case_id
  WHERE  ch.depth < 3
)
SELECT citing_case_id, MIN(depth) AS depth FROM chain GROUP BY citing_case_id;
```

---

## Part C — Data Modeling Walkthrough

Modeling rounds care about **designing a clean model and explaining why**. Use this sequence out loud in any "design a schema for X" question. The three examples below cover the most common prompt shapes: a document-and-relationship platform, an identity/risk platform with audit requirements, and an analytics star schema.

## The 6-step method (say the steps out loud)

1. **Clarify the use cases and access patterns.** "What are the top queries? Is it read-heavy or write-heavy? What volume? Is it OLTP or analytics?"
2. **Identify the entities and relationships.** Nouns become tables. Then mark the cardinality: 1:1, 1:N or M:N (M:N needs a junction table).
3. **Choose the keys.** Surrogate primary keys (`BIGINT`/UUID), natural keys as `UNIQUE` constraints.
4. **Normalize to 3NF**, then **denormalize on purpose** for proven hot reads, and say why.
5. **Add constraints and indexes.** NOT NULL, FK, CHECK, UNIQUE, and indexes tied to the stated queries.
6. **Address change over time and scale.** History (SCD/audit), soft deletes, partitioning, search, and the analytics model.

## Example A — Legal research platform

**Requirements:** store court cases and documents, search them, track which cases cite which, and know whether a case was overturned.

```text
courts(court_id PK, name, jurisdiction_id FK, level)          -- level: SUPREME, APPELLATE, TRIAL
jurisdictions(jurisdiction_id PK, name, parent_id FK NULL)    -- self-ref hierarchy: Federal > Circuit > District
cases(case_id PK, court_id FK, docket_number, title, decision_date, status,
      UNIQUE(court_id, docket_number))
judges(judge_id PK, name)
case_judges(case_id FK, judge_id FK, role, PK(case_id, judge_id))   -- M:N
parties(party_id PK, name, party_type)                              -- PERSON, ORG
case_parties(case_id FK, party_id FK, role, PK(case_id, party_id, role)) -- plaintiff/defendant
documents(document_id PK, case_id FK, doc_type, version, s3_uri, published_at)
case_citations(citing_case_id FK, cited_case_id FK, treatment,      -- treatment: FOLLOWED, DISTINGUISHED, OVERRULED
               PK(citing_case_id, cited_case_id))
topics(topic_id PK, name, parent_id FK NULL)
case_topics(case_id FK, topic_id FK, PK(case_id, topic_id))
```

**Why it's designed this way (the part they're listening for):**
- **Citations are a self-referencing M:N junction table** with an attribute, `treatment`. That's what powers "has this case been overruled?" Recursive CTEs answer citation chains, and a graph database becomes worth it if multi-hop network queries become a core product feature.
- **Document text lives in S3, and search lives in Elasticsearch/OpenSearch.** The relational database is the source of truth for metadata and relationships. The search index is a **denormalized read model** fed by CDC/events. I wouldn't do full-text search in the OLTP database.
- **Versioned documents:** `documents(case_id, version)`, because opinions get amended. Never overwrite.
- **Hierarchies** (jurisdictions, topics) use a `parent_id` self-reference. For deep or frequent hierarchy queries, add a closure table or `ltree`.
- **Indexes from access patterns:** `cases(court_id, decision_date DESC)` for browsing a court's recent decisions, `case_citations(cited_case_id)` for "who cites me" (the PK covers "whom do I cite"), and `case_parties(party_id)` for "all cases involving this company".
- **Scale:** partition `documents` or usage logs by date. Cases are read-heavy and change rarely, so cache them aggressively.

## Example B — Identity and fraud risk

**Requirements:** link identity records from many sources, score risk, and keep a history of every attribute for audit.

```text
persons(person_id PK, created_at)                             -- resolved identity (entity resolution output)
source_records(record_id PK, source_id FK, person_id FK NULL, -- raw record, linked after matching
               raw_name, raw_dob, raw_address, ingested_at)
person_addresses(person_id FK, address_id FK, valid_from, valid_to, source_id FK)  -- SCD2-style history
addresses(address_id PK, line1, city, state, postal_code, normalized_hash UNIQUE)
person_identifiers(person_id FK, id_type, id_value_hash, source_id FK,   -- SSN/phone/email: hashed, never plain
                   PK(person_id, id_type, id_value_hash))
risk_scores(score_id PK, person_id FK, model_version, score, reason_codes JSONB, scored_at)
```

**Why it's designed this way:**
- **Raw source records are kept separate from resolved persons.** Matching can be re-run as algorithms improve, and every link is explainable, which matters for compliance (in the US, consumer-reporting data falls under the FCRA).
- **Effective-dated history** on addresses and identifiers: "where did this person live in 2023?" is a core question. That's SCD Type 2 in an OLTP model.
- **Sensitive identifiers are hashed or tokenized** with keyed hashing (HMAC), so equality matching works without storing plaintext.
- **Risk scores are append-only with `model_version`**, so you can reproduce why a decision was made, which auditors will ask about.

## Example C — Analytics star schema

*"Model product usage so we can report searches, document views and active users by customer and plan over time."*

```text
fact_usage_event (grain: one row per user action)
  date_sk, time_sk, user_sk, customer_sk, document_sk, event_type_sk, session_id,
  duration_ms, results_returned

dim_date      (date_sk, date, week, month, quarter, fiscal_year, is_holiday)
dim_user      (user_sk, user_id, role, practice_area, valid_from, valid_to, is_current)   -- SCD2
dim_customer  (customer_sk, customer_id, firm_name, segment, plan_tier, region,
               valid_from, valid_to, is_current)                                         -- SCD2 on plan_tier
dim_document  (document_sk, document_id, doc_type, jurisdiction, court_level, topic)
dim_event_type(event_type_sk, event_type)   -- SEARCH, VIEW, DOWNLOAD, PRINT
```

- **Grain stated first:** one row per user action.
- **SCD Type 2 on `plan_tier`**, so usage is credited to the plan the customer was on *at the time*. That's essential for "did upgrading increase usage?"
- **A star, not a snowflake.** Jurisdiction and topic are flattened into `dim_document` for simpler BI queries.
- **Daily active users** = `COUNT(DISTINCT user_sk)` per `date_sk`. It's non-additive, so you can't sum daily active users to get monthly active users. Keep a separate aggregate or compute it from the fact table.

---

## Part D — One-Page Cheat Sheet

| Topic | One-line answer |
|---|---|
| Normalize vs denormalize | Normalize for write integrity (OLTP). Denormalize deliberately for read speed, and keep the copies in sync. |
| 3NF | Every non-key column depends on the key, the whole key, and nothing but the key. |
| Star vs snowflake | Star = flat dimensions and fewer joins (the default). Snowflake = normalized dimensions. |
| Fact vs dimension | Facts = measures at a declared grain. Dimensions = descriptive context. Declare the grain first. |
| SCD 1 vs 2 | Type 1 overwrites. Type 2 adds a versioned row with dates, preserving history. |
| INNER vs LEFT | INNER = matches only. LEFT = every left row. Right-table filters go in ON, not WHERE. |
| Indexing | B-tree for range and equality. Speeds reads, slows writes. Functions on columns stop the index being used. |
| Composite index | Leftmost prefix rule. Equality columns first, range/sort last. INCLUDE for covering. |
| Query optimization | Plan first, sargable filters, right index, fetch less, rewrite patterns, then structural changes. |
| Execution plan | `EXPLAIN ANALYZE`. Compare estimated vs actual rows. Know scan and join types. |
| ACID | All-or-nothing, constraints hold, isolated, durable through the WAL. Keep transactions short, no external calls inside. |
| Isolation | Read Committed (PG default) → Repeatable Read (MySQL default) → Serializable (retry on 40001). |
| Locking | Pessimistic = `FOR UPDATE` (high contention). Optimistic = version check (low contention). |
| Partition vs shard | Partition = inside one database (pruning, retention). Shard = across servers (scale writes, hard trade-offs). |
| SQL vs NoSQL | Choose by access pattern and consistency. A ledger goes relational, sessions or idempotency go in a KV store, documents go in search. |

**Common SQL traps to say out loud:** `NOT IN` with NULLs · `COUNT(*)` vs `COUNT(col)` after a LEFT JOIN · WHERE turning a LEFT JOIN into an INNER JOIN · join fan-out inflating SUM · `RANGE` vs `ROWS` frames · ties in top-N · `DATE(col)` making a filter unusable for the index · `NULL = NULL` is not TRUE (use `IS NOT DISTINCT FROM`).

---

## Sources

- PostgreSQL 16 documentation: [Indexes](https://www.postgresql.org/docs/16/indexes.html) (types, multicolumn, partial, expression, index-only scans and `INCLUDE`), [`CREATE INDEX` (`CONCURRENTLY`)](https://www.postgresql.org/docs/16/sql-createindex.html), [Using `EXPLAIN`](https://www.postgresql.org/docs/16/using-explain.html), [Transaction Isolation](https://www.postgresql.org/docs/16/transaction-iso.html), [Explicit Locking and `SKIP LOCKED`](https://www.postgresql.org/docs/16/sql-select.html#SQL-FOR-UPDATE-SHARE), [Table Partitioning](https://www.postgresql.org/docs/16/ddl-partitioning.html), [Window Functions](https://www.postgresql.org/docs/16/functions-window.html), [`WITH RECURSIVE`](https://www.postgresql.org/docs/16/queries-with.html), [Reliability and the WAL](https://www.postgresql.org/docs/16/wal-intro.html)
- MySQL 8.0 Reference Manual: [Clustered and Secondary Indexes (InnoDB)](https://dev.mysql.com/doc/refman/8.0/en/innodb-index-types.html), [Transaction Isolation Levels (InnoDB default `REPEATABLE READ`)](https://dev.mysql.com/doc/refman/8.0/en/innodb-transaction-isolation-levels.html)
- Microsoft SQL Server documentation: [Clustered and nonclustered indexes](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/clustered-and-nonclustered-indexes-described)
- Kimball Group: [Dimensional Modeling Techniques](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/) (grain, fact-table types, additive/semi-additive measures, conformed dimensions, SCD types 0–6)
- Berenson et al., [*A Critique of ANSI SQL Isolation Levels*](https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/) (1995): lost update, write skew, snapshot isolation
