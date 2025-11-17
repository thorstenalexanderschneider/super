CREATE KEYSPACE IF NOT EXISTS jobs
WITH replication = {'class':'SimpleStrategy','replication_factor':1};

USE jobs;

CREATE TABLE IF NOT EXISTS job_articles (
    id text PRIMARY KEY,
    title text,
    category text,
    date date,
    views int
);
