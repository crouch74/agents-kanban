# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 🐳 Docker support for local development with `docker-compose.yml`.
- 📦 Dockerfiles for `apps/api` and `apps/web`.
- 🩺 Health checks for the API service in Docker.

### Changed
- 🔥 Improved hot reload for the backend: now watches both `apps/api` and `packages/core/src`.
- 📡 Optimized frontend hot reload for Docker by listening on `0.0.0.0`.
- 🧭 Updated `scripts/dev-api.sh` to include core package in watch list.
