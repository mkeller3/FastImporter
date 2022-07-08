from fastapi import APIRouter, BackgroundTasks, Request

router = APIRouter()

import_processes = {}

@router.get("/status/{process_id}", tags=["import"])
def status(process_id: str):
    if process_id not in import_processes:
        return {"status": "UNKNOWN", "error": "This process_id does not exist."}
    return import_processes[process_id]