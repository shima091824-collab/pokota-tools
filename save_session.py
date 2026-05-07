from playwright.sync_api import sync_playwright
import pathlib

STATE_YAHOO = str(pathlib.Path.home() / 'yahoo_state.json')
STATE_MERCARI = str(pathlib.Path.home() / 'mercari_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    print('[1/2] Yahoo!フリマにログインします')
    ctx1 = browser.new_context()
    page1 = ctx1.new_page()
    page1.goto('https://paypayfleamarket.yahoo.co.jp')
    print('ログイン完了したらEnterを押してください')
    input()
    ctx1.storage_state(path=STATE_YAHOO)
    print(f'保存完了: {STATE_YAHOO}')
    ctx1.close()

    print('[2/2] メルカリにログインします')
    ctx2 = browser.new_context()
    page2 = ctx2.new_page()
    page2.goto('https://jp.mercari.com')
    print('ログイン完了したらEnterを押してください')
    input()
    ctx2.storage_state(path=STATE_MERCARI)
    print(f'保存完了: {STATE_MERCARI}')
    ctx2.close()

    browser.close()
    print('全て完了')
