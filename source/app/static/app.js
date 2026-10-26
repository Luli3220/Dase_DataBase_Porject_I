'use strict';
const $ = (q, root=document) => root.querySelector(q);
const $$ = (q, root=document) => [...root.querySelectorAll(q)];
const esc = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const app = $('#app');
let csrf = '', me = null;
const typeNames = {single_choice:'单选题',multiple_choice:'多选题',text:'文本填空',number:'数字填空'};
const states = {draft:'草稿',published:'已发布',closed:'已关闭'};
function toast(message) { const el=$('#toast');el.textContent=message;el.hidden=false;setTimeout(()=>el.hidden=true,4000); }
function showError(error) { const box=$('#error');if(box){box.hidden=false;box.textContent=error.message;} else toast(error.message); }
function bind(selector, event, handler, root=document) {const node=$(selector,root);if(node)node.addEventListener(event,async e=>{try{await handler(e);}catch(err){showError(err);}});}
async function api(path, method='GET', data) {
  const response=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json',...(csrf?{'X-CSRF-Token':csrf}:{})},body:data===undefined?undefined:JSON.stringify(data)});
  const result=await response.json();
  if(!response.ok){const error=new Error(result.error?.message||'请求失败');error.code=result.error?.code;error.status=response.status;error.details=result.error?.details;
    if(error.details?.questionId)error.message+='（'+error.details.questionId+'）';
    if(error.details?.fields)error.message+='：'+error.details.fields.map(f=>f.field+' '+f.message).join('；');
    if(error.code==='SURVEY_VERSION_CHANGED')error.message='问卷已更新，需要刷新重填。';
    throw error;}
  return result;
}
function heading(kicker,title,sub,action='') {return `<div class="topline"><div><div class="eyebrow">${esc(kicker)}</div><h1>${esc(title)}</h1><p class="muted">${esc(sub)}</p></div>${action}</div><div id="error" class="error" role="alert" hidden></div>`;}
const date = value => value ? new Date(value).toLocaleString() : '未设置';
function id() {return 'id_'+crypto.randomUUID().replaceAll('-','').slice(0,12);}
function localDate(value) {if(!value)return '';const d=new Date(value);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);}
function safeReturn(){const target=new URLSearchParams(location.search).get('next');return target?.startsWith('/')&&!target.startsWith('//')&&!target.includes('\\')?target:'/dashboard';}

async function authPage(register=false) {
  app.innerHTML=`<div class="auth card"><div class="eyebrow">YOUR NEXT QUESTION</div><h1>${register?'创建账号':'欢迎回来'}</h1><p class="muted">${register?'让每一个问题，都有清晰的答案。':'登录后管理问卷，或填写收到的问卷。'}</p><div id="error" class="error" role="alert" hidden></div><form id="auth"><label for="username">用户名</label><input id="username" name="username" autocomplete="username" minlength="3" maxlength="40" required><label for="password">密码</label><input id="password" type="password" autocomplete="${register?'new-password':'current-password'}" minlength="10" maxlength="128" required><p class="hint">用户名3–40位；密码至少10字符。</p><button class="wide" type="submit">${register?'注册并登录':'登录'}</button></form><p>${register?'已有账号？':'还没有账号？'} <a href="/${register?'login':'register'}${location.search}">${register?'去登录':'注册账号'}</a></p></div>`;
  bind('#auth','submit',async e=>{e.preventDefault();const button=$('button',e.target);button.disabled=true;try{await api('/auth/'+(register?'register':'login'),'POST',{username:$('#username').value,password:$('#password').value});location.href=safeReturn();}finally{button.disabled=false;}});
}

async function dashboard(offset=0) {
  const data=await api(`/surveys?offset=${offset}&limit=20`);
  app.innerHTML=heading('WORKSPACE','我的问卷','从一个好问题开始，听见更多声音。','<a class="button" href="/surveys/new">＋ 创建问卷</a>')+
    (data.items.length?`<div class="grid">${data.items.map(s=>`<article class="card"><div class="split"><span class="badge">${states[s.status]}</span><span class="meta">${date(s.createdAt)}</span></div><h2>${esc(s.title)}</h2><p class="muted">${esc(s.description||'暂无说明')}</p><p class="meta">发布版本 ${s.publishedVersion?'V'+s.publishedVersion:'—'} · 草稿 ${s.draftVersion?'V'+s.draftVersion:'—'}<br>截止：${date(s.deadlineAt)} · ${s.submissionPolicy==='latest_only'?'每人最新一份有效':'每次填写均有效'}</p><div class="toolbar"><a class="button secondary" href="/surveys/${s._id}/edit">编辑管理</a>${s.publishedVersion?`<a class="button secondary" href="/surveys/${s._id}/statistics">查看统计</a><button class="subtle copy" data-url="${esc(location.origin+'/survey/'+s.publicId)}">复制链接</button>`:''}${s.status!=='closed'?`<button class="subtle danger close" data-id="${s._id}">关闭</button>`:''}</div>${s.publishedVersion?`<div class="linkbox"><a href="/survey/${s.publicId}">${esc(location.origin+'/survey/'+s.publicId)}</a></div>`:''}</article>`).join('')}</div>`:'<div class="card empty"><h2>还没有问卷</h2><p class="muted">创建第一份问卷，配置问题并发布分享。</p></div>')+`<div class="toolbar"><button id="previous" ${offset===0?'disabled':''}>上一页</button><span>共 ${data.total} 份</span><button id="more" ${offset+20>=data.total?'disabled':''}>下一页</button></div>`;
  $$('.copy').forEach(b=>b.onclick=()=>navigator.clipboard.writeText(b.dataset.url).then(()=>toast('链接已复制')).catch(()=>toast(b.dataset.url)));
  $$('.close').forEach(b=>b.onclick=async()=>{if(confirm('关闭后不再接收填写；历史数据保留。确认关闭？')){try{await api('/surveys/'+b.dataset.id+'/close','POST');await dashboard(offset);}catch(err){showError(err);}}});
  bind('#previous','click',()=>dashboard(offset-20));bind('#more','click',()=>dashboard(offset+20));
}

async function newSurvey() {
  app.innerHTML=heading('CREATE','创建问卷','设置基本信息，下一步添加题目。')+`<form id="new" class="card"><label for="title">问卷标题</label><input id="title" maxlength="200" required><label for="description">问卷说明</label><textarea id="description" maxlength="5000"></textarea><label class="check"><input id="anonymous" type="checkbox" checked>对创建者隐藏填写者账号身份</label><p class="hint">填写者仍需登录；回答内容本身可能包含身份线索。</p><label for="policy">重复填写策略</label><select id="policy"><option value="latest_only">每人仅最新一份参与有效统计（保留历史）</option><option value="multiple">每次填写均参与统计</option></select><label for="deadline">截止时间（本地时间，可不填）</label><input id="deadline" type="datetime-local"><div class="toolbar"><button type="submit">创建并添加题目</button><a class="button secondary" href="/dashboard">返回</a></div></form>`;
  bind('#new','submit',async e=>{e.preventDefault();const s=await api('/surveys','POST',{title:$('#title').value,description:$('#description').value,anonymous:$('#anonymous').checked,submissionPolicy:$('#policy').value,deadlineAt:$('#deadline').value?new Date($('#deadline').value).toISOString():null});location.href=`/surveys/${s._id}/edit`;});
}

