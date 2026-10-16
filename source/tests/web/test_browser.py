"""Real Chromium + real HTTP + real Mongo. No mocked browser or database."""
import os
import sys
import time
import secrets
import subprocess
from pathlib import Path
from uuid import uuid4
import httpx
import pytest
from playwright.sync_api import sync_playwright, expect

pytestmark = pytest.mark.web
ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(os.getenv('TEST_EVIDENCE_DIR', str(ROOT.parent / 'docs' / 'evidence'))).resolve()


@pytest.fixture
def live_server(db):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'MONGO_URI':os.getenv('TEST_MONGO_URI','mongodb://127.0.0.1:27018/?replicaSet=rs0'),
           'MONGO_DB':db.name, 'SESSION_SECRET':secrets.token_urlsafe(48), 'APP_BASE_URL':'http://127.0.0.1:8001', 'COOKIE_SECURE':'false','ENVIRONMENT':'development'}
    with (EVIDENCE/'browser-server.log').open('w', encoding='utf-8') as output:
        proc = subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8001'],cwd=ROOT,env=env,stdout=output,stderr=output)
        try:
            for _ in range(60):
                if proc.poll() is not None: raise RuntimeError('Live server exited; see browser-server.log')
                try:
                    if httpx.get('http://127.0.0.1:8001/health',timeout=1).status_code==200: break
                except httpx.HTTPError: pass
                time.sleep(.25)
            else: raise RuntimeError('Live server readiness timed out')
            yield 'http://127.0.0.1:8001'
        finally:
            proc.terminate();proc.wait(timeout=15)


@pytest.fixture
def browser():
    with sync_playwright() as p:
        executable=os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
        if not executable:
            installed=sorted((Path(os.getenv('LOCALAPPDATA',''))/'ms-playwright').glob('chromium-*/chrome-win64/chrome.exe'))
            if installed: executable=str(installed[-1])
        b=p.chromium.launch(headless=True,**({'executable_path':executable} if executable else {}))
        yield b
        b.close()


def sign_up(page,base,name):
    page.goto(base+'/register')
    page.get_by_label('用户名',exact=True).fill(name)
    page.get_by_label('密码',exact=True).fill(secrets.token_urlsafe(18))
    page.get_by_role('button',name='注册并登录').click()
    expect(page.get_by_role('heading',name='我的问卷')).to_be_visible()


