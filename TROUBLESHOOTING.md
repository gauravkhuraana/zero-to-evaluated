# Troubleshooting FAQ

**If you get stuck anywhere, contact [Gaurav Khurana on LinkedIn](https://www.linkedin.com/in/gauravkhuraana/).**

Can't message on LinkedIn? Email: **gaurav [dot] khuraana [at] gmail [dot] com** (replace `[dot]` with `.` and `[at]` with `@`, then remove the spaces).

From the project folder with `.venv` active, the setup check prints a FAQ number for every red line:
```bash
python check_setup.py
```

Find that number below. Stuck for more than 3 minutes? Pair with a neighbour, or switch to GitHub Codespaces (#18).
Nothing in this workshop needs editing, so there is nothing to fall behind on: every command works on its own.

---

## Table of contents

- [#1 · Wrong Python version](#1--wrong-python-version)
- [#2 · Library installation fails](#2--library-installation-fails)
- [#3 · Model server not reachable](#3--model-server-not-reachable)
- [#3b · `ModuleNotFoundError: No module named 'config'`](#3b--modulenotfounderror-no-module-named-config)
- [#4 · Windows won't activate the virtual environment](#4--windows-wont-activate-the-virtual-environment)
- [#5 · No admin rights on a company laptop](#5--no-admin-rights-on-a-company-laptop)
- [#6 · Switching between Groq and Ollama](#6--switching-between-groq-and-ollama)
- [#7 · `.env` missing or Groq key missing](#7--env-missing-or-groq-key-missing)
- [#8 · Port 8000 already in use](#8--port-8000-already-in-use)
- [#9 · Model not found](#9--model-not-found)
- [#10 · The agent ignores the policy pages](#10--the-agent-ignores-the-policy-pages)
- [#11 · The model doesn't call tools](#11--the-model-doesnt-call-tools)
- [#12 · The agent loops, or takes very long](#12--the-agent-loops-or-takes-very-long)
- [#13 · Judge error: "invalid JSON" / "could not parse"](#13--judge-error-invalid-json--could-not-parse)
- [#14 · Error 429 / "rate limit"](#14--error-429--rate-limit)
- [#15 · The tests are very slow](#15--the-tests-are-very-slow)
- [#16 · `/docs` shows an error](#16--docs-shows-an-error)
- [#17 · SSL / certificate errors on a company network](#17--ssl--certificate-errors-on-a-company-network)
- [#18 · My laptop can't run it at all](#18--my-laptop-cant-run-it-at-all)
- [#19 · Tests are red for no reason / the agent says strange things](#19--tests-are-red-for-no-reason--the-agent-says-strange-things)
- [#20 · The notebook can't find its kernel, or VS Code has no ▶ button](#20--the-notebook-cant-find-its-kernel-or-vs-code-has-no--button)
- [#21 · LangSmith: no traces, or "401 / invalid API key"](#21--langsmith-no-traces-or-401--invalid-api-key)

### #1 · Wrong Python version
Use a stable **Python 3.12.x**, the required workshop series. The recommended install is **Python 3.12.10**. Both setup scripts flag a different series or prerelease.

**Keep other Python versions installed.** You do not need to uninstall anything. Do **not** install "the latest Python" from python.org, which now advertises 3.14. Install 3.12.10 with the [one-command Windows install or the Mac steps](SETUP.md#1--install-python-one-time), then **open a new terminal** and check it:

**Windows**
```powershell
py -3.12 --version
```

**Mac / Linux**
```bash
python3.12 --version
```

Expect **Python 3.12.x**. Then confirm it can run code:

**Windows**
```powershell
py -3.12 -c "print('Python is working')"
```

**Mac / Linux**
```bash
python3.12 -c "print('Python is working')"
```

**Windows says "py is not recognized" or "No suitable Python runtime found"?** Close PowerShell and open a new one. Still failing? Run `winget install --id Python.Python.3.12 --version 3.12.10 --exact --source winget`. No winget? Use the [official installer](https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe). **Mac says "command not found: python3.12"?** Finish the installer from the guide, then open a new Terminal. Corporate laptop blocking installs? Use [the browser fallback](SETUP.md#path-b--in-the-browser-github-codespaces). Do not replace the failing command with plain `python`, which may be a different version.

**Already have `.venv` from another Python?** Activating it or installing another Python does not change its interpreter. Setup prints the environment's version and stops before package installation when it is incompatible.

1. Stop tutorial servers with **Ctrl+C**. If the current terminal has an active environment, run `deactivate`, then open a new terminal in the project folder.
2. Rename the existing environment with the command for your platform below. Run the rename **only if `.venv` exists** and the backup name **does not exist**; otherwise choose an unused backup name. This preserves a backup, but a moved environment is not intended to run from its backup location.
3. Run setup with 3.12. It creates a fresh `.venv`; it does not delete your `.env` settings or source files.

**Windows**

```powershell
Rename-Item -LiteralPath .venv -NewName .venv-before-python312
```

```powershell
py -3.12 setup_env.py
```

**Mac / Linux**

```bash
mv .venv .venv-before-python312
```

```bash
python3.12 setup_env.py
```

Activate the new `.venv` using your platform's command in the setup guide. Then `python --version` must show **3.12.x** and normal `python` commands use it, even if your system default is another version. Run `python check_setup.py` inside that environment.

VS Code is installed separately from [its official download page](https://code.visualstudio.com/download). Install Microsoft's **Python** extension and open the project folder. **Optional:** if VS Code asks which interpreter to use, choose the one in `.venv` (or use **Python: Select Interpreter**); the terminal commands work without it. Installing the extension alone does not install Python.

### #2 · Library installation fails
- Easiest fix on **Windows**:

  ```powershell
  py -3.12 setup_env.py
  ```

- On **Mac/Linux**:

  ```bash
  python3.12 setup_env.py
  ```

The setup script creates the virtual environment and installs the libraries. You can run it again after a failure. If `py -3.12` or `python3.12` is not found, complete [setup step 1](SETUP.md#1--install-python-one-time) first.

- Use a virtual environment (see SETUP.md) so you don't need admin rights. The setup script installs execution libraries into `.venv`; it does not install Python or VS Code.
- Behind a company proxy:

  ```bash
  pip install --proxy http://your-proxy:port -r requirements.txt
  ```

- SSL errors on a company network: see #17.
- "Microsoft Visual C++ required" on Windows: activate `.venv`, upgrade pip, then retry the installation. Recent packages ship pre-built:

  ```bash
  python -m pip install --upgrade pip
  ```

### #3 · Model server not reachable
Using **Groq** (the default)? Check your internet connection, and that `LLM_API_KEY` in `.env` holds your Groq key (see #7). Company network? See #17.

Using **Ollama** (`localhost:11434`)? First open http://localhost:11434 in a browser. **"Ollama is running" means it is fine: do not run `ollama serve`.** If the page does not load:
- Windows/Mac: start the **Ollama** app (look for the llama icon in the tray/menu bar), then refresh the page.
- Still not loading, or on Linux: open a **new terminal window** and start the server:

  ```bash
  ollama serve
  ```

  **Leave that window open** (closing it stops Ollama). If it says *"Only one usage of each socket address (protocol/network address/port) is normally permitted"* (Windows) or `address already in use`, that is **good news**: Ollama is already running. Check the browser page.
- Using LM Studio instead? Start its **local server** (Developer tab) and use Option C in `.env`.

### #3b · `ModuleNotFoundError: No module named 'step2_agent'` (or `step1_chatbot`)
Run every command from the **project folder** (the one with `app.py` and `check_setup.py`), with `.venv` active. Check where you are:

```bash
ls app.py
```

(Windows: `Get-Item app.py`.) Not found? `cd` back to the project folder first.

### #4 · Windows won't activate the virtual environment
PowerShell says "running scripts is disabled on this system":
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

```powershell
.venv\Scripts\Activate.ps1
```

Or use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

### #5 · No admin rights on a company laptop
- Python: the winget command and the official installer normally install Python for your own user. If your company blocks installs or asks for an administrator password, contact Gaurav and use the [browser fallback](SETUP.md#path-b--in-the-browser-github-codespaces). Do not try to bypass the restriction.
- Ollama is for Path A (your own laptop) only, and may need admin rights. If installation is blocked, tell Gaurav and use Path B (browser) in [SETUP.md](SETUP.md); Groq stays the default.
- Company firewall blocks sign-ups or downloads: pair with a neighbour, or use GitHub Codespaces (#18).

### #6 · Switching between Groq and Ollama
- **Groq** (the default, Option A in `.env`) runs in the cloud. Nothing to install, needs internet and a free key.
- **Ollama** (Option B in `.env`) runs on your laptop. Install it and download the model:

  ```bash
  ollama pull qwen3:4b
  ```

  Then switch the `LLM_*` lines in `.env` to Option B. Laptop too slow? Download a smaller model and set `LLM_MODEL=qwen3:1.7b`:

  ```bash
  ollama pull qwen3:1.7b
  ```

- Every agent version reads all `LLM_*` lines from `.env`, so switching is only a change in `.env`. Restart the API afterwards.

### #7 · `.env` missing or Groq key missing
1. Copy the template on **Windows**:

   ```powershell
   copy .env.example .env
   ```

   Or on **Mac/Linux**:

   ```bash
   cp .env.example .env
   ```

2. Create a free key at https://console.groq.com/keys (no credit card needed)
3. Paste it into `.env` twice: `LLM_API_KEY=gsk_...` (the bot) and `JUDGE_API_KEY=gsk_...` (the judge)
Never commit `.env`: it's in `.gitignore`.

### #8 · Port 8000 already in use
A **port** is a numbered door on your computer, and only one program can use a door at a time. Something else (often an earlier copy of your bot) is already using port 8000, so the new one cannot start.

Easiest fix: **close the terminal** that is running the old bot (or press **Ctrl+C** in it). Not sure which one it is? This command stops whatever is using port 8000:

**Windows (PowerShell)**
```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Get-CimInstance Win32_Process -Filter "ParentProcessId=$($_.OwningProcess)" | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
```

**Mac / Linux**
```bash
kill $(lsof -ti :8000) 2>/dev/null
```

No output means it worked (or nothing was using the port). Now start your bot again.

**Windows said "Cannot find a process with the process identifier…" and the port is still busy?** Windows reports the number of the old bot's main process, which has already closed, while a leftover helper process of that bot still holds the port. The Windows command above also stops that helper. Run it again, then run `python check_setup.py`.

**Free the right port.** The setup check (`check_setup.py`) looks at port **8000**, and the bot uses 8000. Freeing a different port (for example 8080) will not fix a "Port 8000" error. Only if you started the scoreboard server in Codespaces and it says port 8080 is busy, use the same command with `8080` instead.

Or leave the old program alone and use another port:

```bash
uvicorn app:app --reload --port 8001
```

### #9 · Model not found
- **Groq:** `LLM_MODEL` in `.env` must be a model Groq offers, e.g. `openai/gpt-oss-20b` (list: https://console.groq.com/docs/models).
- **Ollama:** download the model at home (about 2.5 GB), not on conference Wi-Fi:

  ```bash
  ollama pull qwen3:4b
  ```

  The name in `.env` (`LLM_MODEL`) must exactly match the model name shown by:

  ```bash
  ollama list
  ```

  In steps 1-3 the Ollama model name is written in the file itself (`qwen3:4b`).

### #10 · The agent ignores the policy pages
Look at the `[agent] runs tool:` lines when you run `python step2_agent/agent.py`:
- No `search_policy` line? The model answered without looking it up. Small models sometimes skip tools: ask again, or say "check the policy".
- Did you change `TOOLS` or `SYSTEM_PROMPT` in `agent.py` during step 5? Undo it (#19).
- Small models still drift sometimes. That's a real finding, and exactly what the step 4 judge catches.

### #11 · The model doesn't call tools
Not every model supports tool calling. The default Groq model (`openai/gpt-oss-20b`) does. On Ollama, use one that does: `qwen3:4b`, `qwen3:8b` or `llama3.1:8b`. Or switch back to Groq (#6).

### #12 · The agent or the crew takes very long
- The agent stops after 5 rounds; the crew's Decider gets at most 2 tries.
- Each run makes 2 to 6 model calls, so it can take a while on a slow connection. Free plans also slow down when many people use them at once (#14).

### #13 · Judge error: "invalid JSON" / "could not parse"
The judge model returned something that isn't valid JSON. Small local models do this often, which is why the default judge is a bigger hosted model. Check `JUDGE_MODEL` in `.env` points at Groq/Cerebras, not your local model.

### #14 · Error 429 / "rate limit"
Free tiers limit requests or tokens per minute. The project lets DeepEval retry transient failures up to 6 times by default.
- Wait a minute and re-run only what failed (`--lf` = **last failed**: run just the tests that failed in the previous run):

  ```bash
  pytest --lf
  ```

- If your provider needs longer backoff, set `DEEPEVAL_RETRY_MAX_ATTEMPTS` and `DEEPEVAL_RETRY_CAP_SECONDS` in `.env`

- Switch to the backup judge (Cerebras) in `.env`

### #15 · The tests are very slow
The judge tests make several judge calls per question. That's the cost of an LLM judge.
- Run one test at a time (`-k` = only tests whose name contains that word):

  ```bash
  pytest step4_judge/test_answers.py -k clearance
  ```

- Step 5's tests mostly need no judge: only the `tool_correctness` and `finishes_the_task` tests call it.

### #16 · `/docs` shows an error
- Is the API running? In its terminal you should see `Application startup complete`. Start it from the project folder:

  ```bash
  uvicorn app:app --reload
  ```

- The API's terminal prints the full error for every failed request. Most often it's the key (#5) or the free-tier limit (#14).
- Try the same question without the API, for a clearer error: `python step2_agent/agent.py`.

### #17 · SSL / certificate errors on a company network
Your company inspects HTTPS traffic. Options:
- Try your phone's hotspot or the conference Wi-Fi.
- Ask IT for the company root certificate and set `SSL_CERT_FILE=path\to\cert.pem`.
- Don't disable certificate checks.

### #18 · My laptop can't run it at all
Use **GitHub Codespaces** (Path B in [SETUP.md](SETUP.md)): everything runs in your browser, nothing to install. You only need a free GitHub account.
Or pair with a neighbour: every step works well in pairs.

### #19 · Tests are red for no reason / the agent says strange things
A change from a **Try these** exercise may still be in the code (a deleted tool, a changed prompt, "60 days" in a policy page).
- In VS Code: open the file and press Ctrl+Z (Mac Cmd+Z) until it's back.
- Cloned with Git? Undo all your changes at once, from the project folder:

  ```bash
  git checkout -- .
  ```

### #20 · The notebook can't find its kernel, or VS Code has no ▶ button
The notebook (`workshop.ipynb`) needs two VS Code extensions and a Jupyter kernel. The setup command installs both when it can.
1. **Extensions:** in VS Code open **Extensions** (Ctrl+Shift+X, Mac Cmd+Shift+X), search **Jupyter** (publisher **Microsoft**) and **Python** (publisher **Microsoft**). Both must say **Installed**. Or, if the `code` command works in your terminal:

   ```bash
   code --install-extension ms-python.python ms-toolsai.jupyter
   ```

2. **Kernel:** top right of the notebook, click the kernel name → **Jupyter Kernel** → **ShopKart agent (.venv)**. Not in the list? With `.venv` active, from the project folder, register it, then reload VS Code (Ctrl+Shift+P → **Developer: Reload Window**):

   ```bash
   python -m ipykernel install --user --name shopkart-agent --display-name "ShopKart agent (.venv)"
   ```

3. **"ipykernel is missing"**: your `.venv` is older than the notebook. Run the setup command again (it reuses the environment).
4. Still stuck? The terminal path runs exactly the same exercises: follow the README instead.

### #21 · LangSmith: no traces, or "401 / invalid API key"
Traces are optional: every exercise works without them.
- In `.env`: `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY=` your key from https://smith.langchain.com/settings (starts with `lsv2_`).
- Restart the API after changing `.env` (Ctrl+C, then `uvicorn app:app --reload` again).
- Your key belongs to more than one workspace? Also set `LANGSMITH_WORKSPACE_ID` (see `.env.example`).
- Traces appear under the project name in `LANGSMITH_PROJECT` (default `shopkart-agent-workshop`), usually within a few seconds.
