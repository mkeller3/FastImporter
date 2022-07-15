import random
import os
import re
import string
import uuid
import datetime
import subprocess
import json
import aiohttp
import pandas as pd
from fastapi import FastAPI

import config
from routers import imports

def get_new_table_id() -> str:
    """
    Method to return a new table id
    """
    letters = string.ascii_lowercase

    return ''.join(random.choice(letters) for i in range(50))

def get_new_process_id() -> str:
    """
    Method to return a new process id
    """

    return str(uuid.uuid4())

def remove_bad_characters(string: str) -> str:
    regex = re.compile('[^a-zA-Z0-9_]')
    return regex.sub('_', string).lower()

async def upload_csv_to_db_with_latitude_and_longitude(file_path: str, new_table_id: str, database: str,
    latitude: str, longitude: str, table_columns: list, app: FastAPI):
    """
    Method to upload data from from a csv file with geographic data into db.

    """

    pd.options.display.max_rows = 10

    df = pd.read_csv(file_path)

    columns = ""

    formatted_table_columns = ""

    for col in table_columns:
        formatted_table_columns += f"{remove_bad_characters(col)},"

    formatted_table_columns = formatted_table_columns[:-1]

    create_table_sql = f"CREATE TABLE {new_table_id} ("

    for name, dtype in df.dtypes.iteritems():
        columns += f"{remove_bad_characters(name)},"
        create_table_sql += f'"{remove_bad_characters(name)}"'
        if dtype == "object" or dtype == "datetime64":
            create_table_sql += " text,"
        if dtype == "int64":
            create_table_sql += " integer,"            
        if dtype == "float64":
            create_table_sql += " double precision,"

    create_table_sql = create_table_sql[:-1]

    columns = columns[:-1]
    
    create_table_sql += ");"

    pool = app.state.databases[f'{database}_pool']

    async with pool.acquire() as con:
        await con.fetch(f"""DROP TABLE IF EXISTS "{new_table_id}";""")

        await con.fetch(create_table_sql)

        insert_sql = f"""COPY {new_table_id}({columns})
        FROM '{file_path}'
        DELIMITER ','
        CSV HEADER;"""

        await con.fetch(insert_sql)

        add_geom_sql = f"""
            SELECT AddGeometryColumn ('public','{new_table_id}','geom',4326,'POINT',2);                
        """

        await con.fetch(add_geom_sql)

        update_geom_sql = f"""
            UPDATE "{new_table_id}" 
            SET geom = ST_SetSRID(ST_MakePoint({longitude},{latitude}), 4326);
        """

        await con.fetch(update_geom_sql)

async def get_arcgis_data(url: str, new_table_id: str, process_id: str, database: str, token: str=None):
    """
    Method get arcgis data from a given url and load it into a database.
    """

    start = datetime.datetime.now()

    try:
        service_url = f"{url}?f=json"

        if token is not None:
            service_url += f"&token={token}"
        
        async with aiohttp.ClientSession() as session:

            async with session.get(service_url) as resp:

                data = await resp.json()

                max_number_of_features_per_query = data['maxRecordCount']

                feature_stats_url = f"{url}/query?where=1%3D1&returnGeometry=false&returnIdsOnly=true&f=json&resultRecordCount=10"

                async with session.get(feature_stats_url) as feature_resp:

                    data = await feature_resp.text()

                    data = json.loads(data)

                    object_ids = data['objectIds']

                    number_of_features = len(data['objectIds'])

                    if number_of_features <= max_number_of_features_per_query:

                        async with session.get(f"{url}/query?where=1=1&outFields=*&returnGeometry=true&geometryPrecision=6&outSR=4326&f=geojson") as resp:

                            data = await resp.json()  
                            
                            with open(f'{new_table_id}.geojson', 'w') as json_file:
                                json.dump(data, json_file)
                            
                            load_geographic_data_to_server(
                                table_id=new_table_id,
                                file_path=f'{new_table_id}.geojson',
                                database=database
                            )

                    else:
                        start_counter = 0
                        
                        feature_collection = {
                            "type": "FeatureCollection",           
                            "features": []
                        }

                        for x in range( start_counter, number_of_features, max_number_of_features_per_query ):
                            ids_requested = object_ids[x: x + max_number_of_features_per_query ]
                            payload = { 'f': 'geojson', 'where': '1=1', 
                                'objectIds': str( ids_requested )[1:-1], 'outSR': '4326',  
                                'returnGeometry': 'true', 'outFields': '*', 
                                'geometryPrecision': '4'}

                            async with session.post( f"{url}/query", data=payload ) as resp:

                                data = await resp.text()

                                data = json.loads(data)

                                if 'error' in data:
                                    print(data['error'])

                                feature_collection['features'] += data['features']

                        with open(f'{new_table_id}.geojson', 'w') as json_file:
                            json.dump(feature_collection, json_file)
                        
                        load_geographic_data_to_server(
                            table_id=new_table_id,
                            file_path=f'{new_table_id}.geojson',
                            database=database
                        )
                os.remove(f'{new_table_id}.geojson')
                imports.import_processes[process_id]['status'] = "SUCCESS"
                imports.import_processes[process_id]['new_table_id'] = new_table_id
                imports.import_processes[process_id]['completion_time'] = datetime.datetime.now()
                imports.import_processes[process_id]['run_time_in_seconds'] = datetime.datetime.now()-start
    except Exception as error:
        if os.path.exists(f'{new_table_id}.geojson'):
            os.remove(f'{new_table_id}.geojson')
        imports.import_processes[process_id]['status'] = "FAILURE"
        imports.import_processes[process_id]['error'] = str(error)
        imports.import_processes[process_id]['completion_time'] = datetime.datetime.now()
        imports.import_processes[process_id]['run_time_in_seconds'] = datetime.datetime.now()-start