async function editor(surveyId) {
  let survey=await api('/surveys/'+surveyId);
  let draft=survey.draftVersion?await api(`/surveys/${surveyId}/draft`):null;
  function render() {
    app.innerHTML=heading('SURVEY BUILDER',survey.title,`对外发布 ${survey.publishedVersion?'V'+survey.publishedVersion:'—'} · ${draft?'编辑草稿 V'+draft.version+' / revision '+draft.revision:'没有草稿'} · ${states[survey.status]}`)+
      `<section class="card"><h2>基本信息</h2><label for="title">标题</label><input id="title" value="${esc(survey.title)}" maxlength="200"><label for="description">说明</label><textarea id="description" maxlength="5000">${esc(survey.description)}</textarea><div class="row"><div><label for="policy">重复填写策略</label><select id="policy" ${survey.hasSubmissions?'disabled':''}><option value="latest_only" ${survey.submissionPolicy==='latest_only'?'selected':''}>每人最新一份有效</option><option value="multiple" ${survey.submissionPolicy==='multiple'?'selected':''}>每次均有效</option></select></div><div><label for="deadline">截止时间（本地）</label><input id="deadline" type="datetime-local" value="${localDate(survey.deadlineAt)}"></div></div><p class="hint">有成功答卷后策略锁定；历史答卷始终保留。问卷标题/说明属于可修改元信息。</p>${draft?`<label class="check"><input id="anonymous" type="checkbox" ${draft.settings.anonymous?'checked':''} ${draft.state==='sealed'?'disabled':''}>草稿版本匿名（仅隐藏账号身份）</label>`:''}</section>`+
      (draft?`<div id="questions"></div><div class="card"><h2>添加题目</h2><div class="toolbar">${Object.entries(typeNames).map(([t,n])=>`<button class="secondary add" data-type="${t}" ${draft.state==='sealed'?'disabled':''}>＋ ${n}</button>`).join('')}</div><p class="hint">题目顺序决定默认路径；修改题目根本含义请新建题目 ID。已发布版本保留原内容。</p></div>`:'<div class="card"><p>已发布版本已冻结。派生下一版本后可以继续编辑，旧版仍对外服务。</p><button id="derive" '+(survey.status==='closed'?'disabled':'')+'>从发布版创建新草稿</button></div>')+
      `<div class="toolbar"><button id="save">保存${draft?'草稿与信息':'基本信息'}</button>${draft?`<button id="preview" class="secondary">保存并预览</button><button id="publish" ${survey.status==='closed'?'disabled':''}>${draft.state==='sealed'?'恢复发布':'保存并发布'}</button>`:''}<a class="button secondary" href="/dashboard">返回工作台</a>${survey.publishedVersion?`<a class="button secondary" href="/surveys/${surveyId}/statistics">查看统计</a>`:''}</div><p id="saved" class="hint"></p>`;
    app.insertAdjacentHTML('beforeend', `<section class="card"><label class="check"><input id="contribute-statistics" type="checkbox" ${survey.statisticsContribution?'checked':''}>允许本问卷为共享题目贡献匿名聚合统计</label><p class="hint">默认关闭。仅贡献精确题目版本的计数与数字分布，不提供账号、原始文本或完整答卷；共享数据每份问卷至少 3 份实际回答才汇入。</p><button id="save-contribution" class="secondary">保存贡献授权</button></section>`);
    bind('#save-contribution','click',async()=>{survey=await api('/surveys/'+surveyId,'PATCH',{statisticsContribution:$('#contribute-statistics').checked});toast('统计贡献授权已保存');});
    if(draft&&draft.state==='draft'){
      $('#questions').insertAdjacentHTML('beforebegin','<section class="card"><h2>从题目库或题库导入</h2><p class="hint">先保存当前草稿，再选择精确版本。导入后的内容固定，题库更新不会自动改变问卷。</p><button id="open-import" class="secondary">从题库添加题目</button><div id="import-panel" hidden></div></section>');
      bind('#open-import','click',async()=>{await save();await showPicker();});
    }
    if(draft){drawQuestions();$$('.add').forEach(b=>b.onclick=()=>{readMeta();const type=b.dataset.type;draft.questions.push({id:id(),type,title:'新'+typeNames[type],required:false,options:type.includes('choice')?[{id:id(),label:'选项一'},{id:id(),label:'选项二'}]:[],validation:{},routingRules:[]});render();});}
    bind('#derive','click',async()=>{draft=await api(`/surveys/${surveyId}/draft-from-published`,'POST');survey=await api('/surveys/'+surveyId);render();});
    bind('#save','click',()=>save());
    bind('#preview','click',async()=>{await save();await api(`/surveys/${surveyId}/preview`);window.open(`/surveys/${surveyId}/preview`,'_blank');});
    bind('#publish','click',async()=>{if(draft.state!=='sealed')await save();const published=await api(`/surveys/${surveyId}/publish`,'POST',{expectedRevision:draft.revision});survey=published;draft=null;render();const box=document.createElement('div');box.className='success';const a=document.createElement('a');a.href=published.publicUrl;a.textContent=published.publicUrl;box.append('发布成功。公开填写链接：',a);app.prepend(box);});
  }
  async function showPicker(replaceLocalId=null){
    const host=$('#import-panel');host.hidden=false;
    await libraryPicker(host,async(qid,version)=>{draft=await api(`/surveys/${surveyId}/draft/import-question`,'POST',{questionId:qid,questionVersion:version,expectedRevision:draft.revision,replaceLocalId});render();toast(replaceLocalId?'题目版本已显式替换，原有外跳规则已清空':'题目已导入，内容固定到所选版本');});
    host.scrollIntoView({block:'center'});
  }
  function readMeta(){survey.title=$('#title').value;survey.description=$('#description').value;survey.submissionPolicy=$('#policy').value;survey.deadlineAt=$('#deadline').value?new Date($('#deadline').value).toISOString():null;if(draft)draft.settings.anonymous=$('#anonymous').checked;}
  let saving=false;
  async function save(){
    if(saving)throw new Error('正在保存，请稍候。');
    saving=true;
    const buttons=$$('button',app).map(button=>[button,button.disabled]);
    buttons.forEach(([button])=>button.disabled=true);
    $('#saved').textContent='正在保存…';$('#error').hidden=true;
    try{
      readMeta();
      const changes={title:survey.title,description:survey.description,submissionPolicy:survey.submissionPolicy,deadlineAt:survey.deadlineAt};
      if(draft&&draft.state==='draft'){
        const result=await api(`/surveys/${surveyId}/save`,'POST',{metadata:changes,draft:{expectedRevision:draft.revision,settings:draft.settings,questions:draft.questions}});
        survey=result.survey;draft=result.draft;
      }else survey=await api('/surveys/'+surveyId,'PATCH',changes);
      $('#saved').textContent='已保存'+(draft?' · revision '+draft.revision:'');toast('保存成功');
    }catch(error){
      const rejected=error.status>=400&&error.status<500;
      $('#saved').textContent=rejected?'本次保存未生效，当前输入仍保留。':'保存结果未确认，请核对后重试。';
      if(error.code==='DRAFT_CONFLICT')error.message+=' 本次保存未生效，当前输入仍保留；请先备份输入，再刷新获取最新草稿。';
      throw error;
    }finally{saving=false;buttons.forEach(([button,disabled])=>button.disabled=disabled);}
  }
  function drawQuestions(){
    const host=$('#questions');
    host.innerHTML=draft.questions.map((q,index)=>`<article class="card question" data-index="${index}"><div class="question-top"><span class="badge">${index+1} · ${typeNames[q.type]}</span><div><button class="subtle up" aria-label="上移题目">↑</button><button class="subtle down" aria-label="下移题目">↓</button><button class="subtle danger remove">删除题目</button></div></div><p class="meta">稳定 ID：${esc(q.id)}</p><label>题目标题<input class="qtitle" maxlength="500" value="${esc(q.title)}"></label><label class="check"><input class="qrequired" type="checkbox" ${q.required?'checked':''}>有效路径上的必答题</label>${q.type.includes('choice')?`<span class="section-label">选项 · 标签可编辑，ID 保持稳定</span><div class="options"></div><button class="secondary add-option">＋ 添加选项</button>`:''}<div class="validation row"></div>${q.type!=='text'?'<span class="section-label">条件跳转 · 数值较小的优先级先匹配</span><div class="rules"></div><button class="secondary add-rule">＋ 添加跳转规则</button>':''}</article>`).join('');
    $$('.question',host).forEach(node=>{
      const index=Number(node.dataset.index),q=draft.questions[index];
      bind('.qtitle','input',e=>q.title=e.target.value,node);bind('.qrequired','change',e=>q.required=e.target.checked,node);
      bind('.remove','click',()=>{readMeta();draft.questions.splice(index,1);render();},node);
      for(const [selector,delta] of [['.up',-1],['.down',1]])bind(selector,'click',()=>{const to=index+delta;if(to>=0&&to<draft.questions.length){readMeta();[draft.questions[index],draft.questions[to]]=[draft.questions[to],draft.questions[index]];render();}},node);
      if(q.type.includes('choice')){
        $('.options',node).innerHTML=q.options.map((o,i)=>`<div class="row option-line"><span>${esc(o.id)}</span><input aria-label="选项${i+1}" maxlength="300" value="${esc(o.label)}"><button class="subtle opt-up" data-i="${i}" aria-label="上移选项">↑</button><button class="subtle opt-down" data-i="${i}" aria-label="下移选项">↓</button><button class="subtle danger opt-remove" data-i="${i}" aria-label="删除选项">×</button></div>`).join('');
        $$('.option-line input',node).forEach((input,i)=>input.oninput=()=>q.options[i].label=input.value);
        $$('.opt-remove',node).forEach(b=>b.onclick=()=>{readMeta();q.options.splice(Number(b.dataset.i),1);render();});
        for(const [selector,delta] of [['.opt-up',-1],['.opt-down',1]])$$(selector,node).forEach(b=>b.onclick=()=>{const i=Number(b.dataset.i),to=i+delta;if(to>=0&&to<q.options.length){readMeta();[q.options[i],q.options[to]]=[q.options[to],q.options[i]];render();}});
        bind('.add-option','click',()=>{readMeta();q.options.push({id:id(),label:'新选项'});render();},node);
      }
      const keys=q.type==='multiple_choice'?['minSelections','maxSelections']:q.type==='text'?['minLength','maxLength']:q.type==='number'?['min','max']:[];
      const labels={minSelections:'最少选择',maxSelections:'最多选择',minLength:'最少字数',maxLength:'最多字数',min:'最小值',max:'最大值'};
      $('.validation',node).innerHTML=keys.map(k=>`<label>${labels[k]}<input type="number" step="${q.type==='number'?'any':'1'}" data-key="${k}" value="${q.validation[k]??''}" placeholder="默认"></label>`).join('')+(q.type==='number'?`<label class="check"><input class="integer" type="checkbox" ${q.validation.integerOnly?'checked':''}>仅整数</label>`:'');
      $$('[data-key]',node).forEach(input=>input.oninput=()=>{if(input.value==='')delete q.validation[input.dataset.key];else q.validation[input.dataset.key]=Number(input.value);});
      bind('.integer','change',e=>q.validation.integerOnly=e.target.checked,node);
      if(q.type!=='text'){
        const ops=q.type==='single_choice'?['eq']:q.type==='multiple_choice'?['contains_any','contains_all']:['eq','gt','gte','lt','lte'];
        $('.rules',node).innerHTML=q.routingRules.map((r,i)=>`<div class="rule" data-rule="${i}"><div class="row"><label>优先级<input class="priority" type="number" min="0" step="1" value="${r.priority}"></label><label>条件<select class="operator">${ops.map(o=>`<option ${o===r.condition.operator?'selected':''}>${o}</option>`).join('')}</select></label><label>操作数${q.type==='number'?`<input class="operand-number" type="number" step="any" value="${r.condition.operand}">`:`<select class="operand" ${q.type==='multiple_choice'?'multiple':''}>${q.options.map(o=>`<option value="${esc(o.id)}" ${(q.type==='multiple_choice'?r.condition.operand.includes(o.id):r.condition.operand===o.id)?'selected':''}>${esc(o.label)}</option>`).join('')}</select>`}</label><label>跳转至<select class="target"><option value="" ${r.target.kind==='end'?'selected':''}>结束问卷</option>${draft.questions.slice(index+1).map(t=>`<option value="${esc(t.id)}" ${r.target.questionId===t.id?'selected':''}>${esc(t.title)} (${esc(t.id)})</option>`).join('')}</select></label><button class="subtle danger remove-rule" aria-label="删除规则">×</button></div></div>`).join('');
        $$('.rule',node).forEach(rnode=>{const i=Number(rnode.dataset.rule),r=q.routingRules[i];bind('.priority','input',e=>r.priority=Number(e.target.value),rnode);bind('.operator','change',e=>r.condition.operator=e.target.value,rnode);bind('.operand-number','input',e=>r.condition.operand=Number(e.target.value),rnode);bind('.operand','change',e=>r.condition.operand=q.type==='multiple_choice'?[...e.target.selectedOptions].map(o=>o.value):e.target.value,rnode);bind('.target','change',e=>r.target=e.target.value?{kind:'question',questionId:e.target.value}:{kind:'end'},rnode);bind('.remove-rule','click',()=>{readMeta();q.routingRules.splice(i,1);render();},rnode);});
        bind('.add-rule','click',()=>{readMeta();q.routingRules.push({id:id(),priority:q.routingRules.length?Math.max(...q.routingRules.map(r=>r.priority))+10:10,condition:{operator:ops[0],operand:q.type==='number'?0:q.type==='multiple_choice'?(q.options.length?[q.options[0].id]:[]):q.options[0]?.id||''},target:{kind:'end'}});render();},node);
      }
      if(q.source){
        node.insertAdjacentHTML('beforeend',`<div class="source-panel"><p class="meta">来源题目 ${esc(q.source.questionId)} · V${q.source.questionVersion}（核心内容已固定）</p><div class="toolbar"><button class="secondary detach-source">解除关联后编辑本地副本</button><button class="secondary upgrade-source">选择版本替换此题</button><a href="/questions/${q.source.questionId}" target="_blank">题目历史与使用情况</a></div></div>`);
        $$('.qtitle,.qrequired,.options input,.options button,.add-option,.validation input',node).forEach(el=>el.disabled=true);
        bind('.detach-source','click',()=>{if(confirm('解除后此题作为本地副本编辑，不再参与该全局题目的跨问卷统计。确认解除？')){readMeta();delete q.source;render();}},node);
        bind('.upgrade-source','click',async()=>{await save();await showPicker(q.id);},node);
      } else {
        node.insertAdjacentHTML('beforeend','<div class="toolbar"><button class="secondary save-library-question">保存为常用题目</button></div>');
        bind('.save-library-question','click',async()=>{readMeta();const content={};for(const key of ['type','title','required','options','validation'])content[key]=q[key];const created=await api('/questions','POST',{content});q.source={questionId:created.definition._id,questionVersion:1};render();toast('已保存为常用题目；保存草稿以保留关联');},node);
      }
      if(draft.state==='sealed')$$('input,select,button',node).forEach(el=>el.disabled=true);
    });
  }
  render();
}

