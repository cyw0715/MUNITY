"""服务器资源监控 — 后台采集 CPU/内存/磁盘数据"""
import os
import json
import time
import threading
import psutil
import logging

MONITOR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor_data.json")
INTERVAL = 60  # 采集间隔（秒）
MAX_ENTRIES = 1440  # 最多保留 24h 数据

logger = logging.getLogger("monitor")


class ServerMonitor:
    def __init__(self):
        self.history: list = []
        self.lock = threading.Lock()
        self.running = False
        self.thread: threading.Thread = None
        self._load_history()

    def _load_history(self):
        if os.path.exists(MONITOR_FILE):
            try:
                with open(MONITOR_FILE, "r") as f:
                    self.history = json.load(f)
                logger.info(f"加载了 {len(self.history)} 条历史监控数据")
            except Exception as e:
                logger.warning(f"加载监控历史失败: {e}")
                self.history = []

    def _save_history(self):
        try:
            with open(MONITOR_FILE, "w") as f:
                json.dump(self.history, f)
        except Exception as e:
            logger.warning(f"保存监控历史失败: {e}")

    def _collect(self) -> dict:
        try:
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return {
                "timestamp": time.time(),
                "cpu_percent": round(cpu, 1),
                "mem_percent": round(mem.percent, 1),
                "mem_used": mem.used,
                "mem_total": mem.total,
                "disk_percent": round(disk.percent, 1),
                "disk_used": disk.used,
                "disk_total": disk.total,
            }
        except Exception as e:
            logger.warning(f"采集系统指标失败: {e}")
            return None

    def _run(self):
        # 先采集一次
        snapshot = self._collect()
        if snapshot:
            with self.lock:
                self.history.append(snapshot)
                self._trim()
                self._save_history()
        
        while self.running:
            time.sleep(INTERVAL)
            snapshot = self._collect()
            if snapshot:
                with self.lock:
                    self.history.append(snapshot)
                    self._trim()
                    self._save_history()

    def _trim(self):
        if len(self.history) > MAX_ENTRIES:
            self.history = self.history[-MAX_ENTRIES:]

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("服务器监控已启动")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=3)
        logger.info("服务器监控已停止")

    def get_current(self) -> dict:
        snapshot = self._collect()
        if snapshot:
            return snapshot
        # 如果采集失败，返回最后一条历史
        with self.lock:
            if self.history:
                return self.history[-1]
        return {
            "cpu_percent": 0, "mem_percent": 0, "mem_used": 0, "mem_total": 1,
            "disk_percent": 0, "disk_used": 0, "disk_total": 1
        }

    def get_history(self, minutes: int = 1440) -> list:
        cutoff = time.time() - minutes * 60
        with self.lock:
            return [s for s in self.history if s["timestamp"] >= cutoff]


monitor = ServerMonitor()
