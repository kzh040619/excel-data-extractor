"""
版本更新服务 - v1.0.2
检查GitHub最新版本
"""
import json
from typing import Any

import httpx

from app.config import VERSION, GITHUB_REPO


async def check_for_updates() -> dict[str, Any]:
    """检查是否有新版本"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get("tag_name", "").lstrip("v")
                current_version = VERSION
                
                # 比较版本
                has_update = _compare_versions(latest_version, current_version)
                
                return {
                    "hasUpdate": has_update,
                    "currentVersion": current_version,
                    "latestVersion": latest_version,
                    "releaseUrl": release_data.get("html_url", ""),
                    "releaseNotes": release_data.get("body", ""),
                    "publishedAt": release_data.get("published_at", ""),
                }
            else:
                return {
                    "hasUpdate": False,
                    "currentVersion": VERSION,
                    "error": f"GitHub API返回{response.status_code}",
                }
    
    except Exception as e:
        return {
            "hasUpdate": False,
            "currentVersion": VERSION,
            "error": str(e),
        }


def _compare_versions(latest: str, current: str) -> bool:
    """比较版本号"""
    try:
        latest_parts = [int(x) for x in latest.split(".")]
        current_parts = [int(x) for x in current.split(".")]
        
        # 补齐长度
        while len(latest_parts) < 3:
            latest_parts.append(0)
        while len(current_parts) < 3:
            current_parts.append(0)
        
        return latest_parts > current_parts
    except Exception:
        return False


def get_current_version() -> dict[str, str]:
    """获取当前版本信息"""
    return {
        "version": VERSION,
        "repo": GITHUB_REPO,
    }