async def upload_geographic_file(file_path: str, new_table_id: str, process_id: str, database: str):
    """
    Method to upload data from geographic file.

    """

    start = datetime.datetime.now()

    try:
        load_geographic_data_to_server(
            table_id=new_table_id,
            file_path=file_path,
            database=database
        )
        media_directory = os.listdir(f"{os.getcwd()}/media/")
        for file in media_directory:
            if new_table_id in file:
                os.remove(f"{os.getcwd()}/media/{file}")  
        imports.import_processes[process_id]['status'] = "SUCCESS"
        imports.import_processes[process_id]['new_table_id'] = new_table_id
        imports.import_processes[process_id]['completion_time'] = datetime.datetime.now()
        imports.import_processes[process_id]['run_time_in_seconds'] = datetime.datetime.now()-start
    except Exception as error:
        media_directory = os.listdir(f"{os.getcwd()}/media/")
        for file in media_directory:
            if new_table_id in file:
                os.remove(f"{os.getcwd()}/media/{file}")  
        imports.import_processes[process_id]['status'] = "FAILURE"
        imports.import_processes[process_id]['error'] = str(error)
        imports.import_processes[process_id]['completion_time'] = datetime.datetime.now()
        imports.import_processes[process_id]['run_time_in_seconds'] = datetime.datetime.now()-start

async def import_geographic_data_from_csv(file_path: str, new_table_id: str, process_id: str, database: str,
    map: str, map_column: str, table_column: str, table_columns: list, map_columns: list, app: FastAPI):
    """
    Method to upload data from from a csv file with geographic data.

    """

    start = datetime.datetime.now()

    try:
        pd.options.display.max_rows = 10

        df = pd.read_csv(file_path)

        columns = ""

        formatted_table_columns = ""

        formatted_map_columns = ""

        for col in table_columns:
            if col not in map_columns:
                formatted_table_columns += f"a.{remove_bad_characters(col)},"
        
        for column in map_columns:
            formatted_map_columns += f"b.{remove_bad_characters(column)},"

        create_table_sql = f"CREATE TABLE {new_table_id}_temp ("

        for name, dtype in df.dtypes.iteritems():
            columns += f"{remove_bad_characters(name)},"
            create_table_sql += f'"{remove_bad_characters(name)}"'
            if dtype == "object" or dtype == "datetime64":
                create_table_sql += " text,"
            if dtype == "int64":
                create_table_sql += " integer,"            
            if dtype == "float64":
                create_table_sql += " double precision,"

        create_table_sql = create_table_sql[:-1]
        columns = columns[:-1]
        
        create_table_sql += ");"

        pool = app.state.databases[f'{database}_pool']

        async with pool.acquire() as con:
            await con.fetch(f"""DROP TABLE IF EXISTS "{new_table_id}_temp";""")

            await con.fetch(create_table_sql)

            insert_sql = f"""COPY {new_table_id}_temp({columns})
            FROM '{file_path}'
            DELIMITER ','
            CSV HEADER;"""

            await con.fetch(insert_sql)

            join_sql = f"""CREATE TABLE "{new_table_id}" AS
                SELECT {formatted_table_columns} {formatted_map_columns} geom
                FROM "{new_table_id}_temp" as a
                LEFT JOIN "{map}" as b
                ON a."{table_column}" = b."{map_column}";
            """

            await con.fetch(join_sql)

            media_directory = os.listdir(f"{os.getcwd()}/media/")
            for file in media_directory:
                if new_table_id in file:
                    os.remove(f"{os.getcwd()}/media/{file}")  
            imports.import_processes[process_id]['status'] = "SUCCESS"
            imports.import_processes[process_id]['new_table_id'] = new_table_id
            imports.import_processes[process_id]['completion_time'] = datetime.datetime.now()
            imports.import_processes[process_id]['run_time_in_seconds'] = datetime.datetime.now()-start
    except Exception as error:
        media_directory = os.listdir(f"{os.getcwd()}/media/")
        for file in media_directory:
            if new_table_id in file:
                os.remove(f"{os.getcwd()}/media/{file}")  
        imports.import_processes[process_id]['status'] = "FAILURE"
        imports.import_processes[process_id]['error'] = str(error)
        imports.import_processes[process_id]['completion_time'] = datetime.datetime.now()
        imports.import_processes[process_id]['run_time_in_seconds'] = datetime.datetime.now()-start

