from crewai import Crew, Process
from agents import doctor, nutritionist, exercise_specialist
from task import help_patients, nutrition_analysis, exercise_planning
from tasks import process_blood_report 
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from pymongo import MongoClient
import hashlib
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify domains: ["http://localhost:3000"]
    allow_methods=["*"],
)


client = MongoClient("mongodb://localhost:27017/")
db = client["blood_analysis"]
jobs = db["jobs"]

# Utility to compute SHA-256 hash of uploaded file


def compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

# Endpoint to handle PDF upload and analysis


@app.post("/upload")
async def analyze_blood_report(
    file: UploadFile = File(...),
    query: str = Form(default="Summarise my Blood Test Report")
):
    # Only allow PDF files
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Only PDF files are supported.")

    # Read file contents and compute hash
    content = await file.read()
    file_hash = compute_file_hash(content)
    existing_job = jobs.find_one({"job_id": file_hash})


    if existing_job:
        status = existing_job.get("status")
        if status == "finished":
            return JSONResponse(content={
                "status": "success",
                "message": "Result found in database.",
                "result": existing_job.get("result", "hehe"),
                "job_id": file_hash
            })
        elif status == "processing":
            return JSONResponse(content={
                "status": "processing",
                "message": "Job is still processing.",
                "job_id": file_hash
            })
        elif status == "failed":
            return JSONResponse(content={
                "status": "failed",
                "message": existing_job.get("message", "Job failed."),
                "job_id": file_hash
            })

    # Save the uploaded file to disk
    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", f"{file_hash}.pdf")
    with open(file_path, "wb") as f:
        f.write(content)

    
    jobs.update_one(
        {"job_id": file_hash},
        {"$set": {
            "status": "processing",
            "message": "Job is being processed.",
            "started_at": datetime.now().isoformat(),
            "file_name": file.filename
        }},
        upsert=True
    )

    try:
        result = process_blood_report(query.strip(), file_path, file_hash)
        return JSONResponse(content={
            "status": "success",
            "message": "Analysis completed.",
            "result": result,
            "job_id": file_hash
        })
    except Exception as e:
        return JSONResponse(content={
            "status": "failed",
            "message": str(e),
            "job_id": file_hash
        }, status_code=500)

# Endpoint to check job status

def serialize_mongo_doc(doc):
    doc["_id"] = str(doc["_id"])  # convert ObjectId to string
    return doc
@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job = jobs.find_one({"job_id": job_id})
    if not job:
        return JSONResponse(content={
            "status": "not_found",
            "message": "Job not found."
        })
    
    return JSONResponse(content=serialize_mongo_doc(job))

@app.get("/jobs/stats")
async def get_mongo_job_stats():

    try:
        total = jobs.count_documents({})
        processing = jobs.count_documents({"status": "processing"})
        finished = jobs.count_documents({"status": "finished"})
        failed = jobs.count_documents({"status": "failed"})
        logger.info(f"📊 Job stats - Total: {total}, Processing: {processing}, Finished: {finished}, Failed: {failed}")
        return JSONResponse(content={
            "total_jobs": total,
            "processing_jobs": processing,
            "finished_jobs": finished,
            "failed_jobs": failed,
            "status": "healthy"
        })
    except Exception as e:
        logger.error(f"Error getting job stats: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": str(e)
        }, status_code=500)

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        client.admin.command('ping')
        
        return JSONResponse(content={
            "status": "healthy",
            "mongo": "connected",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(content={
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

# Root endpoint
@app.get("/")
async def root():
    return JSONResponse(content={
        "message": "Blood Test Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload - POST - Upload PDF for analysis",
            "status": "/status/{job_id} - GET - Check job status",
            "health": "/health - GET - Health check",
            "jobs_stats": "/jobs/stats - GET - Job statistics (MongoDB)",
            "test": "/test - POST - Test with sample data"
        }
    })

# Test endpoint compatible with the test_complete_queue.py
@app.post("/test")
async def test_analysis():
    """Test endpoint that uses the same workflow as test_complete_queue.py"""
    try:
        import time
        
        # Create test parameters similar to test_complete_queue.py
        test_query = "Analyze my blood test report"
        test_file_path = "data/sample.pdf"
        test_hash = f"api_test_{int(time.time())}"
        
        logger.info(f"🧪 Starting API test with hash: {test_hash}")
        
        # Ensure test file exists (same logic as test_complete_queue.py)
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(test_file_path):
            with open(test_file_path, "wb") as f:
                f.write(b"%PDF-1.4\n%Dummy PDF for testing\n")


        jobs.update_one(
            {"job_id": test_hash},
            {"$set": {
                "status": "processing",
                "message": "Test job is being processed.",
                "started_at": datetime.now().isoformat(),
                "test_mode": True
            }},
            upsert=True
        )
        result = process_blood_report(test_query, test_file_path, test_hash)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Test job completed successfully.",
            "job_id": test_hash,
             "result": result,
            "test_parameters": {
                "query": test_query,
                "file_path": test_file_path,
                "hash": test_hash
            }
        })
        
    except Exception as e:
        logger.error(f"Test endpoint failed: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": f"Test failed: {str(e)}"
        }, status_code=500)

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Blood Test Analyzer API")
    logger.info("📋 Available endpoints:")
    logger.info("   POST /upload - Upload blood test PDF")
    logger.info("   GET /status/{job_id} - Check analysis status")
    logger.info("   GET /health - Health check")
    logger.info("   GET /jobs/stats - Job statistics (MongoDB)")
    logger.info("   GET / - API information")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)