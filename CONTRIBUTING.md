# Contributing to PeterSQL

Thank you for your interest in contributing to **PeterSQL**! 🎉  
All contributions are welcome: bug reports, code improvements, documentation, translations, ideas, and feedback.

This document explains how to contribute in a clear and effective way.

---

## 📌 Ways to Contribute

You can help the project in many ways:

- 🐞 Bug reports
- ✨ Feature proposals
- 🧹 Code refactoring and improvements
- 📚 Documentation updates
- 🌍 Translations (gettext / `.po` / `.mo`)
- 🎨 UI / UX improvements
- 🧪 Automated tests

---

## 🐛 Reporting Bugs

Before opening an issue:

1. Check that the bug has not already been reported
2. Make sure you are using a recent version of the project, if possible

When reporting a bug, please include:

- PeterSQL version
- Operating system
- Database used (SQLite, MySQL, PostgreSQL, etc.)
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Logs or traceback, if available

---

## 💡 Proposing Features

New features are welcome, but **PeterSQL aims to remain lightweight and focused**.

Please open an issue describing:

- The problem you want to solve
- The proposed solution
- Possible alternatives considered
- Impact on UI / UX or multi-database compatibility

---

## 🛠️ Development Setup

Main requirements:

- Python **>=3.14**
- wxPython
- Supported databases (optional for development):
    - SQLite
    - MySQL / MariaDB
    - PostgreSQL

```bash
  # 1. clone the repository
  git clone https://github.com/gtripoli/petersql.git
  cd petersql
  
  # 2. install dependency
  uv sync --extra dev

  # 3. run application
  uv run main.py
```

## 🧪 Testing

- Ensure the application works after changes
- Add tests when appropriate
- Avoid regressions across database engines

---

## 🎨 Code Style

Follow the [code style guidelines](CODE_STYLE.md).

---

## 🌍 Translations / i18n

- PeterSQL uses gettext
- UI strings must be wrapped with `_()`
- Translations are stored under `locales/`
- Update `.po` files and regenerate `.mo` files when needed

---

## 🔀 Pull Requests

- Create a dedicated branch (`feature/...`, `fix/...`)
- Keep pull requests small and focused
- Clearly describe what changed and why
- Reference related issues (`Fixes #123`)

---

## 📜 License

By contributing, you agree that your work will be released under the same license as the project.

---

## ❤️ Acknowledgements

PeterSQL is inspired by HeidiSQL.  
Thank you to everyone who contributes to the project.
