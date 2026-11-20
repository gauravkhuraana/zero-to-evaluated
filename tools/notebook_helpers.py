"""
tools/notebook_helpers.py · the "remote control" behind workshop.ipynb

The notebook is just another way to run the SAME commands as the README. Every cell calls one of these
small functions, and each function runs the real repo files:

    nb.set_key()                          paste your Groq key: written into BOTH places in .env
    nb.check()                            python check_setup.py   (+ is the notebook on the right kernel?)
    nb.run(".", "python run.py --version 1 1043")
                                          the same as typing it in a terminal in the project folder
    nb.show("agent/v2_agent.py")          read a file (or part of it) right in the notebook
    nb.start_bot()                        uvicorn agent.app:app --reload, in the background
    nb.bot_log() / nb.stop_bot()          what the server terminal would show / Ctrl+C
    nb.ask("Do you price-match?", version=1)
                                          POST /chat: the reply, the outcome and the flight recorder
    nb.compare("Refund order 1100.")      the same message to v1, v2 and v3, side by side
    nb.plant("skip_lookup") / nb.plant("off")
                                          python plant_bug.py skip_lookup / off
    nb.report()                           open evaluate/report.html

Nothing here changes how the agent works. Terminal users never need this file.
"""
import html
import json
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent      # the project folder (the one with check_setup.py)
PORT = 8000                                        # the bot's port, the same as in the terminal path
BOT_LOG = ROOT / ".notebook_bot.log"               # everything the background bot prints
BOT_PID = ROOT / ".notebook_bot.pid"               # which process is "our" bot (survives a kernel restart)
IS_WINDOWS = sys.platform.startswith("win")
CURSOR_CODES = re.compile(r"\x1b\[\??[0-9;]*[ABCDEFGHJKSTlh]")  # terminal cursor moves (colour codes are kept)


# ---------------------------------------------------------------------------
# Small printing helpers
# ---------------------------------------------------------------------------
def _ok(text):
    print(f"✅ {text}")


def _bad(text):
    print(f"❌ {text}")


def _tip(text):
    print(f"👉 {text}")


def _show_link(url, label):
    """A clickable link in the notebook (plain text if the notebook can't show HTML)."""
    try:
        from IPython.display import HTML, display
        display(HTML(f'👉 <a href="{url}" target="_blank">{html.escape(label)}</a> &nbsp; <code>{url}</code>'))
    except ImportError:
        print(f"👉 {label}: {url}")