async def import_point_data_from_csv(file_path: str, new_table_id: str, process_id: str, database: str,
    latitude: str, longitude: str, table_columns: list, app: FastAPI):
    """
    Method to upload data from csv with lat lng columns.

    """

    start = datetime.datetime.now()

    try:
        await upload_csv_to_db_with_latitude_and_longitude(
            file_path=file_path,
            new_table_id=new_table_id,
            database=database,
            latitude=latitude,
            longitude=longitude,
            table_columns=table_columns,
            app=app
        )

        media_directory = os.listdir(f"{os.getcwd()}/media/")
        for file in media_directory:
            if new_table_id in file:
                os.remove(f"{os.getcwd()}/media/{file}")  

        imports.import_processes[process_id]['status'] = "SUCCESS"
        imports.import_processes[process_id]['new_table_id'] = new_table_id
        imports.import_processes[process_id]['completion_time'] = datetime.datetime.now()
        imports.import_processes[process_id]['run_time_in_seconds'] = datetime.datetime.now()-start
    except Exception as error:
        media_directory = os.listdir(f"{os.getcwd()}/media/")
        for file in media_directory:
            if new_table_id in file:
                os.remove(f"{os.getcwd()}/media/{file}")  
        imports.import_processes[process_id]['status'] = "FAILURE"
        imports.import_processes[process_id]['error'] = str(error)
        imports.import_processes[process_id]['completion_time'] = datetime.datetime.now()
        imports.import_processes[process_id]['run_time_in_seconds'] = datetime.datetime.now()-start

async def import_point_data_from_json_file(file_path: str, new_table_id: str, process_id: str, database: str,
    latitude: str, longitude: str, table_columns: list, app: FastAPI):
    """
    Method to upload data from csv with lat lng columns.

    """

    start = datetime.datetime.now()

    try:
        df = pd.read_json(file_path)
        
        df.to_csv(f"{os.getcwd()}/media/{new_table_id}.csv", index=False, sep=',', encoding="utf-8")

        await upload_csv_to_db_with_latitude_and_longitude(
            file_path=f"{os.getcwd()}/media/{new_table_id}.csv",
            new_table_id=new_table_id,
            database=database,
            latitude=latitude,
            longitude=longitude,
            table_columns=table_columns,
            app=app
        )

        media_directory = os.listdir(f"{os.getcwd()}/media/")
        for file in media_directory:
            if new_table_id in file:
                os.remove(f"{os.getcwd()}/media/{file}")  
        imports.import_processes[process_id]['status'] = "SUCCESS"
        imports.import_processes[process_id]['new_table_id'] = new_table_id
        imports.import_processes[process_id]['completion_time'] = datetime.datetime.now()
        imports.import_processes[process_id]['run_time_in_seconds'] = datetime.datetime.now()-start
    except Exception as error:
        media_directory = os.listdir(f"{os.getcwd()}/media/")
        for file in media_directory:
            if new_table_id in file:
                os.remove(f"{os.getcwd()}/media/{file}")  
        imports.import_processes[process_id]['status'] = "FAILURE"
        imports.import_processes[process_id]['error'] = str(error)
        imports.import_processes[process_id]['completion_time'] = datetime.datetime.now()
        imports.import_processes[process_id]['run_time_in_seconds'] = datetime.datetime.now()-start

def load_geographic_data_to_server(table_id: str, file_path: str, database: object):

    db = config.DATABASES[database]
    host = db['host']
    username = db['username']
    password = db['password']
    database = db['database']
    subprocess.call(f'ogr2ogr -f "PostgreSQL" "PG:host={host} user={username} dbname={database} password={password}" "{file_path}" -lco GEOMETRY_NAME=geom -lco FID=gid -lco PRECISION=no -nln {table_id} -overwrite', shell=True)
