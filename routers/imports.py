import os
from typing import List
from fastapi import APIRouter, BackgroundTasks, Request, Form
from fastapi import File, UploadFile

import utilities
import models

router = APIRouter()

import_processes = {}

@router.get("/status/{process_id}", tags=["import"])
def status(process_id: str):
    if process_id not in import_processes:
        return {"status": "UNKNOWN", "error": "This process_id does not exist."}
    return import_processes[process_id]

@router.post("/arcgis_service/", tags=["import"], response_model=models.BaseResponseModel)
async def import_arcgis_service(info: models.ArcgisModel, request: Request, background_tasks: BackgroundTasks):
    new_table_id = utilities.get_new_table_id()

    process_id = utilities.get_new_process_id()

    process_url = str(request.base_url)

    process_url += f"api/v1/import/status/{process_id}"

    import_processes[process_id] = {
        "status": "PENDING"
    }

    background_tasks.add_task(
        utilities.get_arcgis_data,
        url=info.url,
        token=info.token,
        new_table_id=new_table_id,
        database=info.database,
        process_id=process_id
    )

    return {
        "process_id": process_id,
        "url": process_url
    }

@router.post("/geographic_data_from_geographic_file/", tags=["import"], response_model=models.BaseResponseModel)
async def import_geographic_data_from_geographic_file(
        request: Request,
        background_tasks: BackgroundTasks,
        database: str = Form(...),
        files: List[UploadFile] = File(...)
    ):
    new_table_id = utilities.get_new_table_id()

    process_id = utilities.get_new_process_id()

    process_url = str(request.base_url)

    process_url += f"api/v1/import/status/{process_id}"

    file_path = ""

    for file in files:
        try:
            file_path = f"{os.getcwd()}/media/{new_table_id}_{file.filename}"
            with open(file_path, 'wb') as f:
                [f.write(chunk) for chunk in iter(lambda: file.file.read(1000), b'')]
        except Exception:
            media_directory = os.listdir(f"{os.getcwd()}/media/")
            for file in media_directory:
                if new_table_id in file:
                    os.remove(f"{os.getcwd()}/media/{file}")  

            return {"message": "There was an error uploading the file(s)"}
        finally:
            await file.close()

    import_processes[process_id] = {
        "status": "PENDING"
    }

    background_tasks.add_task(
        utilities.upload_geographic_file,
        file_path=file_path,
        new_table_id=new_table_id,
        database=database,
        process_id=process_id
    )

    return {
        "process_id": process_id,
        "url": process_url
    }