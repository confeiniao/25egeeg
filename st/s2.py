import os
import requests
import tarfile
import subprocess
import pandas as pd
import concurrent.futures
import time
import glob

# 设定常量
working_directory = "/root/tsc/st/zfs"
filename = "CloudflareST_linux_amd64.tar.gz"
extract_path = os.path.join(working_directory, "CloudflareST")
timeout = 6 * 60  # 6分钟超时
num_processes = 20

# 获取最新版本的下载链接
def get_latest_release_url():
    api_url = "https://api.github.com/repos/XIU2/CloudflareSpeedTest/releases/latest"
    response = requests.get(api_url)
    response.raise_for_status()
    release_data = response.json()
    for asset in release_data["assets"]:
        if "CloudflareST_linux_amd64.tar.gz" in asset["name"]:
            return asset["browser_download_url"]
    raise ValueError("CloudflareST_linux_amd64.tar.gz not found in latest release.")

# 下载文件
def download_file(url, path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

# 解压文件并赋予执行权限
def extract_and_set_permissions(tar_path, extract_path):
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=extract_path)
    os.chmod(os.path.join(extract_path, "CloudflareST"), 0o755)

# 运行命令并监控
def run_command(args, timeout):
    try:
        result = subprocess.run(args, cwd=extract_path, timeout=timeout, check=True)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"Process with args {args} timed out.")
        return -1
    except subprocess.CalledProcessError as e:
        print(f"Process with args {args} failed with exit code {e.returncode}.")
        return e.returncode

def huoqu():
    # 获取当前目录下所有CSV文件路径
    csv_files = glob.glob('./*.csv')

    # 用于存储IP地址数据
    data = []

    for file in csv_files:
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 提取列名
            headers = lines[0].strip().split(',')
            #print(f"Headers: {headers}")

            if 'IP 地址' in headers:
                ip_index = headers.index('IP 地址')
                
                # 处理数据行
                for line in lines[1:]:
                    columns = line.strip().split(',')
                    if len(columns) > ip_index:
                        value = columns[ip_index]
                        if value.count('.') == 3:  # IP 地址应当有3个点
                            data.append(value)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    # 去重并保存到变量IPS
    IPS = list(set(data))


    print(IPS)


    # 保存查询结果的列表
    IPSS = []

    # API的基本URL
    api_url = "https://ip100.info/ipaddr?ip="

    xl = 1
    # 遍历IP地址列表
    for ip in IPS:
        try:
            # 构建请求URL
            response = requests.get(api_url + ip)
            response.raise_for_status()  # 确保请求成功
            data = response.json()
            data_str = json.dumps(data, ensure_ascii=False)
            # 检查是否为正常返回
            if "error" in data:
                # 异常返回，直接保存IP地址
                IPSS.append('%s:443#自选IP' % ip)
            else:
                # 正常返回，构建结果字符串
                country = data.get("country", "")

                if "美国" in data_str:
                    result = f"{ip}:443#--{xl}--US-自选IP"
                elif "香港" in data_str:
                    result = f"{ip}:443#--{xl}--CN-HK-自选IP"
                elif "台湾" in data_str:
                    result = f"{ip}:443#--{xl}--CN-TW-自选IP"
                elif "日本" in data_str:
                    result = f"{ip}:443#--{xl}--JP-自选IP"
                else:
                    result = f"{ip}:443#--{xl}--{country}-自选IP"
                    
                IPSS.append(result)
        except requests.RequestException as e:
            # 处理请求错误
            print(f"Request error for IP {ip}: {e}")
            IPSS.append(ip)
        except json.JSONDecodeError as e:
            # 处理JSON解析错误
            print(f"JSON decode error for IP {ip}: {e}")
            IPSS.append(ip)
        xl += 1
    print("Results:")
    print(IPSS)

    # 文件路径
    file_path = '/root/workspace/st/yx.txt'

    try:
        # 打开文件进行写入操作
        with open(file_path, 'w', encoding='utf-8') as file:
            for line in IPSS:
                file.write(line + '\n')  # 写入每一行内容并换行

        print(f"Data successfully written to {file_path}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")

# 主程序
def main():
    if not os.path.exists(working_directory):
        os.makedirs(working_directory)

    # 获取最新版本的下载链接
    latest_url = get_latest_release_url()
    print(f"Downloading from {latest_url}")

    # 下载文件
    tar_path = os.path.join(working_directory, filename)
    download_file(latest_url, tar_path)

    # 解压文件并设置执行权限
    extract_and_set_permissions(tar_path, extract_path)

    # 生成参数并运行
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_processes) as executor:
        futures = [executor.submit(run_command, [
            "./CloudflareST",
            "-f", "ip.txt",
            "-n", "1000",
            "-dn", "3",
            "-tl", "500",
            "-tll", "10",
            "-tlr", "0",
            "-sl", "5",
            "-p", "0",
            "-o", f"{i + 1}.csv"
        ], timeout) for i in range(num_processes)]

        for future in concurrent.futures.as_completed(futures):
            return_code = future.result()
            if return_code == 0:
                print("Process completed successfully.")
            elif return_code == -1:
                print("Process timed out.")
            else:
                print(f"Process ended with return code {return_code}.")

    # 获取当前目录下所有CSV文件路径
    huoqu()

if __name__ == "__main__":
    main()