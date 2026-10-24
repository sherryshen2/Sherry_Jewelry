"""Upload only changed storefront code; keep media in Hangar's asset store."""
import json
import mimetypes
import pathlib
import re
import sys
import urllib.error
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.agents/skills/hangar-app-developer/scripts'))
from hangar_app import Client, read_wingman_token

BASE = 'https://wingman.shopee.io/hangar'
APP = '5e8740f57d03b23'
DIST = ROOT / 'sherry-jewelry-site/dist'
STATE = ROOT / 'hangar-jewelry-shop/.hangar/asset-release.json'
client = Client(BASE, read_wingman_token(), '')


def upload(name, content):
    boundary = 'sherry-' + uuid.uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="assets"; '
            f'filename="{name}"\r\nContent-Type: '
            f'{mimetypes.guess_type(name)[0] or "application/octet-stream"}\r\n\r\n').encode()
    body += content.encode() + f'\r\n--{boundary}--\r\n'.encode()
    request = urllib.request.Request(
        f'{BASE}/api/external/hangar/apps/{APP}/assets', data=body, method='POST',
        headers={'Authorization': f'Bearer {client.token}',
                 'Content-Type': f'multipart/form-data; boundary={boundary}',
                 'Origin': 'https://wingman.shopee.io', 'Referer': BASE + '/'})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
            print(name, 'HTTP', response.status, 'uploaded:', result.get('uploaded', []))
    except urllib.error.HTTPError as error:
        print(name, 'HTTP', error.code, client.redact(error.read().decode()))
        raise SystemExit(1)
    # Resolve the stored filename from a fresh manifest instead of assuming a prefix.
    assets = client.request('GET', f'/apps/{APP}/assets')['assets']
    candidates = [item for item in assets if item.endswith('_' + name)]
    previous = set(manifest.values())
    added = [item for item in candidates if item not in previous]
    if len(added) != 1:
        raise RuntimeError(f'Cannot identify uploaded {name}: {added}')
    return added[0]


assets = client.request('GET', f'/apps/{APP}/assets')['assets']
manifest = {}
for path in DIST.rglob('*'):
    if not path.is_file():
        continue
    candidates = [a for a in assets if a.endswith('_' + path.name)]
    if candidates:
        manifest[path.relative_to(DIST).as_posix()] = candidates[-1]


def rewrite(content):
    for relative, stored in sorted(manifest.items(), key=lambda item: -len(item[0])):
        content = re.sub(r'''(['"])(?:\./)?''' + re.escape(relative) + r'''\1''',
                         lambda match: match[1] + './' + stored + match[1], content)
    return content


if __name__ == '__main__':
    for name in ['engines.js', 'app.js']:
        manifest[name] = upload(name, rewrite((DIST / name).read_text()))
        STATE.write_text(json.dumps(manifest, indent=2) + '\n')
    html = (DIST / 'index.html').read_text().replace(
        '<link rel="stylesheet" href="style.css">',
        '<style>' + (DIST / 'style.css').read_text() + '</style>')
    manifest['index.html'] = upload('index.html', rewrite(html))
    STATE.write_text(json.dumps(manifest, indent=2) + '\n')
    print('Storefront asset:', manifest['index.html'])
