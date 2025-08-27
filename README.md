![status: unstable](https://img.shields.io/badge/status-unstable-orange)

# PeterSQL

> Heidi's (silly?) friend - a wxPython porting of HeidiSQL

**PeterSQL** is a graphical client for database management, inspired by the
excellent [HeidiSQL](https://www.heidisql.com/), but written entirely in **Python** with **wxPython**, and designed to
run natively on **All OS**.

---

## ⚠️ Project Status

PeterSQL is currently under active development.  
The project is **not finished** and should be considered **unstable**.

Features may be incomplete, change without notice, or break between versions.  
Use at your own risk and **do not rely on this project in production environments** yet.

---

## 🧭 Why PeterSQL?

Over the years, I have used **HeidiSQL** as my primary tool for working with MySQL, MariaDB, SQLite, and other
databases. It is a tool that I greatly appreciate: **streamlined**, **intuitive**, **powerful**.

So, as a personal challenge, I decided to port it to Python.

- ✅ An interface similar to HeidiSQL
- ✅ A *simple* and *clean* DB client like HeidiSQL
- ✅ A free and open source project, extensible in Python

---

## 🔧 Tecnologie utilizzate

- [Python 3.11+](https://www.python.org/)
- [wxPython 4.2.3](https://wxpython.org/) - native cross-platform interface
- [wxFormBuilder 4.2.1](https://github.com/wxFormBuilder/wxFormBuilder) - for the construction of the interface

---

## 📸 Screenshot

![Session Manager](screenshot/session_manager.png?raw=true "Session Manager")
![Main Frame](screenshot/main_frame.png?raw=true "Main Frame")

---

## 🚀 How to get started

```bash
git clone https://github.com/Lymagi/petersql.git
cd petersql
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

### 📄 LICENSE

```text
PeterSQL - Database Client for Python lovers
Copyright (C) 2025 [Tuo Nome o Username]

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.
...
# Icons copyright
Icons by [Icons8](https://icons8.com)
