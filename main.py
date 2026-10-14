import os, asyncio, hmac
import discord
from aiohttp import web

TOKEN = os.environ["TOKEN"]
KEY = os.environ["KEY"]
CHANNELS = {"กิจกรรม": 1318467166202363924}
ROLES = {"ยศหลัก": 1317489142539485194}

intents = discord.Intents.default()
intents.members = True
bot = discord.Client(intents=intents)

PAGE = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<body style="font-family:sans-serif;background:#1a1a1a;color:#fff;padding:16px;max-width:480px;margin:auto">
<h2 style="color:#ff7a00">Admin</h2>
<div id=st>กำลังเชื่อมต่อบอท...</div>
<input id=key type=password placeholder="รหัสผ่าน" style="width:100%;margin:8px 0;padding:10px">
<select id=ch style="width:100%;padding:10px">CHOPTS</select>
<div style="margin:8px 0">ROLEOPTS</div>
<textarea id=tx rows=5 placeholder="ข้อความประกาศ" style="width:100%;padding:10px"></textarea>
<button onclick=send() style="width:100%;margin-top:8px;padding:12px;background:#ff7a00;border:0;color:#fff">ส่งประกาศ</button>
<p id=out></p>
<script>
async function st(){
 try{
  let r=await (await fetch('/status')).json();
  document.getElementById('st').textContent=r.online
   ? `บอทออนไลน์ | สมาชิก ${r.total} (คน ${r.humans} / บอท ${r.bots})`
   : 'บอทกำลังเปิด... รอสักครู่';
  if(!r.online) setTimeout(st,3000);
 }catch(e){setTimeout(st,3000)}
}
st();
async function send(){
 let roles=[...document.querySelectorAll('.r:checked')].map(x=>x.value);
 let r=await fetch('/announce',{method:'POST',
  headers:{'X-Key':document.getElementById('key').value,'Content-Type':'application/json'},
  body:JSON.stringify({channel:document.getElementById('ch').value,
   text:document.getElementById('tx').value,roles:roles})});
 document.getElementById('out').textContent=r.ok?'ส่งแล้ว ✅':'ส่งไม่สำเร็จ ❌';
}
</script>"""

async def index(request):
    ch = "".join(f"<option>{k}</option>" for k in CHANNELS)
    ro = "".join(
        f"<label><input type=checkbox class=r value={v}> {k}</label> "
        for k, v in ROLES.items()
    )
    html = PAGE.replace("CHOPTS", ch).replace("ROLEOPTS", ro)
    return web.Response(text=html, content_type="text/html")

async def status(request):
    if not bot.is_ready():
        return web.json_response({"online": False})
    g = bot.guilds[0]
    bots = sum(m.bot for m in g.members)
    return web.json_response({
        "online": True,
        "total": g.member_count,
        "bots": bots,
        "humans": g.member_count - bots,
    })

async def announce(request):
    sent = request.headers.get("X-Key", "").encode()
    if not hmac.compare_digest(sent, KEY.encode()):
        return web.json_response({"ok": False}, status=403)
    if not bot.is_ready():
        return web.json_response({"ok": False}, status=503)
    d = await request.json()
    ch = bot.get_channel(CHANNELS[d["channel"]])
    roles = [int(r) for r in d.get("roles", []) if int(r) in ROLES.values()]
    await ch.send(
        content=" ".join(f"<@&{r}>" for r in roles) or None,
        embed=discord.Embed(
            title="📢 ประกาศ",
            description=d["text"],
            color=0xFF7A00,
        ),
        allowed_mentions=discord.AllowedMentions(roles=True),
    )
    return web.json_response({"ok": True})

async def on_start(app):
    app["bot"] = asyncio.create_task(bot.start(TOKEN))

app = web.Application()
app.add_routes([
    web.get("/", index),
    web.get("/status", status),
    web.post("/announce", announce),
])
app.on_startup.append(on_start)
web.run_app(app, port=int(os.environ.get("PORT", 8080)))
