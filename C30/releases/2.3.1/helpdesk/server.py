"""The web app and its JSON API (standard library only). Runs on http://localhost:8730.

API (JSON):
    GET  /api/version
    GET  /api/customers
    POST /api/chat                          {"message": ..., "conversation_id"?: ..., "customer_id"?: ..., "seed"?: ...}
    GET  /api/traces/<trace_id>
    GET  /api/conversations/<id>/export
    POST /api/reset
    GET  /policies/<doc_id>/v<version>      the policy text that a citation links to
"""

import html
import json
import re
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import APP_VERSION, MODEL_NAME, PROMPT_VERSION, assistant, config, corpus, export, store

STATE = {"seed": None, "mode": "sim"}


class Handler(BaseHTTPRequestHandler):
    server_version = "larkfield-helpdesk"

    def log_message(self, fmt, *args):  # one short line per request
        print(f"{self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")

    def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data, extra: dict | None = None) -> None:
        self._send(status, json.dumps(data, indent=2, ensure_ascii=False).encode(), "application/json; charset=utf-8",
                   extra)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n))
        except json.JSONDecodeError:
            return {"_invalid": True}

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        if path == "/api/version":
            return self._json(200, {"app_version": APP_VERSION, "model": MODEL_NAME if STATE["mode"] == "sim"
                                    else f"live:{config.LIVE_MODEL}", "prompt_version": PROMPT_VERSION,
                                    "app_date": config.TODAY})
        if path == "/api/customers":
            return self._json(200, [{"id": c["id"], "name": c["name"], "language": c["language"]}
                                    for c in store.customers()])
        m = re.fullmatch(r"/api/traces/([\w-]+)", path)
        if m:
            t = store.get_trace(m.group(1))
            return self._json(200, t) if t else self._json(404, {"error": "no such trace"})
        m = re.fullmatch(r"/api/conversations/([\w-]+)/export", path)
        if m:
            try:
                data = export.export(m.group(1))
            except KeyError:
                return self._json(404, {"error": "no such conversation"})
            return self._json(200, data, {"Content-Disposition": f'attachment; filename="{m.group(1)}.json"'})
        m = re.fullmatch(r"/policies/([\w-]+)/v(\d+)", path)
        if m:
            secs = corpus.find(m.group(1), int(m.group(2)))
            if not secs:
                return self._send(404, b"No such policy.", "text/plain; charset=utf-8")
            s0 = secs[0]
            body = "".join(f'<h2 id="{corpus.slug(s.heading)}">{html.escape(s.heading)}</h2>'
                           f"<pre>{html.escape(s.text)}</pre>" for s in secs)
            page = (f"<!doctype html><meta charset=utf-8><title>{html.escape(s0.title)}</title>"
                    f"<style>body{{font:16px system-ui;max-width:46rem;margin:2rem auto;padding:0 1rem}}"
                    f"pre{{white-space:pre-wrap;font:inherit}}</style><p><a href='/'>Back to the help desk</a></p>"
                    f"<h1>{html.escape(s0.title)}</h1><p>Version {s0.version}, in force from {s0.effective_from}"
                    f"{' until ' + s0.effective_to if s0.effective_to else ''}.</p>{body}")
            return self._send(200, page.encode(), "text/html; charset=utf-8")
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/reset":
            store.reset()
            return self._json(200, {"ok": True})
        if path == "/api/chat":
            body = self._body()
            if body.get("_invalid"):
                return self._json(400, {"error": "the body is not valid JSON"})
            try:
                cid = body.get("conversation_id") or assistant.start(
                    body.get("customer_id"), body.get("seed", STATE["seed"]), STATE["mode"])
                out = assistant.send(cid, str(body.get("message", "")))
            except assistant.HelpdeskError as e:
                return self._json(400, {"error": str(e)})
            except Exception:
                traceback.print_exc()
                return self._json(500, {"error": "Internal Server Error"})
            out["seed"] = store.get_conversation(cid)["seed"]
            return self._json(200, out)
        return self._json(404, {"error": "not found"})


def serve(port: int, seed: int | None, mode: str) -> None:
    STATE.update(seed=seed, mode=mode)
    if not store.db_path().exists():
        store.reset()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Larkfield help desk {APP_VERSION} ({'live model' if mode == 'live' else 'simulated model sim-1'}) "
          f"on http://localhost:{port}  (stop: Ctrl+C)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Larkfield help desk (practice app)</title>