function validateLocal(q,value) {
  const v=q.validation||{};
  const empty=value===null||(q.type==='text'&&!value.trim())||(q.type==='multiple_choice'&&!value.length);
  if(empty){if(q.required)throw new Error('请回答此必答题');return null;}
  if(q.type==='multiple_choice'&&(value.length<(v.minSelections??0)||value.length>(v.maxSelections??q.options.length)))throw new Error('选择数量超出范围');
  if(q.type==='text'){value=value.trim();const n=[...value].length;if(n<(v.minLength??0)||n>(v.maxLength??10000))throw new Error('文本长度超出范围');}
  if(q.type==='number'&&(!Number.isFinite(value)||Math.abs(value)>Number.MAX_SAFE_INTEGER||value<(v.min??-Infinity)||value>(v.max??Infinity)||(v.integerOnly&&!Number.isInteger(value))))throw new Error('请输入范围内的'+(v.integerOnly?'整数':'有效数字'));
  return value;
}
function nextIndex(qs,index,value){
  const matched=(c)=>{if(value===null)return false;const x=c.operand;switch(c.operator){case'eq':return value===x;case'contains_any':return x.some(y=>value.includes(y));case'contains_all':return x.every(y=>value.includes(y));case'gt':return value>x;case'gte':return value>=x;case'lt':return value<x;case'lte':return value<=x;default:return false;}};
  for(const r of [...qs[index].routingRules].sort((a,b)=>a.priority-b.priority))if(matched(r.condition))return r.target.kind==='end'?qs.length:qs.findIndex(q=>q.id===r.target.questionId);
  return index+1;
}

