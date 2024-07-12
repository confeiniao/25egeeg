# coding=utf-8
import requests
import socket

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
        except:
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
        ip_sock = socket.getaddrinfo(domain, None)
        return ip_sock
    except:
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

    for url in urls:
        process_filter(url)

    lines_to_keep = list(set(lines_to_keep))

    valid_domains = []
    for domain in lines_to_keep:
        ip = check_dns_resolution(domain)
        if ip:
            valid_domains.append(domain)

    lines_to_keep = []
    output_file = '/root/workspace/st/dnsmasq.conf'
    if valid_domains:
        lines_to_keep = filter_domains(valid_domains)

    valid_domains = []
    unique_lines = []

    if len(lines_to_keep) > 1:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.writelines(lines_to_keep)
    print(len(lines_to_keep))
    lines_to_keep = []