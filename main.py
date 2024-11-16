import re
import requests
import os
import queue
import threading
from bs4 import BeautifulSoup
from datetime import datetime

# 定义学校信息
schools = [
    {
        "name": "山东大学电气工程学院",
        "base_url": "https://www.ee.sdu.edu.cn",
        "list_url": "https://www.ee.sdu.edu.cn/szdw1/zrjs.htm",
        "pattern": r'<li><a href="(../info/\d+/\d+\.htm)" target="_blank" title="([^"]+)">',
        "url_format": lambda url: url.replace("..", "https://www.ee.sdu.edu.cn")
    },
    {
        "name": "天津大学电气自动化与信息工程学院",
        "base_url": "http://seea.tju.edu.cn",
        "list_url": "http://seea.tju.edu.cn/szdw.htm",
        "pattern": r'<li><a href="(info/\d+/\d+\.htm)" target="_blank" title="([^"]+)">',
        "url_format": lambda url: f"http://seea.tju.edu.cn/{url}"
    },
    {
        "name": "大连海事大学船舶电气工程学院",
        "base_url": "https://cbdq.dlmu.edu.cn",
        "list_url": "https://cbdq.dlmu.edu.cn/szdw.htm",
        "pattern": r'<a href="(info/\d+/\d+\.htm)"[^>]*>(?:<span[^>]*>)?([^<]+)(?:</span>)?</a>',
        "url_format": lambda url: f"https://cbdq.dlmu.edu.cn/{url}"
    },
    {
        "name": "哈尔滨工业大学电气工程及自动化学院",
        "base_url": "http://hitee.hit.edu.cn",
        "list_url": "http://hitee.hit.edu.cn/17037/list.htm",
        "pattern": r'<a href="(http://homepage\.hit\.edu\.cn/[^"]+)"[^>]*>([^<]+)</a>',
        "url_format": lambda url: url
    },
    {
        "name": "复旦大学新科学与工程学院电子工程系",
        "base_url": "http://ee.fudan.edu.cn",
        "list_url": ["http://ee.fudan.edu.cn/data/list/zgj",
                     "http://ee.fudan.edu.cn/data/list/fgj",
                     "http://ee.fudan.edu.cn/data/list/zj"],
        "pattern": r'<a[^>]*href="/Data/View/(\d+)"[^>]*>\s*([^<]+)\s*</a>',
        "url_format": lambda url: f"http://ee.fudan.edu.cn/Data/View/{url}"
    },
    {
        "name": "东华大学信息科学与技术学院电气电子工程系",
        "base_url": "https://web.dhu.edu.cn",
        "list_url": "https://web.dhu.edu.cn/cist/dqdzgcx/list.htm",
        "pattern": r'<a href="(http://web\.dhu\.edu\.cn/cist/\d+/\d+/c\d+a\d+/page\.htm)"[^>]*>([^<]+)</a>',
        "url_format": lambda url: url.replace("http://", "https://")
    },
    {
        "name": "东南大学电气工程学院",
        "base_url": "https://ee.seu.edu.cn",
        "list_url": "https://ee.seu.edu.cn/szdw/list.htm",
        "pattern": r'<a href="(http://ee\.seu\.edu\.cn/\d+/\d+/c\d+a\d+/page\.htm)"[^>]*>(?:<span[^>]*>)?([^<]+)(?:</span>)?</a>',
        "url_format": lambda url: url
    },
    {
        "name": "河海大学电气与动力工程学院",
        "base_url": "https://ceee.hhu.edu.cn",
        "list_url": "https://ceee.hhu.edu.cn/12805/list.htm",
        "pattern": r'<a href="(http://jszy\.hhu\.edu\.cn/[^/]+/)"[^>]*>([^<]+)</a>',
        "url_format": lambda url: url
    },
    {
        "name": "南京师范大学电气与自动化工程学院",
        "base_url": "http://eae.njnu.edu.cn",
        "list_url": "http://eae.njnu.edu.cn/xygk/szdw1.htm",
        "pattern": r'<td><a href="\.\./([^"]+)" title="([^"]+)">',
        "url_format": lambda url: f"http://eae.njnu.edu.cn/{url}"
    },
    {
        "name": "合肥工业大学电气与自动化工程学院",
        "base_url": "https://ea.hfut.edu.cn",
        "list_url": "https://ea.hfut.edu.cn/list_xszx.jsp?urltype=tree.TreeTempUrl&wbtreeid=1165",
        "pattern": r'<a href="(http://faculty\.hfut\.edu\.cn/[^/]+/zh_CN/index\.htm)"[^>]*>([^<]+)</a>',
        "url_format": lambda url: url
    },
    {
        "name": "武汉大学电气与自动化学院",
        "base_url": "https://eea.whu.edu.cn",
        "list_url": "https://eea.whu.edu.cn/szdw/jsdw/dqgcx.htm",
        "pattern": r'<a href="\.\.\/\.\.\/(info/\d+/\d+\.htm)">([^<]+)</a>',
        "url_format": lambda url: f"https://eea.whu.edu.cn/{url}"
    }
]

