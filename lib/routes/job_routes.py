"""
Job management routes for the Quantum Computing API
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from api_models import JobResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, job_storage: dict):
    """Get job status and results"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_storage[job_id]
    return JobResponse(**job_data)

@router.get("/")
async def list_jobs(job_storage: dict):
    """List all jobs with their status"""
    jobs_list = []
    for job_id, job_data in job_storage.items():
        jobs_list.append({
            "job_id": job_id,
            "status": job_data["status"],
            "created_at": job_data["created_at"],
            "has_result": job_data["result"] is not None
        })
    
    return {
        "jobs": jobs_list,
        "total": len(job_storage),
        "running": len([j for j in job_storage.values() if j["status"] == "running"]),
        "completed": len([j for j in job_storage.values() if j["status"] == "completed"]),
        "failed": len([j for j in job_storage.values() if j["status"] == "failed"])
    }

@router.delete("/{job_id}")
async def delete_job(job_id: str, job_storage: dict, active_simulators: dict):
    """Delete a job and clean up resources"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Clean up simulator if exists
    if job_id in active_simulators:
        del active_simulators[job_id]
    
    del job_storage[job_id]
    return {"message": f"Job {job_id} deleted successfully"}

@router.post("/cleanup")
async def cleanup_jobs(job_storage: dict, active_simulators: dict):
    """Clean up completed jobs older than 1 hour"""
    current_time = datetime.now()
    cleaned_count = 0
    
    jobs_to_remove = []
    for job_id, job_data in job_storage.items():
        if job_data["status"] in ["completed", "failed"]:
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        if job_id in active_simulators:
            del active_simulators[job_id]
        del job_storage[job_id]
        cleaned_count += 1
    
    return {
        "message": f"Cleaned up {cleaned_count} old jobs",
        "remaining_jobs": len(job_storage)
    }