async function fill(publicId,previewId=null) {
  const data=await api(previewId?`/surveys/${previewId}/preview`:'/public/surveys/'+publicId);
  const qs=data.questions;let cursor=0,history=[],values={},requestId=crypto.randomUUID(),lockedPayload=null,busy=false;
  function render(){
    const q=qs[cursor],done=cursor>=qs.length;
    app.innerHTML=`<div class="fill">${heading(previewId?'DRAFT PREVIEW':'YOUR VOICE MATTERS',data.title,data.description)}<p class="meta">V${data.surveyVersion} · ${data.settings.anonymous?'账号身份对创建者隐藏':'实名问卷'}${data.deadlineAt?' · 截止 '+date(data.deadlineAt):''}${previewId?' · 预览不保存答卷':''}</p><div class="progress"><span style="width:${Math.round(cursor/qs.length*100)}%"></span></div><section class="card">${done?'<h2>已完成本次填写</h2><p class="muted">请核对以下答案后提交。</p><div id="review"></div>':`<p class="meta">第 ${cursor+1} / ${qs.length} 题</p><h2>${esc(q.title)} ${q.required?'<span class="required">*</span>':''}</h2><p class="hint">${q.type==='multiple_choice'?'选择数量 '+(q.validation.minSelections??0)+'–'+(q.validation.maxSelections??q.options.length):q.type==='text'?'文本长度 '+(q.validation.minLength??0)+'–'+(q.validation.maxLength??10000):q.type==='number'?'范围 '+(q.validation.min??'不限')+' 至 '+(q.validation.max??'不限')+(q.validation.integerOnly?'，仅整数':''): '请选择一项'}</p><form id="answer">${q.type.includes('choice')?q.options.map(o=>`<label class="choice"><input type="${q.type==='single_choice'?'radio':'checkbox'}" name="choice" value="${esc(o.id)}" ${(q.type==='single_choice'?values[q.id]===o.id:(values[q.id]||[]).includes(o.id))?'checked':''}>${esc(o.label)}</label>`).join(''):q.type==='text'?`<label for="value">你的回答</label><textarea id="value" maxlength="10000">${esc(values[q.id]??'')}</textarea>`:`<label for="value">数字回答</label><input id="value" type="number" step="${q.validation.integerOnly?'1':'any'}" value="${values[q.id]??''}">`}<div class="toolbar"><button type="submit">下一步</button></div></form>`}<div class="toolbar"><button id="back" class="secondary" ${history.length&&!lockedPayload?'':'disabled'}>上一题</button>${done?`<button id="submit">${previewId?'完成预览':'确认提交'}</button>`:''}</div></section><p class="hint">${data.settings.anonymous?'匿名只隐藏账号身份，请避免在自由文本中填写个人信息。':'本版本为实名问卷，创建者可以看到账号标识。'}</p></div>`;
    if(done){const host=$('#review');for(const idx of history){const question=qs[idx];const p=document.createElement('p');let val=values[question.id];if(question.type.includes('choice'))val=(Array.isArray(val)?val:[val]).map(x=>question.options.find(o=>o.id===x)?.label).filter(Boolean).join('、');p.textContent=question.title+'：'+(val??'未回答');host.append(p);}}
    bind('#answer','submit',e=>{e.preventDefault();let val;if(q.type==='single_choice')val=$('input[name=choice]:checked')?.value??null;else if(q.type==='multiple_choice')val=$$('input[name=choice]:checked').map(x=>x.value);else if(q.type==='text')val=$('#value').value;else val=$('#value').value===''?null:Number($('#value').value);val=validateLocal(q,val);if(val===null)delete values[q.id];else values[q.id]=val;history.push(cursor);cursor=nextIndex(qs,cursor,val);render();});
    bind('#back','click',()=>{const previous=history.pop();if(previous===undefined)return;for(let i=previous+1;i<qs.length;i++)delete values[qs[i].id];cursor=previous;render();});
    bind('#submit','click',async()=>{
      if(busy)return;
      if(previewId){toast('预览完成，未生成正式答卷');return;}
      busy=true;$('#submit').disabled=true;
      lockedPayload??={surveyVersion:data.surveyVersion,requestId,answers:history.filter(i=>values[qs[i].id]!==undefined).map(i=>({questionId:qs[i].id,value:values[qs[i].id]}))};
      try{await api('/public/surveys/'+publicId+'/submissions','POST',lockedPayload);app.innerHTML=`<div class="fill card success"><h1>提交成功</h1><p>感谢你的回答，答卷已保存。</p><p>${data.submissionPolicy==='latest_only'?'再次填写会保留本次历史，仅最新一份参与有效统计。':'每次新填写都会单独计入统计。'}</p><div class="toolbar"><button id="again">开始新一轮填写</button><a class="button secondary" href="/dashboard">返回工作台</a></div></div>`;bind('#again','click',()=>fill(publicId));}
      finally{busy=false;if($('#submit')){$('#submit').disabled=false;if($('#back'))$('#back').disabled=true;}}
    });
  }
  render();
}

