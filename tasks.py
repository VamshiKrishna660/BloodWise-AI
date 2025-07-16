import logging
from datetime import datetime
import traceback
from pymongo import MongoClient


# Configure logging for tasks
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#monogoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["blood_analysis"]
jobs = db["jobs"]


def process_blood_report(query: str, file_path: str, file_hash: str):

    try:
        # Import here to avoid circular imports and ensure all modules are available
        from crewai import Crew, Process
        from agents import doctor, nutritionist, exercise_specialist
        from task import help_patients, nutrition_analysis, exercise_planning

        logger.info(f"🔄 Starting analysis for job {file_hash}")
        logger.info(f"📋 Query: {query}")
        logger.info(f"📁 File path: {file_path}")

        
        # MONGODB
        jobs.update_one(
            {"job_id": file_hash},
            {"$set": {
                "status": "processing",
                "message": "Analysis in progress...",
                "processing_started": datetime.now().isoformat(),
                "current_stage": "initializing"
            }},
            upsert=True
        )

        # Create the crew and run analysis
        logger.info(f"🤖 Creating crew for job {file_hash}")
        
    
        # mongoDB
        jobs.update_one(
            {"job_id": file_hash},
            {"$set": {
                "message": "Creating analysis crew...",
                "current_stage": "crew_creation"
            }}
        )
        
        crew = Crew(
            agents=[doctor, nutritionist, exercise_specialist],
            tasks=[help_patients, nutrition_analysis, exercise_planning],
            process=Process.sequential,
        )

        jobs.update_one(
            {"job_id": file_hash},
            {"$set": {
                "status": "processing",
                "message": "Running analysis...",
                "current_stage": "analysis_running"
            }}
        )
        logger.info(f"🚀 Starting crew analysis for job {file_hash}")
        result = crew.kickoff(inputs={"query": query, "file_path": file_path})
        result_str = str(result)

        logger.info(f"✅ Analysis completed for job {file_hash}")
        logger.info(f"📊 Result length: {len(result_str)} characters")

        

        # MONGODB
        jobs.update_one(
            {"job_id": file_hash},
            {"$set": {
                "status": "finished",
                "result": result_str,
                "message": "Analysis complete.",
                "completed_at": datetime.now().isoformat(),
                "current_stage": "completed"
            }}
        )

        logger.info(f"💾 Results saved to MongoDB for job {file_hash}")
        return result_str

    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        logger.error(f"❌ Error processing job {file_hash}: {error_msg}")
        logger.error(f"📋 Full traceback:\n{error_trace}")

        
        # MONGODB
        jobs.update_one(
            {"job_id": file_hash},
            {"$set": {
                "status": "failed",
                "result": "",
                "message": f"Error: {error_msg}",
                "error_details": error_trace,
                "failed_at": datetime.now().isoformat(),
                "current_stage": "failed"
            }},
            upsert=True
        )

        raise e


def simulate_test_job():
    """
    Simulate a test job similar to test_complete_queue.py
    Useful for debugging the task processing pipeline
    """
    import time
    
    test_hash = f"debug_test_{int(time.time())}"
    test_query = "Analyze my blood test report"
    test_file_path = "data/sample.pdf"
    
    logger.info(f"🧪 Simulating test job with hash: {test_hash}")
    
    try:
        result = process_blood_report(test_query, test_file_path, test_hash)
        logger.info(f"✅ Test job completed successfully")
        return result
    except Exception as e:
        logger.error(f"❌ Test job failed: {e}")
        raise e

# Main execution for testing (similar to test_complete_queue.py structure)
if __name__ == "__main__":
    logger.info("🧪 Testing tasks module directly...")
    
   
    #monfoDB
    try:
        result = simulate_test_job()
        logger.info("🎉 Direct task test completed successfully!")
        logger.info(f"📋 Result preview: {result[:200]}..." if len(result) > 200 else f"📋 Result: {result}")
    except Exception as e:
        logger.error(f"⚠️ Direct task test failed: {e}")