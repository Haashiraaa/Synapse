# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-07-19

**Full Changelog**: https://github.com/Haashiraaa/Synapse/compare/v0.4.0...v0.4.1

## [0.4.0] - 2026-07-15

### Added
 - Multi-group support: `ALLOWED_CHAT_IDS` (comma-separated) replaces `ALLOWED_CHAT_ID`. Each group gets independent conversation history, summary, and message window.

 ### Changed
 - Startup/shutdown notifications now fan out to every configured group instead of a single chat, with per-group failure isolation (one group's send failure no longer blocks the others).

 ### Breaking
 - `ALLOWED_CHAT_ID` env var is no longer read. Rename it to `ALLOWED_CHAT_IDS` in `.env` before upgrading — the bot will fail to start otherwise (fails loudly, not silently).

**Full Changelog**: https://github.com/Haashiraaa/Synapse/compare/v0.3.1...v0.4.0

## [0.3.1] - 2026-07-15

**Full Changelog**: https://github.com/Haashiraaa/Synapse/compare/v0.3.0...v0.3.1

## [0.3.0] - 2026-07-12

**Full Changelog**: https://github.com/Haashiraaa/Synapse/compare/v0.2.5...v0.3.0

## [0.2.5] - 2026-07-11

**Full Changelog**: https://github.com/Haashiraaa/Synapse/compare/v0.2.4...v0.2.5

## [0.2.4] - 2026-07-07

**Full Changelog**: https://github.com/Haashiraaa/Synapse/compare/v0.2.3...v0.2.4

## [0.2.3] - 2026-07-07

**Full Changelog**: https://github.com/Haashiraaa/Synapse/compare/v0.2.2...v0.2.3

## [0.2.2] - 2026-07-05

**Full Changelog**: https://github.com/Haashiraaa/Synapse/compare/v0.2.1...v0.2.2

## [0.2.1] - 2026-07-05

**Full Changelog**: https://github.com/Haashiraaa/Synapse/compare/v0.2.0...v0.2.1

## [0.2.0] - 2026-07-05

**Full Changelog**: https://github.com/Haashiraaa/Synapse/compare/v0.1.0...v0.2.0

## [0.1.0] - 2026-07-05

**Full Changelog**: https://github.com/Haashiraaa/Synapse/commits/v0.1.0
