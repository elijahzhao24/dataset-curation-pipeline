# Database + S3 Setup (From Scratch)

## 1) AWS setup

1. Create an S3 bucket for images.
2. Create one IAM user for S3 access.
3. Attach S3 permissions to that IAM user (`s3:ListBucket`, `s3:GetObject`, `s3:PutObject`).
4. Create an access key + secret for that IAM user.
5. Create an RDS PostgreSQL instance.
6. In the RDS security group, allow inbound `TCP 5432` from your public IP (`x.x.x.x/32`) or your network subnet.
7. Save these values: `RDS endpoint`, `port`, `master username`, `master password`.

For shared IAM keys across the team, this policy is enough (replace bucket name):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BucketList",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::my-dataset-curation-bucket"
    },
    {
      "Sid": "ObjectReadWrite",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::my-dataset-curation-bucket/*"
    }
  ]
}
```

## 2) Bootstrap PostgreSQL

Use `psql`, pgAdmin, DbGate, or another Postgres client.

Connect as master user:

```powershell
psql "host=<RDS_ENDPOINT> port=5432 dbname=postgres user=<MASTER_USER> password=<MASTER_PASSWORD> sslmode=require"
```

Create app user + database:

```sql
CREATE USER app_user WITH PASSWORD 'strong_password';
CREATE DATABASE dataset_curation OWNER app_user;
```

## 3) Create schema

Reconnect as `app_user` to `dataset_curation`, then run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS public.image_vectors (
  id BIGSERIAL PRIMARY KEY,
  s3_bucket TEXT NOT NULL,
  s3_key TEXT NOT NULL,
  embedding_version TEXT NOT NULL DEFAULT 'dinov2_vitb14',
  embedding vector(768) NOT NULL,
  CONSTRAINT image_vectors_s3_unique UNIQUE (s3_bucket, s3_key)
);

CREATE INDEX IF NOT EXISTS idx_image_vectors_embedding_hnsw
ON public.image_vectors
USING hnsw (embedding vector_cosine_ops);
```

## 4) Environment variables

Set these in `.env`:

```env
AWS_S3_BUCKET=my-dataset-curation-bucket
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=

PGHOST=<RDS_ENDPOINT>
PGPORT=5432
PGDATABASE=dataset_curation
PGUSER=app_user
PGPASSWORD=strong_password
PGSSLMODE=require
```

Quick S3 check:

```powershell
python -c "import boto3, os; s=boto3.client('s3', region_name=os.getenv('AWS_REGION')); s.head_bucket(Bucket=os.getenv('AWS_S3_BUCKET')); print('S3 OK')"
```
