# PostgreSQL 备份说明

SQLite 开发库由应用内「创建备份」直接拷贝数据库文件。

生产 PostgreSQL 不在应用进程内调用 `pg_dump`（避免把数据库口令写进业务容器命令行）。建议：

```bash
pg_dump --format=custom --file mer.dump "$MER_DATABASE_URL"
```

与 `config/`、报告目录一起归档。恢复使用 `pg_restore` 后，再把配置与报告目录拷回。应用内恢复接口目前只自动覆盖 SQLite 文件。
