import requests
import json
import time
import os

API_URL = os.getenv("API_URL", "http://localhost:8002")

def create_job():
    print("Creating test job...")
    
    # 1. Get a project and shot (assuming they exist, or use placeholders)
    # For a real test, we might need to create them first, but let's try with likely IDs if the user has data
    # Or better, create a temporary project/shot.
    
    # Let's list projects first
    try:
        projects = requests.get(f"{API_URL}/projects").json()
        if not projects:
            print("No projects found. Creating 'test_project'...")
            requests.post(f"{API_URL}/projects", json={"id": "test_project", "description": "Test"})
            project_id = "test_project"
        else:
            project_id = projects[0]
            
        print(f"Using project: {project_id}")
        
        # Create a dummy shot if needed, or just use a random ID (backend might check existence though)
        # The Current implementation checks if shot exists.
        # So we MUST create a shot.
        
        # Create a dummy shot if needed
        shot_id = "SHT-TEST-001"
        
        # Check if shot exists first
        # But for test simplicity, just try to create. 
        # POST /shots/ expects Shot model in body.
        
        shot_data = {
            "id": shot_id,
            "scene_description": "A cyberpunk city street at night, neon lights, rain.",
            "duration_seconds": 2.0,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        # POST /shots/ (add_shot) requires project_id in query or context?
        # Router says: async def create_shot(shot: Shot, manager: DataManager = Depends(get_data_manager)):
        # Manager needs to know current project. 
        # API doesn't seem to allow setting project via URL for this endpoint?
        # Wait, get_data_manager might need a cookie or something?
        # Actually, DataManager is singleton-ish? 
        # Let's check if we can set current project via API.
        
        # For this test, let's assume 'test_project' is loaded because we listed it?
        # Actually, list_jobs uses project_id param.
        # But shots router depends on 'manager.current_project_id'.
        # We need to set the project first.
        
        requests.post(f"{API_URL}/projects/{project_id}/load")
        
        print(f"Creating shot {shot_id}...")
        res = requests.post(f"{API_URL}/shots/", json=shot_data)
        if res.status_code != 200:
             print(f"Shot creation warning: {res.text}")
        
        # 2. Create Job
        payload = {
            "project_id": project_id,
            "shot_id": shot_id,
            "workflow_type": "text_to_image",
            "params": {
                "prompt": "Cyberpunk city, neon rain",
                "seed": 12345
            }
        }
        
        response = requests.post(f"{API_URL}/jobs/", json=payload)
        
        if response.status_code == 200:
            job = response.json()
            print(f"Job created successfully: {job['id']}")
            print(f"Initial Status: {job['status']}")
            return job['id']
        else:
            print(f"Failed to create job: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def check_status(job_id):
    if not job_id: return
    
    print(f"Checking status for job {job_id}...")
    for _ in range(5):
        time.sleep(2)
        response = requests.get(f"{API_URL}/jobs/{job_id}")
        if response.status_code == 200:
            job = response.json()
            print(f"Status: {job['status']} | Worker: {job.get('assigned_worker_id')}")
            if job['status'] in ['completed', 'failed']:
                break
        else:
            print("Failed to get job status")

if __name__ == "__main__":
    job_id = create_job()
    check_status(job_id)
