-- One trace per ticket (the MLOps course, Module 3).
-- The request that created a ticket saves its request ID and its trace context (the W3C
-- traceparent header) with the job. The worker continues the same trace, and its log lines
-- carry the same request ID, so the API's and the worker's telemetry join up.
ALTER TABLE jobs ADD COLUMN request_id text;
ALTER TABLE jobs ADD COLUMN trace_context text;
