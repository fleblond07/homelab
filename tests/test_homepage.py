"""Render the dashboard with representative inventory, without Vault or a host."""

import unittest
from pathlib import Path

import yaml
from ansible.plugins.filter.core import FilterModule
from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / "roles/homepage"


class HomepageTemplates(unittest.TestCase):
    def setUp(self):
        self.env = Environment(
            loader=FileSystemLoader(ROLE / "templates"),
            undefined=StrictUndefined,
        )
        filters = FilterModule().filters()
        self.env.filters.update({name: filters[name] for name in ("to_json", "bool", "regex_replace")})
        self.context = yaml.safe_load((ROLE / "defaults/main.yml").read_text())
        self.context.update(homepage_hostname="homelab.example.ts.net")
        # Resolve paths declared in role defaults as Ansible would.
        for _ in range(3):
            for key, value in self.context.items():
                if isinstance(value, str) and "{{" in value:
                    self.context[key] = self.env.from_string(value).render(self.context)

    def render(self, name):
        return yaml.safe_load(self.env.get_template(name + ".j2").render(self.context))

    def test_inventory_generates_cards_without_disclosing_credentials(self):
        self.context.update(
            wordpress_sites=[
                {"name": "First: Blog", "host": "first.example.com", "database_password": "SECRET"},
                {"name": "second", "hosts": ["second.example.com", "www.second.example.com"]},
            ],
            beer_festival_enabled=True,
            beer_festival_api_url="https://api.example.com/",
            beer_festival_allowed_origins=["https://festival.example.com"],
        )
        services = self.render("services.yaml")
        self.assertEqual(len(services[0]["WordPress"]), 2)
        self.assertEqual(services[0]["WordPress"][0]["First: Blog"]["siteMonitor"], "https://first.example.com")
        apps = services[1]["Applications"]
        self.assertEqual(len(apps), 3)
        self.assertEqual(apps[1]["Beer Festival API"]["siteMonitor"], "https://api.example.com/health")
        self.assertNotIn("SECRET", str(services))

    def test_standalone_defaults_and_disabled_optional_app(self):
        services = self.render("services.yaml")
        self.assertEqual(len(services), 1)
        self.assertEqual(len(services[0]["Applications"]), 1)
        self.context["beer_festival_enabled"] = True
        self.assertEqual(len(self.render("services.yaml")[0]["Applications"]), 3)

    def test_overrides_and_extra_health_endpoint(self):
        self.context.update(
            wordpress_sites=[{"name": "blog", "host": "blog.example.com", "homepage_monitor_url": "https://blog.example.com/health"}],
            flb_dev_hosts=["portfolio.example.com"],
            homepage_extra_services=[{"name": "Go API", "href": "https://go.example.com", "monitor_url": "https://go.example.com/health"}],
        )
        services = self.render("services.yaml")
        self.assertEqual(services[0]["WordPress"][0]["blog"]["siteMonitor"], "https://blog.example.com/health")
        apps = services[1]["Applications"]
        self.assertEqual(apps[0]["flb.dev"]["href"], "https://portfolio.example.com")
        self.assertEqual(apps[-1]["Go API"]["siteMonitor"], "https://go.example.com/health")

    def test_host_metrics_disk_mounts_and_private_access(self):
        self.context["homepage_disks"].append({"label": "Data", "path": "/mnt/data"})
        compose = self.render("compose.yml")
        homepage = compose["services"]["homepage"]
        glances = compose["services"]["glances"]
        self.assertEqual(homepage["ports"], ["127.0.0.1:3000:3000"])
        hosts = homepage["environment"]["HOMEPAGE_ALLOWED_HOSTS"].split(",")
        self.assertIn("homelab.example.ts.net", hosts)
        self.assertNotIn("*", hosts)
        self.assertNotIn("ports", glances)
        self.assertTrue(compose["networks"]["metrics"]["internal"])
        self.assertEqual(glances["pid"], "host")
        self.assertNotIn("docker.sock", str(compose))
        widgets = self.render("widgets.yaml")
        self.assertTrue(widgets[0]["glances"]["cpu"])
        self.assertTrue(widgets[0]["glances"]["mem"])
        for index, widget in enumerate(widgets[1:]):
            mount = widget["resources"]["disk"]
            source = self.context["homepage_disks"][index]["path"].rstrip("/") + "/.homepage-disk-metrics"
            self.assertIn(source + ":" + mount + ":ro", homepage["volumes"])
            self.assertTrue(widget["resources"]["expanded"])


if __name__ == "__main__":
    unittest.main()
