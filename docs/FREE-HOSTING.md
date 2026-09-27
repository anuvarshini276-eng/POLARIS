# POLARIS: Render Free + Supabase Free

Status: configuration prepared and local tests available. No cloud project has been connected or deployed. Live PostgreSQL, S3 and Docker integration still needs verification after connection.

## 1. Create your free Supabase project

Sign in at https://supabase.com/dashboard using GitHub. Create a dedicated project in a Free organization. Save its database password privately. Do not select a paid plan.

In the project Data API settings, disable the Data API: this app uses its own FastAPI backend and a direct database connection. App migrations also enable row-level security without public policies. The backend connects as the database owner. Do not expose application tables or add public policies.

In Storage, create a PRIVATE bucket named polaris. In the Storage S3 configuration, generate an Access Key ID and Secret Access Key, and copy the endpoint and region. These are S3 credentials, not the Supabase publishable/anon key. Keep the bucket private; file permissions are checked by POLARIS before downloads.

Use Connect > Session pooler to copy the IPv4 PostgreSQL connection URI on port 5432. Replace the password placeholder with the actual database password, URL-encoding special characters. Add ?sslmode=require (or &sslmode=require if it already has query parameters). The application accepts postgresql:// or postgresql+psycopg://. Do not use the transaction pooler for this setup.

## 2. Upload the updated source

Extract the latest POLARIS-source.zip and upload its contents into the existing POLARIS-source directory on GitHub. Replace older files, including render.yaml. Do not upload credentials or local data.

## 3. Connect Render Free

Sign in at https://dashboard.render.com using GitHub. Choose New > Blueprint, connect POLARIS, and enter POLARIS-source/render.yaml as the Blueprint Path.

Render will prompt for these private environment variables:

| Variable | Value |
| --- | --- |
| DATABASE_URL | Supabase Session pooler URI with your password and sslmode=require |
| S3_ENDPOINT | Endpoint copied from Supabase S3 settings |
| S3_REGION | Region copied from Supabase S3 settings |
| S3_ACCESS_KEY | Generated S3 Access Key ID |
| S3_SECRET_KEY | Generated S3 Secret Access Key |
| ADMIN_EMAIL | Email to use for your POLARIS administrator login |
| ADMIN_PASSWORD | A new private password of at least 12 characters |

The Blueprint supplies S3_BUCKET=polaris, STORAGE_PROVIDER=s3, mock AI providers, DEMO_MODE=false, and a generated JWT_SECRET. Retain JWT_SECRET across redeploys so sessions remain valid. These variables belong only in Render's backend environment, never GitHub, frontend code, screenshots or chat.

Confirm the service is Free, with no disk and no paid database. Deploy. The first boot migrates tables, creates synthetic content and your administrator. ADMIN_EMAIL and ADMIN_PASSWORD apply only when the database has no users; later restarts do not reset passwords. Ordinary visitors register through POLARIS, not Supabase Auth.

## 4. Verify persistence

Open the HTTPS URL supplied by Render. Log in as administrator, create a researcher account, upload a small text document, and wait for processing. Restart the Render service. Verify both accounts still log in, the document is searchable and downloadable, and previously private documents remain private. Inspect deployment logs for errors without sharing secrets.

The sample research is still synthetic and AI is still mock mode; no external AI subscription or API key is used.

## Free-plan limits

Render sleeps after 15 minutes idle and has monthly usage limits. Supabase Free currently includes 500 MB database and 1 GB file storage and may pause after a week of low activity. Resume a paused project through its dashboard. This is suitable for a small month-long demonstration within quotas, not guaranteed continuous availability. Keep the accounts on free plans and do not enable paid upgrades. Cloud storage preserves records across Render restarts; it does not replace backups.

Official references:
- https://render.com/docs/free
- https://supabase.com/docs/guides/platform/billing-on-supabase
- https://supabase.com/docs/guides/platform/free-project-pausing
- https://supabase.com/docs/guides/storage/s3/authentication
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://supabase.com/docs/guides/api/securing-your-api
