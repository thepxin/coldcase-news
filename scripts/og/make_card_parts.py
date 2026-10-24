"""Static pieces of the share images: 3 backgrounds (16x9, 4x3, 1x1), the Instagram card (4x5), 5 seals and clear canvases.
Hugo writes each article's headline on top when the site builds (layouts/_partials/og_cards.html).
You only need this to change the look:  pip install pillow && python scripts/og/make_card_parts.py assets/og assets/og"""
import sys, os, math
from PIL import Image, ImageDraw, ImageFont
TTF, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
INK=(15,17,21); IVORY=(236,232,223); BRASS=(201,168,98); MUTED=(154,159,171); RULE=(52,56,66)
cas = lambda s: ImageFont.truetype(f"{TTF}/LibreCaslonDisplay-Regular.ttf", s)
mono = lambda s, b=False: ImageFont.truetype(f"{TTF}/JetBrainsMono-{'Bold' if b else 'Regular'}.ttf", s)
S=2  # draw at 2x, then downsample for smooth lines
for name,(W,H) in {"16x9":(1200,675),"4x3":(1200,900),"1x1":(1200,1200)}.items():
    im=Image.new("RGB",(W*S,H*S),INK); d=ImageDraw.Draw(im)
    m=28*S
    d.rectangle([m,m,W*S-m,H*S-m],outline=BRASS,width=2*S)          # brass frame
    d.rectangle([m+8*S,m+8*S,W*S-m-8*S,H*S-m-8*S],outline=RULE,width=1*S)
    x=80*S; top=62*S
    f=cas(40*S); d.text((x,top),"ColdCase",font=f,fill=IVORY); w=d.textlength("ColdCase",font=f)
    d.text((x+w,top),"Tech",font=f,fill=BRASS)
    t="THE RECORD OF TECH PROMISES"; fm=mono(15*S)
    d.text((W*S-x-d.textlength(t,font=fm),top+18*S),t,font=fm,fill=MUTED)
    y=top+62*S
    d.line([x,y,W*S-x,y],fill=IVORY,width=S); d.line([x,y+5*S,W*S-x,y+5*S],fill=IVORY,width=S)   # double rule
    yb=H*S-118*S
    d.line([x,yb,W*S-x,yb],fill=RULE,width=S)
    t="coldcasetech.com"; d.text((x,yb+24*S),t,font=mono(17*S,True),fill=BRASS)
    im.resize((W,H),Image.LANCZOS).save(f"{OUT}/card-{name}.png",optimize=True)
# seals: transparent PNG, 150 px
seals={"report":("NEWS","REPORT",BRASS,False),"open":("OPEN","CASE",(179,165,255),True),
       "ok":("","DELIVERED",(111,207,159),False),"warn":("PARTLY","DELIVERED",(227,189,107),False),
       "bad":("NOT","DELIVERED",(238,143,136),False)}
Z=150*S
for k,(a,b,c,dash) in seals.items():
    im=Image.new("RGBA",(Z,Z),(0,0,0,0)); d=ImageDraw.Draw(im)
    r=Z//2-3*S; cx=cy=Z//2
    if dash:
        n=36
        for i in range(n):
            if i%2: continue
            a0=360/n*i; d.arc([cx-r,cy-r,cx+r,cy+r],a0,a0+360/n,fill=c,width=3*S)
    else:
        d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=c,width=3*S)
    r2=r-10*S; d.ellipse([cx-r2,cy-r2,cx+r2,cy+r2],outline=c,width=2*S)
    f=mono(17*S,True)
    lines=[l for l in (a,b) if l]
    lh=24*S; y0=cy-lh*len(lines)/2
    for i,l in enumerate(lines):
        # letter-spaced
        sp=2*S; w=sum(d.textlength(ch,font=f) for ch in l)+sp*(len(l)-1); xx=cx-w/2
        for ch in l:
            d.text((xx,y0+i*lh),ch,font=f,fill=c); xx+=d.textlength(ch,font=f)+sp
    im.resize((150,150),Image.LANCZOS).save(f"{OUT}/seal-{k}.png",optimize=True)
# Instagram portrait card (1080x1350, 4:5): frame, masthead, footer. Hugo adds kicker, headline, hook and seal.
W, H = 1080, 1350
im = Image.new("RGB", (W*S, H*S), INK); d = ImageDraw.Draw(im)
m = 26*S
d.rectangle([m, m, W*S-m, H*S-m], outline=BRASS, width=2*S)
d.rectangle([m+8*S, m+8*S, W*S-m-8*S, H*S-m-8*S], outline=RULE, width=1*S)
x = 72*S; top = 62*S
f = cas(46*S); d.text((x, top), "ColdCase", font=f, fill=IVORY); w = d.textlength("ColdCase", font=f)
d.text((x+w, top), "Tech", font=f, fill=BRASS)
t = "THE RECORD OF TECH PROMISES"; fm = mono(15*S)
d.text((W*S-x-d.textlength(t, font=fm), top+22*S), t, font=fm, fill=MUTED)
y = top+72*S
d.line([x, y, W*S-x, y], fill=IVORY, width=S); d.line([x, y+5*S, W*S-x, y+5*S], fill=IVORY, width=S)
yb = H*S-170*S
d.line([x, yb, W*S-x, yb], fill=RULE, width=S)
d.text((x, yb+28*S), "Full story and every source: link in bio", font=mono(21*S), fill=MUTED)
d.text((x, yb+70*S), "coldcasetech.com", font=mono(24*S, True), fill=BRASS)
im.resize((W, H), Image.LANCZOS).save(f"{OUT}/insta-4x5.png", optimize=True)
Image.new("RGBA", (90, 3), BRASS + (255,)).save(f"{OUT}/rule-brass.png", optimize=True)
for w, h in [(936, 470), (936, 280)]:
    Image.new("RGBA", (w, h), (0, 0, 0, 0)).save(f"{OUT}/clear-{w}x{h}.png", optimize=True)
# transparent canvases for wrapped text (Hugo wraps at the canvas edge)
for w,h in [(860,340),(860,560),(860,860)]:
    Image.new("RGBA",(w,h),(0,0,0,0)).save(f"{OUT}/clear-{w}x{h}.png",optimize=True)
print("ok")
