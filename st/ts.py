# coding=utf-8
import requests
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import dns.resolver
 
lines_to_keep = []

def fetch_url(url):
    max_retries = 3
    retries = 0
    if 'github' in url:
        url = 'https://mirror.ghproxy.com/' + url
    while retries < max_retries:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException:
            retries += 1
            if retries == max_retries - 2:
                url = url.replace('mirror.ghproxy', 'gh-proxy')
            if retries == max_retries - 1:
                url = url.replace('https://gh-proxy.com/', '')
    return None

def process_filter(url):
    file_contents = fetch_url(url)
    if file_contents:
        for line in file_contents.splitlines():
            line = line.strip()
            if (line.startswith('||') and line.endswith('^') and '/' not in line and '*' not in line and 'localhost' not in line and '10jqka' not in line) or \
               line.startswith('127.0.0.1'):
                line = line.replace('||', '').replace('^', '').replace('127.0.0.1', '').replace(' ', '')
                lines_to_keep.append(line)

def check_dns_resolution(domain):
    try:
        result = dns.resolver.resolve(domain, 'A')
        ips = [r.address for r in result]
        return ips[0] if ips else None
    except dns.resolver.NoAnswer:
        return None
    except dns.resolver.NXDOMAIN:
        return None
    except dns.resolver.Timeout:
        return None

def filter_domains(lines):
    lines.sort(key=len)
    unique_lines = [lines[0]]
    for i in range(1, len(lines)):
        if not any(('.' + line) in lines[i] for line in unique_lines):
            unique_lines.append(lines[i])
    unique_lines = sorted(unique_lines)
    return unique_lines

if __name__ == '__main__':
    urls = [
        'https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt',
        'https://raw.githubusercontent.com/jdlingyu/ad-wars/master/hosts'
    ]

    # 使用 ThreadPoolExecutor 创建线程池，数量为200
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = [executor.submit(process_filter, url) for url in urls]
        
        # 显示进度条
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching URLs"):
            pass  # 等待所有任务完成
    
    lines_to_keep = list(set(lines_to_keep))

    valid_domains = []
    # 使用 ThreadPoolExecutor 再次创建线程池，数量为200
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = [executor.submit(check_dns_resolution, domain) for domain in lines_to_keep]
        
        # 显示进度条
        for future in tqdm(as_completed(futures), total=len(futures), desc="Checking DNS Resolution"):
            ip = future.result()
            if ip:
                valid_domains.append(ip)

    lines_to_keep = filter_domains(valid_domains)

    output_file = '/root/workspace/st/dnsmasq.conf'
    if lines_to_keep:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.writelines(line + '\n' for line in lines_to_keep)

    print(f"Total unique domains written to {output_file}: {len(lines_to_keep)}")
