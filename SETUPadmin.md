# Production Admin Setup (One-Time)

Use this file for admin-only tasks. Most teammates should use [SETUPDB.md](SETUPDB.md) instead.

## 1) When to Run This

Run this only if:

- production bucket/DB are not created yet
- you are rotating DB credentials
- you are migrating auth from access keys to SSO

If prod infra already exists, teammates do not re-run this.

## 2) Provision Production Infra

### 2.1 S3 bucket

1. Create production S3 bucket.
2. Enable bucket encryption (SSE-S3 or SSE-KMS).
3. Save `AWS_S3_BUCKET`, `AWS_REGION`.

### 2.2 RDS PostgreSQL

1. Create production PostgreSQL RDS.
2. Restrict inbound `TCP 5432` in security group to approved org IP ranges.
3. Save `PGHOST`, `PGPORT`, master username/password.

## 3) Bootstrap Database

Connect as master user:

```powershell
psql "host=<RDS_ENDPOINT> port=5432 dbname=postgres user=<MASTER_USER> password=<MASTER_PASSWORD> sslmode=require"
```

create schema:

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

## 4) Secrets and Sharing

Store `PGPASSWORD` for `app_user` in NordPass (or your team password manager).

- At least 2 maintainers should have access.
- Do not put DB password in git/docs/chat.

## 5) IAM Access Modes

### 5.1 Interim mode (before SSO is ready)

- Teammates can use their own AWS access keys if they already have admin/required permissions.
- Do not share one key across the team.

### 5.2 Target mode (after SSO is ready)

1. In IAM Identity Center, create permission set/role for this pipeline.
2. Minimum S3 permissions:
   - `s3:ListBucket` on `arn:aws:s3:::<bucket>`
   - `s3:GetObject`, `s3:PutObject` on `arn:aws:s3:::<bucket>/*`
3. Assign permission set to a group (not per-user where possible).
4. Share AWS account ID and SSO profile naming convention with team.
