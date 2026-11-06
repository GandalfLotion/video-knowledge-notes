"""Persistent user-authorized browser login and existing Bilibili captions.

No media download, cloud API, cookie export, or automatic authentication.
"""
import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit, parse_qs, urlencode
import urllib.request

SITES = {'bilibili': 'https://www.bilibili.com/',
         'xiaohongshu': 'https://www.xiaohongshu.com/',
         'douyin': 'https://www.douyin.com/'}


class Stop(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def preferred_channel(root, site, explicit=None):
    if explicit:
        return explicit
    try:
        value = json.loads((root / 'preferences' / f'{site}.json').read_text(encoding='utf-8'))
        channel = value.get('last_successful_channel')
        return channel if channel in ('chrome', 'msedge', 'chromium') else None
    except (OSError, ValueError, AttributeError):
        return None


def remember_channel(root, site, channel):
    # Only non-secret preferences; a failed write must not invalidate saved captions.
    try:
        folder = root / 'preferences'
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f'{site}.json'
        temporary = folder / f'{site}.{os.getpid()}.tmp'
        temporary.write_text(json.dumps({'last_successful_channel': channel or 'chromium'}), encoding='utf-8')
        temporary.replace(target)
        return True
    except OSError:
        return False


def identify(url):
    if re.fullmatch(r'BV[A-Za-z0-9]{10}', url):
        return url, 1
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('www.bilibili.com', 'bilibili.com', 'm.bilibili.com'):
        raise Stop('unsupported_platform', '此脚本仅实现B站完整BV链接；其他平台需要适配。')
    match = re.fullmatch(r'/video/(BV[A-Za-z0-9]{10})/?', parsed.path)
    try:
        part = int(parse_qs(parsed.query).get('p', ['1'])[0])
    except ValueError:
        part = 0
    if not match or part < 1:
        raise Stop('invalid_input', '视频编号或分P无效。')
    return match[1], part


def select_track(data):
    tracks = data.get('subtitle', {}).get('subtitles', [])
    tracks = [t for t in tracks if re.search(r'(^|-)zh($|-)', t.get('lan', '').lower()) or '中文' in t.get('lan_doc', '')]
    if data.get('need_login_subtitle'):
        raise Stop('login_required', '平台要求登录后获取字幕。')
    if not tracks:
        if not data.get('login_mid'):
            raise Stop('login_required', '尚未确认登录；不能判断是否无中文字幕。')
        raise Stop('no_chinese_subtitles', '已登录接口未提供中文字幕轨道。')
    available = [t for t in tracks if t.get('subtitle_url')]
    if not available:
        raise Stop('invalid_subtitle', '中文字幕轨道没有可读取地址。')
    return min(available, key=lambda t: (
        not any(s in t.get('lan', '').lower() for s in ('hans', 'zh-cn')),
        t.get('lan', '').startswith('ai-')))


def simplified(text):
    if os.name == 'nt':
        fn = ctypes.windll.kernel32.LCMapStringW
        # UTF-16 count comes from Windows; -1 includes the terminating null.
        size = fn(0x0804, 0x02000000, text, -1, None, 0)
        if size:
            buf = ctypes.create_unicode_buffer(size)
            if fn(0x0804, 0x02000000, text, -1, buf, size):
                return buf.value
    try:
        from opencc import OpenCC
    except ImportError:
        raise Stop('simplifier_required', '需要OpenCC才能保证简体输出。')
    return OpenCC('t2s').convert(text)


def normalize(body, duration):
    if not isinstance(body, list):
        raise Stop('invalid_subtitle', '字幕格式不正确。')
    rows = []
    for row in body:
        try:
            start, end = float(row['from']), float(row['to'])
            text = row['content'].strip()
        except (KeyError, ValueError, TypeError, AttributeError):
            raise Stop('invalid_subtitle', '字幕缺少有效文字或时间戳。')
        if not all(math.isfinite(x) for x in (start, end)) or not 0 <= start < end <= duration + 5:
            raise Stop('invalid_subtitle', '字幕时间戳与视频分P不符。')
        if text:
            rows.append({'from': start, 'to': end, 'content': simplified(text)})
    if not rows:
        raise Stop('invalid_subtitle', '字幕正文为空。')
    return sorted(rows, key=lambda row: row['from'])


def timestamp(seconds):
    value = round(seconds * 1000)
    hours, value = divmod(value, 3600000)
    minutes, value = divmod(value, 60000)
    seconds, millis = divmod(value, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{millis:03}'


def acquire(get_json, bvid, part):
    def api(path, params):
        payload = get_json('https://api.bilibili.com' + path + '?' + urlencode(params))
        if payload.get('code') != 0:
            status = 'login_required' if payload.get('code') == -101 else 'request_failed'
            raise Stop(status, '平台API拒绝或未完成请求；不代表无字幕。')
        return payload.get('data') or {}
    view = api('/x/web-interface/view', {'bvid': bvid})
    pages = view.get('pages', [])
    if part > len(pages):
        raise Stop('invalid_input', '指定分P不存在。')
    page = pages[part - 1]
    params = {'bvid': bvid, 'aid': view['aid'], 'cid': page['cid']}
    try:
        player = api('/x/player/wbi/v2', params)
    except Stop as exc:
        if exc.status != 'request_failed':
            raise
        player = api('/x/player/v2', params)
    track = select_track(player)
    url = track['subtitle_url']
    if url.startswith('//'):
        url = 'https:' + url
    parsed = urlsplit(url)
    host = parsed.hostname or ''
    if parsed.scheme != 'https' or not any(host == domain or host.endswith('.' + domain) for domain in ('hdslb.com', 'bilibili.com', 'bilivideo.com')):
        raise Stop('invalid_subtitle', '字幕地址域名不受支持。')
    rows = normalize(get_json(url).get('body'), float(page['duration']))
    return {'schema': 1, 'bvid': bvid, 'part': part, 'cid': page['cid'],
            'title': view.get('title'), 'author': view.get('owner', {}).get('name'),
            'duration': page['duration'], 'language': track.get('lan'),
            'source_url': f'https://www.bilibili.com/video/{bvid}/?p={part}',
            'source_type': 'platform_subtitles', 'segments': rows}


def cached(out, bvid, part):
    target = out / 'subtitle.json'
    if not target.exists():
        if any((out / name).exists() for name in ('subtitle.txt', 'subtitle.srt')):
            raise Stop('output_conflict', '目标目录已有其他字幕，请换目录。')
        return None
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
        if data['bvid'] != bvid or data['part'] != part or data['source_type'] != 'platform_subtitles':
            raise ValueError()
        data['segments'] = normalize(data['segments'], float(data['duration']))
        return data
    except Stop:
        raise
    except Exception:
        raise Stop('output_conflict', '缓存无效或属于其他视频/分P；未覆盖。')


def save(out, data):
    out.mkdir(parents=True, exist_ok=True)
    rows = data['segments']
    # JSON is canonical; additional formats are generated from the same timestamps.
    files = {
        'subtitle.json': json.dumps(data, ensure_ascii=False, indent=2),
        'subtitle.txt': '\n'.join(f"[{timestamp(r['from'])} --> {timestamp(r['to'])}] {r['content']}" for r in rows),
        'subtitle.srt': '\n\n'.join(f"{i}\n{timestamp(r['from'])} --> {timestamp(r['to'])}\n{r['content']}" for i, r in enumerate(rows, 1)) + '\n',
    }
    for name, content in files.items():
        with (out / name).open('x', encoding='utf-8') as stream:
            stream.write(content)


def execute(args):
    if args.command == 'fetch':
        bvid, part = identify(args.url)
        out = Path(args.output)
        data = cached(out, bvid, part)
        if data:
            return {'status': 'cached', 'segments': len(data['segments'])}
        site = 'bilibili'
    else:
        site = args.site
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise Stop('browser_unavailable', '当前Python未安装Playwright；请按需配置。')
    root = Path(os.environ.get('VKN_DATA_DIR', str(Path.home() / '.video-knowledge-notes'))).expanduser().resolve()
    # Separate channels to avoid incompatible profile versions; use the same channel later.
    channel = preferred_channel(root, site, args.channel)
    profile = root / 'browser-profiles' / site / (channel or 'chromium')
    profile.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                str(profile), channel=None if channel == 'chromium' else channel, headless=args.command != 'login',
                args=['--no-proxy-server'] if args.direct else [],
                timeout=30000, accept_downloads=False)
        except Exception:
            raise Stop('browser_unavailable', '无法启动专用浏览器；检查安装和档案占用，不要删除登录数据。')
        try:
            if args.command == 'login':
                page = context.pages[0] if context.pages else context.new_page()
                closed = []
                context.on('close', lambda *_: closed.append(True))
                page.goto(SITES[site], timeout=30000, wait_until='domcontentloaded')
                print(json.dumps({'status': 'waiting_for_user', 'message': '请在专用窗口正常登录，完成后关闭该窗口。'}, ensure_ascii=False), flush=True)
                deadline = time.monotonic() + args.wait_seconds
                while not closed and time.monotonic() < deadline:
                    try:
                        page.wait_for_timeout(500)
                    except Exception:
                        break
                return {'status': 'login_window_finished', 'message': '会话保留在本机；请执行获取验证登录，不把关窗视为登录成功。'}
            deadline = time.monotonic() + 45
            def get_json(url):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise Stop('request_failed', '请求预算已用完，未启动转写。')
                response = None
                try:
                    if args.direct:
                        # APIRequestContext need not honor Chromium command-line proxy flags.
                        # Use a separate explicit direct transport, scoped to this exact URL.
                        class NoRedirect(urllib.request.HTTPRedirectHandler):
                            def redirect_request(self, *a, **kw):
                                return None
                        headers = {'Referer': f'https://www.bilibili.com/video/{bvid}/',
                                   'User-Agent': 'Mozilla/5.0'}
                        cookies = context.cookies([url])
                        if cookies:
                            headers['Cookie'] = '; '.join(c['name'] + '=' + c['value'] for c in cookies)
                        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
                        with opener.open(urllib.request.Request(url, headers=headers), timeout=min(12, remaining)) as stream:
                            raw = stream.read(8 * 1024 * 1024 + 1)
                        if len(raw) > 8 * 1024 * 1024:
                            raise ValueError()
                        payload = json.loads(raw)
                        if not isinstance(payload, dict):
                            raise ValueError()
                        return payload
                    response = context.request.get(url, timeout=min(12000, remaining * 1000),
                        max_redirects=0, headers={'Referer': f'https://www.bilibili.com/video/{bvid}/'})
                    if response.status != 200:
                        raise Stop('request_failed', f'HTTP {response.status}；不代表无字幕。')
                    payload = response.json()
                    if not isinstance(payload, dict):
                        raise ValueError()
                    return payload
                except Stop:
                    raise
                except Exception:
                    raise Stop('request_failed', '网络或接口响应异常；未输出Cookie或请求凭据。')
                finally:
                    if response is not None:
                        response.dispose()
            data = acquire(get_json, bvid, part)
            save(out, data)
            remembered = remember_channel(root, site, channel)
            return {'status': 'ok', 'segments': len(data['segments']), 'bvid': bvid, 'part': part,
                    'channel': channel or 'chromium', 'channel_preference_saved': remembered}
        finally:
            try:
                context.close()
            except Exception:
                pass


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    login = sub.add_parser('login')
    login.add_argument('site', choices=SITES)
    login.add_argument('--wait-seconds', type=int, default=300)
    fetch = sub.add_parser('fetch')
    fetch.add_argument('url')
    fetch.add_argument('--output', required=True)
    for command in (login, fetch):
        command.add_argument('--channel', choices=['chrome', 'msedge', 'chromium'])
        command.add_argument('--direct', action='store_true')
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        result = execute(args)
        code = 0
    except Stop as exc:
        result, code = {'status': exc.status, 'message': exc.message}, 2
    except Exception:
        result, code = {'status': 'request_failed', 'message': '处理未完成；请检查环境，不自动转写或回显敏感错误。'}, 2
    result['elapsed_seconds'] = round(time.perf_counter() - started, 3)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
