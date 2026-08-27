# SACCT_API
An API to get certain metrics from Sacct based on the user

## Install

```
git clone <this url>
cd SACCT_API
```

## Run

### Virtual machine

```
python -m venv venv
source venv/bin/activate
```

### Certificate

You need to generate this yourself

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

## Call

```
curl -k https://127.0.0.1:5000/user/<user>
```



