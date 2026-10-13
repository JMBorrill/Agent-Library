# ASVS 5.0.0 Level 1 verification checklist - V6 Authentication

Generated with `python -m agentlib asvs checklist --level 1 --chapters V6`. Levels are cumulative, so a
Level 1 checklist contains only the Level 1 requirements; V6 has 13 of them. L2/L3 requirements in V6 are
recommendations at this level and are not listed.

| ID | Level | Requirement | Status | Evidence / finding |
|---|---|---|---|---|
| v5.0.0-6.1.1 | 1 | Verify that application documentation defines how controls such as rate limiting, anti-automation, and adaptive response, are used to defend against attacks such as credential stuffing and password brute force. The documentation must make clear how these controls are configured and prevent malicious account lockout. | not-verified | |
| v5.0.0-6.2.1 | 1 | Verify that user set passwords are at least 8 characters in length although a minimum of 15 characters is strongly recommended. | not-verified | |
| v5.0.0-6.2.2 | 1 | Verify that users can change their password. | not-verified | |
| v5.0.0-6.2.3 | 1 | Verify that password change functionality requires the user’s current and new password. | not-verified | |
| v5.0.0-6.2.4 | 1 | Verify that passwords submitted during account registration or password change are checked against an available set of, at least, the top 3000 passwords which match the application’s password policy, e.g. minimum length. | not-verified | |
| v5.0.0-6.2.5 | 1 | Verify that passwords of any composition can be used, without rules limiting the type of characters permitted. There must be no requirement for a minimum number of upper or lower case characters, numbers, or special characters. | not-verified | |
| v5.0.0-6.2.6 | 1 | Verify that password input fields use type=password to mask the entry. Applications may allow the user to temporarily view the entire masked password, or the last typed character of the password. | not-verified | |
| v5.0.0-6.2.7 | 1 | Verify that “paste”functionality, browser password helpers, and external password managers are permitted. | not-verified | |
| v5.0.0-6.2.8 | 1 | Verify that the application verifies the user’s password exactly as received from the user, without any modifications such as truncation or case transformation. | not-verified | |
| v5.0.0-6.3.1 | 1 | Verify that controls to prevent attacks such as credential stuffing and password brute force are implemented according to the application’s security documentation. | not-verified | |
| v5.0.0-6.3.2 | 1 | Verify that default user accounts (e.g., “root”, “admin”, or “sa”) are not present in the application or are disabled. | not-verified | |
| v5.0.0-6.4.1 | 1 | Verify that system generated initial passwords or activation codes are securely randomly generated, follow the existing password policy, and expire after a short period of time or after they are initially used. These initial secrets must not be permitted to become the long term password. | not-verified | |
| v5.0.0-6.4.2 | 1 | Verify that password hints or knowledge-based authentication (so-called “secret questions”) are not present. | not-verified | |

Every row starts as `not-verified`; a `fail` needs a finding reference and `not-applicable` a justification.
Validate the filled file with `python -m agentlib asvs check-assessment <file> --level 1 --chapters V6`.

Source: [owasp-asvs V6.1.1, p. 45]-[owasp-asvs V6.4.2, p. 49]. Requirement text: OWASP ASVS 5.0.0, (c) The OWASP Foundation, CC BY-SA 4.0.
