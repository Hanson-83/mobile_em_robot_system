-- PostgreSQL 生产库测量表按月分区草案。
-- MVP 开发与 CI 使用 SQLite，不执行本脚本。
-- 触发评估 Timescale 的门槛见 doc/spec/ds.md §5.2。

CREATE TABLE IF NOT EXISTS measurements (
  id varchar(64) PRIMARY KEY,
  idempotency_key varchar(128) NOT NULL UNIQUE,
  task_id varchar(64),
  point_id varchar(64),
  robot_id varchar(64),
  device_id varchar(64),
  metric varchar(64) NOT NULL,
  value double precision,
  unit varchar(32),
  quality varchar(16) NOT NULL,
  ts timestamptz NOT NULL
) PARTITION BY RANGE (ts);

-- 示例：按月增加分区，试点前由运维按保留期执行。
-- CREATE TABLE measurements_2026_09 PARTITION OF measurements
--   FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
