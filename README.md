### [Getting started](#getting-started)

#### [Server](#server)
Create a virtual environment and install the required python packages:
```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r ./test_requirements.txt
```

Ensure MongoDB is running and run the Python server:
```
PROFILE=local python -m account_linking_app
```
Before commit:
```
flake8 ./server
python -m pytest server/test
```

To run all tests in a submodule:
```
python -m pytest --cov=server --cov-report html:htmlcov server/test
```

#### [Testing with curl](#testing)
To mimic attribute aggregation
```
curl -G --user admin:secret 'http://localhost:8083/attribute_aggregation' --data-urlencode "eduperson_principal_name=j.doe@example.com" --data-urlencode "sp_entity_id=https://nope" | jq
```