# ASVS Level 1 checklist - Authentication

| ID | Level | Requirement | Status |
|---|---|---|---|
| V6.1.1 | 1 | Verify that application documentation defines how controls such as rate limiting, anti-automation, and adaptive response, are used to defend against attacks such as credential stuffing and password brute force. The documentation must make clear how these controls are configured and prevent malicious account lockout. | not-verified |
| V6.2.1 | 1 | Verify that user set passwords are at least 8 characters in length although a minimum of 15 characters is strongly recommended. | not-verified |
| V6.2.2 | 1 | Verify that users can change their password. | not-verified |
| V6.2.3 | 1 | Verify that password change functionality requires the user’s current and new password. | not-verified |
| V6.2.4 | 1 | Verify that passwords submitted during account registration or password change are checked against an available set of, at least, the top 3000 passwords which match the application’s password policy, e.g. minimum length. | not-verified |
| V6.2.5 | 1 | Verify that passwords of any composition can be used, without rules limiting the type of characters permitted. There must be no requirement for a minimum number of upper or lower case characters, numbers, or special characters. | not-verified |
| V6.2.6 | 1 | Verify that password input fields use type=password to mask the entry. Applications may allow the user to temporarily view the entire masked password, or the last typed character of the password. | not-verified |
| V6.2.7 | 1 | Verify that “paste”functionality, browser password helpers, and external password managers are permitted. | not-verified |
| V6.2.8 | 1 | Verify that the application verifies the user’s password exactly as received from the user, without any modifications such as truncation or case transformation. | not-verified |
| V6.2.9 | 1 | Verify that passwords of at least 64 characters are permitted. | not-verified |
| V6.3.3 | 1 | Verify that multi-factor authentication is used. | not-verified |
| V2.1.7 | 1 | Verify that passwords submitted are checked against breached password lists. | not-verified |

This checklist covers ASVS Level 1 authentication. Mark each item pass or fail.
