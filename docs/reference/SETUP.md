# Setting This Up in VS Code — Start Here

Written assuming you have never used VS Code, a terminal, or Python before. If a step seems obvious, skip it. Nothing here can break your computer.

Budget about 45 minutes the first time. Most of that is waiting for downloads.

---

## What you're actually building

A few words on jargon before we start, because the rest of this makes no sense otherwise.

**VS Code** is a text editor. That's it. It opens a folder on your computer and lets you edit the files inside it. It does not run Python by itself — it just makes it convenient to.

**A terminal** is a window where you type commands instead of clicking buttons. VS Code has one built in, at the bottom of the window. When I say "run this in the terminal," I mean type it there and press Enter.

**Python** is the language the scripts are written in. You install it once, separately from VS Code.

**A package** is code somebody else wrote that your scripts need. `numpy` does maths, `matplotlib` makes graphs, `rocketcea` is NASA's chemistry program. You install these with a command called `pip`.

**A virtual environment** (or "venv") is a private box of packages that belongs to just this one project. Without it, everything you install goes into one global pile and different projects start fighting over versions. It's a folder called `.venv` that sits inside your project. You make one per project and then forget about it.

**A compiler** turns source code into a program your computer can run. You need one called **gfortran** because `rocketcea` ships NASA's original 1990s Fortran source code and builds it on your machine during installation. This is the single most likely thing to go wrong, and it gets its own section below.

---

## Step 1 — Install VS Code

Go to **https://code.visualstudio.com** and click the big download button. It will detect your operating system.

- **Windows**: run the installer. When it asks, tick **"Add to PATH"**. This matters later.
- **macOS**: you get a `.zip`. Unzip it and drag `Visual Studio Code.app` into your Applications folder.

Open it. You'll get a Welcome tab. Close that.

---

## Step 2 — Install Python

**Windows:** go to **https://www.python.org/downloads/** and download the latest 3.12 or 3.13 installer.

> On the very first screen of the installer, there is a checkbox at the bottom that says **"Add python.exe to PATH"**. **Tick it.** It is off by default. If you miss it, the terminal won't be able to find Python and nothing in this guide will work. If you already installed Python without ticking it, just run the installer again and choose "Modify."

**macOS:** open the Terminal app (Cmd+Space, type "Terminal") and run:

```
xcode-select --install
```

That gives you Apple's developer tools. Then install Homebrew, which is a package manager for macOS, by pasting the command from **https://brew.sh**. Then:

```
brew install python
```