# 创建线程安全的日志写入函数
log_lock = threading.Lock()
output_lock = threading.Lock()

def log_message(message, log_file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    with log_lock:
        print(log_line.strip())
        log_file.write(log_line)
        log_file.flush()

def get_html_content(url, log_file):
    try:
        log_message(f"正在访问URL: {url}", log_file)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        log_message(f"成功获取页面内容，状态码: {response.status_code}", log_file)
        return response.text
    except Exception as e:
        log_message(f"错误：获取URL {url} 失败: {str(e)}", log_file)
        return None

def check_honors(html_content, name, log_file):
    log_message(f"正在检查 {name} 的荣誉称号...", log_file)
    honors = []
    
    honor_keywords = {
        '杰青': [
            '国家杰出青年科学基金',
            '杰出青年科学基金',
            '杰青',
            '国家杰青',
            '获得杰出青年',
            '获国家杰出青年',
            '获杰青',
            '入选杰青',
            '国家杰出青年基金',
            '杰出青年基金获得者'
        ],
        '长江': [
            '长江学者',
            '长江特聘教授',
            '长江学者特聘教授',
            '特聘教授（长江学者）',
            '教育部长江学者',
            '入选长江学者',
            '获聘长江学者',
            '长江特聘',
            '长江讲座教授',
            '长江青年学者'
        ],
        '千人': [
            '千人计划',
            '国家千人',
            '新世纪千人',
            '青年千人',
            '国家特聘专家',
            '入选千人计划',
            '入选国家千人',
            '国家特聘千人计划',
            '国家特聘专家（千人计划）',
            '千人计划特聘专家',
            '青年千人计划入选者'
        ],
        '万人': [
            '万人计划',
            '国家万人',
            '国家高层次人才特殊支持计划',
            '万人计划领军人才',
            '国家"万人计划"',
            '"万人计划"科技创新领军人才',
            '科技创新领军人才',
            '国家高层次人才',
            '入选万人计划',
            '入选国家万人计划',
            '万人计划青年拔尖人才'
        ]
    }
    
    for honor, keywords in honor_keywords.items():
        if any(keyword in html_content for keyword in keywords):
            honors.append(honor)
            log_message(f"找到荣誉: {name} - {honor}", log_file)
    
    if not honors:
        log_message(f"{name} 未找到荣誉称号", log_file)
    
    return honors

def process_teacher(school, url_part, name, log_file, output_file):
    full_url = school['url_format'](url_part)
    
    log_message(f"处理教师: {name}, URL: {full_url}", log_file)
    teacher_html = get_html_content(full_url, log_file)
    
    if not teacher_html:
        with output_lock:
            output_file.write(f"{school['name']} - {name}：获取信息失败\n")
            output_file.flush()
        return
    
    honors = check_honors(teacher_html, name, log_file)
    with output_lock:
        if honors:
            honor_text = '、'.join(honors)
            output_file.write(f"{school['name']} - {name}：{honor_text}\n")
        else:
            output_file.write(f"{school['name']} - {name}：无\n")
        output_file.flush()

def worker(task_queue, log_file, output_file):
    while True:
        try:
            task = task_queue.get_nowait()
            if task is None:
                break
            school, url_part, name = task
            process_teacher(school, url_part, name, log_file, output_file)
        except queue.Empty:
            break
        finally:
            task_queue.task_done()

def process_school(school, task_queue, log_file):
    log_message(f"开始处理 {school['name']}", log_file)
    
    list_urls = school['list_url'] if isinstance(school['list_url'], list) else [school['list_url']]
    
    for list_url in list_urls:
        html_content = get_html_content(list_url, log_file)
        if not html_content:
            continue
        
        matches = re.findall(school['pattern'], html_content)
        log_message(f"在 {list_url} 中找到 {len(matches)} 位教师", log_file)
        
        for match in matches:
            if len(match) != 2:
                continue
            task_queue.put((school, match[0], match[1]))

def main():
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    log_file_path = os.path.join(desktop_path, 'teacher_honors_log.txt')
    output_file_path = os.path.join(desktop_path, 'teacher_honors.txt')
    
    with open(log_file_path, 'w', encoding='utf-8') as log_file, \
         open(output_file_path, 'w', encoding='utf-8') as output_file:
        
        log_message("程序开始执行", log_file)
        
        # 创建任务队列
        task_queue = queue.Queue()
        
        # 收集所有任务
        for school in schools:
            process_school(school, task_queue, log_file)
        
        # 创建4个工作线程
        threads = []
        for _ in range(4):
            task_queue.put(None)  # 添加结束标记
            t = threading.Thread(target=worker, args=(task_queue, log_file, output_file))
            t.start()
            threads.append(t)
        
        # 等待所有线程完成
        for t in threads:
            t.join()
            
        log_message("程序执行完成", log_file)

if __name__ == '__main__':
    main()