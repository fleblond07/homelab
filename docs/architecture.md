## List of Domains
  - wp<1-5>.local # Wordpress domains, redacted for privacy
  - flavienleblond.com
  - beer-festival.fr
  - francoisrieux.com
  - git.francoisrieux.com
  - vault.local
  - nc.local
  - ai.local
  - monitoring.local

## List of applications

- Wordpress <1-5> - Public
- Homepage - Public
- Beer Festival - Public
- François Rieux site - Public
- Forgejo - Public (hosts the François Rieux site repository and CMS login)
- Vaultwarden - Private/VPN-Protected
- NextCloud - Private/VPN-Protected
- Media Stack - Private
- AI Lab - Private
- Monitoring - Private

## External Providers

- Backup provider: Backblaze B2, using encrypted archives through the S3-compatible API.

## Alerting

- Alerting should be done through two means:
  - Emails for p2 and and below
  - Discord for p1

## Network
- Remember to disable CGNAT from the router's admin route

## Recovery

The goal of this homelab is not to turn into another full time job. Recovery should be documented and easy to do.
Backups rules are as below:
- Wordpress: 7days
- Database: 24hrs
- Email: 24hrs
