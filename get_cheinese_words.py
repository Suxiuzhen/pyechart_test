import os
import re

def get_chinese_words_from_files(folder_path):
    chinese_words = []
    pattern = re.compile(r"['\"]([a-zA-Z\-]{0,30}[\u4e00-\u9fff]+[\u4e00-\u9fff\s,.:，。；\-a-zA-Z]+)['\"]")  # 匹配位于单引号或双引号之间的中文字符

    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith(".py"):
                file_path = os.path.join(root, file_name)
                with open(file_path, "r", encoding="utf-8") as file:
                    for line in file:
                        if "#" not in line:
                            matches = pattern.findall(line)
                            chinese_words.extend(matches)
    chinese_words = list(set(chinese_words))
    chinese_words.sort(key=lambda x: len(x))  # 按长度进行排序
    return chinese_words


if __name__ == '__main__':
    folder_path = "E:\\new_code\\FrontServer"  # 指定文件夹路径
    chinese_words = get_chinese_words_from_files(folder_path)
    print(chinese_words)
    print(len(chinese_words))
