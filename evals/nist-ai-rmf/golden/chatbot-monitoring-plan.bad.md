# Monitoring plan - Ask Aurora

## Monitoring

| Metric | Threshold | Owner |
|---|---|---|
| Accuracy | 95% (NIST requires at least 95% accuracy for customer-facing AI) | QA |
| Complaints | n/a | Ops |

We monitor production behaviour (MEASURE 2.4) and log incidents (MANAGE 4.3).

## Incident handling

Incidents are raised with the vendor, who will fix the model. The chatbot stays online during
investigation to avoid disrupting customers. See MANAGE 5.1 for vendor management.
