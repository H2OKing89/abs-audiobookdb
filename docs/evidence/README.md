# Evidence handling

Status: Reviewed for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

Store minimal sanitized fixtures and test outputs by spike ID. Add an EVD record using the evidence template. Replace real keys with synthetic sentinels before saving. Exclude authorization headers, cookies, personal account details and signed URLs. Record installed ABS version, upstream schema version/hash and environment. Do not present generated/synthetic fixtures as live API responses.
