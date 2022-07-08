from fastapi import APIRouter, BackgroundTasks, Request

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