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
    if(draft){drawQuestions();$$('.add').forEach(b=>b.onclick=()=>{readMeta();const type=b.dataset.type;draft.questions.push({id:id(),type,title:'新'+typeNames[type],required:false,options:type.includes('choice')?[{id:id(),label:'选项一'},{id:id(),label:'选项二'}]:[],validation:{},routingRules:[]});render();});}
    bind('#derive','click',async()=>{draft=await api(`/surveys/${surveyId}/draft-from-published`,'POST');survey=await api('/surveys/'+surveyId);render();});
    bind('#save','click',()=>save());
    bind('#preview','click',async()=>{await save();await api(`/surveys/${surveyId}/preview`);window.open(`/surveys/${surveyId}/preview`,'_blank');});
    bind('#publish','click',async()=>{if(draft.state!=='sealed')await save();const published=await api(`/surveys/${surveyId}/publish`,'POST',{expectedRevision:draft.revision});survey=published;draft=null;render();const box=document.createElement('div');box.className='success';const a=document.createElement('a');a.href=published.publicUrl;a.textContent=published.publicUrl;box.append('发布成功。公开填写链接：',a);app.prepend(box);});
  }
  function readMeta(){survey.title=$('#title').value;survey.description=$('#description').value;survey.submissionPolicy=$('#policy').value;survey.deadlineAt=$('#deadline').value?new Date($('#deadline').value).toISOString():null;if(draft)draft.settings.anonymous=$('#anonymous').checked;}
  async function save(){readMeta();const changes={title:survey.title,description:survey.description,submissionPolicy:survey.submissionPolicy,deadlineAt:survey.deadlineAt};survey=await api('/surveys/'+surveyId,'PATCH',changes);if(draft&&draft.state==='draft')draft=await api(`/surveys/${surveyId}/draft`,'PUT',{expectedRevision:draft.revision,settings:draft.settings,questions:draft.questions});$('#saved').textContent='已保存'+(draft?' · revision '+draft.revision:'');toast('保存成功');}
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
      `<div class="toolbar"><button id="value-prev" class="secondary" ${offset?'':'disabled'}>上一页回答内容</button><button id="value-next" class="secondary" ${stats.questions.some(q=>q.values&&offset+20<q.answeredCount)?'':'disabled'}>下一页回答内容</button></div><section class="card"><h2>答卷记录</h2><p class="hint">匿名记录仅展示回答，不提供账号标识。共 ${rows.total} 份。</p><div class="table-wrap"><table><thead><tr><th>提交时间</th><th>版本 / 身份</th><th>回答内容</th></tr></thead><tbody>${rows.items.map(r=>`<tr><td>${date(r.submittedAt)}</td><td>V${r.surveyVersion}<br>${r.anonymous?'匿名':esc(r.respondentId)}</td><td>${r.answers.map(a=>`<p>${esc(allQs.find(q=>q.id===a.questionId)?.title||a.questionId)}：${esc(Array.isArray(a.value)?a.value.join('、'):a.value)}</p>`).join('')}</td></tr>`).join('')}</tbody></table></div><div class="toolbar"><button id="rows-prev" class="secondary" ${rowsOffset?'':'disabled'}>上一页答卷</button><button id="rows-next" class="secondary" ${rowsOffset+20<rows.total?'':'disabled'}>下一页答卷</button></div></section>`;
    bind('#version','change',async e=>{version=Number(e.target.value);question='';offset=rowsOffset=0;await render();});bind('#mode','change',async e=>{mode=e.target.value;offset=rowsOffset=0;await render();});bind('#question','change',async e=>{question=e.target.value;offset=0;await render();});
    bind('#value-prev','click',async()=>{offset-=20;await render();});bind('#value-next','click',async()=>{offset+=20;await render();});bind('#rows-prev','click',async()=>{rowsOffset-=20;await render();});bind('#rows-next','click',async()=>{rowsOffset+=20;await render();});
  }
  await render();
}

async function start(){
  const path=location.pathname;
  try{const info=await api('/me');me=info.user;csrf=info.csrfToken;$('#identity').textContent=me.username;$('#logout').hidden=false;}catch(e){if(e.status!==401)throw e;}
  bind('#logout','click',async()=>{await api('/auth/logout','POST');location.href='/login';});
  if(path==='/login'||path==='/register')return authPage(path==='/register');
  if(!me){location.href='/login?next='+encodeURIComponent(path);return;}
  if(path==='/'||path==='/dashboard')return dashboard();
  if(path==='/surveys/new')return newSurvey();
  const bits=path.split('/');
  if(bits[1]==='survey')return fill(bits[2]);
  if(bits[1]==='surveys'&&bits[3]==='edit')return editor(bits[2]);
  if(bits[1]==='surveys'&&bits[3]==='preview')return fill(null,bits[2]);
  if(bits[1]==='surveys'&&bits[3]==='statistics')return statisticsPage(bits[2]);
  throw new Error('页面不存在');
}
start().catch(error=>{app.innerHTML=heading('NOTICE','暂时无法打开',error.message,'<a class="button secondary" href="/dashboard">返回工作台</a>');});
