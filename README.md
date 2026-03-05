# Py4GW Cryway Custom Behaviours 
Py4GW is a pretty cool framework that lets you do a lot of scripting for multiboxers far beyond what was available with gwa2. I am very happy to come back to the game after ytears and have a nice base tool to build on. 

This will be a mostly compatible fork of Py4GW, with most of the changes being to mutliboxing skill defines. the builds are all built around cryway which despite the changes over time is still my favorite team builds to play this game with. If you love caster teams of necros and mesmers all in caster roles, cryway is the build for you.

## Alys cry of pain was nerfed in 2009... what are you doing?
Yes, yes and yes mesmer and nerco hero ways are still the op path. What if I tell you, discord way and offensive mesmer way are just degredations of cryway. You can have the wide aoe of mesmer ways and the solid single target spike of discord way with less stringent requirements then discord? Thats right we get to play fun bars like ebon vanguard assassin support or ymlad! or air of superiority, cry of pain or technobabble or light of deldrimor, cry of frustration, energy surge, necrosis, then whatever ever, spiritual pain, and rupts you want on our spikers and for primary nercos we can bring EoE like effects with an icy veins character that can still spike with necrosis?  And if youre not a fan of mesmers, Echoing Feast of Corruption spikers work great too instead/in addition to energy surge. 

ymlad! and necrosis get around spell protection as they are a shout and skill respectively which makes a lot of the more obnoxious mobs into just more fodder.

# Py4GW 

**Py4GW** is a Python library designed to enhance the Guild Wars experience by providing tools for automation, scripting, and in-game interactions.
---

## Features

- **Agent Handling**: Manage agents (NPCs, enemies, allies) with ease.
- **Inventory Management**: Automate inventory-related tasks such as item handling and categorization.
- **Pathfinding and Navigation**: Built-in tools for pathfinding and movement.
- **Widgets**: Extensible widgets for customizing user experiences, including travel, titles, and more.
- **Event Hooks**: Hook into game events and create your own custom logic.
- **Multi-Account Support**: Efficiently manage multiple accounts simultaneously.
- **Lightweight and Modular**: Designed to be fast, modular, and easy to extend.

---

## 🚀 Getting Started

### **Prerequisites**

- Python 3.13.0 32-bit [link](https://www.python.org/downloads/release/python-3130/) (other versions could causes GW Client crashes)
- Guild Wars client

### **Installation**

1. Clone the repository:
   ```bash
   git clone https://github.com/apoguita/Py4GW.git
   ```
2. Navigate to the project directory:
   ```bash
   cd Py4GW
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 📂 Directory Structure

```
Py4GW/
├── Py4GW_python_files/             # Main directory containing all project files
│   ├── Addons/                     # Add-on extensions (e.g., GWBlackBOX.dll)
│   ├── DEMO/                       # Example scripts demonstrating library usage
│   ├── HeroAI/                     # Hero AI automation and logic
│   ├── Py4GWCoreLib/               # Core library for Guild Wars automation
│   ├── Widgets/                    # Widgets for in-game interactions
│   ├── resources/                  # Fonts, configs, and other resources
│   ├── stubs/                      # Type hint files for Python development
│   ├── build/                      # Build directory
│   ├── dist/                       # Distribution directory
│   ├── Legacy code and tests/      # Archived code and test scripts
│   ├── Working Miscelaneous code/  # Experimental or temporary scripts
│   ├── Py4GW.dll                   # Main DLL for the project
│   ├── Py4GW.ini                   # Configuration file
│   ├── Py4GW_Launcher.py           # Launcher script
│   ├── Barebones_Example_module.py # Minimal example script
│   └── requirements.txt            # Dependencies
```

---

## 📥 How to Download

1. Go to the [Releases Page](https://github.com/apoguita/Py4GW/releases/tag/Official).
2. Download the files under "Assets."
3. Extract them to your preferred directory.

---

## 🤝 Contributing

We welcome contributions from the community! Here’s how you can get involved:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes and push the branch.
4. Submit a pull request for review.

### Stop tracking log/configuration files

If you want want to stop tracking local changes to the log and configuration files used by Py4GW you can use the following commands to temporarly remove them from the worktree.

```bash
git update-index --skip-worktree Py4GW_injection_log.txt
git update-index --skip-worktree Py4GW.ini
git update-index --skip-worktree Py4GW_Launcher.ini
```

You can then verify that the files are correctly skipped by running this command that should output the list of skipped files: 

```bash
git ls-files -v | grep "^S"
S Py4GW.ini
S Py4GW_Launcher.ini
S Py4GW_injection_log.txt
```

To re-enable local tracking of the files run the following commands: 

```bash
git update-index --no-skip-worktree Py4GW_injection_log.txt
git update-index --no-skip-worktree Py4GW.ini
git update-index --no-skip-worktree Py4GW_Launcher.ini
```