async function statisticsPage(surveyId){
  const s=await api('/surveys/'+surveyId),versions=await api(`/surveys/${surveyId}/versions`);let version=s.publishedVersion,mode='current_effective',question='',offset=0,rowsOffset=0;
  async function render(){
    const params=`version=${version}&mode=${mode}&offset=${offset}&limit=20`;
    const stats=await api(`/surveys/${surveyId}${question?'/questions/'+question:''}/statistics?${params}`);
    const rows=await api(`/surveys/${surveyId}/submissions?version=${version}&mode=${mode}&offset=${rowsOffset}&limit=20`);
    const allQs=versions.items.find(v=>v.version===version).questions;
    for(const record of rows.items)for(const answer of record.answers){const q=allQs.find(item=>item.id===answer.questionId);if(q?.options.length){const label=value=>q.options.find(o=>o.id===value)?.label??value;answer.value=Array.isArray(answer.value)?answer.value.map(label):label(answer.value);}}
    app.innerHTML=heading('INSIGHTS',s.title,'每一道题，按实际回答数统计。',`<a class="button secondary" href="/surveys/${surveyId}/edit">编辑管理</a>`)+
      `<div class="card row"><label>问卷版本<select id="version">${versions.items.filter(v=>v.state==='sealed'&&v.version<=s.publishedVersion).map(v=>`<option value="${v.version}" ${version===v.version?'selected':''}>V${v.version}</option>`).join('')}</select></label><label>统计口径<select id="mode"><option value="current_effective" ${mode==='current_effective'?'selected':''}>当前有效（按重复策略）</option><option value="historical_raw" ${mode==='historical_raw'?'selected':''}>历史原始（不去重）</option></select></label><label>题目<select id="question"><option value="">全部题目</option>${allQs.map(q=>`<option value="${esc(q.id)}" ${question===q.id?'selected':''}>${esc(q.title)}</option>`).join('')}</select></label></div><div class="metrics"><div class="metric">此版本原始提交<strong>${stats.rawSubmissionCount}</strong></div><div class="metric">此版本当前有效<strong>${stats.effectiveSubmissionCount}</strong></div><div class="metric">本次口径选中<strong>${stats.selectedSubmissionCount}</strong></div></div><p class="hint">${s.submissionPolicy==='latest_only'?'整份问卷跨版本选择每人的最新答卷，再筛选此版本。':'每份提交都计入有效统计。'} 跳题会使不同题目回答数不同。</p>`+
      stats.questions.map(q=>`<section class="card"><span class="badge">${typeNames[q.type]}</span><h2>${esc(q.title)}</h2><p class="meta">实际回答 ${q.answeredCount} 份</p>${q.options?q.options.map(o=>`<div class="statline"><span>${esc(o.label)}</span><strong>${o.count}</strong></div><div class="bar"><span style="width:${q.answeredCount?o.count/q.answeredCount*100:0}%"></span></div>`).join(''):`${q.type==='number'?`<h3>平均值：${q.mean??'暂无数据'}</h3>`:''}<div class="answer-list">${q.values.map(v=>`<p>${esc(v)}</p>`).join('')||'<p class="muted">暂无回答</p>'}</div><p class="meta">回答明细 ${offset+1}–${Math.min(offset+20,q.answeredCount)} / ${q.answeredCount}</p>`}</section>`).join('')+
      `<div class="toolbar"><button id="value-prev" class="secondary" ${offset?'':'disabled'}>上一页回答内容</button><button id="value-next" class="secondary" ${stats.questions.some(q=>q.values&&offset+20<q.answeredCount)?'':'disabled'}>下一页回答内容</button></div><section class="card"><h2>答卷记录</h2><p class="hint">匿名记录仅展示回答，不提供账号标识。共 ${rows.total} 份。</p><div class="table-wrap"><table><thead><tr><th>提交时间</th><th>版本 / 身份</th><th>回答内容</th></tr></thead><tbody>${rows.items.map(r=>`<tr><td>${date(r.submittedAt)}</td><td>V${r.surveyVersion}<br>${r.anonymous?'匿名':esc(r.respondentUsername ?? r.respondentId)}</td><td>${r.answers.map(a=>`<p>${esc(allQs.find(q=>q.id===a.questionId)?.title||a.questionId)}：${esc(Array.isArray(a.value)?a.value.join('、'):a.value)}</p>`).join('')}</td></tr>`).join('')}</tbody></table></div><div class="toolbar"><button id="rows-prev" class="secondary" ${rowsOffset?'':'disabled'}>上一页答卷</button><button id="rows-next" class="secondary" ${rowsOffset+20<rows.total?'':'disabled'}>下一页答卷</button></div></section>`;
    bind('#version','change',async e=>{version=Number(e.target.value);question='';offset=rowsOffset=0;await render();});bind('#mode','change',async e=>{mode=e.target.value;offset=rowsOffset=0;await render();});bind('#question','change',async e=>{question=e.target.value;offset=0;await render();});
    bind('#value-prev','click',async()=>{offset-=20;await render();});bind('#value-next','click',async()=>{offset+=20;await render();});bind('#rows-prev','click',async()=>{rowsOffset-=20;await render();});bind('#rows-next','click',async()=>{rowsOffset+=20;await render();});
  }
  await render();
}

