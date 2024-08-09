# coding=utf-8
import datetime
import requests
import dns.resolver
from concurrent.futures import ThreadPoolExecutor, as_completed
import tqdm

lines_to_keep = []
reject_list = []
lines_list = []


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
        except requests.exceptions.RequestException as e:
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
            if ((line.startswith('||') and line.endswith('^') and '/' not in line and '*' not in line) or \
               line.startswith('127.0.0.1')) and 'localhost' not in line:
                line = line.replace('||', '').replace('^', '').replace('127.0.0.1', '').replace(' ', '')
                lines_to_keep.append(line)
        return lines_to_keep

def check_dns_resolution(domain):
    try:
        resolver = dns.resolver.Resolver()
        answers = resolver.resolve(domain)
        ips = [answer.address for answer in answers]
        return ips
    except dns.resolver.NoAnswer:
        return None
    except dns.resolver.NXDOMAIN:
        return None
    except dns.resolver.NoNameservers:
        return None
    except Exception as e:
        pass
        return None

def filter_domains(lines):
    lines.sort(key=len)
    unique_lines = [lines[0]]
    for i in range(1, len(lines)):
        if not any(('.' + line) in lines[i] for line in unique_lines):
            unique_lines.append(lines[i])
    unique_lines = sorted(unique_lines)
    return unique_lines

def address(sock):
    add = []
    now = datetime.datetime.now()
    add.append('domain:{}.{}.{}.test\n'.format(now.month, now.day, now.hour))
    for line in sock:
        add.append('domain:%s\n' % line)
    return add

def process_domains(domain_list):
    valid_domains = []
    with tqdm.tqdm(total=len(domain_list), desc='Processing domains') as pbar:
        with ThreadPoolExecutor(max_workers=199) as executor:
            future_to_domain = {executor.submit(check_dns_resolution, domain): domain for domain in domain_list}
            for future in as_completed(future_to_domain):
                domain = future_to_domain[future]
                ip = future.result()
                pbar.update(1)
                if ip:
                    valid_domains.append(domain)
    return valid_domains

urls = 'https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-hosts.txt'
lines_to_keep = process_filter(urls)

url = 'https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/reject-list.txt'
reject_list = fetch_url(url)
reject_list = reject_list.splitlines()

with open('/root/workspace/st/ad_j.txt', 'r') as file:
    for line in file:
        lines_list.append(line.strip())

he_list = set(lines_to_keep) | set(reject_list) | set(lines_list)

lines_to_keep = list(he_list)

output_file = '/root/workspace/st/ad.txt'
if lines_to_keep:
    valid_domains = process_domains(lines_to_keep)
    lines_to_keep = address(filter_domains(valid_domains))

    if len(lines_to_keep) > 20000:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.writelines(lines_to_keep)
        print('共%s条AD' % len(lines_to_keep))
lines_to_keep = []