## List of Domains
  - wp<1-5>.local # Wordpress domains, redacted for privacy
  - flavienleblond.com
  - beer-festival.fr
  - vault.local
  - nc.local
  - ai.local
  - monitoring.local

## List of applications

- Wordpress <1-5> - Public
- Homepage - Public
- Beer Festival - Public
- Vaultwarden - Private/VPN-Protected
- NextCloud - Private/VPN-Protected
- Media Stack - Private
- AI Lab - Private
- Monitoring - Private

## External Providers

- S3 Backup provider: [OVH](https://www.ovhcloud.com/fr/public-cloud/prices/#439)

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

