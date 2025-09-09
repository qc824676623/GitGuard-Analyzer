# IPGeoAnalyzer for GitLab / IPGeoAnalyzer for GitLab

[![Version](https://img.shields.io/badge/Version-1.0.0-blue)](https://github.com/yourusername/IPGeoAnalyzer)
[![Python](https://img.shields.io/badge/Python-3.6%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL--3.0-orange)](https://www.gnu.org/licenses/gpl-3.0.html)

A specialized IP geographic threat analysis tool built for GitLab, based on nginx log analysis, providing global access source visualization.

专为GitLab构建的IP地理威胁分析工具，基于gitlab内置的nginx日志分析，提供全球异常访问来源可视化。

## 🌐 Table of Contents / 目录
- [English](README.md)
- [中文](README_CN.md)

---

## English

### 📦 Deployment Guide

#### Project Structure
```
ipanalyzer/
├── nginx_ip_geo_stats.py# Main application file
├── map/# Map data directory
│  ├── dbip_geo.txt# Geographic text data
│  ├── dbip_index.bin# Binary index (need to unzip due to upload limits)
│  └── dbip_tobin.py# Data conversion tool
├── dbip-city-lite-2025-09.csv # IP database (too large, download when needed)
└── gitlab_error.log# Error log (for testing)
```

#### Configuration
```python
LOG_DIR = "/var/log/gitlab/nginx/"# Nginx log directory
BIN_INDEX_PATH = "map/dbip_index.bin" # Binary index path
GEO_TEXT_PATH = "map/dbip_geo.txt"# Geographic text path
```

### 🚀 Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| 🌍 IP Geographic Distribution | ✅ | Global access source visualization |
| 📊 Real-time Log Analysis | ✅ | Support .gz compressed logs |
| 🗺️ Interactive Map | ✅ | Folium heatmap |
| ⏰ Multiple Time Granularities | ✅ | Day/Week/Month analysis |
| 🇨🇳 Chinese Support | ✅ | Complete Chinese font support |

### 🔍 How It Works

#### Data Processing Flow
- **Log Parsing**: Read GitLab's built-in nginx logs including gitlab_error.log and gitlab_error.log.*.gz, extract IP, timestamp, URL using regex
- **IP Geolocation**: Convert IP to integer format, binary search to match IP ranges
- **Data Statistics**: Multi-dimensional access frequency statistics, time aggregation analysis
- **Visualization**: Matplotlib charts + Folium interactive maps

#### Core Technologies
- IP conversion algorithm: IPv4 to 32-bit integer for fast lookup
- Binary search optimization: O(log n) efficient IP matching
- Multi-threaded processing: Concurrent log file processing
- Memory mapping: Binary indexing reduces memory usage

### 📋 Usage Instructions

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Prepare Data** [Execute only when updating map information]:
```bash
python3 map/dbip_tobin.py
```

3. **Start Application**:
```bash
python3 nginx_ip_geo_stats.py
```

4. **Access Interface**: `http://localhost:5000`

### ✨ Project Features

- 🚀 Single-file core application
- 📊 Rich data visualization
- 🔧 Cross-platform support
- 📈 Production environment ready
- ⚡ High-performance processing

### 📁 Data Files

#### dbip-city-lite-2025-09.csv
**Source**: DB-IP free geographic database
**Format**: Start IP|End IP|Country Code|Country|Region|City|Latitude|Longitude
**Update**: Monthly download from https://db-ip.com

#### dbip_tobin.py
**Function**: CSV to binary index conversion
- IP range indexing: 12 bytes/record (start IP + end IP + location offset)
- Location deduplication: Reduces storage space
- Performance improvement: 10-100x faster than CSV queries

### 🖼️ Interface Preview

<div align="center">

![Dashboard Interface](https://github.com/user-attachments/assets/26a07ad7-c59e-491d-bb1e-34f266505489)
*Figure 1: System Dashboard Interface*

![Dashboard](https://github.com/user-attachments/assets/92abbd2b-5d23-4e14-9777-9e69e2b49b1e)
*Figure 2: URL Access Frequency Statistics*

![Time Distribution](https://github.com/user-attachments/assets/f7f4be30-5986-46be-9638-43d2d925ee6b)
*Figure 3: Time Distribution Chart*

![Access Statistics](https://github.com/user-attachments/assets/78cc5fbe-1f1d-4b15-95ea-fc8605628c54)
![Detailed Analysis](https://github.com/user-attachments/assets/e28e2e38-007f-4409-a861-105de298271f)
![Real-time Monitoring](https://github.com/user-attachments/assets/8d4f46a7-e309-4371-bce1-8392073a7dcf)
*Figure 4: Detailed Analysis Page*

</div>

### Python Version Requirements
This project recommends using Python 3.6+ version

### Dependencies List
```txt
flask==2.3.3
matplotlib==3.7.2
seaborn==0.12.2
pandas==2.0.3
folium==0.14.0
```

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0**.

### Key Terms:
- ✅ Free use, modification, and distribution allowed
- ✅ Derivative works must be open source
- ✅ Copyright notices must be preserved
- ✅ Same license must be adopted
- 📝 Changes must be clearly documented

**Complete license content please see** [LICENSE](LICENSE) file

---

**📞 Issue Reporting** | **✨ Feature Requests** | **🐛 Bug Reports**

*© 2025 IPGeoAnalyzer Project Team. GPL-3.0 License.*

---
