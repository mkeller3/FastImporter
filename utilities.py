import random
import os
import string
import uuid
import datetime
import subprocess
import json
import aiohttp

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

async def get_arcgis_data(url: str, new_table_id: str, process_id: str, database: str,token: str=None):
    """
    Method get arcgis data
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
    
def load_geographic_data_to_server(table_id: str, file_path: str, database: object):

    db = config.DATABASES[database]
    host = db['host']
    username = db['username']
    password = db['password']
    database = db['database']
    subprocess.call(f'ogr2ogr -f "PostgreSQL" "PG:host={host} user={username} dbname={database} password={password}" "{file_path}" -lco GEOMETRY_NAME=geom -lco FID=gid -lco PRECISION=no -nln {table_id} -overwrite', shell=True)
