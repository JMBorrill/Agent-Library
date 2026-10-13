-- Weekly contact export (synthetic, fixed version)
SELECT c.id, c.email, c.phone
FROM crm_contacts c
WHERE c.tenant_id = :tenant_id
  AND c.created_at > now() - interval '7 days';
