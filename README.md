# Proxy-Wright

![App Icon](assets/app.ico)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)](https://doc.qt.io/qtforpython/)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-orange.svg)](https://playwright.dev/python/)
[![License: Non-Commercial](https://img.shields.io/badge/License-NC--Custom-red)](LICENSE)

**Proxy-Wright** is a desktop application for managing **profiles + proxies** and launching Playwright browsers with
predefined settings.  
It is built with **PySide6 + Playwright**, supports **multi-language (English, Vietnamese)**, and includes a built-in *
*update checker**.

---

## ✨ Features

- 📂 Manage multiple **profiles** (add / edit / delete).
- 🌍 Support for **SOCKS5 / HTTP proxies** (with authentication).
- 🧩 Playwright integration (Chromium, Firefox, WebKit).
- 🔄 In-app update check from GitHub Releases.
- 🌐 Multi-language interface.
- ⚡ Modern UI with **PySide6 (Qt for Python)**.

---

## 🌐 Supported Languages

- 🇬🇧 English
- 🇻🇳 Vietnamese

---

## 🖥️ Supported Browsers (Playwright)

- Chromium

---

## 🔌 Supported Proxy Types

- **SOCKS5 (with username/password)** → via internal **3proxy wrapper**
- **HTTP HTTPS SOCKS5(no auth)** → supported natively by Playwright

---

## ⚠️ Antivirus / SmartScreen Warning

This project bundles **PyInstaller** (for packaging) and **3proxy** (for SOCKS5 with authentication).  
Because of this, some antivirus software (including Windows Defender) may flag the binary as suspicious
or potentially unwanted software.

- This is a **false positive** caused by the way PyInstaller packages executables
  and the networking nature of 3proxy.
- The source code is fully available in this repository.
- If you are concerned, you can always build the executable yourself from source:
```bash
git clone https://github.com/houtadono/Proxy-Wright.git
cd Proxy-Wright

--
Download the latest 3proxy release from the official repo:
👉 [3proxy](https://github.com/z3APA3A/3proxy)
---
Copy the 3proxy.exe into the bin/ folder of the project before running the app:

Proxy-Wright/
├─  bin/
│    └─ 3proxy.exe ← replace it here
└─ ...
--

pip install -r requirements.txt
pyinstaller app.spec --noconfirm
```

---

## 📜 License

This project is licensed under the [Proxy-Wright License (Source-Available, Non-Commercial)](LICENSE).  
© 2025 [houtadono](https://github.com/houtadono). All rights reserved.  

- You may use this project for **personal and educational purposes only**.  
- **Commercial usage requires explicit permission** from the copyright holder.  

This project depends on third-party libraries:  
- Playwright (MIT)  
- PySide6 (LGPL v3)  
- 3proxy (BSD)  

See [NOTICE.md](NOTICE.md) for third-party license details.
