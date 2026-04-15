# DB + S3 Access Setup (Org Users)

Use this file for normal team onboarding.

- Admin-only infra/bootstrap tasks moved to [SETUPadmin.md](SETUPadmin.md).
- DB password (`PGPASSWORD`) should come from NordPass (or your team password manager).
- Auth supports both interim access-key mode and SSO mode.

## 1) Before You Start

Get these values from your admin/handoff docs:

- `AWS_S3_BUCKET`
- `AWS_REGION`
- `PGHOST`
- `PGPORT`
- `PGDATABASE`
- `PGUSER` (usually `app_user`)
- `PGPASSWORD` (from NordPass/password sharer)

## 2) Choose AWS Auth Mode

### 2.1 Mode A: Interim access keys (before SSO is set up)

Use this if your org has not finished IAM Identity Center setup yet.

```env
AWS_S3_BUCKET=<prod_bucket_name>
AWS_REGION=<aws_region>

AWS_ACCESS_KEY_ID=<your_key>
AWS_SECRET_ACCESS_KEY=<your_secret>
AWS_SESSION_TOKEN=<leave blank>
AWS_PROFILE=<leave blank>

PGHOST=<rds_endpoint>
PGPORT=5432
PGDATABASE=dataset_curation
PGUSER=app_user
PGPASSWORD=<from_nordpass>
PGSSLMODE=require
```

Notes:

- Use your own credentials only.
- Do not share one access key across teammates.

### 2.2 Mode B: SSO profile (target state)

Use this after IAM Identity Center is ready.

1. Configure SSO profile:

```powershell
aws configure sso
```

2. Log in:

```powershell
aws sso login --profile <ORG_SSO_PROFILE>
aws sts get-caller-identity --profile <ORG_SSO_PROFILE>
```

3. Use this `.env`:

```env
AWS_S3_BUCKET=<prod_bucket_name>
AWS_REGION=<aws_region>
AWS_PROFILE=<ORG_SSO_PROFILE>

# keep empty when using SSO
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=

PGHOST=<rds_endpoint>
PGPORT=5432
PGDATABASE=dataset_curation
PGUSER=app_user
PGPASSWORD=<from_nordpass>
PGSSLMODE=require
```

## 3) Connectivity Checks (Works for Both Modes)

These checks work with either:

- access keys in env, or
- valid SSO login + `AWS_PROFILE`

S3 check:

```powershell
python -c "import os,boto3; from config import Config; cfg=Config.from_env(); p=(os.getenv('AWS_PROFILE') or '').strip() or None; s=boto3.session.Session(profile_name=p, region_name=cfg.aws_region).client('s3'); s.head_bucket(Bucket=cfg.bucket_name); print('S3 OK')"
```

DB check:

```powershell
python -c "import psycopg; from config import Config; cfg=Config.from_env(); c=psycopg.connect(cfg.db_url); cur=c.cursor(); cur.execute('SELECT 1'); print('DB OK', cur.fetchone()[0]); c.close()"
```

CLI check:

```powershell
python cli.py --help
```

## 4) Migration from Access Keys to SSO

When SSO is ready:

1. Run `aws configure sso`.
2. Run `aws sso login --profile <ORG_SSO_PROFILE>`.
3. Update `.env` to set `AWS_PROFILE` and clear `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`.
4. Re-run connectivity checks.
