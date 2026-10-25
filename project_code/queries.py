"""
queries.py  –  Sections 4 & 5  Parameterised Q1-Q7 for PostgreSQL and Neo4j.

Each Q_x_pg / Q_x_neo function returns (sql/cypher_string, params_dict).
Call run_pg() / run_neo() in compare.py or benchmark.py.

Review accounts and destinations (from the project handout):
  Set  Review account  Destination  September date
  A    998             24755        6
  B    147228          186823       13
  C    206978          6573         8
  D    237998          21755        6
  E    144228          183823       13
  F    203978          3573         8
"""

from datetime import datetime, timezone, timedelta

# CAT = UTC+2
CAT = timezone(timedelta(hours=2))
START_EPOCH = 1788213600   # 2026-09-01 00:00:00 CAT (same as generator)

# Review sets: (account, destination, september_date)
REVIEW_SETS = {
    'A': (998,    24755,  6),
    'B': (147228, 186823, 13),
    'C': (206978, 6573,   8),
    'D': (237998, 21755,  6),
    'E': (144228, 183823, 13),
    'F': (203978, 3573,   8),
}


def cat_hour_window(sept_day: int):
    """Return (start_epoch, end_epoch) for 09:45–10:45 CAT on the given Sept 2026 day."""
    date = datetime(2026, 9, sept_day, 9, 45, 0, tzinfo=CAT)
    start = int(date.timestamp())
    end   = start + 3600  # exclusive
    return start, end


# =============================================================================
# Q1  Account activity in one hour
# =============================================================================
Q1_SQL = """
SELECT COALESCE(COUNT(*), 0)        AS tx_count,
       COALESCE(SUM(amount_rwf), 0) AS total_rwf
FROM   transfers
WHERE  sender_id   = %(account)s
  AND  occurred_at >= %(start)s
  AND  occurred_at <  %(end)s;
"""

Q1_CYPHER = """
MATCH (a:Account {account_id: $account})-[t:TRANSFER]->()
WHERE t.occurred_at >= $start AND t.occurred_at < $end
RETURN count(t)            AS tx_count,
       coalesce(sum(t.amount_rwf), 0) AS total_rwf;
"""

def q1_params(set_key):
    acct, _, day = REVIEW_SETS[set_key]
    s, e = cat_hour_window(day)
    return {'account': acct, 'start': s, 'end': e}


# =============================================================================
# Q2  Daily activity – full month
# =============================================================================
Q2_SQL = """
SELECT to_char(to_timestamp(occurred_at) AT TIME ZONE 'Africa/Kigali', 'YYYY-MM-DD')
           AS day,
       COUNT(*)         AS tx_count,
       SUM(amount_rwf)  AS total_rwf
FROM   transfers
GROUP  BY 1
ORDER  BY 1;
"""

Q2_CYPHER = """
MATCH ()-[t:TRANSFER]->()
WITH  datetime({epochSeconds: t.occurred_at, timezone: 'Africa/Kigali'}) AS dt,
      t.amount_rwf AS amt
RETURN toString(date(dt)) AS day,
       count(*)   AS tx_count,
       sum(amt)   AS total_rwf
ORDER  BY day;
"""

def q2_params():
    return {}


# =============================================================================
# Q3  Shared devices
# =============================================================================
Q3_SQL = """
SELECT ad2.account_id  AS other_account_id,
       ad1.device_id,
       d.access_type,
       GREATEST(ad1.first_day, ad2.first_day) AS overlap_start,
       LEAST   (ad1.last_day,  ad2.last_day)  AS overlap_end
FROM   account_devices ad1
JOIN   account_devices ad2
       ON  ad1.device_id = ad2.device_id
       AND ad1.account_id <> ad2.account_id
       AND GREATEST(ad1.first_day, ad2.first_day)
           <= LEAST(ad1.last_day, ad2.last_day)
JOIN   devices d ON d.device_id = ad1.device_id
WHERE  ad1.account_id = %(account)s
ORDER  BY other_account_id, ad1.device_id;
"""

Q3_CYPHER = """
MATCH (a:Account {account_id: $account})-[ad1:USED_DEVICE]->(d:Device)
      <-[ad2:USED_DEVICE]-(b:Account)
WHERE b.account_id <> $account
  AND ad2.first_day <= ad1.last_day
  AND ad1.first_day <= ad2.last_day
RETURN b.account_id                                 AS other_account_id,
       d.device_id,
       d.access_type,
       CASE WHEN ad1.first_day > ad2.first_day
            THEN ad1.first_day ELSE ad2.first_day END AS overlap_start,
       CASE WHEN ad1.last_day  < ad2.last_day
            THEN ad1.last_day  ELSE ad2.last_day  END AS overlap_end
ORDER  BY other_account_id, d.device_id;
"""

def q3_params(set_key):
    acct, _, _ = REVIEW_SETS[set_key]
    return {'account': acct}


