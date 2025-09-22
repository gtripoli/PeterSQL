![status: unstable](https://img.shields.io/badge/status-unstable-orange)
![Coverage](https://img.shields.io/badge/coverage-27%25-brightgreen)

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

## 🔧 Technologies used

- [Python 3.11+](https://www.python.org/)
- [wxPython 4.2.3](https://wxpython.org/) - native cross-platform interface
- [wxFormBuilder 4.2.1](https://github.com/wxFormBuilder/wxFormBuilder) - for the construction of the interface

---

## 📸 Screenshot
<p align="center">
  <img src="screenshot/session_manager.png" alt="Session Manager" height="200"/>
  <img src="screenshot/main_frame.png" alt="Main Frame" height="200"/>
</p>

---

## 🚀 How to get started

```bash
git clone https://github.com/gtripoli/petersql.git
cd petersql
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```