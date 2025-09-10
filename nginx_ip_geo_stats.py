import os
import re
import gzip
import struct
import socket
import datetime
from collections import defaultdict, OrderedDict
# 添加新的依赖
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，适合服务器环境
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from flask import Flask, render_template, make_response, app
from io import BytesIO
import base64
import folium
from folium import plugins
import platform  # 添加导入platform模块
import threading
import time
# 在generate_charts函数中修改字体设置部分
# 替换原有的字体设置代码
# 设置中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 跨平台字体设置
system = platform.system()
if system == 'Windows':
    plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "SimSun"]
elif system == 'Linux':
    # 在Linux系统中尝试使用常见的中文字体
    cn_fonts = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'SimHei', 'DejaVu Sans']
    plt.rcParams["font.family"] = cn_fonts
else:
    # 其他系统使用默认字体
    plt.rcParams["font.family"] = ['sans-serif']

# 添加全局变量存储统计数据
GLOBAL_STATS = None
# ========================
# 配置参数（根据实际环境修改）
# ========================
# centos7环境
LOG_DIR = "/var/log/gitlab/nginx/"  # 日志文件存放目录（包含 .log 和 .gz 文件）
BIN_INDEX_PATH = "map/dbip_index.bin"  # 二进制索引文件路径
GEO_TEXT_PATH = "map/dbip_geo.txt"  # 地名文本文件路径
# windows测试环境
# LOG_DIR = "../bin/"  # 日志文件存放目录（包含 .log 和 .gz 文件）
# BIN_INDEX_PATH = "../map/dbip_index.bin"  # 二进制索引文件路径
# GEO_TEXT_PATH = "../map/dbip_geo.txt"  # 地名文本文件路径
TOP_N = 20  # 输出Top N结果
TIME_GRANS = {  # 时间粒度定义（名称: 天数）
    "最近一天": 1,
    "最近一周": 7,
    "最近一月": 30,
    "历史情况": 365 * 10  # 足够大的天数覆盖所有历史
}


# 在文件开头添加
LAST_REFRESH_TIME = None
REFRESH_INTERVAL = 3600  # 1小时

# 添加定时刷新线程
def auto_refresh():
    while True:
        time.sleep(REFRESH_INTERVAL)
        try:
            main()
            LAST_REFRESH_TIME = datetime.datetime.now()
            print(f"自动刷新完成于 {LAST_REFRESH_TIME}")
        except Exception as e:
            print(f"自动刷新失败: {e}")

