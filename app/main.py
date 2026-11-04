"""Reseller Fee & Profit Calculator (US): free, no signup."""
import os, re, time, sqlite3, html, datetime as dt
from contextlib import contextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from .fees import PLATFORMS, CHECKED, calc_all
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
EVENTS=("visit","calc_run","email_submit","pro_click")
DB=os.environ.get("DB_PATH","/tmp/resellerfees.db")
@contextmanager
def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    try: yield c; c.commit()
    finally: c.close()
with db() as c:
    c.execute("create table if not exists counters(day text,event text,test integer,n integer,primary key(day,event,test))")
    c.execute("create table if not exists subscribers(id integer primary key,email text unique,created real,ip text)")
    c.execute("create table if not exists hits(key text,ts real)")
def is_test(req:Request):
    return req.headers.get("x-test")=="1" or req.query_params.get("_test")=="1" or "kerbform-bot" in req.headers.get("user-agent","").lower()
def bump(req,ev):
    d=dt.datetime.now(dt.timezone.utc).date().isoformat(); t=1 if is_test(req) else 0
    with db() as c: c.execute("insert into counters values(?,?,?,1) on conflict(day,event,test) do update set n=n+1",(d,ev,t))
e=html.escape
FAV="""data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%23157a5a'/%3E%3Ctext x='16' y='23' font-size='20' font-family='Arial' font-weight='700' fill='white' text-anchor='middle'%3E$%3C/text%3E%3C/svg%3E"""
CSS="""body{font:17px/1.5 system-ui,sans-serif;max-width:680px;margin:0 auto;padding:14px;color:#1a1a1a;background:#fff}h1{font-size:1.45em;margin:.2em 0}
label{display:block;margin:.6em 0 .15em;font-weight:600}input,button{font:inherit;padding:10px;width:100%;box-sizing:border-box}.row{display:flex;gap:10px}.row>div{flex:1}
button{background:#157a5a;color:#fff;border:0;border-radius:6px;margin-top:1em;font-weight:700}table{width:100%;border-collapse:collapse;margin:.6em 0}td,th{padding:7px 5px;border-bottom:1px solid #ddd;text-align:left}
.best{background:#e7f6ef;font-weight:700}.small{font-size:.85em;color:#555}.warn{background:#fff4d6;padding:8px;border-radius:6px}a{color:#0b5c8a}.cb{width:auto}.box{border:1px solid #cde;border-radius:8px;padding:10px;margin:1em 0}"""
def page(title,body,desc="Free eBay, Poshmark, Mercari, Depop and Whatnot fee and profit calculator. Official fee rates with sources. No signup."):
    return HTMLResponse(f"""<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="icon" href="{FAV}"><style>{CSS}</style></head><body>
<p class="small"><a href="/">Fee calculator</a> · <a href="/fees">Fee rates &amp; sources</a> · <a href="/pro">Pro</a></p>{body}
<p class="small">Estimates only, not tax or financial advice. Fees change; rates below were checked on {CHECKED} against each platform's own page (see <a href="/fees">sources</a>). Confirm on the platform before relying on a number. Not affiliated with eBay, Poshmark, Mercari, Depop or Whatnot.</p>
<p class="small">Made by <a href="https://kerbform.com">Kerbform</a>. <a href="https://kerbform.com/privacy.html">Privacy</a> · <a href="https://kerbform.com/terms.html">Terms</a> · <a href="mailto:hello@kerbform.com">hello@kerbform.com</a></p></body></html>""")
def num(v):
    try: return max(0.0,float(re.sub(r"[,$\s]","",v or "0") or 0))
    except ValueError: return 0.0
def form(price="",ship="",tax="",cost="",sc="",act="/calc"):
    f=lambda i,l,v,ph:f'<div><label for="{i}">{l}</label><input id="{i}" name="{i}" inputmode="decimal" value="{e(v)}" placeholder="{ph}"></div>'
    return f"""<form action="{act}" method="get"><div class="row">{f("price","Sale price ($)",price,"50")}{f("ship","Shipping buyer pays ($)",ship,"0")}</div>
<div class="row">{f("cost","What you paid ($)",cost,"10")}{f("sc","Postage you pay ($)",sc,"0")}</div>{f("tax","Sales tax buyer pays ($, optional)",tax,"0")}
<button>Calculate fees &amp; profit</button></form>"""
QA={"ebay":("How much does eBay charge to sell?","how much does ebay charge to sell, how much does ebay take, ebay fees"),
    "poshmark":("How much does Poshmark take?","how much does poshmark take, poshmark fees"),
    "mercari":("How much does Mercari take?","mercari fees"),
    "depop":("How much does Depop take?","how much does depop take, depop fees"),
    "whatnot":("How much does Whatnot take?","how much does whatnot take, whatnot fees")}
def ratebox(k):
    p=PLATFORMS[k]; return f'<div class="box"><b>{p["name"]} (US)</b>: {e(p["summary"])} <br><span class="small">Source: <a href="{p["src"]}" rel="nofollow">{p["name"]} official fee page</a>, checked {CHECKED}.</span></div>'
