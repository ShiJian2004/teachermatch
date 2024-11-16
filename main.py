import re
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime

def log_message(message, log_file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
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

def extract_teacher_info(html_content, log_file):
    log_message("开始提取教师信息...", log_file)
    pattern = r'<li><a href="(../info/\d+/\d+\.htm)" target="_blank" title="([^"]+)">'
    matches = re.findall(pattern, html_content)
    log_message(f"找到 {len(matches)} 位教师", log_file)
    return matches

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
        ],
        # 补充其他可能的人才计划
        '优青': [
            '国家优秀青年科学基金',
            '优秀青年科学基金',
            '优青',
            '国家优青',
            '获得优秀青年',
            '获国家优秀青年',
            '获优青',
            '入选优青',
            '优秀青年基金获得者'
        ],
        '泰山学者': [
            '泰山学者',
            '泰山学者特聘专家',
            '泰山产业领军人才',
            '泰山学者青年专家',
            '入选泰山学者'
        ],
        '青年长江': [
            '青年长江学者',
            '长江学者青年项目',
            '教育部青年长江学者',
            '入选青年长江'
        ],
        '百人计划': [
            '中科院百人计划',
            '百人计划',
            '引进百人计划',
            '科学院百人计划'
        ]
    }
    
    for honor, keywords in honor_keywords.items():
        if any(keyword in html_content for keyword in keywords):
            honors.append(honor)
            log_message(f"找到荣誉: {name} - {honor}", log_file)
    
    if not honors:
        log_message(f"{name} 未找到荣誉称号", log_file)
    
    return honors

def main():
    # 创建日志文件
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    log_file_path = os.path.join(desktop_path, 'teacher_honors_log.txt')
    output_file_path = os.path.join(desktop_path, 'teacher_honors.txt')
    
    with open(log_file_path, 'w', encoding='utf-8') as log_file:
        log_message("程序开始执行", log_file)
        
        # 教师列表页面URL
        base_url = 'https://www.ee.sdu.edu.cn'
        teacher_list_url = 'https://www.ee.sdu.edu.cn/szdw1/zrjs.htm'  # 替换为实际的教师列表URL
        
        # 获取教师列表页面内容
        log_message("开始获取教师列表页面", log_file)
        html_content = get_html_content(teacher_list_url, log_file)
        if not html_content:
            log_message("获取教师列表失败，程序终止", log_file)
            return
        
        # 提取教师信息
        teachers = extract_teacher_info(html_content, log_file)
        
        # 创建输出文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            log_message(f"开始处理每位教师信息，共 {len(teachers)} 位", log_file)
            
            for index, (relative_url, name) in enumerate(teachers, 1):
                log_message(f"正在处理第 {index}/{len(teachers)} 位教师: {name}", log_file)
                
                # 构建完整URL
                full_url = base_url + relative_url.replace('..', '')
                log_message(f"教师主页URL: {full_url}", log_file)
                
                # 获取教师个人页面内容
                teacher_html = get_html_content(full_url, log_file)
                if not teacher_html:
                    log_message(f"警告：无法获取 {name} 的个人页面", log_file)
                    f.write(f'{name}：获取信息失败\n')
                    continue
                
                # 检查荣誉
                honors = check_honors(teacher_html, name, log_file)
                
                # 写入文件
                if honors:
                    honor_text = '、'.join(honors)
                    f.write(f'{name}：{honor_text}\n')
                else:
                    f.write(f'{name}：无\n')
                
                log_message(f"完成处理：{name}", log_file)
            
            log_message("所有教师信息处理完成", log_file)
        
        log_message(f"程序执行完成。输出文件：{output_file_path}", log_file)
        log_message(f"日志文件：{log_file_path}", log_file)

if __name__ == '__main__':
    main()