# François Rieux site

`francoisrieux.com` is a static Astro site edited by François through Sveltia CMS
(French UI) at `https://francoisrieux.com/admin/`. Content lives in a Forgejo
repository on the homelab; every commit (from the CMS or from a developer) is
picked up and published automatically.

```
François ──► francoisrieux.com/admin (Sveltia CMS, static JS)
               │ OAuth (PKCE) + API calls, CORS-allowed
               ▼
           git.francoisrieux.com ── homelab-forgejo:3000 (Forgejo, SQLite)
               │ polled every 60 s over the homelab-forgejo network
               ▼
           homelab-francois-rieux-builder (npm ci && npm run build)
               │ dist/ → /srv/homelab/data/francois-rieux/site/releases/<sha>, `current` symlink swapped atomically
               ▼
           homelab-francois-rieux-web:8080 (Caddy, read-only) ◄── Cloudflare Tunnel
```

There is no Docker socket mount and no Actions runner. A failed build leaves the
previous release online and is not retried until a new commit lands; check
`docker logs homelab-francois-rieux-builder`.

## Paths

| What | Path |
| --- | --- |
| Forgejo data (repos, SQLite, `custom/conf/app.ini`, generated secrets) | `/srv/homelab/data/forgejo` |
| Site releases and `current` symlink | `/srv/homelab/data/francois-rieux/site` |
| Builder clone and npm cache | `/srv/homelab/data/francois-rieux/work` |
| Compose files | `/srv/homelab/compose/forgejo`, `/srv/homelab/compose/francois-rieux` |

## 1. Enable and deploy

In `inventories/production/host_vars/homelab.yml`:

```yaml
forgejo_enabled: true
francois_rieux_enabled: true
```

Optional overrides: `forgejo_host`, `forgejo_cors_allowed_origins`,
`francois_rieux_repo_owner` (default `flavien`), `francois_rieux_repo_name`,
`francois_rieux_repo_branch`, `francois_rieux_poll_interval`.

Optional Vault key, only if the repository is private:

```yaml
francois_rieux_repo_token: <Forgejo token with read:repository scope>
```

Deploy:

```bash
ansible-playbook playbooks/forgejo.yml
ansible-playbook playbooks/francois_rieux.yml --ask-vault-pass
ansible-playbook playbooks/cloudflare_tunnel.yml --ask-vault-pass
```

Both roles depend on `homelab_networks`, which creates the networks. The tunnel must be redeployed once so `cloudflared` joins the
`homelab-forgejo` and `homelab-francois-rieux` networks.

## 2. Cloudflare Tunnel public hostnames

Add the domain to Cloudflare, then in Zero Trust → Networks → Tunnels → the
homelab tunnel → Public hostnames:

| Hostname | Service |
| --- | --- |
| `francoisrieux.com` | `http://homelab-francois-rieux-web:8080` |
| `www.francoisrieux.com` | `http://homelab-francois-rieux-web:8080` (Caddy redirects to the apex) |
| `git.francoisrieux.com` | `http://homelab-forgejo:3000` |

## 3. First-run Forgejo setup

Registration is disabled and the installer is locked; accounts are created
from the CLI.

```bash
docker exec -it homelab-forgejo forgejo admin user create \
  --admin --username flavien --email <your email> --random-password
docker exec -it homelab-forgejo forgejo admin user create \
  --username francois --email <françois email> --random-password --must-change-password
```

Then, signed in as `flavien` on `https://git.francoisrieux.com`:

1. Create the repository `flavien/francoisrieux` (default branch `main`).
2. Add `francois` as a collaborator with **Write** access.
3. Push the site: `git remote add origin https://git.francoisrieux.com/flavien/francoisrieux.git && git push -u origin main`.
4. Settings → Applications → **Create OAuth2 application**:
   - Name: `Sveltia CMS`
   - Redirect URI: `https://francoisrieux.com/admin/`
   - **Confidential client: unchecked** (PKCE public client)
5. Copy the client ID into the site repository, `public/admin/config.yml`:

```yaml
backend:
  name: gitea
  repo: flavien/francoisrieux
  base_url: https://git.francoisrieux.com
  api_root: https://git.francoisrieux.com/api/v1
  app_id: <client id>
```

Sveltia requires Forgejo 12 or later; CORS for the site origins is configured
by the role (`forgejo_cors_allowed_origins`).

## 4. DNS move

1. Lower the TTL at the current registrar/host a day before.
2. Add `francoisrieux.com` to Cloudflare and switch the registrar nameservers
   to Cloudflare (or, if the zone stays elsewhere, CNAME the three hostnames to
   `<tunnel-id>.cfargotunnel.com`).
3. Check `https://francoisrieux.com`, the `www` redirect, and an end-to-end CMS
   edit before cancelling the old hosting.

## Backups

Forgejo data is not yet covered by the Backblaze backups (the existing backup
role is WordPress-specific). The site content is plain git, so a push mirror
(Forgejo repository settings → Mirror settings) to another remote is a cheap
interim safeguard.
