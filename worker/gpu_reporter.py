import GPUtil
import platform
import psutil
import logging

# 로깅 설정
logger = logging.getLogger("worker.gpu_reporter")

def get_system_info():
    info = {
        "hostname": platform.node(),
        "os": platform.system(),
        "cpu_usage": psutil.cpu_percent(),
        "ram_usage": psutil.virtual_memory().percent,
        "gpus": [],
        "gpu_detection_error": None  # GPU 감지 에러 메시지
    }
    
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            logger.warning("No GPUs detected by GPUtil")
            info["gpu_detection_error"] = "No GPUs detected"
        else:
            for gpu in gpus:
                info["gpus"].append({
                    "id": gpu.id,
                    "name": gpu.name,
                    "load": gpu.load * 100,
                    "memory_total": gpu.memoryTotal,
                    "memory_used": gpu.memoryUsed,
                    "memory_free": gpu.memoryFree,
                    "temperature": gpu.temperature,
                    "is_simulated": False
                })
    except Exception as e:
        error_msg = f"Failed to get GPU info: {e}"
        logger.error(error_msg)
        info["gpu_detection_error"] = str(e)
        
        # 개발/테스트 환경용 시뮬레이션 데이터 (명시적으로 표시)
        info["gpus"].append({
            "id": 0,
            "name": "Simulated GPU (Development Mode)",
            "load": 0,
            "memory_total": 24576,
            "memory_used": 1024,
            "memory_free": 23552,
            "temperature": 45,
            "is_simulated": True  # Master가 구분할 수 있도록 플래그
        })
        
    return info

