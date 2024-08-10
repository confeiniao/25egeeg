import os
import requests
import tarfile
import subprocess
import pandas as pd
import concurrent.futures
import time

# 设定常量
working_directory = "/root/cs"
filename = "CloudflareST_linux_amd64.tar.gz"
extract_path = os.path.join(working_directory, "CloudflareST")
timeout = 6 * 60  # 6分钟超时
num_processes = 3

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

# 提取 A2 到 A4 行内容
def extract_ips_from_csv(directory):
    ips_set = set()
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    for file in csv_files:
        file_path = os.path.join(directory, file)
        df = pd.read_csv(file_path, header=None)
        for i in range(1, 4):
            if i < len(df):
                cell = df.iloc[i, 0]
                if pd.notna(cell) and cell.strip():
                    ips_set.add(cell.strip())
    return list(ips_set)

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

    # 提取并打印 IPs
    ips_list = extract_ips_from_csv(working_directory)
    print("Unique IPs:", ips_list)

if __name__ == "__main__":
    main()
