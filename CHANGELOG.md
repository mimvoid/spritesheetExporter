# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.3.0 - 2025-11-30

### Changed

- Rename the plugin to **Sprites Exporter** to distinguish it from Spritesheet Exporter going forward.
  The code has been extensively refactored, the UI overhauled, and new features added. However, the
  name remains similar to pay homage to its origins.
- Rewire UI signals (exporting is noticeably more responsive) ([`1ad3539`](/../../commit/1ad3539))
- Lazy load dialog window ([`72d78bc`](/../../commit/72d78bc))
- Limit start and end frame spin boxes' values to each other ([`ebe364b`](/../../commit/ebe364b))

### Fixed

- Fix frame spin boxes initializing with `0` instead of `Auto` ([`c12f369`](/../../commit/c12f369))

## 0.2.0 - 2025-11-12

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
