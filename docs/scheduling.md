# Scheduling

This project is a batch tool. It is intended to generate an HTML digest at
08:00 and 18:00, not to run as a real-time news service or Web application.

The example launchd configuration is:

```text
scripts/com.local.ai-newspaper.plist.example
```

It runs:

```bash
uv run ai-newspaper run
```

## Replace Placeholders

Copy the example plist and replace these values with absolute paths for the
target Mac:

```text
/ABSOLUTE/PATH/TO/uv
/ABSOLUTE/PATH/TO/ai-newspaper
/ABSOLUTE/PATH/TO/LOG_DIR
```

Useful commands for finding local paths:

```bash
command -v uv
pwd
mkdir -p "$HOME/Library/Logs/ai-newspaper"
```

For example, the working directory should be the repository root, and the log
directory can be a user-owned directory such as:

```text
/Users/YOUR_USER/Library/Logs/ai-newspaper
```

## Install Manually

Do not register the `.plist.example` file directly. Copy it to the user
LaunchAgents directory after replacing all placeholders:

```bash
mkdir -p "$HOME/Library/LaunchAgents"
cp scripts/com.local.ai-newspaper.plist.example \
  "$HOME/Library/LaunchAgents/com.local.ai-newspaper.plist"
```

Validate the copied plist:

```bash
plutil -lint "$HOME/Library/LaunchAgents/com.local.ai-newspaper.plist"
```

Register it with launchd:

```bash
launchctl bootstrap "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.local.ai-newspaper.plist"
```

## Check Status

Check whether launchd knows about the job:

```bash
launchctl print "gui/$(id -u)/com.local.ai-newspaper"
```

Run one manual launchd-triggered execution:

```bash
launchctl kickstart -k "gui/$(id -u)/com.local.ai-newspaper"
```

Check logs:

```bash
tail -n 100 "$HOME/Library/Logs/ai-newspaper/ai-newspaper.out.log"
tail -n 100 "$HOME/Library/Logs/ai-newspaper/ai-newspaper.err.log"
```

## Stop Or Unregister

Unload the job:

```bash
launchctl bootout "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.local.ai-newspaper.plist"
```

Remove the installed plist if it is no longer needed:

```bash
rm "$HOME/Library/LaunchAgents/com.local.ai-newspaper.plist"
```

The project example file under `scripts/` is only a template. Editing or
removing the installed copy under `~/Library/LaunchAgents/` controls the actual
launchd registration.
