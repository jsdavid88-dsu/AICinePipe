import GPUtil
import platform
import psutil

def get_system_info():
    info = {
        "hostname": platform.node(),
        "os": platform.system(),
        "cpu_usage": psutil.cpu_percent(),
        "ram_usage": psutil.virtual_memory().percent,
        "gpus": []
    }
    
    try:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            info["gpus"].append({
                "id": gpu.id,
                "name": gpu.name,
                "load": gpu.load * 100,
                "memory_total": gpu.memoryTotal,
                "memory_used": gpu.memoryUsed,
                "memory_free": gpu.memoryFree,
                "temperature": gpu.temperature
            })
    except Exception as e:
        print(f"Failed to get GPU info: {e}")
        # Dummy data for dev/test without GPU
        info["gpus"].append({
            "id": 0,
            "name": "Simulated GPU (RTX 4090)",
            "load": 0,
            "memory_total": 24576,
            "memory_used": 1024,
            "memory_free": 23552,
            "temperature": 45
        })
        
    return info
