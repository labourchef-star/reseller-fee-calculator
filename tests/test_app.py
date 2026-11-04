import os; os.environ["DB_PATH"]="/tmp/rfc_test.db"; os.environ["METRICS_TOKEN"]="t"
if os.path.exists("/tmp/rfc_test.db"): os.remove("/tmp/rfc_test.db")
from fastapi.testclient import TestClient
from app.main import app
from app.fees import calc, PLATFORMS
c=TestClient(app)
def test_ebay(): r=calc("ebay",100); assert r["fee"]==13.60+0.40 and r["payout"]==86.0
def test_ebay_small(): assert calc("ebay",10)["fee"]==round(1.36+0.30,2)
def test_ebay_over_7500(): assert calc("ebay",10000)["fee"]==round(0.136*7500+0.0235*2500+0.40,2)
def test_posh(): assert calc("poshmark",10)["fee"]==2.95 and calc("poshmark",15)["fee"]==3.0
def test_mercari(): assert calc("mercari",50,ship=8)["payout"]==52.2
def test_depop(): assert calc("depop",100)["fee"]==3.75
def test_whatnot(): assert calc("whatnot",50,ship=5)["fee"]==5.90
def test_all_sources(): assert all(p["src"].startswith("https://") for p in PLATFORMS.values())
def test_pages():
    for u in ["/","/fees","/pro","/ebay-fees","/poshmark-fees","/depop-fees","/whatnot-fees","/mercari-fees","/health","/favicon.ico"]:
        assert c.get(u).status_code==200,u
    h=c.get("/").text; assert "kerbform.com/privacy.html" in h and "hello@kerbform.com" in h and "not tax" in h.lower()
def test_pro_no_price(): t=c.get("/pro").text; assert "coming soon" in t.lower() and "$" not in t.split("<h1>")[1].split("</body>")[0].replace("$</text>","")
def test_calc_and_alert():
    t=c.get("/calc?price=50&cost=10").text; assert "Fee change alerts" in t
    assert "Saved" in c.post("/alerts",data={"email":"a@example.com","consent":"1"}).text
def test_metrics_and_test_tag():
    assert c.get("/metrics").status_code==401
    c.get("/",headers={"X-Test":"1"})
    m=c.get("/metrics",headers={"authorization":"Bearer t"}).json()
    assert any(r["test"]==1 for r in m["counters"]) and m["real_totals"]["calc_run"]>=1
