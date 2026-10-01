"""服务器资源监控 — 后台采集 CPU/内存/磁盘数据"""
import os
import json
import time
import threading
import psutil
import logging

MONITOR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor_data.json")
INTERVAL = 60  # 历史采集间隔（秒）
MAX_ENTRIES = 1440  # 最多保留 24h 数据
REALTIME_INTERVAL = 2  # 实时采样间隔（秒）
REALTIME_MAX = 300  # 实时缓冲最多保留 300 条（约 10 分钟）

logger = logging.getLogger("monitor")


class ServerMonitor:
    def __init__(self):
        self.history: list = []
        self.realtime: list = []
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

    def sample_realtime(self) -> dict:
        """实时采样：由实时推送循环按 REALTIME_INTERVAL 调用。

        psutil.cpu_percent(interval=0) 返回的是「距上次调用」区间的使用率，
        因此必须由单一调用方按固定节奏驱动，避免多处调用互相干扰采样窗口。
        """
        snapshot = self._collect()
        if snapshot:
            with self.lock:
                self.realtime.append(snapshot)
                if len(self.realtime) > REALTIME_MAX:
                    self.realtime = self.realtime[-REALTIME_MAX:]
        return snapshot

    def _run(self):
        # 历史循环只负责归档，指标由实时采样提供，避免重复调用 cpu_percent 破坏采样窗口
        while self.running:
            time.sleep(INTERVAL)
            with self.lock:
                snapshot = dict(self.realtime[-1]) if self.realtime else None
            if snapshot is None:
                snapshot = self.sample_realtime()
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
        # 预热 CPU 采样基线：psutil 首次调用只建立基线（返回 0.0），
        # 不预热会让重启后的第一个采样点、第一条历史记录出现假的 0%。
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass
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
        # 优先使用最近的实时采样，避免额外调用 _collect() 干扰实时采样窗口
        with self.lock:
            if self.realtime:
                last = self.realtime[-1]
                if time.time() - last["timestamp"] < REALTIME_INTERVAL * 3:
                    return dict(last)

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

    def get_realtime_history(self, seconds: int = 120) -> list:
        """返回最近 seconds 秒内的实时采样序列"""
        cutoff = time.time() - seconds
        with self.lock:
            return [dict(s) for s in self.realtime if s["timestamp"] >= cutoff]

    def get_history(self, minutes: int = 1440) -> list:
        cutoff = time.time() - minutes * 60
        with self.lock:
            return [s for s in self.history if s["timestamp"] >= cutoff]


monitor = ServerMonitor()
