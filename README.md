# SACCT_API
An API to get certain metrics from Sacct based on the user

## Install

```
git clone <this url>
cd SACCT_API
```

## Run the API

### Virtual machine

```
python -m venv venv
source venv/bin/activate
```

### Certificate

You can generate a certificate yourself, however it does run off adhoc if needed

```
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

### Activate flask

```
python3 API.py
```

#### Potential imports required

```
pip install flask
pip install pyopenssl
```

## Call API without CLI

### User only
```
curl -k https://127.0.0.1:5000/user/<user>
```

### User and time in days
```
curl -k https://127.0.0.1:5000/user/<user>/<days>
```

## Run the CLI
### Activate ruby
```
bundle install
bundle exec rake install
```

## Call the CLI
```
bundle exec bin/jobrep
```

### Commands

```
Commands:
  jobrep config [SUBCOMMAND]
  jobrep report                            # Report based on flags sent to the cli
  jobrep version                           # Print the version
```

#### Config main

```
Commands:
  jobrep config set            # Save API configuration settings
  jobrep config show           # Display current API configuration settings
```

#### Config set
```
Command:
  jobrep config set

Usage:
  jobrep config set

Description:
  Save API configuration settings

Options:
  --url=VALUE, -u VALUE             # API base URL
  --[no-]ssl                        # Verify SSL certificate
  --help, -h                        # Print this help
```

#### Report

```
Command:
  jobrep report

Usage:
  jobrep report

Description:
  Report based on flags sent to the cli

Options:
  --days=VALUE, -d VALUE, --date VALUE  # Go back n amount of days
  --[no-]timespread, -t, --times    # Show 7,30,90 days
  --user=VALUE, -u VALUE, --username VALUE  # Select user(leave blank for self)
  --json=VALUE, -j VALUE            # Save json if not none
  --help, -h                        # Print this help
```
