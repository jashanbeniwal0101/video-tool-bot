import os
from datetime import datetime
from aiohttp import web
from config import LOG_FILE_PATH

routes = web.RouteTableDef()

APP_LOG_FILE = LOG_FILE_PATH
ACCESS_LOG_FILE = 'access.log'
AUTH_KEY = 'abc'

def log_message(msg):
    with open(APP_LOG_FILE, 'a') as f:
        f.write(f"{datetime.utcnow().isoformat()} - {msg}\n")

def log_access(request):
    with open(ACCESS_LOG_FILE, 'a') as f:
        f.write(f"{datetime.utcnow().isoformat()} - {request.remote} - {request.method} {request.path_qs}\n")

def check_key(request):
    key = request.query.get("key")
    return key == AUTH_KEY

@routes.get('/status')
async def status(request):
    uptime = (datetime.utcnow() - status.start_time).total_seconds()
    data = {
        "status": "ok",
        "server_time": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
    }
    return web.json_response(data)
status.start_time = datetime.utcnow()

# --------- Root route ---------
@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({"message": "running...."})

# --------- Application Log Viewer ---------
@routes.get('/l')
async def index(request):
    if not check_key(request):
        return web.Response(text="Unauthorized", status=401)
    return web.Response(text=f"""
    <!DOCTYPE html>
    <html>
    <head><title>Log Viewer</title></head>
    <body>
    <h1>Application Logs</h1>
    <pre id="log-container">Loading logs...</pre>
    <script>
    const key = '{AUTH_KEY}';
    async function fetchLogs() {{
        const res = await fetch('/logs?key=' + key);
        const text = await res.text();
        document.getElementById('log-container').textContent = text;
    }}
    setInterval(fetchLogs, 3000);
    fetchLogs();
    </script>
    </body>
    </html>
    """, content_type='text/html')

# --------- Access Log Viewer ---------
@routes.get('/access-log-viewer')
async def access_log_viewer(request):
    if not check_key(request):
        return web.Response(text="Unauthorized", status=401)
    return web.Response(text=f"""
    <!DOCTYPE html>
    <html>
    <head><title>Access Log Viewer</title></head>
    <body>
    <h1>Access Logs</h1>
    <pre id="log-container">Loading access logs...</pre>
    <script>
    const key = '{AUTH_KEY}';
    async function fetchLogs() {{
        const res = await fetch('/access-logs?key=' + key);
        const text = await res.text();
        document.getElementById('log-container').textContent = text;
    }}
    setInterval(fetchLogs, 3000);
    fetchLogs();
    </script>
    </body>
    </html>
    """, content_type='text/html')

# --------- Get Application Logs ---------
@routes.get('/logs')
async def get_logs(request):
    if not check_key(request):
        return web.Response(text="Unauthorized", status=401)
    if os.path.exists(APP_LOG_FILE):
        with open(APP_LOG_FILE, 'r') as f:
            content = f.read()
    else:
        content = "Log file not found."
    return web.Response(text=content, content_type='text/plain')

# --------- Get Access Logs ---------
@routes.get('/access-logs')
async def get_access_logs(request):
    if not check_key(request):
        return web.Response(text="Unauthorized", status=401)
    if os.path.exists(ACCESS_LOG_FILE):
        with open(ACCESS_LOG_FILE, 'r') as f:
            content = f.read()
    else:
        content = "Access log file not found."
    return web.Response(text=content, content_type='text/plain')

# --------- Example Endpoint that logs both app and access ---------
@routes.get('/demo')
async def demo_route(request):
    log_message("Demo endpoint was accessed.")
    return web.json_response({"message": "Demo log entry created!"})

# --------- App setup ---------

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app
