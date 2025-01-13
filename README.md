# Milthm_Score-Checker_python
用python写的Milthm查分器



目前只支持json格式的存档

需先导入Pillow库
pip install Pillow

转到main.py所在目录
运行python3 main.py "存档路径" "输出图片路径(png结尾)"
如未指定输出图片路径则输出到main.py所在目录
如未指定存档路径则从mian.py所在目录读取save.json
如不存在save.json则读取save.txt

内含格式转换的脚本是由[http://k9.lv/c/]上解析出的格式转换为json格式，如果有需要使用其他格式的文件，可以使用此网站进行转换

### Instructions for Using the Python Score Checker:

The score checker currently only supports save files in JSON format.

#### Required Library:
You need to install the Pillow library first:
pip install Pillow

#### Usage:
1. Navigate to the directory where `main.py` is located.
2. Run the following command:
   python3 main.py "path_to_save_file" "output_image_path (must end with .png)"

3. If the output image path is not specified, the image will be saved in the same directory as `main.py`.
4. If the save file path is not specified, the program will try to read `save.json` from the same directory as `main.py`.
5. If `save.json` does not exist, the program will attempt to read `save.txt`.

The included script for save file conversion（格式转换) is designed to convert files from the format parsed by [http://k9.lv/c/] into JSON format. If you need to use files in other formats, you can use this website for conversion.
