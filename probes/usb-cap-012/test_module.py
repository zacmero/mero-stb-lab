import subprocess
from pathlib import Path


def test_module_completes_when_local_uri_apis_throw():
    module = Path(__file__).parents[2] / "web" / "app-hub-module.js"
    check = f"""
const fs = require('fs');
eval(fs.readFileSync({str(module)!r}, 'utf8'));
const reports = [];
global.XMLHttpRequest = function () {{ throw new Error('blocked'); }};
global.getURL = function () {{ throw new Error('blocked'); }};
global.setTimeout = function (fn) {{ fn(); return 1; }};
global.clearTimeout = function () {{}};
global.document = {{ documentElement: {{ addEventListener: function () {{}} }} }};
meroHubModule({{
  report: function (name, value) {{ reports.push([name, String(value)]); }},
  setStatus: function () {{}},
  setDetail: function () {{}}
}});
if (!reports.some(function (item) {{ return item[0] === 'usb.probe.complete' && item[1] === 'yes'; }})) process.exit(1);
if (reports.filter(function (item) {{ return item[0] === 'usb.cycle.complete'; }}).length !== 12) process.exit(2);
"""
    subprocess.run(["node", "-e", check], check=True)