function libraryContentForm(c={type:'number',title:'',required:true,options:[],validation:{}}) {
  return `<label for="lib-type">题型</label><select id="lib-type">${Object.entries(typeNames).map(([t,n])=>`<option value="${t}" ${t===c.type?'selected':''}>${n}</option>`).join('')}</select>
    <label for="lib-title">题目名称</label><input id="lib-title" maxlength="500" required value="${esc(c.title)}">
    <label class="check"><input id="lib-required" type="checkbox" ${c.required?'checked':''}>必答题</label>
    <div id="lib-options-wrap"><label for="lib-options">选项（每行一项，已有选项按原顺序保留身份）</label><textarea id="lib-options">${esc(c.options.map(o=>o.label).join('\n'))}</textarea></div>
    <div id="lib-constraints"></div>`;
}
function wireContentForm(c={type:'number',validation:{}}) {
  function draw(){const t=$('#lib-type').value,v=c.type===t?c.validation:{};
    $('#lib-options-wrap').hidden=!t.includes('choice');
    const fields=t==='number'?[['min','最小值'],['max','最大值']]:t==='text'?[['minLength','最少字数'],['maxLength','最多字数']]:t==='multiple_choice'?[['minSelections','最少选择'],['maxSelections','最多选择']]:[];
    $('#lib-constraints').innerHTML='<div class="row">'+fields.map(([k,n])=>`<label>${n}<input class="lib-bound" data-key="${k}" type="number" step="${t==='number'?'any':'1'}" value="${v[k]??''}"></label>`).join('')+'</div>'+(t==='number'?`<label class="check"><input id="lib-integer" type="checkbox" ${v.integerOnly?'checked':''}>仅整数</label>`:'');}
  draw();bind('#lib-type','change',draw);
}
function readContentForm(previous={options:[]}) {
  const type=$('#lib-type').value, validation={};
  $$('.lib-bound').forEach(n=>{if(n.value!=='')validation[n.dataset.key]=Number(n.value);});
  if(type==='number')validation.integerOnly=$('#lib-integer').checked;
  const options=type.includes('choice')?$('#lib-options').value.split('\n').filter(x=>x.trim()).map((label,i)=>({id:previous.options[i]?.id||id(),label:label.trim()})):[];
  return {type,title:$('#lib-title').value,required:$('#lib-required').checked,options,validation};
}

async function questionsPage(search='',scope='accessible',offset=0) {
  const data=await api(`/questions?search=${encodeURIComponent(search)}&scope=${scope}&offset=${offset}&limit=12`);
  app.innerHTML=heading('QUESTION LIBRARY','我的题目与共享题目','题目拥有独立身份，每次修改生成新版本。', '<a class="button secondary" href="/question-banks">管理题库</a>')+
    `<form id="lib-search" class="card row"><label>搜索题目<input id="search" value="${esc(search)}" maxlength="200"></label><label>范围<select id="lib-scope"><option value="accessible">全部可用题目</option><option value="mine">我的题目</option><option value="shared">共享给我</option></select></label><button>搜索</button></form>
    <div class="grid">${data.items.map(q=>`<article class="card"><span class="badge">V${q.currentVersion} · ${q.canEdit?'我的题目':'共享给我'}${q.archived?' · 已归档':''}</span><h2><a href="/questions/${q._id}">${esc(q.current.content.title)}</a></h2><p class="meta">${typeNames[q.current.content.type]} · 创建者 ${esc(q.ownerUsername)}<br>来源：${q.forkedFrom?'独立派生自 '+esc(q.forkedFrom.questionId)+' / V'+q.forkedFrom.questionVersion:'原创题目'}</p><a class="button secondary" href="/questions/${q._id}">历史与使用情况</a></article>`).join('')||'<p class="muted">没有符合条件的题目。</p>'}</div>
    <div class="toolbar"><button id="lib-prev" ${offset?'':'disabled'}>上一页</button><span>共 ${data.total} 题</span><button id="lib-next" ${offset+12<data.total?'':'disabled'}>下一页</button></div>
    <form id="lib-create" class="card"><h2>创建常用题目</h2>${libraryContentForm()}<p class="hint">跳转规则由每份问卷独立设置。新题默认私有。</p><button>保存到题目库</button></form>`;
  $('#lib-scope').value=scope;wireContentForm();
  bind('#lib-search','submit',e=>{e.preventDefault();return questionsPage($('#search').value,$('#lib-scope').value);});
  bind('#lib-prev','click',()=>questionsPage(search,scope,offset-12));bind('#lib-next','click',()=>questionsPage(search,scope,offset+12));
  bind('#lib-create','submit',async e=>{e.preventDefault();const q=await api('/questions','POST',{content:readContentForm()});location.href='/questions/'+q.definition._id;});
}

