import json
import io
import copy
import os
from PIL import Image
from pdf2image import convert_from_path

def image_to_decimal_array(image_path):
    # 读取图片文件
    with open(image_path, 'rb') as file:
        image_data = file.read()
    # 将二进制数据转换为十进制数组
    decimal_array = list(image_data)
    return decimal_array

def decimal_array_to_image(decimal_array, output_path):
    # 将十进制数组转换为字节数据
    byte_data = bytes(decimal_array)
    image = Image.open(io.BytesIO(byte_data))
    image.save(output_path)

def convert_to_target_format(data, template):
    result = []
    template["文件id"] = data['paper_id']
    template["处理时间"] = data["header"]["date_generated"]
    
    for i in data:
        if i == 'title':
            new_entry = copy.deepcopy(template)
            new_entry["块id"] = '0'
            new_entry["文本"] = data["title"]
            new_entry["数据类型"] = 'text' 
            result.append(copy.deepcopy(new_entry))
        
        if "_parse" in i:
            for entry in data.get(i, {}).get("abstract", []):
                new_entry = copy.deepcopy(template)
                new_entry["数据类型"] = 'text' 
                new_entry["块id"] = '0'
                text = entry.get("text", "")
                new_entry["文本"] = text
                result.append(copy.deepcopy(new_entry))
            
            for entry in data.get(i, {}).get("body_text", []):
                new_entry = copy.deepcopy(template)
                new_entry["数据类型"] = 'text' 
                id = entry.get("sec_num", "")
                new_entry["块id"] = id
                text = entry.get("text", "")
                new_entry["文本"] = text
                result.append(copy.deepcopy(new_entry))
    
    for i in data["latex_parse"]["ref_entries"]:
        new_entry = copy.deepcopy(template)
        if data["latex_parse"]["ref_entries"][i]["type_str"] == "figure":
            temdir_path = '/root/autodl-tmp/s2orc-doc2json/temp_dir/latex'
            paper_repath = data["latex_parse"]["ref_entries"][i]["uris"]
            image_path = os.path.join(temdir_path, data['paper_id'], ''.join(paper_repath))
            if image_path.lower().endswith('.pdf'):
                images = convert_from_path(image_path)
                image_path = os.path.splitext(image_path)[0] + ".png"
                images[0].save(image_path, 'PNG')
            decimal_array = image_to_decimal_array(image_path)
            new_entry["图片"] = decimal_array       
            new_entry["数据类型"] = 'image'
            result.append(new_entry)
    
    return result

if __name__ == '__main__':
    template = {"文件md5": None, "文件id": None, "页码": None, "块id": None, "文本": None, "图片": None, "处理时间": None, "数据类型": None, "bounding_box": None, "额外信息": None}
    json_path = '/root/autodl-tmp/s2orc-doc2json/output_dir/2004.14974.json'
    with open(json_path, 'r') as file:
        data = json.load(file)
        result = convert_to_target_format(data, template)
        
    output_json_path = '/root/autodl-tmp/s2orc-doc2json/output_dir/converted_result2.json'
    with open(output_json_path, 'w') as outfile:
            json.dump(result, outfile, ensure_ascii=False, indent=1)
