#!/usr/bin/env python3
"""
save_research_session.py
リサーチ専用のメルカリセッションを保存する（初回のみ手動実行）。
~/research_state.json に保存し、sales 用の mercari_state.json とは完全に分離。
"""
import json
import os
import pathlib
from playwright.sync_api import sync_playwright

CONFIG_FILE   = os.path.expanduser('~/research_config.json')
DEFAULT_STATE = os.path.expanduser('~/research_state.json')


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def main():
    config     = load_config()
    state_path = os.path.expanduser(config.get('session_file', DEFAULT_STATE))

    print('=' * 55)
    print(' メルカリ リサーチ用セッション保存ツール')
    print('=' * 55)
    print(f'保存先: {state_path}')
    print()
    print('注意: このブラウザプロファイルは販売アカウントとは')
    print('      完全に独立しています（research_state.json）。')
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            locale='ja-JP',
            timezone_id='Asia/Tokyo',
        )
        page = ctx.new_page()
        page.goto('https://jp.mercari.com')

        print('ブラウザが開きました。')
        print('メルカリにログイン（またはログインせず閲覧状態でも可）してから')
        print('Enter を押してください...')
        input()

        ctx.storage_state(path=state_path)
        print(f'セッションを保存しました: {state_path}')
        ctx.close()
        browser.close()

    print('完了。mercari_research.py を実行できます。')


if __name__ == '__main__':
    main()