async function questionPage(qid,selected=null,historyOffset=0) {
  const q=await api('/questions/'+qid), history=await api(`/questions/${qid}/versions?offset=${historyOffset}&limit=20`);
  let chosen=history.items.find(v=>v.version===selected)||history.items[0];
  app.innerHTML=heading('VERSIONED QUESTION',q.current.content.title,`${typeNames[q.current.content.type]} · 创建者 ${q.ownerUsername} · 当前 V${q.currentVersion}`,'<a class="button secondary" href="/questions">全部题目</a>')+
    `<section class="card"><h2>版本历史</h2><p class="hint">从任意历史版本派生；恢复会追加新版本。已导入问卷始终固定原版本。</p><label for="lib-history">选择版本</label><select id="lib-history">${history.items.map(v=>`<option value="${v.version}" ${v.version===chosen.version?'selected':''}>V${v.version} · ${v.changeType} · ${v.parentVersion?'源于 V'+v.parentVersion:'初始版本'}${v.restoredFromVersion?' · 恢复 V'+v.restoredFromVersion:''}</option>`).join('')}</select><p class="meta">题目身份：${esc(qid)}${q.forkedFrom?'<br>派生来源：'+esc(q.forkedFrom.questionId)+' / V'+q.forkedFrom.questionVersion:''}</p><div class="toolbar"><button id="history-prev" ${historyOffset?'':'disabled'}>上一页历史</button><button id="history-next" ${historyOffset+20<history.total?'':'disabled'}>下一页历史</button></div></section>
    <form id="lib-edit" class="card"><h2>${q.canEdit?'从所选版本创建新版本':'所选版本内容'}</h2>${libraryContentForm(chosen.content)}<div class="toolbar">${q.canEdit?`<button ${q.archived?'disabled':''}>保存为 V${q.currentVersion+1}</button><button type="button" id="lib-restore" class="secondary" ${q.archived?'disabled':''}>恢复所选版本</button>`:''}<button type="button" id="lib-fork" class="secondary" ${q.archived?'disabled':''}>独立派生为我的题目</button></div></form>
    ${q.canEdit?`<form id="lib-share" class="card"><h2>共享与归档</h2><label for="share-users">共享给注册用户名（用逗号分隔，留空撤销）</label><input id="share-users" value="${esc(q.sharedUsernames.join(', '))}"><p class="hint">共享允许读取与复用；答卷统计由问卷所有者另行授权。</p><div class="toolbar"><button>保存共享范围</button><button type="button" class="secondary" id="lib-archive">${q.archived?'取消归档':'归档题目'}</button></div></form>`:''}
    <section class="card"><h2>加入我的题库</h2><div id="bank-choices"></div></section>
    <section class="card"><h2>使用情况</h2><div id="lib-usage"></div></section>
    <section class="card"><h2>跨问卷统计</h2><p class="hint">统计所选精确版本 V${chosen.version}；按提交次数统计，不代表跨问卷去重人数。共享数据每份问卷至少 3 份实际回答才汇入。</p><div class="row"><label>统计范围<select id="stat-scope"><option value="mine">我拥有的问卷</option><option value="consented_shared">加上已授权贡献的数据</option></select></label><label>统计口径<select id="stat-mode"><option value="current_effective">当前有效</option><option value="historical_raw">历史原始</option></select></label></div><div id="lib-statistics"></div></section>`;
  wireContentForm(chosen.content);
  if(!q.canEdit)$$('#lib-edit input,#lib-edit select,#lib-edit textarea').forEach(n=>n.disabled=true);
  bind('#lib-history','change',e=>questionPage(qid,Number(e.target.value),historyOffset));
  bind('#history-prev','click',()=>questionPage(qid,null,historyOffset-20));bind('#history-next','click',()=>questionPage(qid,null,historyOffset+20));
  bind('#lib-edit','submit',async e=>{e.preventDefault();await api(`/questions/${qid}/versions`,'POST',{content:readContentForm(chosen.content),parentVersion:chosen.version,expectedCurrentVersion:q.currentVersion});await questionPage(qid);toast('已追加新版本');});
  bind('#lib-restore','click',async()=>{await api(`/questions/${qid}/restore`,'POST',{version:chosen.version,expectedCurrentVersion:q.currentVersion});await questionPage(qid);toast('恢复完成，旧版本保留');});
  bind('#lib-fork','click',async()=>{const fork=await api(`/questions/${qid}/fork`,'POST',{version:chosen.version});location.href='/questions/'+fork.definition._id;});
  bind('#lib-share','submit',async e=>{e.preventDefault();await api(`/questions/${qid}/sharing`,'PATCH',{usernames:$('#share-users').value.split(/[,，]/).map(s=>s.trim()).filter(Boolean),expectedRevision:q.revision});await questionPage(qid,chosen.version,historyOffset);toast('共享范围已更新');});
  bind('#lib-archive','click',async()=>{await api(`/questions/${qid}/archive`,'PATCH',{archived:!q.archived,expectedRevision:q.revision});await questionPage(qid,chosen.version,historyOffset);});
  const banks=await api('/question-banks?limit=100');
  $('#bank-choices').innerHTML=banks.items.length?`<label>题库<select id="target-bank">${banks.items.map(b=>`<option value="${b._id}">${esc(b.name)}</option>`).join('')}</select></label><label class="check"><input id="bank-pin" type="checkbox" checked>固定所选 V${chosen.version}（取消后在选题时解析最新版）</label><button id="add-to-bank" class="secondary">加入题库</button>`:'<a href="/question-banks">先创建题库</a>';
  bind('#add-to-bank','click',async()=>{const bank=await api('/question-banks/'+$('#target-bank').value);await api('/question-banks/'+bank._id+'/items','PUT',{questionId:qid,pinnedVersion:$('#bank-pin').checked?chosen.version:null,expectedRevision:bank.revision});toast('已加入题库');});
  async function usage(offset=0){const rows=await api(`/questions/${qid}/usage?version=${chosen.version}&offset=${offset}&limit=10`);$('#lib-usage').innerHTML=`<p class="hint">显示我的版本与当前可公开访问的问卷，其他私有使用记录不披露。</p>${rows.items.map(r=>`<p>${esc(r.title)} · 问卷 V${r.surveyVersion} · ${esc(({draft:'草稿',published:'当前发布',historical:'历史版本'})[r.status])}</p>`).join('')||'<p>暂无可见使用记录。</p>'}<div class="toolbar"><button id="usage-prev" ${offset?'':'disabled'}>上一页使用记录</button><span>${rows.total} 条</span><button id="usage-next" ${offset+10<rows.total?'':'disabled'}>下一页使用记录</button></div>`;bind('#usage-prev','click',()=>usage(offset-10));bind('#usage-next','click',()=>usage(offset+10));}
  async function statistics(){const s=await api(`/questions/${qid}/statistics?version=${chosen.version}&scope=${$('#stat-scope').value}&mode=${$('#stat-mode').value}`);$('#lib-statistics').innerHTML=`<div class="metrics"><div class="metric">参与统计的问卷<strong>${s.surveyCount}</strong></div><div class="metric">提交次数<strong>${s.submissionCount}</strong></div><div class="metric">实际回答<strong>${s.answeredCount}</strong></div></div>${s.options?s.options.map(o=>`<div class="statline"><span>${esc(o.label)}</span><strong>${o.count}</strong></div>`).join(''):s.type==='number'?`<h3>平均值：${s.mean??'暂无数据'}</h3>${s.distribution.map(bin=>`<div class="statline"><span>${bin.lower===null?'小于 '+bin.upper:bin.upper===null?bin.lower+' 及以上':'['+bin.lower+', '+bin.upper+')'}</span><strong>${bin.count}</strong></div>`).join('')}`:'<p class="hint">这里只展示回答数；文本原文可在自己问卷的统计中查看。</p>'}<p class="hint">问卷数仅计当前口径下有提交参与统计的去重问卷：无提交、全部答卷被新版替代或被小样本抑制的问卷不计入；题目被跳过仍可计入问卷数，但不计实际回答。使用关系数量另见上方“使用情况”。</p><p class="hint">其他未授权问卷已排除；${s.exclusions.suppressedSurveyCount} 份共享问卷因样本不足而排除。不同题目版本分别统计。</p>`;}
  bind('#stat-scope','change',statistics);bind('#stat-mode','change',statistics);await usage();await statistics();
}