**Check it worked.** In VS Code, open a terminal with **Ctrl+`** (that's the backtick key, top-left of your keyboard, under Escape). Or use the menu: **Terminal → New Terminal**. Type:

```
python --version
```

You should see something like `Python 3.12.4`. If you get "command not found" or "not recognized", Python isn't on your PATH — reinstall and tick the box.

> **Mac users:** you may need to type `python3` and `pip3` instead of `python` and `pip` everywhere in this guide. If `python` doesn't work, try `python3`.

---

## Step 3 — Install the Python extension

In VS Code, look at the icons down the far-left edge. Click the one that looks like four squares with one flying off — that's **Extensions**. (Or press Ctrl+Shift+X.)

Search for **Python**. Install the one published by **Microsoft**. It has tens of millions of downloads, you can't miss it.

That's the only extension you actually need.

---

## Step 4 — Set up your folder

You said you have a `hybridrocket` folder with a papers subfolder. Let's organise it like this:

```
hybridrocket/
├── papers/              <- your research PDFs, leave them alone
├── analysis/            <- NEW: everything from Claude goes here
│   ├── cea_deck.py
│   ├── cea_sweep.py
│   ├── motorsim.py
│   ├── design_sweep.py
│   ├── run_baseline.py
│   ├── requirements.txt
│   └── SETUP.md         <- this file
└── ...
```

Make the `analysis` folder however you normally make folders (right-click → New Folder in Explorer or Finder).

**Important:** keep all five `.py` files loose in `analysis/`, side by side. Don't nest them in further subfolders. They import each other by filename, and moving them into subfolders will break those imports.

**Download the files.** Each file I sent appears as a card in our conversation. Click a card, then click the download icon. Your browser will drop it in your Downloads folder. Move all of them into `analysis/`.

**Open the folder in VS Code.** **File → Open Folder**, then pick `hybridrocket`. (On Mac it might say "Open…") You'll see your files listed in the left sidebar — that panel is called the **Explorer**. Click any `.py` file to view it.

> Open the *whole* `hybridrocket` folder, not just `analysis`. That way your papers are visible too, and later on Claude Code can see everything at once.

---

## Step 5 — Install gfortran (the fiddly one)

This is where most people get stuck. Read the section for your OS.

### macOS

You already have it if you installed Homebrew above:

```
brew install gcc
```

That's it. Homebrew's `gcc` package includes `gfortran`. Skip to Step 6.

### Windows — the honest recommendation

Getting a Fortran compiler working natively on Windows is genuinely painful. The reliable path is **WSL**, which stands for Windows Subsystem for Linux. It runs a real Ubuntu Linux inside Windows, and VS Code connects to it seamlessly. This is also *exactly* the environment I used to generate your results, so you'll get identical numbers.

Open **PowerShell as Administrator** (right-click the Start button → "Terminal (Admin)" or "Windows PowerShell (Admin)") and run:

```
wsl --install
```

Restart your computer when it asks. On restart, a black Ubuntu window opens and asks you to pick a username and password. Pick anything — write the password down, you'll need it for `sudo`. Note that when you type the password, **nothing appears on screen**. That's normal, not a frozen terminal. Just type it and press Enter.

Then in VS Code, install the extension called **WSL** (also by Microsoft). Press **Ctrl+Shift+P** to open the Command Palette — that's a search box for every VS Code command, and it's the single most useful thing in the editor. Type `WSL: Connect to WSL` and press Enter.

VS Code reopens, now connected to Linux. The bottom-left corner will show a green badge saying `WSL: Ubuntu`. Open your folder again from inside there — your Windows drives are at `/mnt/c/`, so if your folder is at `C:\Users\You\hybridrocket`, it's at `/mnt/c/Users/You/hybridrocket`.

Now in the VS Code terminal (which is now an Ubuntu terminal):

```
sudo apt update
sudo apt install -y python3 python3-pip python3-venv gfortran
```

It'll ask for that password you set. Done.

### Windows — if you really don't want WSL

Install **Miniforge** from https://conda-forge.org/download/, open the "Miniforge Prompt" from your Start menu, and run:

```
conda create -n hybrid python=3.12
conda activate hybrid
conda install -c conda-forge m2w64-toolchain
```

Then skip the venv part of Step 6 and just `pip install -r requirements.txt` inside that conda environment. Fair warning: this route breaks more often than WSL, and I can't test it for you.

---

## Step 6 — Make the virtual environment and install packages

In the VS Code terminal, first move into the analysis folder. `cd` means "change directory":

```
cd analysis
```

> If VS Code opened you somewhere unexpected, `pwd` prints where you currently are and `ls` (Mac/Linux) or `dir` (Windows) lists what's in there.

Create the venv:

```
python3 -m venv .venv
```

(Windows without WSL: `python -m venv .venv`)

This makes a hidden `.venv` folder. Now **activate** it — this tells the terminal "use this project's private package box":

- **Mac / Linux / WSL:** `source .venv/bin/activate`
- **Windows PowerShell:** `.venv\Scripts\Activate.ps1`

Your terminal prompt will now start with `(.venv)`. That's how you know it worked.

> **You have to activate every time you open a new terminal.** This trips up everyone. If a script suddenly says "No module named numpy", 90% of the time you just forgot to activate. Look for `(.venv)` in the prompt.

> **Windows PowerShell may refuse** with a message about "running scripts is disabled". Run this once, then try again:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Now install everything:

```
pip install -r requirements.txt
```

This takes 3–10 minutes. Most of it is `rocketcea` compiling NASA's Fortran. You'll see a wall of scrolling text. That's fine. What you want at the end is `Successfully installed ... rocketcea-1.2.3 ...`.

---

## Step 7 — Point VS Code at the right Python

VS Code doesn't automatically know about your venv. Tell it:

1. Press **Ctrl+Shift+P** (Command Palette)
2. Type `Python: Select Interpreter`
3. Choose the one with `.venv` in the path — it'll usually say `('.venv': venv)` and be at the top

Do this once per project. It's what makes the little squiggly "unresolved import" underlines go away, and it's what the Run button uses.

---

## Step 8 — Run something

Open `run_baseline.py` in the Explorer sidebar. Press the **▶ play button** in the top-right corner of the editor.

Or, in the terminal:

```
python run_baseline.py
```

After a minute or two you should see the design table print out, ending with:

```
APOGEE  49,965 ft (15.23 km)  burnout 2,969 m at 671 m/s, Mmax 2.04
```

Look in the Explorer sidebar — a new `outputs/` folder appeared with a PNG and a CSV in it. Click the PNG; VS Code displays images directly. That's your baseline design.

**If you get exactly that number, everything works.** You now have a full working copy of the analysis.

---

## What each script does

Run them in this order the first time.

| Script | Runtime | What it does |
|---|---|---|
| `cea_deck.py` | instant | Defines the propellant chemistry. You don't run this directly — the others import it. Run it alone to print the fuel card and check the derivation. |
| `cea_sweep.py` | ~2 min | Sweeps O/F, writes the CEA lookup table and the four-panel performance chart. |
| `motorsim.py` | — | The physics: tank, injector, regression, chamber, nozzle, trajectory. Imported, not run directly. |
| `design_sweep.py` | ~5 min | The diameter and oxidiser-load trade chart. |
| `run_baseline.py` | ~2 min | The converged 50,000 ft design, plots and time history. |

---

## Making your first change

Open `run_baseline.py`. Find this line near the top:

```python
cfg, mf = design_sweep.autodesign(20.42, 0.127, tb_target=8.0, m_fixed=22.0)
```

That's oxidiser mass (kg), airframe diameter (m), target burn time (s), and fixed structural mass (kg).

Try changing `20.42` to `23.0` and re-running. Apogee should jump to roughly 57,000 ft. Change it back.

Now try adding a line right after it, before the `simulate` call:

```python
cfg['eps'] = 8.0          # bigger nozzle expansion ratio
```

Re-run and see what happens to apogee. That's the whole workflow: change a number, run, look at the result.

**Save before you run.** Ctrl+S. VS Code runs what's on disk, not what's on screen. If your edit seems to have no effect, you probably didn't save.

---

## When something goes wrong

| Message | What it means | Fix |
|---|---|---|
| `'python' is not recognized` / `command not found` | Python isn't on your PATH | Reinstall Python, tick "Add to PATH". Try `python3`. |
| `No module named numpy` (or scipy, CoolProp…) | Venv not activated, or packages not installed | Check for `(.venv)` in your prompt. Activate, then `pip install -r requirements.txt`. |
| `No module named cea_deck` | You're running from the wrong folder | `cd` into `analysis` first. All five `.py` files must sit together. |
| rocketcea install fails, mentions `gfortran`/`ifort`/`g95` | No Fortran compiler | Step 5. This is the big one. |
| `running scripts is disabled on this system` | Windows PowerShell policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Squiggly underlines under imports, but it runs fine | VS Code is looking at the wrong Python | Step 7, select the `.venv` interpreter. |
| Nothing shows when typing your WSL password | Normal Linux behaviour | Just type it and press Enter. |

**How to read an error.** Python prints a "traceback" — a stack of lines ending with the actual error. **Read the last line first.** Everything above it is just the path the code took to get there. The last line tells you what actually broke.

---

## Optional but worth it: version control

Git tracks every change you make, so you can always get back to a working version. Essential once more than one person is editing.

```
cd ..                    # back up to hybridrocket/
git init
git add .
git commit -m "Initial CEA and motor sizing analysis from Claude"
```

The `.gitignore` file I included tells git to skip the `.venv` folder and generated outputs, since those get rebuilt and would otherwise bloat the repo.

If your team wants to share, make an empty repo on GitHub and follow the "push an existing repository" instructions it gives you. **Be careful about making it public** if your team has competition rules about publishing designs.

---

## Getting your papers back to me

Two ways:

**For the papers folder** — upload the PDFs into this conversation's **Project knowledge** (the Project panel → Add content). Then I can search them in every future conversation, the way I searched the six PDFs already there. This is the right home for reference material you'll come back to.

**For one-off files** — just drag them into the chat.

---

## The better long-term setup

Everything above involves downloading files from a chat and uploading them back. That gets old fast.

**Claude Code** is a VS Code extension that works directly on your `hybridrocket` folder. It reads your papers, edits `motorsim.py` in place, runs the sweeps in your terminal, and commits to git — no round trips. It also sees your whole project at once instead of only what you remembered to paste.

Install it from the Extensions panel (search "Claude Code") or from **https://claude.com/code**. You sign in with the same account you're using now.

Once it's set up, you can just say things like *"add a helium supercharge option to the tank model and show me what it does to the O/F curve"* and it will edit the file and run it.
