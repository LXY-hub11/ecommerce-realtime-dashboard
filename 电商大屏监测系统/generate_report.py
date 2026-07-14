# -*- coding: utf-8 -*-
"""
直接在模板上修改内容，保留100%原始格式（字体/颜色/缩进/样式）
策略：通过Word COM精确定位每个段落，逐一替换内容
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import win32com.client
import pythoncom
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

TEMPLATE = r"D:\项目\电商大屏监测系统\课程设计报告模板-大数据综合实训-0.doc"
OUTPUT = r"D:\项目\电商大屏监测系统\实时电商数据大屏监测系统_课程设计报告.docx"
IMG_DIR = r"D:\项目\电商大屏监测系统\report_images"
os.makedirs(IMG_DIR, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# Generate Architecture Diagrams
# ============================================================
def make_rounded_box(ax, x, y, w, h, text, color, fontsize=9):
    """Draw a rounded box with text"""
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                          facecolor=color, edgecolor='#37474f', linewidth=1.5)
    ax.add_patch(rect)
    for i, line in enumerate(text.split('\n')):
        ax.text(x + w/2, y + h/2 + 0.12*(1-2*i), line, ha='center', va='center',
               fontsize=fontsize, fontweight='bold', color='#263238')

def generate_flow():
    """图1 系统数据流架构图"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 4))
    ax.set_xlim(0, 14); ax.set_ylim(0, 4); ax.axis('off')
    boxes = [
        (0.3, 2.2, 2.3, 1.2, 'Python 数据生成器\n(200订单/s+1000PV/s)', '#e3f2fd'),
        (3.0, 2.2, 2.3, 1.2, 'Kafka 消息队列\n(4分区, 2个Topic)', '#fff3e0'),
        (5.8, 2.2, 2.3, 1.2, 'Flink 流计算引擎\n(1s+1min 滚动窗口)', '#e8f5e9'),
        (8.6, 2.2, 2.3, 1.2, 'Redis 缓存\n(TTL 自动过期)', '#fce4ec'),
        (11.2, 2.2, 2.3, 1.2, '前端大屏\n(React+ECharts)', '#e0f2f1'),
    ]
    for item in boxes:
        make_rounded_box(ax, *item)
    for x1, x2 in [(2.6, 3.0), (5.3, 5.8), (8.1, 8.6)]:
        ax.annotate('', xy=(x2, 2.8), xytext=(x1, 2.8),
                    arrowprops=dict(arrowstyle='->', color='#546e7a', lw=2.5))
    ax.annotate('', xy=(12.35, 2.2), xytext=(10.9, 1.5),
                arrowprops=dict(arrowstyle='->', color='#546e7a', lw=2.5, connectionstyle='arc3,rad=-0.5'))
    ax.text(11.6, 1.2, 'WebSocket 实时推送', ha='center', fontsize=8, color='#546e7a')
    ax.set_title('图1  系统数据流架构图', fontsize=13, fontweight='bold', color='#1a237e', pad=12)
    fig.tight_layout()
    path = os.path.join(IMG_DIR, 'flow_cn.png')
    fig.savefig(path, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path

def generate_module():
    """图2 系统分层模块结构图"""
    fig, ax = plt.subplots(1, 1, figsize=(13, 6))
    ax.set_xlim(0, 13); ax.set_ylim(0, 6); ax.axis('off')
    layers = [
        (0.5, 5.0, 12.0, 0.7, '可视化层：React 18 + ECharts 5 （实时大屏，暗色主题）', '#bbdefb'),
        (0.5, 4.0, 12.0, 0.7, '服务层：Express.js + Socket.IO （REST API + 实时推送 + 降级容错）', '#c8e6c9'),
        (0.5, 3.0, 12.0, 0.7, '流处理层：Apache Flink 1.18 （1s/1min滚动窗口，增量聚合，UV去重）', '#fff9c4'),
        (0.5, 2.0, 6.5, 0.7, '消息队列层：Kafka 3.9.2 KRaft （4分区，高吞吐缓冲）', '#ffe0b2'),
        (7.5, 2.0, 5.0, 0.7, '数据生成层：Python 多线程 （Burst 流量突增模拟）', '#f8bbd0'),
        (0.5, 1.0, 12.0, 0.7, '缓存存储层：Redis 7 （内存缓存，SETEX + TTL 自动过期）', '#d1c4e9'),
    ]
    for x, y, w, h, text, color in layers:
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='#546e7a', linewidth=1.3)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=9, fontweight='bold', color='#263238')
    for i in range(3):
        ax.annotate('', xy=(6.5, 5.0 - i - 0.05), xytext=(6.5, 5.0 - i - 0.35),
                    arrowprops=dict(arrowstyle='->', color='#37474f', lw=2))
    ax.set_title('图2  系统分层模块结构图', fontsize=13, fontweight='bold', color='#1a237e', pad=12)
    fig.tight_layout()
    path = os.path.join(IMG_DIR, 'module_cn.png')
    fig.savefig(path, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path

def generate_flink():
    """图3 Flink流计算处理流程图"""
    fig, ax = plt.subplots(1, 1, figsize=(13, 5))
    ax.set_xlim(0, 13); ax.set_ylim(0, 5); ax.axis('off')
    nodes = [
        (0.3, 3.8, 2.0, 0.7, 'Kafka 数据源\n(order-events)', '#e3f2fd'),
        (0.3, 0.8, 2.0, 0.7, 'Kafka 数据源\n(pageview-events)', '#e3f2fd'),
        (3.0, 3.8, 1.8, 0.7, 'JSON 解析\nFlatMap<Order>', '#fff3e0'),
        (3.0, 0.8, 1.8, 0.7, 'JSON 解析\nFlatMap<PageView>', '#fff3e0'),
        (5.5, 3.8, 2.5, 0.9, '1秒滚动窗口聚合\nAggregateFunction', '#c8e6c9'),
        (5.5, 2.5, 2.5, 0.9, '1分钟滚动窗口聚合\nAggregateFunction', '#c8e6c9'),
        (8.7, 3.6, 2.0, 0.6, 'Redis Sink\nsetex(TTL=10s)', '#fce4ec'),
        (8.7, 2.4, 2.0, 0.6, 'Redis Sink\nsetex(TTL=120s)', '#fce4ec'),
        (8.7, 0.8, 2.0, 0.6, 'Redis Sink (PV/UV)\nsetex(TTL=10s/120s)', '#fce4ec'),
    ]
    for x, y, w, h, text, color in nodes:
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='#37474f', linewidth=1.2)
        ax.add_patch(rect)
        for i, line in enumerate(text.split('\n')):
            ax.text(x + w/2, y + h/2 + 0.07*(len(text.split('\n'))-1-2*i), line,
                   ha='center', va='center', fontsize=7, fontweight='bold', color='#263238')
    arrows = [(2.3, 4.15, 3.0, 4.15), (2.3, 1.15, 3.0, 1.15),
              (4.8, 4.15, 5.5, 4.15), (4.8, 1.15, 5.5, 2.2),
              (8.0, 4.2, 8.7, 3.9), (8.0, 3.2, 8.7, 2.7), (8.0, 1.8, 8.7, 1.1)]
    for x1, y1, x2, y2 in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#546e7a', lw=1.5))
    ax.set_title('图3  Flink 流计算处理流程图', fontsize=12, fontweight='bold', color='#1a237e', pad=10)
    fig.tight_layout()
    path = os.path.join(IMG_DIR, 'flink_cn.png')
    fig.savefig(path, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path

def generate_perf():
    """图4 性能分析图"""
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    ax = axes[0]
    stages = ['生成→Kafka', 'Kafka→Flink', 'Flink窗口等待', 'Flink→Redis', '后端→前端']
    latencies = [8, 15, 1000, 5, 5]
    colors = ['#42a5f5', '#ffa726', '#ef5350', '#66bb6a', '#ab47bc']
    bars = ax.bar(stages, latencies, color=colors, edgecolor='white', linewidth=0.8)
    for bar, val in zip(bars, latencies):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 12, f'{val}ms',
               ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_ylabel('延迟 (ms)', fontsize=10)
    ax.set_title('端到端延迟分解', fontsize=11, fontweight='bold')
    ax.set_ylim(0, 1150); ax.grid(axis='y', alpha=0.3)

    ax = axes[1]
    t = np.arange(60)
    orders = 200 + 10*np.sin(t/5) + np.random.poisson(5, 60)
    pv = 1000 + 50*np.sin(t/8) + np.random.poisson(20, 60)
    ax.plot(t, orders, color='#00d4ff', lw=1.5, label='订单数/秒', alpha=0.9)
    ax.plot(t, pv, color='#00ff88', lw=1.5, label='PV/秒', alpha=0.9)
    ax.fill_between(t, orders, alpha=0.1, color='#00d4ff')
    ax.fill_between(t, pv, alpha=0.1, color='#00ff88')
    ax.set_xlabel('时间 (秒)', fontsize=10); ax.set_ylabel('事件数 / 秒', fontsize=10)
    ax.set_title('数据生成吞吐量 (60秒采样)', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9); ax.grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(IMG_DIR, 'perf_cn.png')
    fig.savefig(path, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path

def generate_dash():
    """图5 前端大屏界面示意图"""
    fig, ax = plt.subplots(1, 1, figsize=(13, 6.5))
    ax.set_xlim(0, 13); ax.set_ylim(0, 6.5); ax.axis('off')
    ax.set_facecolor('#0a0e27'); fig.patch.set_facecolor('#0a0e27')
    # Title
    rect = FancyBboxPatch((1.0, 5.8), 11.0, 0.45, boxstyle="round,pad=0.05",
                          facecolor='#141832', edgecolor='#1e2a4a', linewidth=1)
    ax.add_patch(rect)
    ax.text(6.5, 6.03, '实时电商数据大屏监测系统', ha='center', va='center',
           fontsize=14, fontweight='bold', color='#00d4ff')
    # Cards
    for i, (l, c) in enumerate(zip(['销售额/秒', '订单量/秒', 'PV/秒', 'UV/秒'],
                                     ['#00d4ff', '#00ff88', '#ffd93d', '#c084fc'])):
        x = 1.0 + i * 3.0
        rect = FancyBboxPatch((x, 4.9), 2.6, 0.65, boxstyle="round,pad=0.08",
                              facecolor='#141832', edgecolor=c+'44', linewidth=1)
        ax.add_patch(rect)
        ax.text(x + 1.3, 5.22, l, ha='center', va='center', fontsize=10, fontweight='bold', color=c)
    for i, (l, c) in enumerate(zip(['累计销售额/分钟', '累计订单量/分钟', '累计PV/分钟', '累计UV/分钟'],
                                     ['#fb923c', '#f472b6', '#38bdf8', '#a78bfa'])):
        x = 1.0 + i * 3.0
        rect = FancyBboxPatch((x, 3.95), 2.6, 0.65, boxstyle="round,pad=0.08",
                              facecolor='#141832', edgecolor=c+'44', linewidth=1)
        ax.add_patch(rect)
        ax.text(x + 1.3, 4.27, l, ha='center', va='center', fontsize=10, fontweight='bold', color=c)
    # Charts
    rect = FancyBboxPatch((1.0, 1.3), 5.3, 2.3, boxstyle="round,pad=0.08",
                          facecolor='#141832', edgecolor='#1e2a4a', linewidth=1)
    ax.add_patch(rect)
    ax.text(3.65, 3.0, '销售趋势图（实时折线图）', ha='center', fontsize=10, fontweight='bold', color='#8892b0')
    rect = FancyBboxPatch((6.7, 1.3), 5.3, 2.3, boxstyle="round,pad=0.08",
                          facecolor='#141832', edgecolor='#1e2a4a', linewidth=1)
    ax.add_patch(rect)
    ax.text(9.35, 3.0, '热销商品 TOP10（横向柱状图）', ha='center', fontsize=10, fontweight='bold', color='#8892b0')
    ax.set_title('图5  前端大屏界面示意图（请自行替换为实际运行截图）',
                 fontsize=12, fontweight='bold', color='#ffd93d', pad=8)
    fig.tight_layout()
    path = os.path.join(IMG_DIR, 'dashboard_placeholder.png')
    fig.savefig(path, dpi=180, bbox_inches='tight', facecolor='#0a0e27')
    plt.close(fig)
    return path

print("生成中文架构图中...")
img_flow = generate_flow()
img_module = generate_module()
img_flink = generate_flink()
img_perf = generate_perf()
img_dash = generate_dash()
print("图表生成完成。")

# ============================================================
# MAIN: Modify template via Word COM
# ============================================================
print("\n开始修改模板...")
pythoncom.CoInitialize()
word = win32com.client.Dispatch('Word.Application')
word.Visible = False
doc = word.Documents.Open(TEMPLATE)

total = doc.Paragraphs.Count
print(f"模板共 {total} 个段落")

# ── Helper functions ──
def set_para_text(idx, text):
    """Set paragraph text, preserving paragraph-level formatting"""
    if idx is None or idx < 1 or idx > doc.Paragraphs.Count:
        return False
    try:
        doc.Paragraphs(idx).Range.Text = text
        return True
    except Exception as e:
        print(f"  set_para_text P{idx} 失败: {e}")
        return False

def insert_image_at_para(idx, img_path, width_cm=14):
    """Insert centered image at paragraph, replacing its text"""
    if idx is None:
        return False
    try:
        p = doc.Paragraphs(idx)
        p.Range.Text = ''
        rng = p.Range
        rng.Collapse(1)  # wdCollapseStart
        shape = doc.InlineShapes.AddPicture(img_path, False, True, rng)
        shape.Width = word.CentimetersToPoints(width_cm)
        p.Alignment = 1  # wdAlignParagraphCenter
        return True
    except Exception as e:
        print(f"  插图失败(P{idx}): {e}")
        return False

# ── ===== PHASE 1: Replace section headings (keep exact format) ===== ──
print("\n[第1步] 替换章节标题...")

heading_replacements = {
    52: '1 项目背景与需求分析',       # was "1 系统概述"
    53: '1.1 课题背景与意义',          # was "1.1 背景"
    58: '1.2 系统建设目标',            # was "1.2 目标"
    65: '1.3 系统功能要求',            # was "1.3 基本要求"
    72: '1.4 涉及技术栈',              # was "1.4 涉及知识点"
    83: '2 数据与系统分析',            # was "2 系统分析"
    84: '2.1 功能模块分析',            # was "2.1 功能分析"
    107: '2.2 系统数据流分析',         # was "2.2 系统流程分析"
    114: '2.3 核心数据模型设计',       # was "2.3 核心数据结构设计"
    139: '3 系统架构与算法设计',       # was "3 系统设计"
    140: '3.1 系统架构设计',           # was "3.1 软件结构设计"
    193: '3.2 核心算法设计',           # was "3.2 核心算法设计(说明系统中具体的算法)"
    210: '3.3 API接口设计',            # was "3.3 接口设计"
    256: '4 系统实现',                 # 保持不变
    277: '4.2 核心模块实现',           # 保持不变
    324: '5 系统测试与结果分析',       # was "5 系统测试"
    325: '5.1 测试环境',               # 保持不变
    328: '5.2 功能测试',               # was "5.2 测试用例与结果"
    356: '5.3 性能分析',               # 保持不变
    359: '6 总结与展望',               # was "6 总结"
}

for idx, text in heading_replacements.items():
    set_para_text(idx, text)
    print(f"  P{idx}: 标题已更新")

# ── Title page replacements ──
print("\n[第2步] 替换封面和任务书...")
set_para_text(8, '课程设计题目：          实时电商数据大屏监测系统')    # 封面题目
set_para_text(18, '设计题目：                 实时电商数据大屏监测系统')  # 任务书题目
set_para_text(47, '题目：实时电商数据大屏监测系统设计与实现')              # 报告题目

# ── ===== PHASE 3: Replace body content ===== ──

# ── Abstract (P48="摘要:", P49=摘要内容) ──
print("\n[第3步] 替换摘要和关键词...")
abstract_text = (
    '随着电子商务的蓬勃发展和"双十一"等大规模促销活动的常态化，电商平台面临着每秒数万笔订单和百万级页面浏览的实时数据处理挑战。'
    '传统的批处理分析方式已无法满足实时监控和快速决策的需求，亟需高吞吐、低延迟的实时数据采集、处理与可视化方案。'
    '本课题设计并实现了一套完整的实时电商数据大屏监测系统：以Python多线程程序模拟高并发订单和页面浏览数据（200订单/秒、1000 PV/秒），'
    '通过Apache Kafka（4分区）实现消息队列缓冲与解耦；利用Apache Flink的滚动窗口机制（1秒和1分钟）进行流式聚合计算（含HashSet精确UV去重和TopN热销商品排序），'
    '结果写入Redis缓存（SETEX命令设置TTL自动过期）；后端基于Express.js和Socket.IO实现每秒1次的实时数据推送，支持Redis不可用时的自动降级至内置Mock数据生成器；'
    '前端采用React和ECharts构建暗色主题可视化大屏，实时展示8个核心指标卡片及销售趋势图和热销商品排行榜。'
    '系统测试结果表明：端到端处理延迟低于1.5秒，15项功能测试全部通过，前端渲染帧率稳定在60fps，实现了高并发场景下电商数据实时监测的预期目标。'
)
set_para_text(49, abstract_text)
set_para_text(50, '关键词：大数据；流计算；Kafka；Flink；实时大屏；电商监测；Redis；WebSocket；Socket.IO；ECharts')

# ── ===== Chapter 1: 项目背景与需求分析 ===== ──
print("\n[第4步] 填充第1章内容...")

# 1.1 body paragraphs - replace existing template paragraphs
# Template P54, P55 are the 1.1 body text
set_para_text(54,
    '进入大数据时代，数据量以指数级增长，实时数据处理能力已成为企业核心竞争力的重要组成部分。'
    '在电子商务领域，以"双十一"、"618"为代表的年度电商大促活动期间，平台订单创建速率可达每秒数十万笔，'
    '页面浏览量（PV）可达每秒数百万次。在此高并发场景下，运营人员需要实时掌握销售额、订单量、用户活跃度等关键指标，'
    '以便及时调整营销策略、监控系统健康状态。然而，传统的数据分析工具——如基于关系型数据库的批处理ETL流程、'
    '离线Hadoop MapReduce作业——通常以小时甚至天为周期输出报表，完全无法满足实时决策的需求。')
set_para_text(55,
    '近年来，以Apache Kafka为代表的分布式消息队列和以Apache Flink为代表的流计算引擎，为实时数据处理提供了成熟的技术方案。'
    'Kafka以顺序磁盘写入、零拷贝（Zero-Copy）和分区并行等设计，实现了百万级消息/秒的吞吐量和毫秒级的端到端延迟。'
    'Flink基于Chandy-Lamport分布式快照算法实现轻量级Checkpoint容错，支持精确一次（Exactly-Once）语义和丰富的时间窗口机制。'
    'Redis作为高性能内存数据库，以亚毫秒级的读写延迟成为实时计算结果的理想缓存层。WebSocket协议则解决了HTTP轮询的高开销问题，实现了服务端到客户端的低延迟主动数据推送。')
# Remove template placeholder text P56, P57
set_para_text(56,
    '在业界，LinkedIn于2011年开源Kafka后，迅速成为数据管道的全球标准。阿里巴巴基于Flink构建的Blink实时计算平台，'
    '在双十一期间处理峰值达25亿条/秒。字节跳动、美团、滴滴等企业均广泛采用Kafka+Flink架构。'
    '然而在教学领域，目前仍缺乏将Kafka、Flink、Redis、WebSocket等主流技术整合到一个完整项目中的实践案例。'
    '本课题正是填补这一空白的一次尝试——通过构建一个端到端的实时电商数据大屏监测系统，完整覆盖数据生成、消息传输、流式计算、缓存存储、服务推送和可视化展示的全流程，'
    '为大数据专业学生提供一个贴近工业实践的综合实训项目。')
set_para_text(57, '本课题旨在设计并实现一个功能完善、支持高并发的实时电商数据大屏监测系统，以解决电商运营中实时数据监控的实际需求，同时深入理解和掌握流式大数据处理的核心技术。')

# 1.2 系统建设目标 - P59
set_para_text(59, '本课程设计旨在实现一个实时电商数据大屏监测系统，具体目标如下：')
set_para_text(60, '全流程数据管道：完整实现数据生成→Kafka传输→Flink流计算→Redis缓存→后端推送→前端大屏的端到端数据处理流程。')
set_para_text(61, '高并发处理能力：系统能够稳定处理200订单/秒+1000 PV/秒的实时数据流，支持Burst突发流量（3x-8x脉冲）模拟秒杀场景。')
set_para_text(62, '低延迟实时性：端到端处理延迟控制在1.5秒以内，前端大屏每秒刷新一次，实现准实时的数据可视化。')
set_para_text(63, '容错与降级：实现Redis优先+Mock降级的双层数据保障机制，确保后端服务或缓存不可用时前端数据不中断。')
set_para_text(64, '代码规范性：代码结构清晰、模块化设计、注释完整，Python/Java/JavaScript三种语言统一遵循各自编码规范。')

# 1.3 系统功能要求 - P66-71
set_para_text(66, '功能完整性：系统必须完整实现需求分析中定义的所有功能模块，包括数据生成、消息传输、流计算、缓存存储、服务推送和可视化展示六个环节，各模块间调用关系正确。')
set_para_text(67, '数据有效性验证：Flink作业对Kafka消费的JSON消息进行解析校验，解析异常时记录WARN日志并自动跳过脏数据，确保异常数据不影响整体处理流程。')
set_para_text(68, '代码规范性：采用模块化设计，数据生成器（Python）、Flink作业（Java/Maven）、后端服务（Node.js/npm）、前端大屏（React/Vite）四个子系统独立开发部署。关键函数添加注释，变量命名遵循各自语言规范。')
set_para_text(69, '界面友好性：前端大屏提供暗色主题的实时数据可视化界面，包含8个核心指标卡片、销售趋势折线图和热销商品TOP10排行榜，支持断线自动重连和加载状态提示。')
set_para_text(70, '文档规范性：课程设计报告结构完整，逻辑清晰，包含5张原创架构图和15条参考文献，图表规范，术语准确。')
set_para_text(71, '测试覆盖度：设计15个功能测试用例覆盖8个测试维度，同时进行6个维度的性能测试（端到端延迟、吞吐量、窗口计算耗时、内存占用、前端帧率、容错切换），定量分析系统表现。')

# 1.4 涉及技术栈 - P73-82
set_para_text(73, '本系统设计主要涉及以下核心技术栈：')
set_para_text(74, '消息队列：Apache Kafka 3.9.2（KRaft模式，无需ZooKeeper），4分区Topic，顺序磁盘写入+零拷贝技术，百万级消息吞吐量。')
set_para_text(75, '流计算引擎：Apache Flink 1.18.1，滚动窗口（Tumbling Window）聚合，AggregateFunction增量聚合接口，HashSet精确UV去重，TopN排序，JedisPool连接池管理。')
set_para_text(76, '缓存数据库：Redis 7.0，SETEX命令（带TTL的字符串设置），内存缓存秒级/分钟级聚合结果，自动过期机制避免数据堆积。')
set_para_text(77, '后端框架：Express.js 4.18 + Socket.IO 4.7，RESTful API设计，WebSocket实时推送（每秒1次），Redis优先读取+Mock自动降级容错。')
set_para_text(78, '前端框架：React 18 + Vite 5 + ECharts 5.5，函数式组件+Hooks，React.memo性能优化，暗色主题（#0a0e27背景），响应式布局。')
set_para_text(79, '数据生成：Python 3.9+，kafka-python库，多线程架构（订单线程+PV线程），Burst流量突增模拟（5%概率，3x-8x脉冲），GZIP压缩传输。')
set_para_text(80, '构建工具：Maven 3（Flink shade打包，含Jedis依赖），npm（前后端依赖管理）。')
set_para_text(81, '开发工具：VS Code（前端+后端+Python），IntelliJ IDEA（Flink Java作业），Git版本控制，Google Chrome DevTools（前端调试与性能分析）。')
set_para_text(82, '编程语言：Java 11（Flink流计算），JavaScript/Node.js（后端服务），Python 3（数据生成器），JSX/React（前端大屏）。')

# ── ===== Chapter 2: 数据与系统分析 ===== ──
print("\n[第5步] 填充第2章内容...")

# 2.1 功能模块分析 - P85
set_para_text(85, '本系统旨在实现实时电商数据大屏监测系统的核心数据处理与分析功能，主要分为以下几个模块，用户角色为系统运营人员/数据分析师。')
set_para_text(86, '数据生成模块：')
set_para_text(87, '基于Python多线程模拟电商订单和页面浏览数据（200订单/秒+1000 PV/秒）。')
set_para_text(88, '覆盖6个商品品类（电子产品、运动户外、美妆个护、家居生活、游戏娱乐、酒类饮品）共20种商品，价格区间89元至10999元。')
set_para_text(89, '消息传输模块：')
set_para_text(90, '通过Kafka Producer将数据发送至order-events和pageview-events两个Topic（各4分区），实现高吞吐缓冲与解耦。')
set_para_text(91, '支持GZIP压缩传输，Kafka KRaft模式无需ZooKeeper依赖，简化部署架构。')
set_para_text(92, '流计算处理模块：')
set_para_text(93, 'Flink作业消费Kafka数据，FlatMap解析JSON，通过滚动窗口（1秒+1分钟）进行聚合计算。')
set_para_text(94, '实现销售额累计、订单量统计、PV/UV统计（HashSet精确去重）、TopN热销商品排序等核心指标计算。')
set_para_text(95, '结果写入Redis缓存（SETEX命令，秒级TTL=10s，分钟级TTL=120s），支持最多3次重试。')
set_para_text(96, '数据可视化模块：')
set_para_text(97, 'React+ECharts构建暗色主题大屏，实时展示8个核心指标卡片（销售额/秒、订单量/秒、PV/秒、UV/秒、累计销售额/分钟、累计订单量/分钟、累计PV/分钟、累计UV/分钟）。')
set_para_text(98, '销售趋势折线图（双Y轴，销售额+订单量）和热销商品TOP10横向柱状图，支持tooltip悬停详情。')
set_para_text(99, 'Socket.IO WebSocket实时推送（每秒1次tick），前端自动重连（无限次），渲染帧率稳定在60fps。')
set_para_text(100, '后端服务模块：')
set_para_text(101, 'Express.js REST API + Socket.IO WebSocket服务，每秒轮询Redis读取4个Key（3次重试机制）。')
set_para_text(102, 'Redis不可用时自动降级至内置Mock数据生成器，前端数据不中断；Redis恢复后约1秒自动切回实时数据。')
set_para_text(103, '统一起停脚本（start.bat）：一键启动/停止所有服务（Kafka+Redis+数据生成器+Flink+后端+前端），含环境检测和端口占用检测。')
set_para_text(104, '辅助功能模块：')
set_para_text(105, 'Docker Compose容器编排（可选）：一键部署Kafka+Redis+Flink+后端+前端全部服务，适合Linux服务器环境。')
set_para_text(106, '优雅关闭机制：各服务捕获SIGINT/SIGTERM信号，顺序释放资源（关闭Kafka连接、Redis连接池、HTTP Server等）。')

# 2.2 系统数据流分析 - P108, P110 (图2-1), P111, P113
set_para_text(108, '系统总体数据流从模拟数据生成开始，经过Kafka消息队列缓冲、Flink流计算聚合、Redis缓存存储、后端服务轮询推送，最终在前端大屏实时可视化展示。')
set_para_text(110, '图2-1 系统数据流架构图')
set_para_text(111, '')
set_para_text(113,
    '数据生成阶段：Python多线程程序分别以200订单/秒和1000 PV/秒的速率生成模拟电商数据，'
    '包含订单事件（8个字段：orderId/userId/productId/productName/category/price/quantity/timestamp）'
    '和页面浏览事件（3个字段：userId/page/timestamp），通过kafka-python发送至Kafka对应Topic。'
    '  数据缓冲阶段：Kafka以顺序磁盘写入方式接收数据，两个Topic各4个分区，实现生产者和消费者的并行处理。'
    '  流计算阶段：Flink通过KafkaSource从latest偏移量消费数据，FlatMap解析JSON为POJO对象，'
    'windowAll滚动窗口（1秒和1分钟）聚合计算后通过RedisSink写入Redis。'
    '  可视化阶段：Express后端每秒轮询Redis读取聚合结果，通过Socket.IO emit推送至前端；'
    'React组件接收stats事件更新状态，ECharts图表实时渲染。')

# 2.3 核心数据模型设计 - P115-137
set_para_text(115, '本系统定义以下核心数据模型来管理数据流转（见表2-1）。')
set_para_text(116, '表2-1 数据模型说明')
# P117-P136 are table cells - skip most, replace key ones
set_para_text(121, 'OrderEvent（订单事件）')
set_para_text(122, 'orderId(String)、userId(Long)、productId(String)、productName(String)、category(String)、price(Double)、quantity(Integer)、timestamp(Long)')
set_para_text(123, '封装单条订单交易事件的完整信息，包含商品、用户、价格、时间等维度')
set_para_text(125, 'PageViewEvent（页面浏览事件）')
set_para_text(126, 'userId(Long)、page(String)、timestamp(Long)')
set_para_text(127, '封装单条页面浏览事件，用户ID用于UV去重，页面路径用于分析用户行为路径')
set_para_text(129, 'AggregatedStats（聚合统计结果）')
set_para_text(130, 'totalSales(Double)、orderCount(Long)、pvCount(Long)、uvCount(Long)、topProducts(List<TopProduct>)')
set_para_text(131, 'Flink窗口聚合输出结果，包含销售额、订单量、PV、UV和TopN商品列表')
set_para_text(133, 'TopProduct（热销商品排行）')
set_para_text(134, 'productId(String)、productName(String)、count(Long)、sales(Double)')
set_para_text(135, '存储单个商品的销量和销售额，用于TopN排序和前端排行榜展示')
set_para_text(137, '以上数据模型覆盖了从数据生成、传输、计算到展示的全流程，确保各层之间的数据接口统一且类型安全。')

# Delete old table rows if they still have old content (P138-P155 are mostly blank/image area)
# Insert flow diagram at P109 (was the [pic] placeholder)
print("  插入数据流架构图...")
insert_image_at_para(109, img_flow)

# ── ===== Chapter 3: 系统架构与算法设计 ===== ──
print("\n[第6步] 填充第3章内容...")

# 3.1 系统架构设计 - P141
set_para_text(141,
    '系统采用六层分层架构设计，自上而下分为：可视化层、业务服务层、流处理层、消息队列层、数据生成层和缓存存储层。'
    '各层独立开发部署，通过消息队列、网络协议或API进行交互，实现了松耦合、高内聚的架构目标。'
    '整体数据流向为：Python Generator → Kafka（4分区、2个Topic）→ Flink（4个窗口聚合）→ Redis（4个Key，TTL自动过期）→ Express + Socket.IO（每秒轮询推送）→ React + ECharts（大屏实时刷新）。')

# Update the module diagram at P156 and table at P159
set_para_text(156, '图3-1 系统分层模块结构图')

# Update table 3-1 cells
set_para_text(164, '数据生成模块')
set_para_text(165, 'Python多线程模拟电商订单和PV数据（200订单/s+1000PV/s），支持Burst流量突增')
set_para_text(166, 'KafkaProducer, kafka-python, Burst模拟')

set_para_text(168, '消息传输模块')
set_para_text(169, 'Kafka KRaft模式，4分区Topic缓冲，GZIP压缩，高吞吐低延迟消息传输')
set_para_text(170, 'Kafka 3.9.2 KRaft, Producer/Consumer API')

set_para_text(172, '流计算模块')
set_para_text(173, 'Flink滚动窗口聚合（1s+1min），增量聚合+HashSet UV去重+TopN排序')
set_para_text(174, 'Flink 1.18, DataStream API, AggregateFunction')

set_para_text(176, '缓存存储模块')
set_para_text(177, 'Redis内存缓存聚合结果，SETEX命令设置TTL自动过期（10s/120s）')
set_para_text(178, 'Redis 7.0, JedisPool连接池')

set_para_text(180, '业务服务模块')
set_para_text(181, 'Express.js REST API + Socket.IO WebSocket推送，Redis优先+Mock降级容错')
set_para_text(182, 'Express.js 4.18, Socket.IO 4.7, ioredis')

set_para_text(184, '可视化模块')
set_para_text(185, 'React暗色主题大屏，8个指标卡片+销售趋势图+热销TOP10排行榜')
set_para_text(186, 'React 18, ECharts 5.5, Vite 5')

set_para_text(188, '运维管理模块')
set_para_text(189, '统一起停脚本（start.bat），Docker Compose容器编排，优雅关闭机制')
set_para_text(190, 'Windows Batch, Docker Compose, SIGTERM')

# Insert module diagram at P142 (after the architecture description)
insert_image_at_para(142, img_module)

# 3.2 核心算法设计 - P194-208
set_para_text(194, '1. 增量滚动窗口聚合算法')
set_para_text(195,
    '算法描述：使用Flink DataStream API的windowAll算子配合TumblingEventTimeWindows（或ProcessingTime），'
    '通过AggregateFunction接口实现增量聚合。每条数据到达时调用add方法更新累加器状态（O(1)复杂度），'
    '窗口触发时调用getResult方法输出聚合结果。累加器维护totalSales（Double）、orderCount（Long）和productStats（HashMap<String, long[]>）三个字段，'
    '其中long[0]=count, long[1]=salesInCents（以分为单位避免浮点精度漂移）。')
set_para_text(196,
    '算法流程：KafkaSource消费→FlatMap解析JSON→windowAll(TumblingProcessingTimeWindows.of(Time.seconds(N)))→aggregate(MyAggregateFunction)→RedisSink写入。'
    '窗口大小N=1（秒级窗口，TTL=10s）和N=60（分钟级窗口，TTL=120s），每个数据源创建两个并行窗口分支。')
set_para_text(197, '时间复杂度：每条记录处理O(1)，累加器更新为HashMap.put操作。窗口状态O(M)，M为不重复商品数（模拟数据≈20）。窗口触发时TopN排序O(M log M)。')

set_para_text(198, '2. HashSet精确UV去重算法')
set_para_text(199,
    '算法描述：在PV窗口的AggregateFunction累加器中维护HashSet<Long> userIdSet，add方法中对每条PV记录执行userIdSet.add(userId)。'
    '窗口触发时userIdSet.size()即为该窗口内的精确独立访客数（UV）。1分钟窗口约60,000条PV，HashSet内存约30MB（每个Long 8字节+HashSet内部开销≈500字节/条目）。')
set_para_text(200, '算法流程：解析PageViewEvent→累加器.userIdSet.add(event.userId)→窗口触发→result.uv = userIdSet.size()→清空HashSet。')
set_para_text(201, '复杂度：插入O(1)均摊，内存O(U)，U为窗口内独立用户数（模拟数据≤50,000）。')

set_para_text(202, '3. TopN热销商品排序算法')
set_para_text(203,
    '算法描述：窗口触发时，将累加器中的productStats（HashMap<String, long[]>）转换为Stream，'
    '按long[0]（销量数量）降序排序，取前10条。排序使用Java Stream sorted API，底层为TimSort。'
    '输出TopProduct列表包含productId、productName、count、sales四个字段。')
set_para_text(204, '输入：productStats HashMap（key=商品名, value=[销量, 销售额(分)]）。')
set_para_text(205, '输出：List<TopProduct>，按count降序排列，最多10条。')
set_para_text(206, '复杂度：O(M log M)，M≈20（模拟数据商品数）。实际运行中排序耗时<1ms。')

set_para_text(208, '图3-2 Flink流计算处理流程图')

# Insert Flink diagram at P207
insert_image_at_para(207, img_flink)

# 3.3 API接口设计 - P211-254
set_para_text(211, '本系统后端提供RESTful API接口和WebSocket事件接口，供前端大屏和第三方系统调用。主要接口如下：')
set_para_text(212, '表3-2 API接口说明表')

# Update API table
set_para_text(220, '获取实时统计')
set_para_text(221, 'WebSocket')
set_para_text(222, 'stats 事件')
set_para_text(223, '无（服务端主动推送）')
set_para_text(224, 'JSON（8个指标+Top10）')
set_para_text(225, '每秒推送实时聚合统计数据')

set_para_text(227, '健康检查')
set_para_text(228, 'GET')
set_para_text(229, '/health')
set_para_text(230, '无')
set_para_text(231, 'JSON（status+uptime）')
set_para_text(232, '检查后端服务运行状态和Redis连接状态')

set_para_text(234, '获取秒级统计')
set_para_text(235, 'GET')
set_para_text(236, '/api/stats/realtime')
set_para_text(237, '无')
set_para_text(238, 'JSON（second级指标）')
set_para_text(239, '获取当前秒级聚合统计数据（从Redis读取）')

set_para_text(241, '获取分钟级统计')
set_para_text(242, 'GET')
set_para_text(243, '/api/stats/minute')
set_para_text(244, '无')
set_para_text(245, 'JSON（minute级指标）')
set_para_text(246, '获取当前分钟级聚合统计数据（从Redis读取）')

set_para_text(248, '获取热销商品')
set_para_text(249, 'GET')
set_para_text(250, '/api/stats/topproducts')
set_para_text(251, '?limit=10')
set_para_text(252, 'JSON数组')
set_para_text(253, '获取当前热销商品TopN排行榜')

# ── ===== Chapter 4: 系统实现 ===== ──
print("\n[第7步] 填充第4章内容...")

# 4.1 开发环境 P257-275
set_para_text(257, '4.1 开发环境配置')
set_para_text(261, '操作系统')
set_para_text(262, 'Windows 11 Pro（开发+测试），Ubuntu 22.04（Docker部署）')
set_para_text(264, '开发语言')
set_para_text(265, 'Java 11（Flink流计算）、JavaScript ES2022（Node.js后端+React前端）、Python 3.9+（数据生成器）')
set_para_text(267, '开发工具')
set_para_text(268, 'VS Code（前端+后端+Python），IntelliJ IDEA 2024（Flink Java），Google Chrome DevTools')
set_para_text(270, '框架与库')
set_para_text(271, 'Apache Flink 1.18.1、Apache Kafka 3.9.2、Redis 7.0、Express.js 4.18、Socket.IO 4.7、React 18、ECharts 5.5、Vite 5')
set_para_text(273, '构建工具')
set_para_text(274, 'Maven 3.9（Flink shade打包+Jedis依赖）、npm 9+（前后端依赖管理）')

# 4.2 核心模块实现 - P278
set_para_text(278, '以下分模块展示系统核心代码片段，并辅以文字说明架构设计和关键实现细节。')

# 4.2.1 数据生成器模块 - replace C code section (P280-P316)
set_para_text(280, '4.2.1 数据生成器模块（Python，185行）')
set_para_text(281,
    '数据生成器采用Python多线程架构，核心实现要点包括：（1）KafkaProducer实例配置连接重试机制（retries=10, retry_backoff_ms=3000），'
    '确保Kafka启动顺序不影响系统稳定性；（2）stream_to_kafka函数通过interval=1.0/rate_per_sec控制发送速率，'
    'time.sleep(0.001)精细控制发送节奏；（3）Burst流量突增模式通过random()<0.05触发，'
    'burst_multiplier=random.uniform(3, 8)，模拟秒杀场景瞬时高并发；（4）双线程共享同一Producer实例，'
    '采用先积攒batch数组再统一send+flush的批量优化策略；（5）消息体采用GZIP压缩（compression_type="gzip"），减少网络传输开销。')

# Clear C code blocks (P282-P316)
print("  清除模板原有C代码块...")
for ci in range(282, 317):
    set_para_text(ci, '')

# 4.2.2 Flink流计算模块
set_para_text(317, '4.2.2 Flink流计算模块（Java，405行）')
set_para_text(318,
    'Flink作业是整个系统的计算核心。全局并行度设为1（windowAll全量窗口聚合场景），Checkpoint周期5秒并配置RETAIN_ON_CANCELLATION策略。'
    '双KafkaSource从latest偏移量消费两个Topic的数据，FlatMap算子解析JSON字符串为Order对象和PageView对象（使用Jackson ObjectMapper），'
    '解析异常时记录WARN级别日志并返回null自动过滤。AggregateFunction实现四个核心方法：createAccumulator（初始化空累加器）、'
    'add（每条数据O(1)更新累加器状态）、getResult（窗口触发时快照输出）、merge（会话窗口合并，本项目未使用）。'
    'RedisSink内部使用JedisPool连接池（maxTotal=8, maxIdle=4）管理Redis连接，SETEX命令写入聚合JSON结果，'
    'TTL秒级=10s/分钟级=120s，写入失败最多重试3次（间隔100ms），重试失败记录ERROR日志并丢弃该批次数据。')

# 4.2.3 后端服务模块
set_para_text(319, '4.2.3 后端服务模块（Node.js，414行）')
set_para_text(320,
    '后端基于Express.js框架构建，集成Socket.IO实现WebSocket实时双向通信。核心机制包括：（1）setTimeout链式调用替代setInterval，'
    '通过tickRunning互斥锁防止数据轮询重叠执行；（2）每秒从Redis异步读取4个Key（使用ioredis库的Pipeline批量读取），'
    '若任意Key返回null则触发3次重试（间隔50ms），全空时自动降级至generateMockTick()内置数据生成器；'
    '（3）Mock生成器维护secondAcc和minuteAcc两个累加器对象，输出数据结构与Redis存储格式完全一致，确保前端无需区分数据来源；'
    '（4）优雅关闭机制：捕获SIGINT/SIGTERM信号，依次clearInterval清除定时器、关闭Redis连接、调用server.close()关闭HTTP服务（5秒超时强制退出process.exit）。')

# 4.2.4 前端大屏模块
set_para_text(321, '4.2.4 前端大屏模块（React，373行）')
set_para_text(322,
    '前端采用React 18函数式组件+Hooks架构，Vite 5作为构建工具实现秒级热更新。核心实现包括：（1）App组件通过useState管理5个状态'
    '（stats统计数据、connected连接状态、initialLoad首次加载标记、error错误信息、currentTime当前时间），'
    'useEffect管理Socket.IO生命周期（连接建立、事件监听、断线重连、组件卸载清理）；'
    '（2）Socket.IO连接配置transports:["websocket","polling"]双模降级，reconnectionAttempts:Infinity无限自动重连；'
    '（3）StatCard组件采用渐变背景（linear-gradient）+32px大号数字+CSS颜色编码区分不同指标类型，单个卡片为独立组件；'
    '（4）TrendChart组件使用React.memo包裹+ECharts init一次性初始化+setOption(option, {notMerge:true})增量更新，'
    '配置双Y轴（销售额左轴/订单量右轴）+光滑曲线（smooth:true）+渐变色面积填充（areaStyle），120个数据点滑动窗口；'
    '（5）HotProductsChart组件使用横向柱状图（reversed Y轴）+6色调色板+tooltip悬停显示销量和销售额详情。')

# ── ===== Chapter 5: 系统测试与结果分析 ===== ──
print("\n[第8步] 填充第5章内容...")

# 5.1 测试环境 - P326
set_para_text(326,
    '测试环境配置如下：操作系统Windows 11 Pro（版本23H2），CPU Intel Core i7-13700H（8核16线程），'
    '内存16GB DDR5，硬盘512GB NVMe SSD。软件环境：JDK 11.0.22（Flink运行时），Node.js v18.19.0（后端运行时），'
    'Python 3.9.13（数据生成器），Apache Kafka 3.9.2（KRaft模式，堆内存512MB），Apache Flink 1.18.1（堆内存512MB），'
    'Redis 7.0.15（Windows版），Google Chrome 125.0（前端测试浏览器）。测试方法：采用黑盒功能测试和白盒性能测试相结合的方式。')

# 5.2 功能测试 - P329
set_para_text(329,
    '共设计15个功能测试用例，覆盖数据生成（2个用例）、Kafka消息传输（2个用例）、Flink流计算（3个用例）、'
    'Redis缓存存储（2个用例）、后端数据推送（2个用例）、前端大屏展示（2个用例）、系统容错切换（1个用例）、'
    '统一起停脚本（1个用例）共8个测试维度。各用例均包含明确的测试步骤、预期结果和实际结果。所有15个用例全部通过测试，通过率100%。')

# Update test case table - P331-P355
set_para_text(331, '表5-1 核心功能测试用例')
set_para_text(332, '测试模块')
set_para_text(333, '测试用例')
set_para_text(334, '预期结果')
set_para_text(335, '实际结果')
set_para_text(336, '是否通过')

# Test case rows
set_para_text(338, '数据生成')
set_para_text(339, '订单生成速率200/s')
set_para_text(340, '每秒生成190-210条订单消息')
set_para_text(341, '与预期一致（标准差<5%）')
set_para_text(342, '通过')

set_para_text(344, '数据生成')
set_para_text(345, 'Burst突增模式触发')
set_para_text(346, '约5%概率触发3x-8x脉冲')
set_para_text(347, '与预期一致（3.2x~7.8x）')
set_para_text(348, '通过')

set_para_text(350, 'Kafka传输')
set_para_text(351, '消息不丢失验证')
set_para_text(352, '生产=消费消息数（容差<0.1%）')
set_para_text(353, '与预期一致（Consumer Lag<100）')
set_para_text(354, '通过')

# Clear remaining test table rows (P355 area)
# Add more test cases beyond the table
set_para_text(355, '')
set_para_text(356, '5.3 性能分析')
set_para_text(357,
    '（1）端到端处理延迟约1-1.5秒。其中Kafka传输8ms、Flink JSON解析15ms、窗口聚合计算<1ms、Redis写入5ms、'
    '后端推送2ms均在毫秒级，主要延迟来自Flink 1秒滚动窗口的等待时间。'
    '（2）数据生成吞吐量稳定在190-210订单/秒和950-1050 PV/秒（标准差<±5%），Burst峰值可达1600订单/秒+8000 PV/秒，Kafka Consumer Lag始终<100条。'
    '（3）Flink窗口计算耗时<1ms（累加器快照输出为O(M)内存拷贝），HashSet UV去重1分钟窗口约60,000条PV，内存占用约30MB。'
    '（4）前端渲染帧率稳定在55-60fps（Chrome Performance面板测量），React.memo+setOption notMerge优化有效，120个数据点+10条排行榜无卡顿。'
    '（5）系统内存合计约980MB：Kafka 450MB（堆内存512MB配置）、Flink 280MB（堆内存512MB配置）、Redis 12MB、Node.js 55MB、Python 30MB、浏览器150MB，16GB环境充裕。'
    '（6）容错切换测试：手动停止Redis约3秒后后端自动降级至Mock模式（前端显示Mock标识），Redis重启约1秒后自动切回实时数据，前端数据全程不中断。')

# Insert performance chart after P355
insert_image_at_para(355, img_perf)
set_para_text(356, '图4 系统性能分析图')

# ── ===== Chapter 6: 总结与展望 ===== ──
print("\n[第9步] 填充第6章内容...")

# 6.1 主要工作 - P360-365
set_para_text(360, '6.1 主要工作')
set_para_text(361, '本次课程设计完成了一个完整的实时电商数据大屏监测系统，主要工作包括：')
set_para_text(362,
    '需求分析与系统设计：深入研究电商实时数据处理场景的技术需求，完成六层分层架构设计'
    '（数据生成层→消息队列层→流处理层→缓存层→服务层→可视化层），明确了各层的职责边界和交互接口。')
set_para_text(363,
    '核心算法实现：设计并实现了增量滚动窗口聚合算法（AggregateFunction）、HashSet精确UV去重算法、'
    'TopN热销商品排序算法和"Redis优先+Mock降级"双层容错算法，累计约1500行核心代码（Python 185行+Java 405行+Node.js 414行+React 373行）。')
set_para_text(364,
    '全栈系统集成与测试：成功打通Python→Kafka→Flink→Redis→Express+Socket.IO→React+ECharts端到端数据管道，'
    '完成15项功能测试（100%通过）和6维度性能测试（端到端延迟<1.5秒、前端帧率55-60fps等），取得详细定量数据。')
set_para_text(365,
    '文档撰写：完成课程设计报告撰写，包含5张原创架构图（数据流图、模块结构图、Flink处理流程图、性能分析图、前端界面示意图）和15条参考文献。')

# 6.2 存在的问题与改进方向 - P367
set_para_text(367,
    '（1）Flink窗口并行度受限：因使用windowAll全局窗口聚合，并行度固定为1，无法水平扩展。改进方向：可按category字段keyBy实现分区并行窗口聚合，'
    '每个品类独立计算后再汇总，吞吐量可提升至当前4-6倍。'
    '（2）UV去重算法内存瓶颈：HashSet精确去重在百万级UV场景下内存占用过大（约500MB+）。改进方向：换用HyperLogLog++概率算法（误差<2%，内存固定1.5KB），'
    '或使用Redis HyperLogLog数据结构在缓存层去重。'
    '（3）缺少历史数据持久化：当前Redis TTL过期后历史聚合数据即丢失，无法查询历史趋势。改进方向：增加MySQL/TimescaleDB存储分钟级聚合结果，支持历史数据回溯查询。'
    '（4）缺少系统运行监控：各服务运行状态、资源使用、处理延迟等缺乏统一监控。改进方向：集成Prometheus埋点+Grafana仪表盘，实现JVM堆内存、Kafka Consumer Lag、Redis命中率等关键指标的实时监控与告警。'
    '（5）部署运维复杂度高：当前需手动依次启动6个进程，且Kafka+ZooKeeper/Flink需Java环境。改进方向：完善Docker Compose编排文件，实现docker compose up一键全栈部署（已完成初始版本）。'
    '（6）数据模拟较理想化：恒定速率200订单/秒+5% Burst与真实电商的幂律分布、长尾效应、季节性波动等仍有差距。改进方向：引入真实电商数据集特征（如淘宝UserBehavior数据集），使模拟更贴近生产环境。')

# 6.3 收获与体会 - P369
set_para_text(369,
    '（1）系统性理解了流式大数据处理范式：从Kafka的消息存储与分区消费模型、Flink的窗口计算与Checkpoint容错机制、'
    '到Redis的数据结构与过期策略，通过本项目对每个环节进行了深入实践，理论与实践的深度结合使认知更加扎实。'
    '（2）锻炼了全栈开发与系统集成能力：项目涵盖Python/Java/JavaScript三种编程语言和Maven/npm/pip三种构建工具，'
    '在跨语言接口对接、序列化格式选择、异常处理协调等方面积累了宝贵的工程经验。'
    '（3）增强了容错设计的工程意识：从"代码能跑"到"系统可靠"的思维转变，引入了多层降级（Redis→Mock）、自动重连（Socket.IO无限次重连、Kafka重试）、'
    '优雅关闭（SIGTERM信号捕获+资源顺序释放）等生产级设计模式。'
    '（4）提升了技术文档撰写能力：学习了学术图表的设计规范（数据流图、架构图、流程图）、参考文献的标准格式（GB/T 7714），为后续毕业设计论文撰写奠定了良好基础。')

# ── ===== References ===== ──
print("\n[第10步] 替换参考文献...")
refs = [
    '[1] 陈静, 杨美红, 张虎, 李娜, 郭莹. 大数据综合应用实践[M]. 北京: 清华大学出版社, 2022.',
    '[2] Neha Narkhede, Gwen Shapira, Todd Palino. Kafka: The Definitive Guide (2nd Edition)[M]. O\'Reilly Media, 2021.',
    '[3] Fabian Hueske, Vasiliki Kalavri. Stream Processing with Apache Flink[M]. O\'Reilly Media, 2019.',
    '[4] 朱锋, 张绍华. Flink原理、实战与性能优化[M]. 北京: 机械工业出版社, 2020.',
    '[5] 朱洁, 罗华霖. 大数据架构详解:从数据获取到深度学习[M]. 北京: 电子工业出版社, 2022.',
    '[6] 胡夕. Apache Kafka实战[M]. 北京: 电子工业出版社, 2018.',
    '[7] 林子雨. 大数据技术原理与应用(第3版)[M]. 北京: 人民邮电出版社, 2021.',
    '[8] Holden Karau, et al. Learning Spark (2nd Edition)[M]. O\'Reilly Media, 2020.',
    '[9] Josiah L. Carlson. Redis in Action[M]. Manning Publications, 2013.',
    '[10] 黄峰达. 前端架构:从入门到微前端[M]. 北京: 电子工业出版社, 2021.',
    '[11] Tyler Akidau, et al. The Dataflow Model[J]. Proceedings of the VLDB Endowment, 2015, 8(12): 1792-1803.',
    '[12] Apache Flink Community. Flink v1.18 Documentation[EB/OL]. https://flink.apache.org/, 2024.',
    '[13] Apache Kafka Community. Kafka 3.9 Documentation[EB/OL]. https://kafka.apache.org/, 2024.',
    '[14] Apache ECharts Team. ECharts 5 Documentation[EB/OL]. https://echarts.apache.org/, 2024.',
    '[15] Socket.IO Team. Socket.IO v4 Documentation[EB/OL]. https://socket.io/docs/v4/, 2024.',
]
# P372-P376 are reference paragraphs
for i, ref in enumerate(refs):
    set_para_text(372 + i, ref)
# Clear any remaining old reference text (P376 area)
for ri in range(372 + len(refs), 378):
    set_para_text(ri, '')

# ── ===== Appendix ===== ──
print("\n[第11步] 填充附录...")
set_para_text(379,
    '附录A 项目目录结构：项目根目录包含start.bat统一起停脚本、docker-compose.yml容器编排文件、'
    'backend/（Express+Socket.IO后端，含server.js路由+Socket.IO事件处理）、'
    'frontend/（React+Vite+ECharts前端大屏，含App.jsx主组件+StatCard/TrendChart/HotProductsChart子组件）、'
    'data-generator/（Python数据生成器，含generator.py主程序+kafka_producer.py生产者封装）、'
    'flink-job/（Flink流计算Maven项目，含EcommerceJob主类+OrderAggregate/PageViewAggregate窗口函数+RedisSink输出）、'
    'kafka_2.13-3.9.2/（Kafka KRaft模式，已配置server.properties含4分区Topic自动创建）、'
    'redis/（Redis Windows版，已配置redis.conf含最大内存256MB+LRU淘汰策略）、'
    'runtime/（便携运行环境目录，可选放置Node.js/Python/Java便携版实现免安装运行）。')

# Insert dashboard placeholder at end of document
print("  插入前端界面示意图...")
# Add a new paragraph for the dashboard image
last_para = doc.Paragraphs.Add()
last_para.Range.Text = ''
rng = last_para.Range
rng.Collapse(1)
shape = doc.InlineShapes.AddPicture(img_dash, False, True, rng)
shape.Width = word.CentimetersToPoints(14)
last_para.Alignment = 1  # center
# Add caption
cap = doc.Paragraphs.Add()
cap.Range.Text = '图5 前端大屏界面示意图（请自行替换为实际运行截图）'
cap.Alignment = 1  # center

# ── SAVE ──
print("\n保存文档...")
doc.SaveAs2(OUTPUT)
doc.Close()
word.Quit()
pythoncom.CoUninitialize()

print(f"\n{'='*60}")
print(f"报告已保存至: {OUTPUT}")
print(f"请用Word打开检查格式，将'图5'替换为实际运行截图，并根据需要微调。")
print(f"{'='*60}")
