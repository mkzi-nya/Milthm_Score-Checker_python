import os
import re


def find_beatmap_dict(filename="BeatmapID字典.txt"):
    """
    查找当前目录下的 BeatmapID字典.txt 文件。
    如果找到，返回其路径；否则，返回 None。
    """
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, filename)
    if os.path.isfile(file_path):
        return file_path
    else:
        return None


def parse_beatmap_dict(file_path):
    """
    解析 BeatmapID字典.txt 文件，提取 name, category, constant。
    返回一个列表，包含每个条目的字典。
    """
    beatmaps = []
    # 定义正则表达式以提取所需字段
    pattern = re.compile(
        r'"[^"]+":\s*\{\s*constant:\s*([-]?\d+\.?\d*)\s+category:\s*"([^"]+)"\s+name:\s*"([^"]+)"\s*\},?'
    )

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # 跳过空行
            match = pattern.match(line)
            if match:
                constant = match.group(1)
                category = match.group(2)
                name = match.group(3)
                beatmaps.append(
                    {"name": name, "category": category, "constant": constant}
                )
            else:
                print(f"警告：无法解析行：{line}")
    return beatmaps


def prompt_username():
    """
    提示用户输入名字，如果输入为空，则使用默认值。
    """
    username = input("请输入用户名（默认为'名字'）：").strip()
    if not username:
        username = "名字"
    return username


def format_output(username, beatmaps):
    """
    按照指定格式格式化输出内容。
    """
    output_lines = []
    output_lines.append(f"[{username}],{{")
    for i, bm in enumerate(beatmaps):
        constant_display = f"{float(bm['constant'])}"
        line = f"  [{bm['name']},{bm['category']},{constant_display},1010000,1.0000,0]"
        if i < len(beatmaps) - 1:
            line += ","
        output_lines.append(line)
    output_lines.append("}")
    return "\n".join(output_lines)


def write_output(file_path, content):
    """
    将内容写入指定文件。
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"已成功写入 {file_path}")


def main():
    # 查找 BeatmapID字典.txt
    beatmap_dict_path = find_beatmap_dict()
    if not beatmap_dict_path:
        print("错误：当前目录下未找到 'BeatmapID字典.txt' 文件。")
        return

    # 解析 BeatmapID字典.txt
    beatmaps = parse_beatmap_dict(beatmap_dict_path)
    if not beatmaps:
        print("错误：没有找到任何有效的 Beatmap 条目。")
        return

    # 提示用户输入用户名
    username = prompt_username()

    # 格式化输出内容
    output_content = format_output(username, beatmaps)

    # 写入测试存档.txt
    output_file = os.path.join(os.getcwd(), "测试存档.txt")
    write_output(output_file, output_content)


if __name__ == "__main__":
    main()