def test_full_browser_flow(browser,live_server,db):
    base=live_server
    owner_context=browser.new_context(viewport={'width':1440,'height':1000})
    reader_context=browser.new_context(viewport={'width':1100,'height':850})
    a,b=owner_context.new_page(),reader_context.new_page()
    page_errors=[]
    a.on('pageerror',lambda err:page_errors.append(str(err)));b.on('pageerror',lambda err:page_errors.append(str(err)))
    sign_up(a,base,'ui_owner_'+uuid4().hex[:8])
    a.get_by_role('link',name='＋ 创建问卷').click()
    a.get_by_label('问卷标题').fill('浏览器验收 · 学习体验')
    a.get_by_label('问卷说明').fill('四种题型、路径切换与匿名版本验收')
    a.get_by_role('button',name='创建并添加题目').click()
    expect(a.get_by_role('heading',name='添加题目')).to_be_visible()
    survey_id=a.url.split('/')[4]
    for t in ['single_choice','multiple_choice','number','text']:
        a.locator(f'.add[data-type="{t}"]').click()
    questions=a.locator('.question')
    for i,title in enumerate(['是否有编程经验？','熟悉哪些语言？','每周学习几小时？','课程建议？']):
        questions.nth(i).locator('.qtitle').fill(title)
        if i<3: questions.nth(i).locator('.qrequired').check()
    q1,q2,q3,q4=[questions.nth(i) for i in range(4)]
    q1.locator('.option-line input').nth(0).fill('有');q1.locator('.option-line input').nth(1).fill('没有')
    q2.locator('.option-line input').nth(0).fill('python');q2.locator('.option-line input').nth(1).fill('java')
    q2.locator('.add-option').click()
    q2.locator('.option-line input').nth(2).fill('cpp')
    q2.locator('[data-key=minSelections]').fill('1');q2.locator('[data-key=maxSelections]').fill('3')
    q3.locator('[data-key=min]').fill('0');q3.locator('[data-key=max]').fill('80')
    q4.locator('[data-key=minLength]').fill('0');q4.locator('[data-key=maxLength]').fill('500')
    qids=[q.locator('.meta').first.inner_text().split('：')[1] for q in [q1,q2,q3,q4]]
    no=q1.locator('.option-line span').nth(1).inner_text()
    language_ids=q2.locator('.option-line span').all_inner_texts()
    q1.locator('.add-rule').click();r=q1.locator('.rule').nth(0);r.locator('.operand').select_option(no);r.locator('.target').select_option(qids[2])
    q2.locator('.add-rule').click();r=q2.locator('.rule').nth(0);r.locator('.operator').select_option('contains_all');r.locator('.operand').select_option(language_ids[:2]);r.locator('.target').select_option(qids[3])
    q2.locator('.add-rule').click();r=q2.locator('.rule').nth(1);r.locator('.operand').select_option(language_ids[2]);r.locator('.target').select_option('')
    q3.locator('.add-rule').click();r=q3.locator('.rule').nth(0);r.locator('.operator').select_option('gte');r.locator('.operand-number').fill('10');r.locator('.target').select_option(qids[3])
    q3.locator('.add-rule').click();r=q3.locator('.rule').nth(1);r.locator('.operator').select_option('lt');r.locator('.operand-number').fill('10')
    a.screenshot(path=str(EVIDENCE/'editor.png'),full_page=True)
    with a.expect_popup() as popup:
        a.get_by_role('button',name='保存并预览').click()
    preview=popup.value
    expect(preview.get_by_role('heading',name='是否有编程经验？')).to_be_visible()
    assert db.submissions.count_documents({})==0
    preview.close()
    a.get_by_role('button',name='保存并发布').click()
    expect(a.get_by_text('发布成功。公开填写链接：')).to_be_visible()
    public_url=a.locator('.success a').get_attribute('href')
    a.screenshot(path=str(EVIDENCE/'published.png'),full_page=True)
    # Login return link: an unauthenticated reader is redirected and registration preserves next.
    b.goto(public_url);expect(b.get_by_role('heading',name='欢迎回来')).to_be_visible()
    b.get_by_role('link',name='注册账号').click()
    reader_name='ui_reader_'+uuid4().hex[:8]
    b.get_by_label('用户名',exact=True).fill(reader_name);b.get_by_label('密码',exact=True).fill(secrets.token_urlsafe(18));b.get_by_role('button',name='注册并登录').click()
    expect(b.get_by_role('heading',name='是否有编程经验？')).to_be_visible()
    b.get_by_label('没有',exact=True).check();b.get_by_role('button',name='下一步').click()
    expect(b.get_by_role('heading',name='每周学习几小时？')).to_be_visible()
    b.get_by_label('数字回答').fill('-1');b.get_by_role('button',name='下一步').click();expect(b.locator('#error')).to_contain_text('范围')
    b.get_by_label('数字回答').fill('8');b.get_by_role('button',name='下一步').click();expect(b.get_by_role('heading',name='已完成本次填写')).to_be_visible()
    b.get_by_role('button',name='上一题').click();b.get_by_role('button',name='上一题').click()
    b.get_by_label('有',exact=True).check();b.get_by_role('button',name='下一步').click();b.get_by_label('cpp',exact=True).check();b.get_by_role('button',name='下一步').click()
    expect(b.locator('#review')).not_to_contain_text('每周学习几小时')
    b.get_by_role('button',name='确认提交').click();expect(b.get_by_role('heading',name='提交成功')).to_be_visible()
    assert db.submissions.count_documents({})==1
    b.get_by_role('button',name='开始新一轮填写').click();b.get_by_label('没有',exact=True).check();b.get_by_role('button',name='下一步').click();b.get_by_label('数字回答').fill('12');b.get_by_role('button',name='下一步').click()
    b.get_by_label('你的回答').fill('<img src=x onerror=alert(1)> 更清晰的示例');b.get_by_role('button',name='下一步').click();b.get_by_role('button',name='确认提交').click();expect(b.get_by_role('heading',name='提交成功')).to_be_visible()
    a.goto(f'{base}/surveys/{survey_id}/statistics');expect(a.get_by_text('此版本原始提交')).to_be_visible()
    expect(a.locator('.metric').nth(0).locator('strong')).to_have_text('2');expect(a.locator('.metric').nth(1).locator('strong')).to_have_text('1')
    assert a.locator('img').count()==0
    a.screenshot(path=str(EVIDENCE/'statistics.png'),full_page=True)
    a.locator('#question').select_option(qids[1]);expect(a.get_by_role('heading',name='熟悉哪些语言？')).to_be_visible()
    # Keep a V1 form open while owner publishes V2.
    b.get_by_role('button',name='开始新一轮填写').click();b.get_by_label('没有',exact=True).check();b.get_by_role('button',name='下一步').click();b.get_by_label('数字回答').fill('8');b.get_by_role('button',name='下一步').click()
    a.goto(f'{base}/surveys/{survey_id}/edit');a.get_by_role('button',name='从发布版创建新草稿').click();expect(a.locator('.question')).to_have_count(4)
    a.locator('#anonymous').uncheck();a.get_by_role('button',name='保存并发布').click();expect(a.get_by_text('发布成功。公开填写链接：')).to_be_visible()
    b.get_by_role('button',name='确认提交').click();expect(b.locator('#error')).to_contain_text('问卷已更新，需要刷新重填')
    b.reload();b.get_by_label('没有',exact=True).check();b.get_by_role('button',name='下一步').click();b.get_by_label('数字回答').fill('8');b.get_by_role('button',name='下一步').click();b.get_by_role('button',name='确认提交').click();expect(b.get_by_role('heading',name='提交成功')).to_be_visible()
    a.goto(f'{base}/surveys/{survey_id}/statistics');expect(a.locator('tbody')).to_contain_text(reader_name)
    reader_id=reader_context.request.get(base+'/api/me').json()['user']['id']
    expect(a.locator('tbody')).not_to_contain_text(reader_id)
    a.locator('#version').select_option('1');expect(a.locator('.metric').nth(1).locator('strong')).to_have_text('0')
    a.locator('#mode').select_option('historical_raw');expect(a.locator('.metric').nth(2).locator('strong')).to_have_text('2')
    expect(a.locator('tbody')).not_to_contain_text(reader_name)
    expect(a.locator('tbody')).not_to_contain_text(reader_id)
    a.goto(base+'/dashboard');a.once('dialog',lambda dialog:dialog.accept());a.get_by_role('button',name='关闭',exact=True).click();expect(a.get_by_text('已关闭',exact=True)).to_be_visible()
    b.goto(public_url);expect(b.get_by_role('heading',name='暂时无法打开')).to_be_visible();expect(b.get_by_text('问卷已关闭',exact=True)).to_be_visible()
    assert page_errors==[],page_errors
    owner_context.close();reader_context.close()


def test_mobile_keyboard_and_labels(browser,live_server):
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,device_scale_factor=1)
    page=context.new_page();page.goto(live_server+'/register')
    page.get_by_label('用户名',exact=True).fill('mobile_'+uuid4().hex[:8]);page.keyboard.press('Tab')
    expect(page.get_by_label('密码',exact=True)).to_be_focused()
    page.get_by_label('密码',exact=True).fill(secrets.token_urlsafe(18));page.get_by_role('button',name='注册并登录').click()
    expect(page.get_by_role('heading',name='我的问卷')).to_be_visible()
    page.get_by_role('link',name='＋ 创建问卷').click();page.get_by_label('问卷标题').fill('手机端问卷');page.get_by_role('button',name='创建并添加题目').click()
    expect(page.get_by_role('heading',name='添加题目')).to_be_visible();page.locator('.add[data-type=text]').click()
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path=str(EVIDENCE/'mobile.png'),full_page=True)
    context.close()