@app.get("/",response_class=HTMLResponse)
def home(request:Request):
    bump(request,"visit")
    links=" · ".join(f'<a href="/{k}-fees">{e(q[0])}</a>' for k,q in QA.items())
    return page("Reseller Fee & Profit Calculator: eBay, Poshmark, Mercari, Depop, Whatnot",f"""<h1>What will you actually keep?</h1>
<p>Enter one sale and see the fee, payout and profit on eBay, Poshmark, Mercari, Depop and Whatnot side by side. US rates, no signup.</p>{form()}<p class="small">{links}</p>""")
@app.get("/{plat}-fees",response_class=HTMLResponse)
def qpage(plat:str,request:Request):
    if plat not in QA: return page("Not found","<p>Not found.</p>")
    bump(request,"visit"); q=QA[plat]; ex=calc_all(price=100.0)
    r=[x for x in ex if x["platform"]==plat][0]
    return page(f"{q[0]} ({CHECKED[:4]} fee calculator)",f"""<h1>{e(q[0])}</h1>{ratebox(plat)}
<p>Example: on a $100 item with no shipping or tax, {PLATFORMS[plat]['name']} takes about <b>${r['fee']:.2f}</b> and you get <b>${r['payout']:.2f}</b>.</p>
<h2>Work out your own sale</h2>{form()}""",desc=f"{q[0]} Current {PLATFORMS[plat]['name']} US seller fees with the official source, plus a free profit calculator.")
@app.get("/calc",response_class=HTMLResponse)
def calc(request:Request,price:str="",ship:str="",tax:str="",cost:str="",sc:str="",boost:str="",coins:str=""):
    p=num(price)
    if p<=0: return page("Enter a price",'<p class="warn">Enter a sale price.</p>'+form())
    rows=calc_all(price=p,ship=num(ship),tax=num(tax),cost=num(cost),ship_cost=num(sc))
    bump(request,"calc_run"); best=rows[0]["profit"]
    tr="".join(f'<tr class="{"best" if x["profit"]==best else ""}"><td><a href="/{x["platform"]}-fees">{PLATFORMS[x["platform"]]["name"]}</a></td><td>${x["fee"]:.2f}</td><td>${x["payout"]:.2f}</td><td>${x["profit"]:.2f}</td></tr>' for x in rows)
    return page(f"Fees on a ${p:,.2f} sale",f"""<h1>Fees on a ${p:,.2f} sale</h1>
<table><tr><th>Platform</th><th>Fee</th><th>Payout</th><th>Profit</th></tr>{tr}</table>
<p class="small">Payout excludes sales tax (the platform remits it). Profit = payout minus what you paid and postage you pay. Poshmark assumes the buyer-paid prepaid label. eBay uses the most-categories rate; Whatnot uses the standard 8% tier; Depop excludes Boost.</p>
<h2>Fee change alerts</h2><p>Optional. We'll email you when one of these platforms changes its US seller fees.</p>
<form action="/alerts" method="post"><label for="em">Email</label><input id="em" type="email" name="email" required autocomplete="email">
<label><input class="cb" type="checkbox" name="consent" value="1" required> Email me fee change alerts. Unsubscribe any time.</label><button>Get fee change alerts</button></form>
<p><a href="/pro?from=result">Track every sale's profit? See Pro (coming soon).</a></p><h2>Try another sale</h2>{form(price,ship,tax,cost,sc)}""")
EM=re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[a-z]{2,}$",re.I)
@app.post("/alerts",response_class=HTMLResponse)
def alerts(request:Request,email:str=Form(""),consent:str=Form("")):
    email=email.strip().lower()
    if not EM.match(email) or not consent: return page("Check your email",'<p class="warn">Enter a valid email and tick the box.</p><p><a href="/">Back</a></p>')
    ip=(request.headers.get("x-forwarded-for") or (request.client.host if request.client else "")).split(",")[0].strip()
    with db() as c:
        if c.execute("select count(*) from hits where key=? and ts>?",(ip,time.time()-3600)).fetchone()[0]>=10: return page("Slow down",'<p class="warn">Too many requests. Try later.</p>')
        c.execute("insert into hits values(?,?)",(ip,time.time()))
        c.execute("insert or ignore into subscribers(email,created,ip) values(?,?,?)",(email,time.time(),ip))
    bump(request,"email_submit")
    return page("Saved",f"<h1>Saved</h1><p>We'll email {e(email)} when a platform's US seller fees change.</p><p><a href='/'>Back to the calculator</a></p>")
@app.get("/pro",response_class=HTMLResponse)
def pro(request:Request):
    bump(request,"pro_click")
    return page("Reseller Profit Pro (coming soon)","""<h1>Reseller Profit Pro: coming soon</h1><p>Planned: a saved sales log, monthly profit and fee totals by platform, and a CSV export for your records.</p>
<p>It isn't available yet and has no price yet. Sign up for fee change alerts on any result page and we'll let you know when it launches.</p><p><a href="/">Back to the calculator</a></p>""")
@app.get("/fees",response_class=HTMLResponse)
def fees(request:Request):
    return page("Seller fee rates and sources","<h1>US seller fee rates and sources</h1>"+"".join(ratebox(k) for k in PLATFORMS))
@app.get("/privacy")
def priv(): return RedirectResponse("https://kerbform.com/privacy.html",301)
@app.get("/terms")
def terms(): return RedirectResponse("https://kerbform.com/terms.html",301)
@app.get("/favicon.ico")
def favicon(): return Response(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#157a5a"/><text x="16" y="23" font-size="20" font-family="Arial" font-weight="700" fill="white" text-anchor="middle">$</text></svg>',media_type="image/svg+xml")
@app.get("/health")
def health(): return {"ok":True}
@app.get("/metrics")
def metrics(request:Request):
    tok=os.environ.get("METRICS_TOKEN")
    if not tok or request.headers.get("authorization")!="Bearer "+tok: return JSONResponse({"error":"unauthorised"},401)
    with db() as c:
        rows=[dict(r) for r in c.execute("select day,event,test,n from counters order by day")]
        tot={ev:sum(r["n"] for r in rows if r["event"]==ev and not r["test"]) for ev in EVENTS}
        return {"real_totals":tot,"counters":rows,"subscribers":c.execute("select count(*) from subscribers").fetchone()[0],"note":"test=1 rows are our own test hits (X-Test: 1 header or _test=1)"}
