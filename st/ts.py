#!/usr/bin/env python3
import os

def write_to_file():
    try:
        with open('cc.txt', 'w') as file:
            file.write('你好')
        print("写入成功")
    except PermissionError:
        print("权限不足,无法写入文件")
    except Exception as e:
        print(f"发生未知错误: {e}")
    script_path = os.path.abspath(__file__)
    print(f"当前脚本文件路径: {script_path}")    

if __name__ == '__main__':
    write_to_file()