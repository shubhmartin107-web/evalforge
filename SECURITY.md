# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in EvalForge, please report it privately by emailing security@anthropic.com.

Please do **not** report security vulnerabilities through public GitHub issues.

## What to Expect

We will acknowledge receipt of your report within 48 hours and provide an initial assessment within 5 business days.

## Security Best Practices

1. **Never commit API keys or secrets** to the repository. Use `.env` files (listed in `.gitignore`).
2. **Environment variable blocklist**: `capture_env_snapshot()` automatically filters out env vars containing `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, or `API` (case-insensitive).
3. **SQL injection prevention**: All user inputs use parameterized queries. Do not use raw string interpolation in SQL queries.
4. **Keep dependencies updated**: Run `pip-audit` or `pip install --upgrade` on your dependencies regularly.
