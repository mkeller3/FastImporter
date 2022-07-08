# FastImporter

FastImporter is a [PostGIS](https://github.com/postgis/postgis) geospatial api to enable loading data into a PostGIS database from a multitude of locations such as files, and url endpoints. FastImporter is written in [Python](https://www.python.org/) using the [FastAPI](https://fastapi.tiangolo.com/) web framework. 

---

**Source Code**: <a href="https://github.com/mkeller3/FastImporter" target="_blank">https://github.com/mkeller3/FastImporter</a>

---

## Requirements

FastImporter requires PostGIS >= 2.4.0.

## Configuration

In order for the api to work you will need to edit the `config.py` file with your database connections.

Example
```python
DATABASES = {
    "data": {
        "host": "localhost",
        "database": "data",
        "username": "postgres",
        "password": "postgres",
        "port": 5432,
    }
}
```

## Usage

### Running Locally

To run the app locally `uvicorn main:app --reload`

### Production
Build Dockerfile into a docker image to deploy to the cloud.

## API

| Method | URL | Description |
| ------ | --- | ----------- |
| `GET` | `/api/v1/import/status/{process_id}` | [Import Status](#Import-Status)  |


## Endpoint Description's

## Import Status
Any time an import is submitted it given a process_id to have the import run in the background using [FastAPI's Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/). To check the
status of an import, you can call this endpoint with the process_id.

## Example Call
```shell
/api/v1/import/status/472e29dc-91a8-41d3-b05f-cee34006e3f7
```

## Example Output - Still Running
```json
{
    "status": "PENDING"
}
```

## Example Output - Complete
```json
{
    "status": "SUCCESS",
    "new_table_id": "shnxppipxrppsdkozuroilkubktfodibtqorhucjvxlcdrqyhh",
    "completion_time": "2022-07-06T19:33:17.950059",
    "run_time_in_seconds": 1.78599
}
```

## Example Output - Error
```json
{
    "status": "FAILURE",
    "error": "ERROR HERE",
    "completion_time": "2022-07-08T13:39:47.961389",
    "run_time_in_seconds": 0.040892
}
```

