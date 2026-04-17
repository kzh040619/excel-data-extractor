"""
缓存服务 - v1.0.2
使用内存缓存提升性能
"""
import hashlib
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import CACHE_DIR, CACHE_EXPIRY


class CacheService:
    """缓存服务类"""
    
    def __init__(self):
        self.memory_cache: dict[str, tuple[Any, datetime]] = {}
    
    def _get_cache_key(self, file_id: str, sheet_name: str | int | None = None) -> str:
        """生成缓存键"""
        key_str = f"{file_id}_{sheet_name}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return CACHE_DIR / f"{cache_key}.pkl"
    
    def get_dataframe(self, file_id: str, sheet_name: str | int | None = None) -> pd.DataFrame | None:
        """从缓存获取DataFrame"""
        cache_key = self._get_cache_key(file_id, sheet_name)
        
        # 先检查内存缓存
        if cache_key in self.memory_cache:
            data, timestamp = self.memory_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=CACHE_EXPIRY):
                print(f"命中内存缓存: {cache_key}")
                return data
            else:
                # 过期，删除
                del self.memory_cache[cache_key]
        
        # 检查文件缓存
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                # 检查文件时间
                file_mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
                if datetime.now() - file_mtime < timedelta(seconds=CACHE_EXPIRY):
                    with open(cache_path, 'rb') as f:
                        df = pickle.load(f)
                    print(f"命中文件缓存: {cache_key}")
                    # 加载到内存
                    self.memory_cache[cache_key] = (df, datetime.now())
                    return df
                else:
                    # 过期删除
                    cache_path.unlink()
            except Exception as e:
                print(f"读取缓存失败: {e}")
        
        return None
    
    def set_dataframe(self, file_id: str, df: pd.DataFrame, sheet_name: str | int | None = None) -> None:
        """设置DataFrame缓存"""
        cache_key = self._get_cache_key(file_id, sheet_name)
        
        # 存入内存
        self.memory_cache[cache_key] = (df, datetime.now())
        
        # 存入文件（异步）
        try:
            cache_path = self._get_cache_path(cache_key)
            with open(cache_path, 'wb') as f:
                pickle.dump(df, f)
            print(f"缓存已保存: {cache_key}")
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def invalidate(self, file_id: str, sheet_name: str | int | None = None) -> None:
        """使缓存失效"""
        cache_key = self._get_cache_key(file_id, sheet_name)
        
        # 删除内存缓存
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
        
        # 删除文件缓存
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            cache_path.unlink()
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        self.memory_cache.clear()
        for cache_file in CACHE_DIR.glob("*.pkl"):
            cache_file.unlink()
    
    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        memory_count = len(self.memory_cache)
        file_count = len(list(CACHE_DIR.glob("*.pkl")))
        
        return {
            "memoryCache": memory_count,
            "fileCache": file_count,
            "cacheDir": str(CACHE_DIR),
        }


# 全局缓存实例
cache_service = CacheService()