<style>
:root{--bg:#f7f5ef;--panel:#fff;--ink:#1d2321;--muted:#5b6461;--line:#d9d6cc;--accent:#2f6b4f;--you:#e6efe9;--warn:#8a3b12}
@media (prefers-color-scheme: dark){:root{--bg:#161a18;--panel:#1f2522;--ink:#e8ece9;--muted:#a3ada8;--line:#38403c;--accent:#7cc39d;--you:#24352c;--warn:#f0a070}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}
header{padding:12px 16px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:12px;align-items:center}
header h1{font-size:18px;margin:0 auto 0 0}label{font-size:14px;color:var(--muted)}
select,input,button,textarea{font:inherit;color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:6px 8px}
button{cursor:pointer}button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
main{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,2fr);gap:16px;padding:16px;max-width:1200px;margin:0 auto}
@media (max-width:800px){main{grid-template-columns:1fr}}
section{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px}
#log{min-height:300px;max-height:60vh;overflow:auto;display:flex;flex-direction:column;gap:10px}
.msg{padding:8px 10px;border-radius:8px;white-space:pre-wrap;overflow-wrap:anywhere}.you{background:var(--you);align-self:flex-end;max-width:85%}
.bot{border:1px solid var(--line);max-width:95%}.meta{font-size:13px;color:var(--muted)}.err{color:var(--warn)}
form{display:flex;gap:8px;margin-top:10px}form textarea{flex:1;min-height:44px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;margin:0}
.note{font-size:13px;color:var(--muted);margin:8px 0 0}
</style></head><body>
<header><h1>Larkfield help desk <span class="meta" id="ver"></span></h1>
<label>Test customer <select id="customer"></select></label>
<label>Seed <input id="seed" size="6" inputmode="numeric" placeholder="random"></label>
<button id="new">New conversation</button><button id="export" disabled>Export</button><button id="reset">Reset data</button></header>
<main><section aria-label="Conversation"><div id="log" role="log" aria-live="polite"></div>
<form id="f"><label for="msg" class="meta" style="position:absolute;left:-9999px">Message</label>
<textarea id="msg" placeholder="Type a message"></textarea><button class="primary">Send</button></form>
<p class="note">Practice app with a simulated model (sim-1). Test data only. Every reply has a trace ID: select it to see the trace.</p></section>
<section aria-label="Trace"><h2 style="font-size:16px;margin:0 0 8px">Trace</h2><pre id="trace">Select a trace ID.</pre></section></main>
<script>
let conv=null;const $=s=>document.querySelector(s);
async function j(u,o){const r=await fetch(u,o);let d;try{d=await r.json()}catch(e){d={error:'HTTP '+r.status}}return [r.status,d]}
function linkify(el,text){const re=/\/policies\/[\w-]+\/v\d+(#[\w-]+)?/g;let i=0,m;while((m=re.exec(text))){el.append(text.slice(i,m.index));const a=document.createElement('a');a.href=m[0];a.target='_blank';a.textContent=m[0];el.append(a);i=m.index+m[0].length}el.append(text.slice(i))}
function add(cls,text,meta){const d=document.createElement('div');d.className='msg '+cls;linkify(d,text);if(meta){const m=document.createElement('div');m.className='meta';m.append(meta);d.append(m)}$('#log').append(d);d.scrollIntoView()}
async function showTrace(id){const [s,d]=await j('/api/traces/'+id);$('#trace').textContent=JSON.stringify(d,null,2)}
async function init(){const [,v]=await j('/api/version');$('#ver').textContent=v.app_version+' | '+v.model+' | prompt '+v.prompt_version;
const [,cs]=await j('/api/customers');for(const c of cs){const o=document.createElement('option');o.value=c.id;o.textContent=c.id+' '+c.name;$('#customer').append(o)}}
$('#new').onclick=()=>{conv=null;$('#log').textContent='';$('#export').disabled=true;$('#trace').textContent='Select a trace ID.'};
$('#customer').onchange=()=>$('#new').click();
$('#reset').onclick=async()=>{await j('/api/reset',{method:'POST'});$('#new').click();add('bot','The test data is reset.')};
$('#export').onclick=()=>{if(conv)location.href='/api/conversations/'+conv+'/export'};
$('#f').onsubmit=async e=>{e.preventDefault();const text=$('#msg').value;add('you',text);$('#msg').value='';
const body={message:text,conversation_id:conv,customer_id:$('#customer').value};const sd=$('#seed').value.trim();if(sd)body.seed=Number(sd);
const [s,d]=await j('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
if(s!==200){add('bot err','Error '+s+': '+(d.error||''));return}
conv=d.conversation_id;$('#export').disabled=false;const b=document.createElement('button');b.textContent=d.trace_id;b.onclick=()=>showTrace(d.trace_id);
const meta=document.createElement('span');meta.append('trace ',b,' | conversation '+d.conversation_id+' | seed '+d.seed);
add('bot',d.reply,meta)};
init();
</script></body></html>
"""
