# Code review: booking service (synthetic, deliberately defective record)

Looks mostly fine.

| Severity | Aspect | Location | Comment |
|---|---|---|---|
| Required | security | booking_service.py | Secret in code. |
| | functionality | src/scheduling/booking_service.py:78 | Bare except hides calendar sync failures, so bookings silently go missing. |
| Major | vibes | line 12 | why would you write it like this |