async function banksPage(offset=0) {
  const banks=await api(`/question-banks?offset=${offset}&limit=12`);
  app.innerHTML=heading('COLLECTIONS','我的题库','将常用题组织为多个题库；移除成员不会删除原题。')+`<div class="grid">${banks.items.map(b=>`<article class="card"><h2><a href="/question-banks/${b._id}">${esc(b.name)}</a></h2><p>${esc(b.description)}</p><p class="meta">${b.items.length} 道题目</p></article>`).join('')}</div><div class="toolbar"><button id="bank-prev" ${offset?'':'disabled'}>上一页</button><span>共 ${banks.total} 个题库</span><button id="bank-next" ${offset+12<banks.total?'':'disabled'}>下一页</button></div><form id="bank-create" class="card"><h2>新建题库</h2><label for="bank-name">题库名称</label><input id="bank-name" required maxlength="200"><label for="bank-desc">题库说明</label><textarea id="bank-desc" maxlength="2000"></textarea><button>创建题库</button></form>`;
  bind('#bank-create','submit',async e=>{e.preventDefault();const b=await api('/question-banks','POST',{name:$('#bank-name').value,description:$('#bank-desc').value});location.href='/question-banks/'+b._id;});
  bind('#bank-prev','click',()=>banksPage(offset-12));bind('#bank-next','click',()=>banksPage(offset+12));
}
async function bankPage(bid) {
  const b=await api('/question-banks/'+bid);
  app.innerHTML=heading('QUESTION BANK',b.name,b.description,'<a class="button secondary" href="/question-banks">全部题库</a>')+`<form id="bank-edit" class="card"><label for="bank-name">题库名称</label><input id="bank-name" value="${esc(b.name)}" required maxlength="200"><label for="bank-desc">题库说明</label><textarea id="bank-desc" maxlength="2000">${esc(b.description)}</textarea><button>保存题库信息</button></form><div class="grid">${b.items.map(item=>`<article class="card"><h2>${item.available?`<a href="/questions/${item.questionId}">${esc(item.content.title)}</a>`:'原题已归档或撤销共享'}</h2><p>${item.available?'选用 V'+item.resolvedVersion:''} · ${item.pinnedVersion?'固定 V'+item.pinnedVersion:'选题时使用最新版'}</p><button class="secondary bank-remove" data-q="${item.questionId}">移除成员</button></article>`).join('')||'<p>题库还没有成员。</p>'}</div><section class="card"><h2>从可用题目中添加</h2><div id="library-picker"></div></section>`;
  bind('#bank-edit','submit',async e=>{e.preventDefault();await api('/question-banks/'+bid,'PATCH',{name:$('#bank-name').value,description:$('#bank-desc').value,expectedRevision:b.revision});await bankPage(bid);toast('题库已保存');});
  $$('.bank-remove').forEach(n=>bind(`[data-q="${n.dataset.q}"]`,'click',async()=>{await api(`/question-banks/${bid}/items/${n.dataset.q}?expectedRevision=${b.revision}`,'DELETE');await bankPage(bid);}));
  await libraryPicker($('#library-picker'),async(qid,version)=>{await api('/question-banks/'+bid+'/items','PUT',{questionId:qid,pinnedVersion:version,expectedRevision:b.revision});await bankPage(bid);});
}
async function libraryPicker(host,onSelect,search='',offset=0,bankId='') {
  const banks=await api('/question-banks?limit=100');
  let rows,total;
  if(bankId){const bank=await api('/question-banks/'+bankId);const filtered=bank.items.filter(i=>i.available&&i.content.title.toLowerCase().includes(search.toLowerCase()));total=filtered.length;rows=filtered.slice(offset,offset+10).map(i=>({_id:i.questionId,currentVersion:i.resolvedVersion,current:{content:i.content}}));}
  else {const data=await api(`/questions?search=${encodeURIComponent(search)}&offset=${offset}&limit=10&activeOnly=true`);rows=data.items;total=data.total;}
  host.innerHTML=`<form id="picker-search" class="row"><label>题库范围<select id="picker-bank"><option value="">全部可用题目</option>${banks.items.map(b=>`<option value="${b._id}">${esc(b.name)}</option>`).join('')}</select></label><label>搜索<input id="picker-term" value="${esc(search)}" maxlength="200"></label><button>搜索选题</button></form><div id="picker-results">${rows.map(q=>`<div class="picker-row"><span>${esc(q.current.content.title)} · ${typeNames[q.current.content.type]}</span><label>版本<select class="picker-version" data-qid="${q._id}"><option value="${q.currentVersion}">V${q.currentVersion}</option></select></label><button class="secondary pick-question" data-qid="${q._id}">选用</button></div>`).join('')||'<p class="muted">暂无可用题目。</p>'}</div><div class="toolbar"><button type="button" id="picker-prev" ${offset?'':'disabled'}>上一页选题</button><button type="button" id="picker-next" ${offset+10<total?'':'disabled'}>下一页选题</button></div>`;
  $('#picker-bank',host).value=bankId;
  bind('#picker-search','submit',e=>{e.preventDefault();return libraryPicker(host,onSelect,$('#picker-term',host).value,0,$('#picker-bank',host).value);},host);
  bind('#picker-prev','click',()=>libraryPicker(host,onSelect,search,offset-10,bankId),host);bind('#picker-next','click',()=>libraryPicker(host,onSelect,search,offset+10,bankId),host);
  for(const q of rows){let vOffset=0;const select=$(`.picker-version[data-qid="${q._id}"]`,host);async function moreVersions(){const history=await api(`/questions/${q._id}/versions?offset=${vOffset}&limit=100`);const selected=select.value==='more'?String(q.currentVersion):select.value;const versions=history.items;select.innerHTML=(vOffset?select.innerHTML.replace(/<option value="more">.*?<\/option>/,''):versions.some(v=>v.version===q.currentVersion)?'':`<option value="${q.currentVersion}">V${q.currentVersion} · 固定选用</option>`)+versions.map(v=>`<option value="${v.version}">V${v.version} · ${esc(v.content.title)}</option>`).join('')+(vOffset+100<history.total?'<option value="more">加载更早版本…</option>':'');select.value=selected;vOffset+=100;}await moreVersions();select.onchange=()=>{if(select.value==='more')moreVersions().catch(showError);};}
  $$('.pick-question',host).forEach(button=>bind(`.pick-question[data-qid="${button.dataset.qid}"]`,'click',()=>onSelect(button.dataset.qid,Number($(`.picker-version[data-qid="${button.dataset.qid}"]`,host).value)),host));
}

async function start(){
  const path=location.pathname;
  try{const info=await api('/me');me=info.user;csrf=info.csrfToken;$('#identity').textContent=me.username;$('#logout').hidden=false;}catch(e){if(e.status!==401)throw e;}
  bind('#logout','click',async()=>{await api('/auth/logout','POST');location.href='/login';});
  if(path==='/login'||path==='/register')return authPage(path==='/register');
  if(!me){location.href='/login?next='+encodeURIComponent(path);return;}
  if(path==='/'||path==='/dashboard')return dashboard();
  if(path==='/surveys/new')return newSurvey();
  if(path==='/questions')return questionsPage();
  if(path==='/question-banks')return banksPage();
  const bits=path.split('/');
  if(bits[1]==='questions')return questionPage(bits[2]);
  if(bits[1]==='question-banks')return bankPage(bits[2]);
  if(bits[1]==='survey')return fill(bits[2]);
  if(bits[1]==='surveys'&&bits[3]==='edit')return editor(bits[2]);
  if(bits[1]==='surveys'&&bits[3]==='preview')return fill(null,bits[2]);
  if(bits[1]==='surveys'&&bits[3]==='statistics')return statisticsPage(bits[2]);
  throw new Error('页面不存在');
}
start().catch(error=>{app.innerHTML=heading('NOTICE','暂时无法打开',error.message,'<a class="button secondary" href="/dashboard">返回工作台</a>');});
