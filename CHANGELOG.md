# Changelog

## [Unreleased]

- **NEW**: Add a Windows desktop interface with a first-run setup wizard and an import dashboard.
- **ADD**: Add saved user configuration for the JSONL source and PostgreSQL connection, including optional SSL/TLS.
- **UPDATE**: Configure the import flow from saved settings and report processed snapshots and inserted records.
- **CHANGES**: Validate JSONL input and report invalid records with their line numbers.
- **CHANGES**: Reuse one cargo-normalization function for requested and current cargo; remove the obsolete commented-out formatter.

## 2026-10-28

- **ADD**: Add repository-specific instructions for AI agents.

## 2026-09-12

- **UPDATE**: Move application and database settings to the shared configuration provider.
- **CHANGES**: Align database models, repositories, services, and the entry point with the updated configuration.

## 2026-09-05

- **UPDATE**: Extend order data to include current cargo and adjust train and event handling.
- **NEW**: Add a service container to construct and connect application services.

## 2026-08-31

- **NEW**: Implement the initial Factorio LTN snapshot processing flow, including JSONL parsing, schema conversion, and batched order and event persistence.
- **ADD**: Add asynchronous PostgreSQL access, ORM models, repositories, services, and shared configuration and logging.
- **ADD**: Add the project's initial dependencies.