# =============================================================================
# Q4  Ownership and device network (depths 4, 6, 8, 10)
# =============================================================================
Q4_SQL = """
WITH RECURSIVE edges(sk, si, dk, di) AS (
  -- ownership: Customer -> Account and Account -> Customer (both directions)
  SELECT 'Customer'::text, c.customer_id, 'Account'::text, a.account_id
  FROM   accounts a JOIN customers c ON c.customer_id = a.customer_id
  UNION ALL
  SELECT 'Account'::text, a.account_id, 'Customer'::text, c.customer_id
  FROM   accounts a JOIN customers c ON c.customer_id = a.customer_id
  -- device-use: Account -> Device and Device -> Account (both directions)
  UNION ALL
  SELECT 'Account'::text, ad.account_id, 'Device'::text, ad.device_id
  FROM   account_devices ad
  UNION ALL
  SELECT 'Device'::text, ad.device_id, 'Account'::text, ad.account_id
  FROM   account_devices ad
),
walk(kind, id, depth) AS (
  SELECT 'Account'::text, %(account)s::integer, 0
  UNION
  SELECT e.dk, e.di, w.depth + 1
  FROM   walk w
  JOIN   edges e ON e.sk = w.kind AND e.si = w.id
  WHERE  w.depth < %(depth)s
)
SELECT cu.region, COUNT(DISTINCT w.id) AS reached_accounts
FROM   walk w
JOIN   accounts a  ON a.account_id  = w.id AND w.kind = 'Account'
JOIN   customers cu ON cu.customer_id = a.customer_id
WHERE  w.kind = 'Account'
  AND  w.id  <> %(account)s
GROUP  BY cu.region
ORDER  BY cu.region;
"""

Q4_CYPHER = """
MATCH (a:Account {account_id: $account})
MATCH (a)-[:OWNS|USED_DEVICE*1..$depth]-(b:Account)
WHERE b.account_id <> $account
WITH  DISTINCT b
MATCH (c:Customer)-[:OWNS]->(b)
RETURN c.region AS region, count(b) AS reached_accounts
ORDER  BY region;
"""

def q4_params(set_key, depth):
    acct, _, _ = REVIEW_SETS[set_key]
    return {'account': acct, 'depth': depth}


# =============================================================================
# Q5  Rapid onward payments (exactly 3 transfers through 4 distinct accounts)
# =============================================================================
Q5_SQL = """
WITH t1 AS (
  SELECT transfer_id AS id1, sender_id AS s1, receiver_id AS r1,
         occurred_at AS at1, amount_rwf AS amt1
  FROM   transfers
  WHERE  sender_id   = %(account)s
    AND  occurred_at >= %(start)s
    AND  occurred_at <  %(end)s
)
SELECT t1.id1, t2.transfer_id AS id2, t3.transfer_id AS id3,
       t3.receiver_id AS final_receiver
FROM   t1
JOIN   transfers t2 ON t2.sender_id   = t1.r1
                    AND t2.occurred_at > t1.at1
                    AND t2.occurred_at <= t1.at1 + 600
                    AND 90*t1.amt1 <= 100*t2.amount_rwf
                    AND 100*t2.amount_rwf <= 105*t1.amt1
JOIN   transfers t3 ON t3.sender_id   = t2.receiver_id
                    AND t3.occurred_at > t2.occurred_at
                    AND t3.occurred_at <= t2.occurred_at + 600
                    AND 90*t2.amount_rwf <= 100*t3.amount_rwf
                    AND 100*t3.amount_rwf <= 105*t2.amount_rwf
-- four distinct accounts
WHERE  t2.sender_id <> t1.s1
  AND  t3.sender_id <> t1.s1 AND t3.sender_id <> t1.r1
  AND  t3.receiver_id<> t1.s1 AND t3.receiver_id<> t1.r1 AND t3.receiver_id<> t2.receiver_id
ORDER  BY t1.id1, t2.transfer_id, t3.transfer_id, t3.receiver_id;
"""

Q5_CYPHER = """
MATCH (a:Account {account_id: $account})-[t1:TRANSFER]->(b:Account)
      -[t2:TRANSFER]->(c:Account)
      -[t3:TRANSFER]->(d:Account)
WHERE t1.occurred_at >= $start AND t1.occurred_at < $end
  AND t2.occurred_at >  t1.occurred_at AND t2.occurred_at <= t1.occurred_at + 600
  AND t3.occurred_at >  t2.occurred_at AND t3.occurred_at <= t2.occurred_at + 600
  AND 90*t1.amount_rwf <= 100*t2.amount_rwf AND 100*t2.amount_rwf <= 105*t1.amount_rwf
  AND 90*t2.amount_rwf <= 100*t3.amount_rwf AND 100*t3.amount_rwf <= 105*t2.amount_rwf
  AND a <> b AND a <> c AND a <> d
  AND b <> c AND b <> d
  AND c <> d
RETURN t1.transfer_id AS id1, t2.transfer_id AS id2,
       t3.transfer_id AS id3, d.account_id   AS final_receiver
ORDER  BY id1, id2, id3, final_receiver;
"""

def q5_params(set_key):
    acct, _, day = REVIEW_SETS[set_key]
    s, e = cat_hour_window(day)
    return {'account': acct, 'start': s, 'end': e}


