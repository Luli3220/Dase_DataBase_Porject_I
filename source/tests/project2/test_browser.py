"""Two real browser contexts share, import, version, restore and aggregate persistent data."""
from uuid import uuid4
from pathlib import Path
import os
from playwright.sync_api import expect
from tests.web.test_browser import browser, live_server, sign_up


def test_project2_browser_workflow(browser, live_server, db):
    output = Path(os.environ['TEST_EVIDENCE_DIR']); output.mkdir(parents=True, exist_ok=True)
    ctx_a = browser.new_context(viewport={'width': 1440, 'height': 1000})
    ctx_b = browser.new_context(viewport={'width': 1100, 'height': 850})
    a, b = ctx_a.new_page(), ctx_b.new_page(); errors = []
    a.on('pageerror', lambda e: errors.append(str(e))); b.on('pageerror', lambda e: errors.append(str(e)))
    suffix = uuid4().hex[:8]; owner, reader = 'lib_owner_'+suffix, 'lib_reader_'+suffix
    sign_up(a, live_server, owner); sign_up(b, live_server, reader)
    a.get_by_role('link', name='题目', exact=True).click()
    a.get_by_label('题目名称').fill('你的年龄 · 共享验收')
    a.get_by_label('最小值', exact=True).fill('0'); a.get_by_label('最大值', exact=True).fill('120')
    a.get_by_label('仅整数').check()
    a.get_by_role('button', name='保存到题目库').click()
    expect(a.get_by_role('heading', name='版本历史')).to_be_visible()
    qid = a.url.split('/')[-1]
    a.get_by_label('共享给注册用户名', exact=False).fill(reader)
    a.get_by_role('button', name='保存共享范围').click()
    expect(a.get_by_label('共享给注册用户名', exact=False)).to_have_value(reader)
    a.get_by_role('link', name='题库', exact=True).click()
    a.get_by_label('题库名称').fill('人口统计题库')
    a.get_by_role('button', name='创建题库', exact=True).click()
    expect(a.get_by_role('heading', name='从可用题目中添加')).to_be_visible()
    a.get_by_role('button', name='选用', exact=True).click()
    expect(a.get_by_role('button', name='移除成员')).to_be_visible()
    a.screenshot(path=str(output/'p2-bank.png'), full_page=True)

    public_urls = {}
    def make(page, title, use_bank=False):
        page.goto(live_server+'/surveys/new'); page.get_by_label('问卷标题').fill(title)
        if not use_bank: page.get_by_label('重复填写策略').select_option('multiple')
        page.get_by_role('button', name='创建并添加题目').click()
        expect(page.get_by_role('heading', name='添加题目', exact=True)).to_be_visible()
        sid = page.url.split('/')[4]
        page.get_by_role('button', name='从题库添加题目', exact=True).click()
        if use_bank:
            page.get_by_label('题库范围').select_option(label='人口统计题库')
            page.get_by_role('button', name='搜索选题').click()
        page.get_by_role('button', name='选用', exact=True).click()
        expect(page.locator('.qtitle')).to_have_value('你的年龄 · 共享验收')
        expect(page.locator('.qtitle')).to_be_disabled()
        page.get_by_role('button', name='保存并发布').click()
        expect(page.get_by_text('发布成功。公开填写链接：')).to_be_visible()
        public_urls[sid] = page.locator('.success a').get_attribute('href')
        return sid

    sa = make(a, 'A 问卷 · 固定旧题', True)
    sb = make(b, 'B 问卷 · 复用共享题')
    b.get_by_label('允许本问卷为共享题目贡献匿名聚合统计', exact=True).check()
    b.get_by_role('button', name='保存贡献授权').click()
    expect(b.get_by_role('status')).to_contain_text('授权已保存')
    for sid, value in [(sa, 18), (sb, 24), (sb, 30), (sb, 45)]:
        b.goto(public_urls[sid])
        b.get_by_label('数字回答').fill(str(value))
        b.get_by_role('button', name='下一步', exact=True).click()
        b.get_by_role('button', name='确认提交', exact=True).click()
        expect(b.get_by_role('heading', name='提交成功', exact=True)).to_be_visible()
    a.goto(live_server+'/questions/'+qid)
    a.get_by_label('题目名称').fill('你的年龄 · v2')
    a.get_by_role('button', name='保存为 V2', exact=True).click()
    expect(a.get_by_role('heading', name='你的年龄 · v2', exact=True)).to_be_visible()
    a.get_by_label('选择版本', exact=True).select_option('1')
    expect(a.get_by_label('题目名称')).to_have_value('你的年龄 · 共享验收')
    a.get_by_role('button', name='恢复所选版本', exact=True).click()
    expect(a.get_by_label('选择版本', exact=True)).to_have_value('3')
    assert db.question_versions.count_documents({}) == 3
    a.get_by_label('选择版本', exact=True).select_option('1')
    expect(a.locator('#lib-usage')).to_contain_text('A 问卷 · 固定旧题')
    expect(a.locator('#lib-usage')).to_contain_text('B 问卷 · 复用共享题')
    expect(a.locator('#lib-statistics')).to_contain_text('实际回答')
    expect(a.locator('#lib-statistics')).to_contain_text('平均值：18')
    a.locator('#stat-scope').select_option('consented_shared')
    expect(a.locator('#lib-statistics')).to_contain_text('平均值：29.25')
    a.screenshot(path=str(output/'p2-question-history-statistics.png'), full_page=True)
    a.goto(live_server+f'/surveys/{sa}/edit')
    a.get_by_role('button', name='从发布版创建新草稿').click()
    expect(a.locator('.qtitle')).to_have_value('你的年龄 · 共享验收')
    a.screenshot(path=str(output/'p2-frozen-snapshot.png'), full_page=True)
    a.set_viewport_size({'width': 390, 'height': 844})
    a.goto(live_server+'/questions/'+qid)
    expect(a.get_by_role('heading', name='版本历史')).to_be_visible()
    assert a.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    a.screenshot(path=str(output/'p2-mobile.png'), full_page=True)
    assert not errors, errors
    ctx_a.close(); ctx_b.close()
