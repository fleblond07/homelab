import unittest
from pathlib import Path

import yaml
from ansible.plugins.filter.core import FilterModule
from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]


def role_env(role, extra=None):
    env = Environment(
        loader=FileSystemLoader(ROOT / "roles" / role / "templates"),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    filters = FilterModule().filters()
    env.filters.update({name: filters[name] for name in ("to_json", "bool", "quote", "regex_replace")})
    context = yaml.safe_load((ROOT / "roles" / role / "defaults/main.yml").read_text())
    context.update(extra or {})
    for _ in range(4):
        for key, value in context.items():
            if isinstance(value, str) and "{{" in value:
                context[key] = env.from_string(value).render(context)
    return env, context


class ForgejoTemplates(unittest.TestCase):
    def setUp(self):
        self.env, self.context = role_env("forgejo")

    def render(self):
        return yaml.safe_load(self.env.get_template("compose.yml.j2").render(self.context))

    def test_hardened_sqlite_instance_without_ssh_or_registration(self):
        service = self.render()["services"]["forgejo"]
        environment = service["environment"]
        self.assertEqual(environment["FORGEJO__database__DB_TYPE"], "sqlite3")
        self.assertEqual(environment["FORGEJO__server__DISABLE_SSH"], "true")
        self.assertEqual(environment["FORGEJO__service__DISABLE_REGISTRATION"], "true")
        self.assertEqual(environment["FORGEJO__server__ROOT_URL"], "https://git.francoisrieux.com/")
        self.assertEqual(environment["FORGEJO__service__REQUIRE_SIGNIN_VIEW"], "false")
        self.assertEqual(service["cap_drop"], ["ALL"])
        self.assertNotIn("ports", service)

    def test_cors_allows_site_origins_and_authorization_header(self):
        self.context["forgejo_cors_allowed_origins"] = ["https://a.example", "https://b.example"]
        environment = self.render()["services"]["forgejo"]["environment"]
        self.assertEqual(environment["FORGEJO__cors__ALLOW_DOMAIN"], "https://a.example,https://b.example")
        self.assertIn("Authorization", environment["FORGEJO__cors__HEADERS"].split(","))


class FrancoisRieuxTemplates(unittest.TestCase):
    def setUp(self):
        self.env, self.context = role_env("francois_rieux")

    def render(self, name):
        return self.env.get_template(name + ".j2").render(self.context)

    def test_builder_reaches_forgejo_and_web_only_serves_read_only_site(self):
        compose = yaml.safe_load(self.render("compose.yml"))
        builder = compose["services"]["builder"]
        web = compose["services"]["web"]
        self.assertEqual(builder["environment"]["REPO_URL"], "http://homelab-forgejo:3000/flavien/francoisrieux.git")
        self.assertEqual(sorted(builder["networks"]), ["forgejo", "origin"])
        self.assertEqual(web["networks"], ["origin"])
        self.assertTrue(web["read_only"])
        self.assertTrue(any(v.endswith(":/srv/site:ro") for v in web["volumes"]))
        self.assertNotIn("ports", web)
        self.assertNotIn("/var/run/docker.sock", str(compose))
        self.assertEqual(compose["networks"]["origin"]["name"], "homelab-francois-rieux")
        self.assertEqual(compose["networks"]["forgejo"]["name"], "homelab-forgejo")

    def test_token_is_escaped_for_compose(self):
        self.context["francois_rieux_repo_token"] = "abc$def"
        compose = yaml.safe_load(self.render("compose.yml"))
        self.assertEqual(compose["services"]["builder"]["environment"]["REPO_TOKEN"], "abc$$def")

    def test_caddyfile_redirects_www_and_has_no_csp(self):
        caddyfile = self.render("Caddyfile")
        self.assertIn("@redirect host www.francoisrieux.com", caddyfile)
        self.assertIn("redir @redirect https://francoisrieux.com{uri} permanent", caddyfile)
        self.assertIn(":8080 {", caddyfile)
        self.assertNotIn("Content-Security-Policy", caddyfile)

    def test_build_loop_uses_configured_branch_and_interval(self):
        self.context.update(francois_rieux_repo_branch="release", francois_rieux_poll_interval=30)
        script = self.render("build-loop.sh")
        self.assertIn("branch=release", script)
        self.assertIn("interval=30", script)
        self.assertIn('mv -T "$site/.current.tmp" "$site/current"', script)


if __name__ == "__main__":
    unittest.main()