def generate_charts(time_name, stats):
    charts = {}
    top_n = TOP_N
    total = stats['total']
    if total == 0:
        return charts

    # 设置中文字体
    plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "SimSun"]  # 仅保留Windows兼容字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    # 1. IP访问频次饼图
    plt.figure(figsize=(10, 6))
    ip_data = sorted(stats['ip_freq'].items(), key=lambda x: -x[1])[:top_n]
    if len(ip_data) > 0:
        ips, counts = zip(*ip_data)
        # 添加"其他"类别
        other_count = total - sum(counts)
        if other_count > 0:
            ips = list(ips) + ['other']
            counts = list(counts) + [other_count]
        plt.pie(counts, labels=ips, autopct='%1.1f%%', startangle=90)
        # plt.title(f'{time_name} IP访问分布')
        plt.axis('equal')
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        charts['ip_pie'] = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()

    # 2. 国家/地区访问频次柱状图
    plt.figure(figsize=(12, 6))
    country_data = sorted(stats['country_freq'].items(), key=lambda x: -x[1])[:top_n]
    if len(country_data) > 0:
        countries, counts = zip(*country_data)
        country_labels = [f'{country}' for country, _ in country_data]
        sns.barplot(x=list(counts), y=country_labels)
        # plt.title(f'{time_name} 国家访问分布')
        plt.xlabel('times')
        plt.ylabel('country/region')
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        charts['country_bar'] = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()

    # 3. 生成地图
    if 'geo_data' in stats and stats['geo_data']:
        # 创建基础地图 - 使用全球视角
        m = folium.Map(
            location=[0, 0],  # 全球中心
            zoom_start=2,  # 全球缩放级别
            tiles="https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",

            # tiles="CartoDB Positron",  # 简洁风格瓦片（无需 Key）
            attr="CartoDB",
            subdomains = None  # 禁用子域名随机选择

        )

        # m = folium.Map(
        #     location=[35.8617, 104.1954],  # 中国区域中心（确保初始视野在数据区域）
        #     zoom_start=4,  # 缩放级别4（国家视野，避免低级别下瓦片请求过少）
        #     # 正确URL：子域名使用 {s} 占位符，匹配 subdomains 参数
        #     tiles='http://webrd0{1-4}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=8&style=8&x={x}&y={y}&z={z}&key=922781733eec18a7e4343d716bce367f',
        #     # tiles='https://webst0{s}.is.autonavi.com/appmaptile?style=8&x={x}&y={y}&z={z}&key=9f3e711ced6cb40d97dce65fa3cb816c',
        #     attr='高德地图',
        #     subdomains=['1', '2', '3', '4'],  # 子域名后缀（与URL中的 "0{s}" 组合为 "01~04"）
        #     control_scale=True
        # )
        # 准备热力图数据
        heat_data = []
        marker_data = []

        # 收集所有IP的地理位置数据
        for ip, locations in stats['geo_data'].items():
            for location in locations:
                lat = location['latitude']
                lon = location['longitude']
                count = location['count']

                # 添加到热力图数据
                heat_data.append([lat, lon, count])

                # 添加到标记数据
                marker_data.append({
                    'location': [lat, lon],
                    'ip': ip,
                    'count': count,
                    'country': location['country'],
                    'region': location['region'],
                    'city': location['city']
                })

        # 添加热力图层
        if heat_data:
            plugins.HeatMap(heat_data).add_to(m)

        # 添加标记层
        for marker in marker_data:
            folium.CircleMarker(
                location=marker['location'],
                radius=max(marker['count'] / 10, 5),  # 气泡大小代表访问次数
                popup=f"IP: {marker['ip']}<br>访问次数: {marker['count']}<br>国家/地区: {marker['country']}<br>地区: {marker['region']}<br>城市: {marker['city']}",
                color='red',
                fill=True,
                fillColor='red',
                fillOpacity=0.6
            ).add_to(m)

        # 保存地图到HTML字符串
        charts['map'] = m._repr_html_()

    # 4. 访问时段分布柱状图
    plt.figure(figsize=(12, 6))
    hour_data = sorted(stats['hour_freq'].items(), key=lambda x: x[0])
    if len(hour_data) > 0:
        hours, counts = zip(*hour_data)
        hour_labels = [f'{hour}:00' for hour in hours]
        sns.barplot(x=hour_labels, y=list(counts))
        # plt.title(f'{time_name} 访问时段分布')
        plt.xlabel('hour')
        plt.ylabel('times')
        plt.xticks(rotation=45)  # 旋转x轴标签以避免重叠
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        charts['hour_bar'] = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()

        # 5. URL访问频次柱状图
    plt.figure(figsize=(12, 8))
    url_data = sorted(stats['url_freq'].items(), key=lambda x: -x[1])[:top_n]
    if len(url_data) > 0:
        urls, counts = zip(*url_data)
        # 截断过长的URL以便显示
        url_labels = [url[:50] + '...' if len(url) > 50 else url for url in urls]
        sns.barplot(x=list(counts), y=url_labels)
        plt.xlabel('访问次数')
        plt.ylabel('URL路径')
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        charts['url_bar'] = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
    return charts
# ========================
# 1. 工具函数：IP和时间处理
# ========================
def ip_to_int(ip_str):
    """IP字符串→4字节整数"""
    try:
        return struct.unpack(">I", socket.inet_aton(ip_str))[0]
    except:
        return None


def parse_log_time(log_line):
    """从日志行提取时间戳（适配格式：2025/09/03 01:16:09）"""
    # 正则匹配：2025/09/03 01:16:09
    time_pattern = re.compile(r'^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})')
    match = time_pattern.search(log_line)
    if not match:
        return None  # 未找到时间戳
    time_str = match.group(1)
    try:
        # 解析为datetime对象（格式：年/月/日 时:分:秒）
        return datetime.datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
    except ValueError as e:
        print(f"时间解析失败：{time_str}，错误：{e}")
        return None


