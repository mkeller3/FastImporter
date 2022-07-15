# FastImporter

FastImporter is a [PostGIS](https://github.com/postgis/postgis) geospatial api to enable loading data into a PostGIS database from a multitude of locations such as files, and url endpoints. FastImporter is written in [Python](https://www.python.org/) using the [FastAPI](https://fastapi.tiangolo.com/) web framework. 

---

**Source Code**: <a href="https://github.com/mkeller3/FastImporter" target="_blank">https://github.com/mkeller3/FastImporter</a>

---

## Requirements

FastImporter requires PostGIS >= 2.4.0 and ogr2ogr.

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
| `POST` | `/api/v1/import/arcgis_service` | [ArcGIS Service](#ArcGIS-Service)  |
| `POST` | `/api/v1/import/geographic_data_from_geographic_file` | [Geographic Data From Geographic File](#Geographic-Data-From-Geographic-File)  |
| `POST` | `/api/v1/import/geographic_data_from_csv` | [Geographic Data From CSV](#Geographic-Data-From-CSV)  |
| `POST` | `/api/v1/import/point_data_from_csv` | [Point Data From CSV](#Point-Data-From-CSV)  |
| `POST` | `/api/v1/import/geographic_data_from_json_file` | [Geographic Data From Json File](#Geographic-Data-From-Json-File)  |
| `POST` | `/api/v1/import/point_data_from_json_file` | [Point Data From Json File ](#Point-Data-From-Json-File)  |
| `POST` | `/api/v1/import/geographic_data_from_json_url` | [Geographic Data From Json URL](#Geographic-Data-From-Json-Url)  |
| `POST` | `/api/v1/import/point_data_from_json_url` | [Point Data From Json URL](#Point-Data-From-Json-Url)  |
| `POST` | `/api/v1/import/geographic_data_from_json_string` | [Geographic Data From Json String](#Geographic-Data-From-Json-String)  |
| `POST` | `/api/v1/import/point_data_from_json_string` | [Point Data From Json String](#Point-Data-From-Json-String)  |
| `POST` | `/api/v1/import/geojson_from_json` | [Geojson From URL](#Geojson-From-Url)  |


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

## ArcGIS Service

### Description
Import data from any `FeatureServer` or `MapServer` that allows for geojson as an output.

Example: Download a point dataset of Tennesse State Parks.

### Example Input
```json
{
    "url": "https://services5.arcgis.com/bPacKTm9cauMXVfn/ArcGIS/rest/services/TN_State_Parks_Points/FeatureServer/0",
    "database": "data"
}
```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```

## Geographic Data From Geographic File

### Description
Import geographic data from a file/files.

Example: Import geojson from file

### Example Input
```json
{
    "database": "data",
    "files": "FILES IN MULTI PART FORM"
}
```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```

## Geographic Data From CSV

### Description
Import a csv file and join to a map already within the database based off a column.

Example: Uploading a csv with two columns `state_abbr` and `Number of Rest Stops`
and joining to the `states` map based off of the `state_abbr` column.

### Example Input
```json
{
  "database": "data",
  "map": "states",
  "map_column": "state_abbr",
  "map_columns": ["state_abbr"],
  "table_column": "state_abbr",
  "table_columns": ["state_abbr","Number of Rest Stops"],
  "files": "FILES IN MULTI PART FORM"
}
```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```

## Point Data From CSV

### Description
Import a csv file with latitude and longitude columns into database.

Example: A csv file with latitude and longitude columns for US Capitals.

### Example Input
```json
{
  "database": "data",
  "longitude": "longitude",
  "latitude": "latitude",
  "table_columns": ["name","description","latitude","longitude"],
  "files": "FILES IN MULTI PART FORM"
}
```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```

## Geographic Data From Json File

### Description


Example: 

### Example Input
```json

```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```

## Point Data From Json File

### Description


Example: 

### Example Input
```json

```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```

## Geographic Data From Json URL

### Description


Example: 

### Example Input
```json

```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```

## Point Data From Json URL

### Description


Example: 

### Example Input
```json

```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```

## Geographic Data From Json String

### Description


Example: 

### Example Input
```json

```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```

## Point Data From Json String

### Description


Example: 

### Example Input
```json

```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```

## Geojson From URL

### Description


Example: 

### Example Input
```json

```

### Example Output
```json
{
  "process_id": "c8d7b8d8-3e82-4f93-b441-55a5f51c4171",
  "url": "http://127.0.0.1:8000/api/v1/import/status/c8d7b8d8-3e82-4f93-b441-55a5f51c4171"
}
```