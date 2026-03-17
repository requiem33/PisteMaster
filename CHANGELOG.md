# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Electron desktop application infrastructure
- Multi-environment Django settings (development/production/desktop)
- PyInstaller build configuration for bundling Python backend
- GitHub Actions CI/CD workflows for desktop and web builds
- Auto-update support via electron-updater

## [0.1.0] - 2026-03-17

### Added
- Initial MVP release
- Tournament management (CRUD)
- Event management
- Fencer import (manual + Excel paste)
- Pool generation and scoring
- Direct elimination (DE) brackets
- Final ranking calculation
- i18n support (Chinese/English)
- IndexedDB offline storage