def is_in_time_range(log_time, days):
    """判断日志时间是否在最近N天内"""
    if not log_time:
        return False
    delta = datetime.datetime.now() - log_time
    return delta.days < days


# ========================
# 2. 加载二进制索引（复用之前的高效加载逻辑）
# ========================
def load_bin_index():
    """加载二进制索引和地名文本"""
    with open(GEO_TEXT_PATH, 'r', encoding='utf-8') as f:
        geo_lines = f.readlines()
    with open(BIN_INDEX_PATH, 'rb') as f:
        bin_data = f.read()
    ip_segments = []
    for i in range(0, len(bin_data), 12):
        start_ip = struct.unpack(">I", bin_data[i:i + 4])[0]
        end_ip = struct.unpack(">I", bin_data[i + 4:i + 8])[0]
        geo_offset = struct.unpack(">I", bin_data[i + 8:i + 12])[0]
        ip_segments.append((start_ip, end_ip, geo_offset))
    ip_segments.sort(key=lambda x: x[0])
    return ip_segments, geo_lines


# ========================
# 3. 处理单个日志文件（支持.gz和.log）
# ========================
def process_log_file(file_path, time_days, ip_segments, geo_lines, stats):
    """处理单个日志文件，按时间粒度统计IP和地理信息"""
    # 打开文件（根据后缀判断是否解压）
    open_func = gzip.open if file_path.endswith('.gz') else open
    ip_pattern = re.compile(r'client:\s*(\d+\.\d+\.\d+\.\d+)')  # 提取客户端IP
    url_pattern = re.compile(r'request: "(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH) ([^ ]+)')  # 添加URL提取正则

    with open_func(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            # 1. 提取时间戳并过滤时间范围
            log_time = parse_log_time(line)
            if not is_in_time_range(log_time, time_days):
                continue  # 不在目标时间范围内，跳过

            # 添加时段统计
            if log_time:
                hour = log_time.hour
                stats['hour_freq'][hour] += 1

            # 2. 提取URL
            url_match = url_pattern.search(line)
            if url_match:
                url = url_match.group(2)
                stats['url_freq'][url] += 1

            # 3. 提取客户端IP
            ip_match = ip_pattern.search(line)
            if not ip_match:
                continue
            ip_str = ip_match.group(1)
            ip_int = ip_to_int(ip_str)
            if not ip_int:
                continue

            # 4. 二分查找地理信息
            left, right = 0, len(ip_segments) - 1
            while left <= right:
                mid = (left + right) // 2
                start_ip, end_ip, geo_offset = ip_segments[mid]
                if start_ip <= ip_int <= end_ip:
                    # 解析地名信息（格式：国家|地区|城市|纬度|经度）
                    geo_text = geo_lines[geo_offset]
                    parts = geo_text.strip().split('|')
                    if len(parts) == 5:
                        country, region, city, latitude, longitude = parts
                        # 更新统计数据（stats是按时间粒度区分的字典）
                        stats['ip_freq'][ip_str] += 1
                        stats['country_freq'][country] += 1
                        # 使用元组作为键，以匹配模板中的解包方式
                        stats['region_freq'][(region, region)] += 1  # 这里使用(region, region)是因为没有中英文区分
                        stats['city_freq'][(city, city)] += 1  # 这里使用(city, city)是因为没有中英文区分
                        # 添加地理位置信息到统计数据
                        if 'geo_data' not in stats:
                            stats['geo_data'] = defaultdict(list)
                        print(f"IP: {ip_str}, 纬度: {latitude}, 经度: {longitude}, 国家/地区: {country}")

                        stats['geo_data'][ip_str].append({
                            'count': stats['ip_freq'][ip_str],
                            'country': country,
                            'region': region,
                            'city': city,
                            'latitude': float(latitude),
                            'longitude': float(longitude)
                        })
                    stats['total'] += 1  # 总记录数
                    break
                elif ip_int < start_ip:
                    right = mid - 1
                else:
                    left = mid + 1


# ========================
# 4. 主函数：遍历文件+多维度统计
# ========================
def main():
    global LAST_REFRESH_TIME  # 添加global声明

    # 先执行统计
    try:
        refresh_stats_only()
        # 第一次统计完成后更新最后刷新时间
        LAST_REFRESH_TIME = datetime.datetime.now()
        print("GLOBAL_STATS 初始化成功")
        print(f"首次数据刷新完成于 {LAST_REFRESH_TIME}")
    except Exception as e:
        print(f"GLOBAL_STATS 初始化失败: {e}")
        return  # 初始化失败时直接返回

    # 启动自动刷新线程（在Web服务器之前）
    refresh_thread = threading.Thread(target=auto_refresh, daemon=True)
    refresh_thread.start()

    # 启动Web服务器
    start_web_server()
    # ========================
    # 输出多维度统计结果
    # ========================
    print("\n" + "=" * 100)
    print("📊 GitLab Nginx错误日志IP地理统计报告")
    print("=" * 100)

    for time_name, stats in GLOBAL_STATS.items():
        print(f"\n\n【{time_name}】（异常总访问：{stats['total']}次）")
        print("-" * 60)

        # 1. IP访问频次Top N
        print("\n[IP访问频次 Top 20]")
        for ip, cnt in sorted(stats['ip_freq'].items(), key=lambda x: -x[1])[:TOP_N]:
            print(f"  {ip}: {cnt}次 (占比：{cnt / stats['total']:.2%})" if stats['total'] else f"  {ip}: {cnt}次")

        # 2. 国家频次Top N（中英文）
        print("\n[国家/地区频次 Top 20]")
        for (en, cn), cnt in sorted(stats['country_freq'].items(), key=lambda x: -x[1])[:TOP_N]:
            print(f"  {en} ({cn}): {cnt}次 (占比：{cnt / stats['total']:.2%})" if stats[
                'total'] else f"  {en} ({cn}): {cnt}次")

        # 3. 地区频次Top N（中英文）
        print("\n[地区频次 Top 20]")
        for (en, cn), cnt in sorted(stats['region_freq'].items(), key=lambda x: -x[1])[:TOP_N]:
            print(f"  {en} ({cn}): {cnt}次")

        # 4. 城市频次Top N（中英文）
        print("\n[城市频次 Top 20]")
        for (en, cn), cnt in sorted(stats['city_freq'].items(), key=lambda x: -x[1])[:TOP_N]:
            print(f"  {en} ({cn}): {cnt}次")

    print("\n" + "=" * 100)
    print("统计完成！")


# 添加新函数：启动Flask Web服务器
def start_web_server():
    app = Flask(__name__)

    @app.route('/')
    def index():
        # 默认显示当日统计
        default_time_name = '最近一天'
        if default_time_name not in GLOBAL_STATS:
            return "暂无统计数据", 404

        stats = GLOBAL_STATS[default_time_name]
        try:
            charts = generate_charts(default_time_name, stats)
        except Exception as e:
            charts = {}
            print(f"生成图表时出错: {str(e)}")

        last_refresh_time = LAST_REFRESH_TIME.strftime('%Y-%m-%d %H:%M:%S') if LAST_REFRESH_TIME else '从未刷新'

        return render_template('stats.html',
                               time_name=default_time_name,
                               stats=stats,
                               charts=charts,
                               top_n=TOP_N,
                               last_refresh_time=last_refresh_time,
                               time_periods=GLOBAL_STATS.keys())

    @app.route('/stats/<time_name>')
    def show_stats(time_name):
        if time_name not in GLOBAL_STATS:
            return "无效的时间范围", 404

        stats = GLOBAL_STATS[time_name]
        try:
            charts = generate_charts(time_name, stats)
        except Exception as e:
            charts = {}
            print(f"生成图表时出错: {str(e)}")

        last_refresh_time = LAST_REFRESH_TIME.strftime('%Y-%m-%d %H:%M:%S') if LAST_REFRESH_TIME else '从未刷新'

        return render_template('stats.html',
                               time_name=time_name,
                               stats=stats,
                               charts=charts,
                               top_n=TOP_N,
                               last_refresh_time=last_refresh_time,
                               time_periods=GLOBAL_STATS.keys())

    @app.route('/refresh')
    def refresh_data():
        try:
            refresh_stats_only()
            global LAST_REFRESH_TIME
            LAST_REFRESH_TIME = datetime.datetime.now()
            return "数据刷新成功！<a href='/'>返回首页</a>"
        except Exception as e:
            return f"数据刷新失败: {str(e)}"
    # 创建简单的HTML模板
    create_templates()

    print("\n启动Web服务器...")
    print("访问 http://0.0.0.0:5000 查看可视化结果")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

# 添加新函数：创建HTML模板
# 添加新函数：创建HTML模板
def create_templates():
    # 创建templates目录
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)

    # 创建index.html
    index_html = '''<!DOCTYPE html>
<html>
<head>
    <title>IP地理统计分析</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .time-period { display: inline-block; margin: 10px; padding: 15px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; }
        .time-period:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <h1>gitlab公网服务威胁分析</h1>
    <h2>请选择时间范围:</h2>
    {% for period in time_periods %}
        <a href="/stats/{{ period }}" class="time-period">{{ period }}</a>
    {% endfor %}
</body>
</html>'''
    with open(os.path.join(template_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

    # 创建stats.html
    stats_html = '''<!DOCTYPE html>
<html>
<head>
    <title>{{ time_name }} - gitlab公网服务威胁分析</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1e1e2d;
            color: #e0e0e0;
            position: relative; /* 添加相对定位 */
        }
        .refresh-container {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            background-color: #252536;
            padding: 10px 15px;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }
        .refresh-time {
            color: #6c757d;
            font-size: 14px;
        }
        .dashboard-container {
            display: grid;
            grid-template-columns: 2fr 1fr; /* 地图占2份，图表占1份 */
            gap: 20px;
        }
        .map-section {
            grid-column: 1; /* 地图在左侧 */
            background-color: #2d2d44;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        .charts-section {
            grid-column: 2; /* 图表在右侧 */
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .chart-card {
            background-color: #2d2d44;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease; /* 添加过渡动画 */
        }
        .chart-card:hover {
            transform: translateY(-5px); /* 悬停时上移 */
            box-shadow: 0 6px 12px rgba(0,0,0,0.4);
        }
        .dashboard-card {
            background-color: #2d2d44;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        .dashboard-card h3 {
            margin-top: 0;
            color: #6ab0f3;
            border-bottom: 2px solid #6ab0f3;
            padding-bottom: 10px;
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin-bottom: 20px; 
        }
        th, td { 
            border: 1px solid #444; 
            padding: 8px; 
            text-align: left; 
        }
        th { 
            background-color: #3d3d5c; 
        }
        #map { 
            width: 100%; 
            height: 700px; /* 增加地图高度 */
            border-radius: 10px; 
        }
        .chart-container img {
            max-width: 100%;
            border-radius: 10px;
        }
         .header {
            background-color: #252536;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            text-align: center; /* 添加居中显示 */
        }
        .header h1, .header h2 {
            margin: 0 0 10px 0;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>{{ time_name }} Gitlab威胁分布与统计</h1>
        <h2>总访问：{{ stats.total }}次</h2>
    </div>
    
    <!-- 在页面顶部添加日期范围选择器 -->
    <div class="time-period-selector" style="margin-bottom: 30px; background-color: #252536; padding: 15px; border-radius: 8px;">
        <h2 style="margin-top: 0; color: #6ab0f3;">选择时间范围:</h2>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            {% for period in time_periods %}
                <a href="/stats/{{ period }}" 
                   class="time-period" 
                   style="display: inline-block; padding: 10px 15px; background-color: {% if period == time_name %}#28a745{% else %}#007bff{% endif %}; color: white; text-decoration: none; border-radius: 5px; transition: background-color 0.3s;">
                    {{ period }}
                </a>
            {% endfor %}
        </div>
    </div>
    <!-- 将刷新按钮和时间移到右上方 -->
    <div class="refresh-container">
        <a href="/refresh" class="time-period" style="background-color: #28a745;">🔄 立即刷新数据</a>
        <span class="refresh-time">最后刷新: {{ last_refresh_time }}</span>
    </div>
            
    
    
    <div class="dashboard-container">
        <!-- 地图区域 -->
        <div class="map-section">
            {% if charts.map %}
            <div class="dashboard-card">
                <h3>威胁IP地理分布</h3>
                <div id="map">{{ charts.map|safe }}</div>
            </div>
            {% endif %}
        </div>

        <!-- 图表区域 -->
        <div class="charts-section">
            {% if charts.ip_pie %}
            <div class="chart-card">
                <h3>IP访问分布</h3>
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.ip_pie }}" alt="IP访问分布">
                </div>
            </div>
            {% endif %}

            {% if charts.country_bar %}
            <div class="chart-card">
                <h3>国家/地区访问分布</h3>
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.country_bar }}" alt="国家访问分布">
                </div>
            </div>
            {% endif %}

        </div>
    </div>
    
     {% if charts.hour_bar %}
        <div class="chart-card">
            <h3>访问时段分布</h3>
            <div class="chart-container">
                <img src="data:image/png;base64,{{ charts.hour_bar }}" alt="访问时段分布">
            </div>
        </div>
    {% endif %}
    
     <!-- 添加URL访问频次表格 -->
    <div class="dashboard-card">
        <h3>URL访问频次</h3>
        <div id="url-table-container">
            <table id="url-table">
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>URL路径</th>
                        <th>访问次数</th>
                        <th>占比</th>
                    </tr>
                </thead>
                <tbody>
                    {% set sorted_urls = stats['url_freq'].items() | sort(reverse=true, attribute='1') | list %}
                    {% for url, count in sorted_urls %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td title="{{ url }}">{{ url[:80] }}{% if url|length > 80 %}...{% endif %}</td>
                        <td>{{ count }}</td>
                        <td>{{ "%.2f"|format(count / stats['total'] * 100) }}%</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div id="pagination-controls" style="margin-top: 20px;">
            <button id="prev-page" disabled>上一页</button>
            <span id="page-info">第 1 页</span>
            <button id="next-page">下一页</button>
        </div>
    </div>
    
    <!-- 表格部分保持原有结构 -->
    <div class="dashboard-card">
        <h3>IP访问频次 Top {{ top_n }}</h3>
        {% if stats.ip_freq %}
        {% set sorted_ips = stats.ip_freq.items() | sort(reverse=true, attribute='1') | list %}
        {% set top_ips = sorted_ips[:top_n if top_n > 0 else 20] %}
        <table>
            <tr><th>IP地址</th><th>访问次数</th><th>占比</th></tr>
            {% for ip, cnt in top_ips %}
            <tr>
                <td>{{ ip }}</td>
                <td>{{ cnt }}</td>
                <td>{{ (cnt / stats.total * 100) | round(2) }}%</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p>没有找到IP访问数据</p>
        {% endif %}
    </div>

    <div class="dashboard-card">
        <h3>国家频次 Top {{ top_n }}</h3>
        {% if stats.country_freq %}
        {% set sorted_countries = stats.country_freq.items() | sort(reverse=true, attribute='1') | list %}
        {% set top_countries = sorted_countries[:top_n if top_n > 0 else 20] %}
        <table>
            <tr><th>国家</th><th>访问次数</th><th>占比</th></tr>
            {% for (en, cn), cnt in top_countries %}
            <tr>
                <td>{{ en }} ({{ cn }})</td>
                <td>{{ cnt }}</td>
                <td>{{ (cnt / stats.total * 100) | round(2) }}%</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p>没有找到国家访问数据</p>
        {% endif %}
    </div>

    <div class="dashboard-card">
        <h3>地区频次 Top {{ top_n }}</h3>
        {% if stats.region_freq %}
        {% set sorted_regions = stats.region_freq.items() | sort(reverse=true, attribute='1') | list %}
        {% set top_regions = sorted_regions[:top_n if top_n > 0 else 20] %}
        <table>
            <tr><th>地区</th><th>访问次数</th></tr>
            {% for (en, cn), cnt in top_regions %}
            <tr>
                <td>{{ en }} ({{ cn }})</td>
                <td>{{ cnt }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p>没有找到地区访问数据</p>
        {% endif %}
    </div>

    <div class="dashboard-card">
        <h3>城市频次 Top {{ top_n }}</h3>
        {% if stats.city_freq %}
        {% set sorted_cities = stats.city_freq.items() | sort(reverse=true, attribute='1') | list %}
        {% set top_cities = sorted_cities[:top_n if top_n > 0 else 20] %}
        <table>
            <tr><th>城市</th><th>访问次数</th></tr>
            {% for (en, cn), cnt in top_cities %}
            <tr>
                <td>{{ en }} ({{ cn }})</td>
                <td>{{ cnt }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p>没有找到城市访问数据</p>
        {% endif %}
    </div>
    <div style="margin-top: 40px; padding: 20px; text-align: center; color: #6c757d; border-top: 1px solid #444;">
        <p>© 2025 GitLab威胁分析系统 | 版权所有</p>
        <p>Powered by Python Flask & Folium</p>
    </div>
</body>

<script>
    // URL表格分页功能
    const table = document.getElementById('url-table');
    const rows = table.querySelectorAll('tbody tr');
    const pageSize = 10; // 每页显示10行
    let currentPage = 1;
    
    function showPage(page) {
        const startIndex = (page - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        
        rows.forEach((row, index) => {
            row.style.display = (index >= startIndex && index < endIndex) ? '' : 'none';
        });
        
        document.getElementById('page-info').textContent = `第 ${page} 页`;
        document.getElementById('prev-page').disabled = page === 1;
        document.getElementById('next-page').disabled = endIndex >= rows.length;
    }
    
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            showPage(currentPage);
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        if (currentPage * pageSize < rows.length) {
            currentPage++;
            showPage(currentPage);
        }
    });
    
    // 初始显示第一页
    showPage(1);
</script>
</html>'''
    with open(os.path.join(template_dir, 'stats.html'), 'w', encoding='utf-8') as f:
        f.write(stats_html)

def auto_refresh():
    global LAST_REFRESH_TIME  # 添加global声明
    while True:
        time.sleep(REFRESH_INTERVAL)
        try:
            # 只执行统计功能，不启动Web服务器
            refresh_stats_only()
            LAST_REFRESH_TIME = datetime.datetime.now()
            print(f"自动刷新完成于 {LAST_REFRESH_TIME}")
        except Exception as e:
            print(f"自动刷新失败: {e}")


# 添加新的统计函数，不包含Web服务器启动
def refresh_stats_only():
    global GLOBAL_STATS
    # 步骤1：加载二进制索引（仅加载一次）
    print("[自动刷新] 加载二进制索引和地名数据...")
    try:
        ip_segments, geo_lines = load_bin_index()
    except Exception as e:
        print(f"❌ 索引加载失败：{e}")
        return

    # 步骤2：遍历日志目录下的所有文件
    log_files = []
    for filename in os.listdir(LOG_DIR):
        if filename.startswith('gitlab_error') and (filename.endswith('.log') or filename.endswith('.gz')):
            log_files.append(os.path.join(LOG_DIR, filename))

    if not log_files:
        return

    # 步骤3：按时间粒度统计
    time_stats = OrderedDict()
    for time_name, days in TIME_GRANS.items():
        stats = {
            'total': 0,
            'ip_freq': defaultdict(int),
            'country_freq': defaultdict(int),
            'region_freq': defaultdict(int),
            'city_freq': defaultdict(int),
            'hour_freq': defaultdict(int),
            'url_freq': defaultdict(int),
            'geo_data': defaultdict(list)
        }
        for file_path in log_files:
            process_log_file(file_path, days, ip_segments, geo_lines, stats)
        time_stats[time_name] = stats

    # 更新全局统计数据
    GLOBAL_STATS = time_stats
    print("[自动刷新] 统计完成！")

if __name__ == "__main__":
    main()
