# INSTALL
pip3 install mysql-connector
pip3 install python-dateutil



# IMPORTANT QUERIES

```sql
-- get databases size 
SELECT table_schema AS "Database", ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS "Size (MB)" FROM information_schema.TABLES GROUP BY table_schema;
-- create index numero do processo
CREATE  INDEX numeroProcesso ON stagging_processed_mags(numero);
``` 