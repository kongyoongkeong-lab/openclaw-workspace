# Secret Policy

## Forbidden Secrets in Git
Never commit to Git:
- .env files
- *.pem files
- *.key files
- *.token files
- Discord bot tokens
- Discord webhook URLs
- GitHub tokens
- API keys
- Passwords
- Private keys

## Secret Scanning
Enable GitHub secret scanning for:
- Private repositories
- Pull requests
- Branches
- Main branches

## Runtime Verifier
All code must pass:
1. Python syntax check
2. YAML validity check
3. Forbidden file check
4. Secret scan
5. Runtime verifier
6. Render policy test
7. Context manager test
8. Discord router test (if changed)

## Secret Detection Rules
- Check for base64-encoded secrets
- Check for hardcoded API keys
- Check for password patterns
- Check for JWT tokens
- Check for AWS keys
- Check for database credentials

## Remediation
If secret is detected:
1. Rotate immediately
2. Revoke access
3. Audit affected systems
4. Update policy
5. Document incident
