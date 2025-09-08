# IPGeoAnalyzer_nginx_gitlab
Customized IP Geographic Threat Analysis Tool for GitLab Built in nginx

部署指南
📁 项目文件清单
ipanalyzer/
├── nginx_ip_geo_stats_.py     # 主Web应用文件（已优化）
├── map/                       # 地图数据目录
│   ├── dbip_geo.txt          # 地理文本数据
│   ├── dbip_index.bin        # 二进制索引文件
│   └── dbip_tobin.py         # 数据转换工具
├── dbip-city-lite-2025-09.csv # DB-IP数据库
├── gitlab_access.log.9       # 示例日志文件
└── gitlab_error.log          # 错误日志文件

配置文件说明
# CentOS7环境配置
LOG_DIR = "/var/log/gitlab/nginx/"
BIN_INDEX_PATH = "map/dbip_index.bin"
GEO_TEXT_PATH = "map/dbip_geo.txt"

🎯 核心功能
✅ IP地理分布统计 - 可视化全球访问来源
✅ 实时日志分析 - 支持.gz压缩日志
✅ 交互式地图 - Folium热力图展示
✅ 多时间粒度 - 天/周/月/历史分析
✅ 中文支持 - 完整的中文字体配置

💡 使用说明
1.安装依赖: pip install -r requirements.txt
2.准备数据: 运行 python map/dbip_tobin.py 生成索引
3.启动应用: python nginx_ip_geo_stats_.py
4.访问界面: 打开 http://localhost:5000

🌟 项目特点
🚀 单文件核心 - 主要功能集成在一个文件中
📊 数据可视化 - 丰富的图表和地图展示
🔧 跨平台 - 支持Windows和Linux环境
📈 生产就绪 - 直接部署到CentOS服务器


<img width="1839" height="914" alt="image" src="https://github.com/user-attachments/assets/26a07ad7-c59e-491d-bb1e-34f266505489" />
<img width="1721" height="880" alt="image" src="https://github.com/user-attachments/assets/3b68cf55-fd96-4e63-b9df-ddc7d3fbc5d4" />
<img width="1721" height="500" alt="image" src="https://github.com/user-attachments/assets/78cc5fbe-1f1d-4b15-95ea-fc8605628c54" />
<img width="1842" height="822" alt="image" src="https://github.com/user-attachments/assets/e28e2e38-007f-4409-a861-105de298271f" />
<img width="1797" height="596" alt="image" src="https://github.com/user-attachments/assets/8d4f46a7-e309-4371-bce1-8392073a7dcf" />

所需依赖requirements.txt
flask==2.3.3
matplotlib==3.7.2
seaborn==0.12.2
pandas==2.0.3
folium==0.14.0
