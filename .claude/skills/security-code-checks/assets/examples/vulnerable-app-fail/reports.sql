-- Weekly contact export (synthetic, deliberately vulnerable)
SELECT c.id, c.email, c.phone
FROM crm_contacts c
WHERE c.created_at > now() - interval '7 days';
