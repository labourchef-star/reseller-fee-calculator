"""Fee tables (US). Every rate is copied from the platform's own page; checked date recorded. No invented rates."""
CHECKED="2026-11-04"
PLATFORMS={
 "ebay":{"name":"eBay","verified":True,"src":"https://www.ebay.com/help/selling/fees-credits-invoices/selling-fees?id=4822",
   "summary":"Most categories: 13.6% final value fee on the total amount of the sale (item + shipping + tax) up to $7,500, 2.35% on the portion over $7,500, plus $0.30 per order (orders $10 or less) or $0.40 (over $10). First 250 listings a month free, then $0.35 insertion fee. Some categories (e.g. books, media) differ."},
 "poshmark":{"name":"Poshmark","verified":True,"src":"https://poshmark.com/posh_guide/get_started_on_poshmark",
   "summary":"Flat $2.95 on sales under $15; 20% on sales of $15 or more. Buyer pays the shipping label."},
 "mercari":{"name":"Mercari","verified":True,"src":"https://www.mercari.com/us/help_center/article/169/",
   "summary":"10% selling fee on item price + buyer-paid shipping (listings created or updated since Jan 6, 2025). No separate payment processing fee for sellers. Instant Pay $3 per cash-out (optional, not included)."},
 "depop":{"name":"Depop","verified":True,"src":"https://depophelp.zendesk.com/hc/en-gb/articles/360001791127-Seller-fees-and-charges",
   "summary":"US sellers: no selling fee. Payment processing 3.3% + $0.45 on item price + shipping + tax. Boosted listings add 12% (not included unless you tick Boosted)."},
 "whatnot":{"name":"Whatnot","verified":True,"src":"https://help.whatnot.com/hc/en-us/articles/4847069165965-Whatnot-seller-fees",
   "src2":"https://www.whatnot.com/seller/fees",
   "summary":"US standard tier: 8% commission on item price only (coins 4%; lower rates at higher 4-week sales tiers), plus payment processing 2.9% + $0.30 on the total order (item + shipping + tax)."},
}
def r2(x): return round(x+1e-9,2)
def calc(platform,price,ship=0.0,tax=0.0,cost=0.0,ship_cost=0.0,boost=False,coins=False):
    """price=item sale price, ship=shipping the buyer pays, tax=sales tax buyer pays, cost=what you paid, ship_cost=postage you pay.
    Returns fee, payout (what reaches you, excluding tax pass-through), profit."""
    p,s,t=max(price,0),max(ship,0),max(tax,0); total=p+s+t
    if platform=="ebay":
        fvf=0.136*min(total,7500)+0.0235*max(total-7500,0); fee=fvf+(0.30 if total<=10 else 0.40); recv=p+s
    elif platform=="poshmark":
        fee=2.95 if p<15 else 0.20*p; recv=p; ship_cost=0  # buyer-paid prepaid label
    elif platform=="mercari":
        fee=0.10*(p+s); recv=p+s
    elif platform=="depop":
        fee=0.033*total+0.45+(0.12*(p+s) if boost else 0); recv=p+s
    elif platform=="whatnot":
        fee=(0.04 if coins else 0.08)*p+0.029*total+0.30; recv=p+s
    else: raise KeyError(platform)
    fee=r2(fee); payout=r2(recv-fee)
    return {"platform":platform,"fee":fee,"payout":payout,"profit":r2(payout-cost-ship_cost),"fee_pct":r2(100*fee/p) if p else 0}
def calc_all(**kw): return sorted((calc(k,**kw) for k in PLATFORMS),key=lambda r:-r["profit"])