def _environment():
    """The settings every command gets: unbuffered output (so you see it live) and UTF-8 on Windows."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    # Colours yes, animations no: spinners redraw themselves with cursor codes a notebook can't show.
    env["TERM"] = "dumb"
    env["FORCE_COLOR"] = "1"
    env["PY_COLORS"] = "1"
    # Put this Python's folder first on PATH, so tools started by the scripts use the .venv too.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")

    # VS Code copies .env into the notebook's memory when the kernel STARTS. Added your key after that?
    # Then the notebook still holds the empty placeholder, and the scripts (which never overwrite a value
    # that is already set) would use it. So: an empty or placeholder value is replaced by the one in .env.
    # A real key from a Codespaces secret is left alone: secrets still win, exactly like in a terminal.
    for name, value in _read_env_file().items():
        if value and _is_placeholder(env.get(name)):
            env[name] = value
    return env


def _is_placeholder(value):
    """True for a missing value or one of the example values from .env.example."""
    return not value or "your_key_here" in value


def _read_env_file():
    """The settings in .env, as a dictionary (empty if there is no .env yet)."""
    from dotenv import dotenv_values
    env_file = ROOT / ".env"
    if not env_file.exists():
        return {}
    return {name: value for name, value in dotenv_values(env_file).items() if value is not None}


def url(path="/"):
    """The address of the bot. In GitHub Codespaces that is the forwarded-port address, not localhost."""
    codespace = os.getenv("CODESPACE_NAME")
    domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    if codespace:
        return f"https://{codespace}-{PORT}.{domain}{path}"
    return f"http://localhost:{PORT}{path}"


# ---------------------------------------------------------------------------
# 0 · Your key, and is everything ready?
# ---------------------------------------------------------------------------
def set_key(key=None):
    """
    Put your Groq key into .env, in BOTH places (LLM_API_KEY for your bot, JUDGE_API_KEY for the judge).
    Without an argument it asks for the key in a hidden box, so it doesn't stay visible in the notebook.
    """
    env_file = ROOT / ".env"
    if not env_file.exists():
        shutil.copy(ROOT / ".env.example", env_file)
        _ok("Created .env from .env.example")

    if key is None:
        from getpass import getpass
        key = getpass("Paste your Groq key (starts with gsk_) and press Enter: ")
    key = key.strip().strip('"').strip("'")

    if not key:
        _bad("No key pasted. Run the cell again. Free key, no credit card: https://console.groq.com/keys")
        return False
    if not key.startswith("gsk_"):
        _tip("Groq keys start with gsk_. Double-check you copied the whole key.")

    # Replace the value of the first active LLM_API_KEY= and JUDGE_API_KEY= lines (comments are left alone).
    lines = env_file.read_text(encoding="utf-8").splitlines()
    done = set()
    for index, line in enumerate(lines):
        for name in ("LLM_API_KEY", "JUDGE_API_KEY"):
            if name not in done and line.startswith(f"{name}="):
                lines[index] = f"{name}={key}"
                done.add(name)
    for name in ("LLM_API_KEY", "JUDGE_API_KEY"):
        if name not in done:
            lines.append(f"{name}={key}")
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _ok(f"Saved in .env: LLM_API_KEY and JUDGE_API_KEY = {key[:4]}…{key[-4:]}")

    # Also fix the notebook's own copy (see _environment), unless a Codespaces secret holds a real key.
    for name in ("LLM_API_KEY", "JUDGE_API_KEY"):
        current = os.environ.get(name)
        if _is_placeholder(current):
            os.environ[name] = key
        elif current != key:
            _bad(f"{name} is also set as a Codespaces secret (or system variable), and that one wins over .env.")
            _tip("Wrong key there? Fix it at github.com/settings/codespaces, then stop and restart the codespace.")

    print()
    return check()


def check():
    """The notebook version of `python check_setup.py`, plus: is this notebook using the .venv?"""
    version = sys.version_info
    in_venv = ".venv" in Path(sys.prefix).parts

    if in_venv:
        _ok(f"The notebook runs on the project's .venv (Python {version.major}.{version.minor}.{version.micro})")
    else:
        _bad(f"The notebook runs on {sys.executable}, not on the project's .venv")
        _tip("Click 'Select Kernel' (top right) → Jupyter Kernel → 'ShopKart agent (.venv)'. Not listed? Python Environments → .venv.")
        _tip("Then run this cell again. Still stuck: TROUBLESHOOTING.md #20.")
        _tip("No .venv yet? Run the setup once in a terminal: see SETUP.md (or use GitHub Codespaces).")
        return False

    print()
    return run(".", "python check_setup.py") == 0


# ---------------------------------------------------------------------------
# 1 · Run a command, exactly like typing it in a terminal
# ---------------------------------------------------------------------------
def run(folder, command, timeout=None):
    """
    Run one command inside `folder` ("." = the project folder) and show its output live.
        run(".", "python run.py --version 1 1043")
        run(".", "pytest evaluate/rules -v --agent-version 2")
    Returns the exit code (0 = success).
    """
    parts = shlex.split(command)
    if parts[0] == "python":
        parts = [sys.executable] + parts[1:]
    elif parts[0] == "pytest":
        parts = [sys.executable, "-m", "pytest"] + parts[1:]
    elif parts[0] == "uvicorn":
        _bad("Use nb.start_bot(...) for uvicorn: a server would keep this cell busy forever.")
        return 1

    work_folder = ROOT / folder
    print(f"$ cd {folder}   ·   {command}\n")

    process = subprocess.Popen(
        parts,
        cwd=work_folder,
        env=_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    started = time.time()
    try:
        for line in process.stdout:
            line = CURSOR_CODES.sub("", line)
            print(line, end="")
            if timeout and time.time() - started > timeout:
                process.kill()
                _bad(f"Stopped after {timeout} seconds.")
                break
        code = process.wait()
    except KeyboardInterrupt:          # the ■ (stop) button of the cell
        process.kill()
        process.wait()
        print()
        _bad("Stopped by you.")
        return 1

    print()
    if code == 0:
        _ok("Finished.")
    elif parts[1:3] == ["-m", "pytest"]:
        _bad(f"pytest exit code {code}: at least one test FAILED (see above). "
             "With a planted bug, that is exactly what you want!")
    else:
        _bad(f"Exit code {code}. Read the last lines above; TROUBLESHOOTING.md has the common fixes.")
    return code


def plant(bug):
    """Break the running agent on purpose (Part 2): plant("liar"). ALWAYS finish with plant("off")."""
    return run(".", f"python plant_bug.py {bug}")


# ---------------------------------------------------------------------------
# 2 · The bot in the background (replaces terminal window 2)
# ---------------------------------------------------------------------------
def _port_busy():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", PORT)) == 0


def _bot_answers():
    """True when the bot's web server answers on port 8000."""
    import httpx
    try:
        return httpx.get(f"http://127.0.0.1:{PORT}/openapi.json", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


def _kill(pid):
    """Stop a process and everything it started (uvicorn --reload starts a second process)."""
    try:
        if IS_WINDOWS:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True)
        else:
            os.killpg(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _our_bot():
    """The bot this notebook started last: {"pid", "folder", "app"}, or None."""
    try:
        return json.loads(BOT_PID.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def stop_bot(quiet=False):
    """Stop the bot this notebook started: the same as Ctrl+C in terminal window 2."""
    stopped = False
    running = _our_bot()
    if running:
        _kill(running["pid"])
        stopped = True
    BOT_PID.unlink(missing_ok=True)

    for _ in range(40):                     # wait up to 10 s for port 8000 to be free again
        if not _port_busy():
            break
        time.sleep(0.25)

    if quiet:
        return
    if _port_busy():
        _bad(f"Port {PORT} is still in use by a bot this notebook did not start (a terminal bot?).")
        _tip("Go to that terminal and press Ctrl+C.")
    elif stopped:
        _ok("Bot stopped.")
    else:
        _ok("No bot was running.")


def start_bot(folder=".", app="agent.app:app", wait=90, restart=True):
    """
    Start a step's bot in the background:  cd <folder>  then  uvicorn <app> --reload
    Any bot this notebook started before is stopped first (only one bot fits on port 8000).
    restart=False keeps the bot if exactly this one is already running (see ensure_bot).
    """
    running = _our_bot()
    if not restart and running and running.get("folder") == folder and running.get("app") == app and _bot_answers():
        _ok(f"Bot is already running: {folder} · {app} (port {PORT}).")
        return True

    stop_bot(quiet=True)

    if _port_busy():
        _bad(f"Port {PORT} is already in use, probably by a bot you started in a terminal.")
        _tip("Pick one path: go to that terminal and press Ctrl+C, then run this cell again.")
        return False

    command = [sys.executable, "-m", "uvicorn", app, "--reload", "--port", str(PORT)]
    print(f"$ cd {folder}   ·   uvicorn {app} --reload   (running in the background)\n")

    extra = {}
    if IS_WINDOWS:
        extra["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        extra["start_new_session"] = True   # its own process group, so stop_bot() stops the reloader too

    log = open(BOT_LOG, "w", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=ROOT / folder,
        env=_environment(),
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        **extra,
    )
    BOT_PID.write_text(json.dumps({"pid": process.pid, "folder": folder, "app": app}), encoding="utf-8")

    started = time.time()
    while time.time() - started < wait:
        if process.poll() is not None:
            _bad("The bot stopped right after starting. Its last lines:")
            bot_log(20)
            BOT_PID.unlink(missing_ok=True)
            return False
        if _bot_answers():
            _ok(f"Agent API is running: {app} (port {PORT}). Try {url('/docs')}")
            return True
        time.sleep(0.5)

    _bad(f"The bot did not answer within {wait} seconds. Its last lines:")
    bot_log(20)
    return False


def ensure_bot(folder=".", app="agent.app:app"):
    """Make sure this bot is running; leave it alone if it already is. Part 2 uses this."""
    return start_bot(folder, app, restart=False)


def bot_log(lines=25):
    """Show the last lines the bot printed: what terminal window 2 would show you."""
    if not BOT_LOG.exists():
        _tip("No bot log yet: start a bot first.")
        return
    text = BOT_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    print("─── bot log (terminal window 2) " + "─" * 40)
    print("\n".join(text[-lines:]) or "(empty)")
    print("─" * 72)


def open_page(path="/", label="Open the chat page"):
    """A clickable link to the bot (the chat page, or /docs)."""
    if not _port_busy():
        _bad("No bot is running yet: run the 'start the bot' cell first.")
        return
    _show_link(url(path), label)
    if os.getenv("CODESPACE_NAME"):
        _tip("Codespaces: the link opens in a new tab. You can also use the PORTS tab → port 8000 → 🌐.")


# ---------------------------------------------------------------------------
# 3 · Talk to the agent from the notebook (POST /chat)
# ---------------------------------------------------------------------------
def _print_steps(steps):
    for step in steps:
        kind = step.get("type", "")
        if kind == "review":
            detail = ("APPROVED: " if step.get("approved") else "SENT BACK: ") + step.get("reason", "")
        elif kind in ("tool_result", "plan"):
            detail = (step.get("name", "") + " " + str(step.get("content", "")).replace("\n", " "))[:90]
        elif kind == "reply":
            continue
        else:
            detail = step.get("name", "") + " " + json.dumps(step.get("args", ""))
        print(f"   {step.get('agent', ''):<17} {kind:<11} {detail}")


def ask(message, version=None, steps=True):
    """Send one customer message to the running agent API and show what happened."""
    import httpx
    if not _bot_answers():
        _bad("No agent API is answering on port 8000: run the 'start the agent' cell first.")
        return None
    body = {"message": message}
    if version:
        body["version"] = version
    try:
        response = httpx.post(f"http://127.0.0.1:{PORT}/chat", json=body, timeout=300)
    except httpx.HTTPError as error:
        _bad(f"The request failed: {error}")
        return None
    if response.status_code != 200:
        _bad(f"HTTP {response.status_code}: {response.text[:300]}")
        _tip("Look at the server log (nb.bot_log()) for the full error.")
        return None
    data = response.json()
    print(f"🧑 v{data.get('version')} · You: {message}")
    if steps:
        _print_steps(data.get("steps", []))
    print(f"   outcome: {json.dumps(data.get('outcome'))}")
    if data.get("sources"):
        print(f"   📚 pages it read: {', '.join(data['sources'])}")
    print(f"🤖 Agent: {data.get('reply', '')}\n")
    return data


def compare(message, versions=(1, 2, 3)):
    """The same message to several versions, one after the other: spot the difference."""
    for version in versions:
        ask(message, version=version)


def show(path, start=None, end=None):
    """Print a file from the repo (or lines start..end) so you can read the real code in the notebook."""
    file = ROOT / path
    if not file.exists():
        _bad(f"No such file: {path}")
        return
    text = file.read_text(encoding="utf-8").splitlines()
    first = (start or 1) - 1
    last = end or len(text)
    print(f"─── {path} (lines {first + 1}-{last}) " + "─" * 30)
    for number, line in enumerate(text[first:last], start=first + 1):
        print(f"{number:>4}  {line}")


# ---------------------------------------------------------------------------
# 4 · The scoreboard (Part 2)
# ---------------------------------------------------------------------------
def report(height=600):
    """Show evaluate/report.html inside the notebook (every pytest run in Part 2 writes it)."""
    file = ROOT / "evaluate" / "report.html"
    if not file.exists():
        _tip("No scoreboard yet: run a pytest cell first.")
        return
    page = file.read_text(encoding="utf-8").replace('<meta http-equiv="refresh" content="2">', "")
    try:
        import warnings
        from IPython.display import HTML, display
        warnings.filterwarnings("ignore", message="Consider using IPython.display.IFrame")
        display(HTML(
            f'<iframe srcdoc="{html.escape(page)}" '
            f'style="width:100%;height:{height}px;border:1px solid #ccc;border-radius:6px;background:#fff"></iframe>'
        ))
        _tip("Run this cell again after the next pytest run to refresh it. "
             "Or open evaluate/report.html from the Explorer.")
    except ImportError:
        print(f"Open {file} in your browser.")
