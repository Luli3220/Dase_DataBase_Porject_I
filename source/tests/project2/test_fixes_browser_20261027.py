from pathlib import Path
from uuid import uuid4
import os
from playwright.sync_api import expect
from app.services.questions import QuestionService
from tests.project2.test_library import content
from tests.web.test_browser import browser, live_server, sign_up


def test_editor_atomic_failure_keeps_inputs_and_prevents_preview(browser, live_server, db):
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    sign_up(page, live_server, 'atomic_ui_'+uuid4().hex[:8])
    page.goto(live_server+'/surveys/new'); page.get_by_label('问卷标题').fill('数据库原题名')
    page.get_by_role('button', name='创建并添加题目').click()
    expect(page.get_by_role('heading', name='添加题目', exact=True)).to_be_visible()
    sid = page.url.split('/')[4]
    page.locator('.add[data-type="number"]').click()
    page.get_by_label('标题', exact=True).fill('仍保留的本地标题')
    page.locator('.qtitle').fill('仍保留的本地题目')
    csrf = page.request.get(live_server+'/api/me').json()['csrfToken']
    # Another real HTTP writer advances the draft revision after this editor loaded it.
    other = page.request.put(live_server+f'/api/surveys/{sid}/draft', headers={'X-CSRF-Token': csrf},
        data={'expectedRevision': 0, 'settings': {'anonymous': True}, 'questions': []})
    assert other.status == 200
    requests, popups = [], []
    page.on('request', lambda r: requests.append((r.method, r.url)))
    page.on('popup', lambda p: popups.append(p))
    page.get_by_role('button', name='保存并预览', exact=True).click()
    expect(page.locator('#error')).to_contain_text('本次保存未生效')
    expect(page.locator('#saved')).to_contain_text('当前输入仍保留')
    expect(page.get_by_label('标题', exact=True)).to_have_value('仍保留的本地标题')
    expect(page.locator('.qtitle')).to_have_value('仍保留的本地题目')
    expect(page.get_by_role('button', name='保存草稿与信息', exact=True)).to_be_enabled()
    assert not popups
    assert any(m == 'POST' and url.endswith(f'/api/surveys/{sid}/save') for m, url in requests)
    assert not any(m == 'PATCH' and url.endswith(f'/api/surveys/{sid}') for m, url in requests)
    assert page.request.get(live_server+f'/api/surveys/{sid}').json()['title'] == '数据库原题名'
    assert page.request.get(live_server+f'/api/surveys/{sid}/draft').json()['questions'] == []
    output = Path(os.environ['TEST_EVIDENCE_DIR']); output.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(output/'fix-atomic-conflict.png'), full_page=True)
    page.reload(); expect(page.get_by_role('heading', name='添加题目', exact=True)).to_be_visible()
    page.get_by_label('标题', exact=True).fill('成功保存的标题')
    page.locator('.add[data-type="number"]').click(); page.locator('.qtitle').fill('成功保存的题目')
    page.get_by_role('button', name='保存草稿与信息', exact=True).click()
    expect(page.locator('#saved')).to_contain_text('已保存 · revision 2')
    assert page.request.get(live_server+f'/api/surveys/{sid}').json()['title'] == '成功保存的标题'
    assert page.request.get(live_server+f'/api/surveys/{sid}/draft').json()['questions'][0]['title'] == '成功保存的题目'
    page.close()


def test_picker_filters_before_paging_and_management_still_shows_archived(browser, live_server, db):
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    sign_up(page, live_server, 'active_ui_'+uuid4().hex[:8])
    uid = db.users.find_one()['_id']
    library = QuestionService(db)
    ids = [library.create(uid, content(title=f'分页题-{i:02}'))['definition']['_id'] for i in range(23)]
    db.question_definitions.update_many({'_id': {'$in': ids[-10:]}}, {'$set': {'archived': True}})
    page.goto(live_server+'/surveys/new'); page.get_by_label('问卷标题').fill('归档分页验收')
    page.get_by_role('button', name='创建并添加题目').click()
    page.get_by_role('button', name='从题库添加题目', exact=True).click()
    expect(page.locator('.pick-question')).to_have_count(10)
    expect(page.locator('#picker-results')).not_to_contain_text('分页题-22')
    page.get_by_role('button', name='下一页选题').click()
    expect(page.locator('.pick-question')).to_have_count(3)
    expect(page.get_by_role('button', name='下一页选题')).to_be_disabled()
    page.locator('.pick-question').first.click()
    expect(page.locator('.qtitle')).to_have_value('分页题-02')
    page.goto(live_server+'/questions')
    expect(page.get_by_text('共 23 题', exact=True)).to_be_visible()
    expect(page.get_by_text('V1 · 我的题目 · 已归档', exact=True)).to_have_count(10)
    page.goto(live_server+'/questions/'+str(ids[0]))
    expect(page.locator('#lib-statistics')).to_contain_text('参与统计的问卷')
    expect(page.locator('#lib-statistics')).to_contain_text('无提交')
    page.close()
