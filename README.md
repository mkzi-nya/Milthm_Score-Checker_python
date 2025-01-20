# Milthm_Score-Checker_python
用 Python 写的 Milthm 查分器  
Milthm Score Checker written in Python

---

## 更新日志 / Changelog
### v1.1.1

- 将`userReality`计算方式改为向下取整，`Broken Conviction_CL`定数更改为11.899

  Change the calculation method of `userReality` to floor rounding, and update the constant `Broken Conviction_CL` to 11.899.

### v1.1

- 增加了各平台存档格式的支持 (JSON, XML, plist, reg 以及在 [http://k9.lv/c/] 解析出的格式)  
  Added support for various platform save file formats (JSON, XML, plist, reg, and the format parsed from [http://k9.lv/c/]).
- 增加控制绘制曲目数量  
  Added control for the number of tracks to be drawn.
- 改为在线下载曲绘文件  
  Change to download jacket files online.

---

## 使用说明 / Instructions

### 中文

1. 需先导入 Pillow 库:
   ```bash
   pip install Pillow
   ```

2. 转到 `main.py` 所在目录:
   ```bash
   python3 main.py [绘制曲目数量] "存档路径" "输出图片路径"
   ```
   - `[绘制曲目数量]` 为选填，默认为 22。  
   - 如未指定输出图片路径，则图片输出到 `main.py` 所在目录。  
   - 如未指定存档路径，则程序尝试从 `main.py` 所在目录读取 `save.json`。  
   - 如不存在 `save.json`，则读取 `save.txt`。

3. 内含格式转换脚本:
   - 用于将 [http://k9.lv/c/] 上解析出的格式转换为 JSON 格式。  
   - 如需其他格式文件，可使用该网站进行转换。

---

### English

1. Install the required Pillow library:
   ```bash
   pip install Pillow
   ```

2. Navigate to the directory where `main.py` is located:
   ```bash
   python3 main.py [Number of Tracks to Draw] "Save File Path" "Output Image Path"
   ```
   - `[Number of Tracks to Draw]` is optional, defaulting to 22.  
   - If the output image path is not specified, the image will be saved in the same directory as `main.py`.  
   - If the save file path is not specified, the program will try to read `save.json` from the same directory as `main.py`.  
   - If `save.json` does not exist, the program will attempt to read `save.txt`.

3. Included conversion script:
   - Converts files from the format parsed by [http://k9.lv/c/] into JSON format.  
   - For other formats, use the website for conversion.

---

## 关于 / About

Milthm 查分器用于从不同平台的存档中提取分数信息并生成图像输出。支持 JSON、XML、plist、reg 等多种格式。

The Milthm Score Checker extracts score information from save files on various platforms and generates image outputs. It supports multiple formats including JSON, XML, plist, and reg.
```

---
