# Changelog

All notable changes to **tessara** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- `tessara -v` and `tessara --version` print the version and exit with status 0, as the
  command-line conventions of the workspace require; they previously stopped on a missing
  command with status 2.
