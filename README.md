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


