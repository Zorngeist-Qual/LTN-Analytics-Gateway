# LTN Analytics Gateway

Standalone Windows desktop application for importing JSONL snapshots produced by the [LTN Analitic Factorio mod](https://github.com/bumbon4eg/LTN_Analitic_0.1.0). The Gateway reads the selected JSONL file, validates and transforms its snapshots, and imports orders and order events into PostgreSQL. It is not required by the mod.

This repository copy contains the Python/Tkinter application source. A packaged executable may be published separately; check the [Gateway Releases page](https://github.com/Zorngeist-Qual/LTN-Analytics-Gateway/releases) for current downloads.

## Requirements

- Windows
- Python 3.12
- PostgreSQL database reachable from this computer
- A JSONL file produced by the Factorio mod

## Run from source

From the `gateway/` directory, create an environment, install the pinned dependencies, and launch the GUI:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

On first launch, the setup wizard asks for the JSONL source and PostgreSQL connection details. The default source is:

```text
%APPDATA%\Factorio\script-output\LTN_Analitic\data.jsonl
```

Choose another file with the browse control if Factorio uses a different user-data directory or if you copied the file elsewhere. The wizard tests the database connection before saving the configuration.

## Use the application

After setup, the dashboard lets you run an import, check the saved database connection, and update source/database settings. Import processing reads non-empty JSONL lines and writes orders and events in batches. PostgreSQL constraints handle duplicate records. The application reports the number of snapshots processed and rows added.

The database form accepts username, password, host, port, and database name. Enable **SSL/TLS** when required by the server. The default port is `5432`; the default host is `localhost`.

## Configuration and credentials

User configuration is stored outside the source tree:

```text
%APPDATA%\LTN_Analitics_gateway\config.conf
```

It contains the source path, database connection settings, and import statistics. The database password is stored in this local configuration file so the application can reuse it. Protect the Windows user account and do not share or commit this file. To reconfigure the app, edit settings in the dashboard; remove `config.conf` to start the setup wizard again.

The configuration file is written under the Windows roaming AppData directory. If the `APPDATA` environment variable is unavailable, the application falls back to `%USERPROFILE%\AppData\Roaming\LTN_Analitics_gateway`.

## Troubleshooting

- **JSONL not found:** confirm the selected source path exists and that the Factorio mod has written at least one packet.
- **Database connection fails:** verify PostgreSQL host, port, database, user permissions, and network/firewall access. Enable SSL/TLS if the server requires it.
- **Invalid JSONL:** the error reports the line that could not be parsed. Check that the file is produced by a compatible version of the mod.
- **Configuration cannot be read:** close the application and inspect or remove `config.conf`; the setup wizard will recreate it.

For issues specific to Factorio recording, see the mod's [documentation](https://github.com/bumbon4eg/LTN_Analitic_0.1.0/tree/main/docs).
