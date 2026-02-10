![status: unstable](https://img.shields.io/badge/status-unstable-orange)
![Coverage](https://img.shields.io/badge/coverage-50%25-brightgreen)

![SQLite](https://img.shields.io/badge/SQLite-tested-green)
![MySQL](https://img.shields.io/badge/MySQL-5.7%20%7C%208.0%20%7C%20latest-green)
![MariaDB](https://img.shields.io/badge/MariaDB-5.5%20%7C%2010.11%20%7C%2011.8%20%7C%20latest-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%20%7C%2016%20%7C%20latest-green)

# PeterSQL

<p align="center">
  <img src="petersql_large.png" alt="PeterSQL"/>
</p>

> Heidi's (silly?) friend — a wxPython-based reinterpretation of HeidiSQL

**PeterSQL** is a graphical client for database management, inspired by the
excellent [HeidiSQL](https://www.heidisql.com/), but written entirely in **Python**
using **wxPython**, with a focus on portability and native look & feel.

---

## ⚠️ Project Status

The project is in **active development** and currently unstable.
Features may be incomplete or change without notice.

Use at your own risk and **do not rely on this project in production environments** yet.

---

## 🧭 Why PeterSQL?

Over the years, I have used **HeidiSQL** as my primary tool for working with
MySQL, MariaDB, SQLite, and other databases.
It is a tool I deeply appreciate: **streamlined**, **intuitive**, and
**powerful**.

Rather than trying to compete with HeidiSQL, PeterSQL started as a personal
challenge: to recreate the same *spirit* in a **pure Python** application.

PeterSQL is not a 1:1 port.
It is a Python-first reinterpretation, built with different goals in mind.

- 🐍 **Written entirely in Python**
- 🧩 **Built entirely in Python to enable easy modification and extension**
- 🎯 **Focused on simplicity and clarity**, inspired by HeidiSQL
- 🆓 **Free and open source**

PeterSQL exists for developers who love HeidiSQL’s approach, but want a tool
that feels native to the Python ecosystem.

---

## 🔧 Technologies used

- [Python 3.14+](https://www.python.org/)
- [wxPython 4.2.5](https://wxpython.org/) - native cross-platform interface
- [wxFormBuilder 4.2.1](https://github.com/wxFormBuilder/wxFormBuilder) - for the construction of the interface

---

## 🚀 Installation

PeterSQL uses [uv](https://github.com/astral-sh/uv) for fast and reliable dependency management.

### Prerequisites

- Python 3.11+
- uv (install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/gtripoli/petersql.git
   cd petersql
   ```

2. Install dependencies (including dev tools for testing):
   ```bash
   uv sync
   ```

3. Run the application:
   ```bash
   uv run main.py
   ```

### Development

```bash
uv sync --extra dev
```

To run tests:

```bash
uv run pytest
```

### Troubleshooting installation

#### wxPython

If `uv sync` fails because no compatible wxPython wheel is available for your platform/Python version, reinstall it from source with:
This forces a source build and usually unblocks the setup.

```bash
uv pip install -U --reinstall wxPython==4.2.4 --no-binary wxPython
```

###### Once the build finishes, rerun `uv sync` so the refreshed environment picks up the manually installed wxPython.

## 📸 Screenshot

<p align="center">
  <img src="screenshot/session_manager.png" alt="Session Manager" height="200"/>
  <img src="screenshot/main_frame_columns.png" alt="Main Frame - Columns" height="200"/>
  <img src="screenshot/main_frame_datatypes.png" alt="Main Frame - Datatypes" height="200"/>
  <img src="screenshot/main_frame_default.png" alt="Main Frame - Default" height="200"/>
  <img src="screenshot/main_frame_indexes.png" alt="Main Frame - Indexes" height="200"/>
  <img src="screenshot/main_frame_foreign_keys.png" alt="Main Frame - Foreign Keys" height="200"/>
  <img src="screenshot/main_frame_foreign_keys_columns.png" alt="Main Frame - Foreign Keys Columns" height="200"/>
</p>