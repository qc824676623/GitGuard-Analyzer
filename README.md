# IPGeoAnalyzer for GitLab - nginx IP地理威胁分析工具

[![Version](https://img.shields.io/badge/Version-1.0.0-blue)](https://github.com/yourusername/IPGeoAnalyzer)
[![Python](https://img.shields.io/badge/Python-3.6%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL--3.0-orange)](https://www.gnu.org/licenses/gpl-3.0.html)

专为GitLab构建的IP地理威胁分析工具，基于nginx日志分析，提供全球异常访问来源可视化。

## 📦 部署指南

### 项目结构
```
ipanalyzer/
├── nginx_ip_geo_stats.py# 主应用文件
├── map/# 地图数据
│  ├── dbip_geo.txt# 地理文本数据
│  ├── dbip_index.bin# 二进制索引
│  └── dbip_tobin.py# 数据转换工具
├── dbip-city-lite-2025-09.csv # IP数据库（文件过大，需要更新时请自行下载）
└── gitlab_error.log# 错误日志（用于测试）
```

### 配置说明
```python
LOG_DIR = "/var/log/gitlab/nginx/"# nginx日志目录
BIN_INDEX_PATH = "map/dbip_index.bin" # 二进制索引路径
GEO_TEXT_PATH = "map/dbip_geo.txt"# 地理文本路径
```

## 🚀 核心功能

| 功能 | 状态 | 描述 |
|------|------|------|
| 🌍 IP地理分布 | ✅ | 全球访问来源可视化 |
| 📊 实时日志分析 | ✅ | 支持.gz压缩日志 |
| 🗺️ 交互式地图 | ✅ | Folium热力图 |
| ⏰ 多时间粒度 | ✅ | 天/周/月分析 |
| 🇨🇳 中文支持 | ✅ | 完整中文字体 |

## 🔍 工作原理

### 数据处理流程
- **日志解析**：读取gitlab内置nginx日志，包括gitlab_error.log gitlab_error.log.*.gz日志，正则提取IP、时间戳、URL
- **IP定位**：IP转整数格式，二分查找匹配IP段
- **数据统计**：多维度统计访问频次，时间聚合分析
- **可视化**：Matplotlib图表 + Folium交互地图

### 核心技术
- IP转换算法：IPv4转32位整数快速查找
- 二分查找优化：O(log n)高效IP匹配
- 多线程处理：并发处理日志文件
- 内存映射：二进制索引减少内存占用

## 📋 使用说明

1. **安装依赖**:
```bash
pip install -r requirements.txt
```

2. **准备数据**:[仅需要更新地图信息时执行]
```bash
python3 map/dbip_tobin.py
```

3. **启动应用**:
```bash
python3 nginx_ip_geo_stats.py
```

4. **访问界面**: `http://localhost:5000`

## ✨ 项目特点

- 🚀 单文件核心应用
- 📊 丰富数据可视化
- 🔧 跨平台支持
- 📈 生产环境就绪
- ⚡ 高性能处理

## 📁 数据文件

### dbip-city-lite-2025-09.csv
**来源**: DB-IP免费地理数据库
**格式**: 起始IP|结束IP|国家代码|国家|地区|城市|纬度|经度
**更新**: 每月从https://db-ip.com下载更新

### dbip_tobin.py
**功能**: CSV转二进制索引
- IP段索引：12字节/记录（起始IP+结束IP+地名偏移）
- 地名去重：减少存储空间
- 性能提升：比CSV查询快10-100倍

## 🖼️ 界面预览

<div align="center">

![仪表盘界面](https://github.com/user-attachments/assets/26a07ad7-c59e-491d-bb1e-34f266505489)
*图1：系统仪表盘界面*

![仪表盘](https://github.com/user-attachments/assets/92abbd2b-5d23-4e14-9777-9e69e2b49b1e)
*图2：*URL访问频次统计*

![时间分布图](https://github.com/user-attachments/assets/f7f4be30-5986-46be-9638-43d2d925ee6b)
*图3：*时间分布图*

![访问统计](https://github.com/user-attachments/assets/78cc5fbe-1f1d-4b15-95ea-fc8605628c54)
![详细分析](https://github.com/user-attachments/assets/e28e2e38-007f-4409-a861-105de298271f)
![实时监控](https://github.com/user-attachments/assets/8d4f46a7-e309-4371-bce1-8392073a7dcf)
*图4：详细分析页面*



</div>

## Python版本要求
本项目推荐使用 Python 3.6+ 版本

## 依赖列表
```txt
flask==2.3.3
matplotlib==3.7.2
seaborn==0.12.2
pandas==2.0.3
folium==0.14.0
```

---

**📞 问题反馈** | **✨ 功能请求** | **🐛 Bug报告**

*© 2025 IPGeoAnalyzer 项目组。MIT许可证。*