# =============================================================================
# Q6  Circular payments (3–8 transfers returning to start, within 1800 s)
# =============================================================================
Q6_SQL = """
WITH RECURSIVE circ(
  current_account, transfer_ids, first_at, last_at, last_amount, hops
) AS (
  -- base: first transfer out from review account within hour
  SELECT t.receiver_id,
         ARRAY[t.transfer_id],
         t.occurred_at, t.occurred_at,
         t.amount_rwf,
         1
  FROM   transfers t
  WHERE  t.sender_id   = %(account)s
    AND  t.occurred_at >= %(start)s
    AND  t.occurred_at <  %(end)s

  UNION ALL

  -- recursive: extend with next eligible transfer
  SELECT t.receiver_id,
         c.transfer_ids || t.transfer_id,
         c.first_at,
         t.occurred_at,
         t.amount_rwf,
         c.hops + 1
  FROM   circ c
  JOIN   transfers t ON t.sender_id    = c.current_account
  WHERE  c.hops < 8
    AND  t.occurred_at > c.last_at
    AND  t.occurred_at >= %(start)s
    AND  t.occurred_at <  %(end)s
    AND  (t.occurred_at - c.first_at) <= 1800
    AND  90 * c.last_amount <= 100 * t.amount_rwf
    AND  100 * t.amount_rwf <= 105 * c.last_amount
    AND  NOT (t.transfer_id = ANY(c.transfer_ids))
)
SELECT transfer_ids, hops AS length
FROM   circ
WHERE  current_account = %(account)s
  AND  hops >= 3
ORDER  BY transfer_ids;
"""

Q6_CYPHER = """
MATCH p = (a:Account {account_id: $account})
          ((x)-[t:TRANSFER]->(y) WHERE t.occurred_at >= $start AND t.occurred_at < $end){3,8}
          (a)
WITH p,
     [r IN relationships(p) | r.occurred_at] AS times,
     [r IN relationships(p) | r.amount_rwf]  AS amts,
     [r IN relationships(p) | r.transfer_id] AS ids
WHERE all(i IN range(0, size(times)-2)
          WHERE times[i+1] > times[i])
  AND (times[-1] - times[0]) <= 1800
  AND all(i IN range(0, size(amts)-2)
          WHERE 90*amts[i] <= 100*amts[i+1]
            AND 100*amts[i+1] <= 105*amts[i])
RETURN ids AS transfer_ids, size(ids) AS length
ORDER  BY transfer_ids;
"""

def q6_params(set_key):
    acct, _, day = REVIEW_SETS[set_key]
    s, e = cat_hour_window(day)
    return {'account': acct, 'start': s, 'end': e}


# =============================================================================
# Q7  Shortest transfer connection (bounds 4 and 6)
# =============================================================================
Q7_SQL_LENGTH = """
WITH RECURSIVE bfs(account_id, depth) AS (
  SELECT %(account)s::integer, 0
  UNION
  SELECT t.receiver_id, b.depth + 1
  FROM   bfs b
  JOIN   transfers t ON t.sender_id = b.account_id
  JOIN   accounts  a ON a.account_id = t.receiver_id AND a.role = 'person'
  WHERE  b.depth < %(bound)s
    AND  b.account_id <> %(dest)s
)
SELECT MIN(depth) AS min_length
FROM   bfs
WHERE  account_id = %(dest)s
HAVING MIN(depth) IS NOT NULL;
"""

Q7_SQL_PATH = """
WITH RECURSIVE bfs(account_id, depth, path_ids) AS (
  SELECT %(account)s::integer, 0,
         ARRAY[%(account)s::integer]
  UNION
  SELECT t.receiver_id, b.depth + 1,
         b.path_ids || t.receiver_id
  FROM   bfs b
  JOIN   transfers t ON t.sender_id = b.account_id
  JOIN   accounts  a ON a.account_id = t.receiver_id AND a.role = 'person'
  WHERE  b.depth < %(bound)s
    AND  NOT (t.receiver_id = ANY(b.path_ids))
    AND  b.account_id <> %(dest)s
)
SELECT path_ids, depth AS length
FROM   bfs
WHERE  account_id = %(dest)s
ORDER  BY depth
LIMIT  1;
"""

Q7_CYPHER_LENGTH = """
MATCH (src:Account {account_id: $account}),
      (dst:Account {account_id: $dest})
MATCH p = shortestPath((src)-[:TRANSFER*1..$bound]->(dst))
WHERE all(n IN nodes(p) WHERE n.role = 'person' OR n = src)
RETURN length(p) AS min_length
LIMIT 1;
"""

Q7_CYPHER_PATH = """
MATCH (src:Account {account_id: $account}),
      (dst:Account {account_id: $dest})
MATCH p = shortestPath((src)-[:TRANSFER*1..$bound]->(dst))
WHERE all(n IN nodes(p) WHERE n.role = 'person' OR n = src)
RETURN [n IN nodes(p) | n.account_id] AS path_ids, length(p) AS length
LIMIT 1;
"""

def q7_params(set_key, bound):
    acct, dest, _ = REVIEW_SETS[set_key]
    return {'account': acct, 'dest': dest, 'bound': bound}
