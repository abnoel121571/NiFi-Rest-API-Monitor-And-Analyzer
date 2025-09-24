import psutil
from datetime import datetime

def get_system_metrics():
    """Collects key OS-level metrics."""
    io_counters = psutil.disk_io_counters()
    
    system_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_cores_logical": psutil.cpu_count(logical=True),
        "cpu_cores_physical": psutil.cpu_count(logical=False),
        "memory_total_mb": round(psutil.virtual_memory().total / (1024 ** 2), 2),
        "memory_used_mb": round(psutil.virtual_memory().used / (1024 ** 2), 2),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_total_gb": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
        "disk_used_gb": round(psutil.disk_usage('/').used / (1024 ** 3), 2),
        "disk_percent": psutil.disk_usage('/').percent,
        "disk_io_read_count": io_counters.read_count if io_counters else None,
        "disk_io_write_count": io_counters.write_count if io_counters else None,
        "disk_io_read_bytes": io_counters.read_bytes if io_counters else None,
        "disk_io_write_bytes": io_counters.write_bytes if io_counters else None
    }
    
    return [system_data]
