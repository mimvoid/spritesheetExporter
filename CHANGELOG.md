# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Changed

- Enable column or row sizing for both horizontal and vertical directions ([`5593a36`](/../../commit/5593a36))
- Shorten tooltips for quicker reading ([`b2dac58`](/../../commit/b2dac58))

## 0.1.0 - 2025-08-08

_Initial release._

### Added

- Add ability to export only unique frames ([`839c5e7`](/../../commit/839c5e7))
- Add sprite padding and clipping ([`991ed8a`](/../../commit/991ed8a))
- Add custom base name option ([`9915b21`](/../../commit/9915b21))

### Changed

- **Breaking:** Only set columns with horizontal placement, only set rows with vertical placement ([`ff0a43a`](/../../commit/ff0a43a))
- Change path operations to respect user's file extension ([`9053518`](/../../commit/9053518))
- Overhaul dialog widget UI

### Fixed

- Fix occasional empty sprite ([`13b8e07`](/../../commit/13b8e07))
- Check if there is an active document before doing anything ([`f287ceb`](/../../commit/f287ceb))
