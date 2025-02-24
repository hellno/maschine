CREATE TABLE public.builds (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id),
  vercel_build_id text,       -- optional Vercel build identifier
  status text NOT NULL,       -- e.g. queued, running, success, failed
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,    -- null until complete
  logs text,                  -- aggregated build logs or pointer to external storage
  meta jsonb,                 -- any additional metadata (error codes, durations, etc.)
  CONSTRAINT builds_pkey PRIMARY KEY (id)
);