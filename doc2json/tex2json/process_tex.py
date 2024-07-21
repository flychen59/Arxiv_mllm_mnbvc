import os
import json
import argparse
import time,sys
from typing import Optional, Dict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from doc2json.tex2json.tex_to_xml import convert_latex_to_s2orc_json
from doc2json.tex2json.xml_to_json import convert_latex_xml_to_s2orc_json
import json
import io
import copy
import os
from PIL import Image
import pandas as pd
from pdf2image import convert_from_path
import pyarrow as pa
import pyarrow.parquet as pq
from collections import OrderedDict
 


BASE_TEMP_DIR = 'temp'
BASE_OUTPUT_DIR = 'output'
BASE_LOG_DIR = 'log'


def process_tex_stream(
        fname: str,
        stream: bytes,
        temp_dir: str=BASE_TEMP_DIR,
        keep_flag: bool=False,
        grobid_config: Optional[Dict] = None
):
    """
    Process a gz file stream
    :param fname:
    :param stream:
    :param temp_dir:
    :param keep_flag:
    :param grobid_config:
    :return:
    """
    temp_input_dir = os.path.join(temp_dir, 'input')
    temp_input_file = os.path.join(temp_input_dir, fname)

    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(temp_input_dir, exist_ok=True)

    with open(temp_input_file, 'wb') as outf:
        outf.write(stream)

    output_file = process_tex_file(
        temp_input_file, temp_dir=temp_dir, keep_flag=keep_flag, grobid_config=grobid_config
    )

    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            contents = json.load(f)
            return contents
    else:
        return []


def process_tex_file(
        input_file: str,
        temp_dir: str=BASE_TEMP_DIR,
        output_dir: str=BASE_OUTPUT_DIR,
        log_dir: str=BASE_LOG_DIR,
        keep_flag: bool=False,
        grobid_config: Optional[Dict]=None
) -> Optional[str]:
    """
    Process files in a TEX zip and get JSON representation
    :param input_file:
    :param temp_dir:
    :param output_dir:
    :param log_dir:
    :param keep_flag:
    :param grobid_config:
    :return:
    """
    # create directories
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # get paper id as the name of the file
    paper_id = os.path.splitext(input_file)[0].split('/')[-1]
    output_file = os.path.join(output_dir, f'{paper_id}.json')
    cleanup_flag = not keep_flag

    # check if input file exists and output file doesn't
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"{input_file} doesn't exist")
    if os.path.exists(output_file):
        print(f'{output_file} already exists!')

    # process LaTeX
    xml_file = convert_latex_to_s2orc_json(input_file, temp_dir, cleanup_flag)
    if not xml_file:
        return None

    # convert to S2ORC
    paper = convert_latex_xml_to_s2orc_json(xml_file, log_dir, grobid_config=grobid_config)

    # write to file
    with open(output_file, 'w') as outf:
        json.dump(paper.release_json("latex"), outf, indent=4, sort_keys=False)

    return output_file,output_file



def read_image(image_path):
    # 打开图像文件
    if image_path.lower().endswith('.pdf'):
                images = convert_from_path(image_path)
                new_image_path = os.path.splitext(image_path)[0] + ".png"
                images[0].save(new_image_path, 'PNG')
                image_path = new_image_path
    with open(image_path, 'rb') as file:
        image = Image.open(file)
        # 将图像转换为二进制格式
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format)
        img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


def save_to_parquet(data, output_path):
    df = pd.DataFrame(data)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, output_path)

def convert_to_target_format_cyp(data, template):
    result=[]
    template["文件id"] = data['paper_id']
    template["处理时间"] = data["header"]["date_generated"]
    
    ## step 1 bod_text map to section
    doc_parse = data["latex_parse"] # todo other doc types
    body_text = doc_parse["body_text"]
    body_dict = OrderedDict() # key: section, value: text
    for text_dict in body_text:
        if text_dict["section"] in body_dict:
            body_dict[text_dict["section"]].append(text_dict) # keep all info
        else:
            body_dict[text_dict["section"]] = [text_dict] # keep all info
    
    ## step 2 build list
    new_entry = copy.deepcopy(template)
    new_entry["块id"] = 'title'
    new_entry["文本"] = data["title"]
    new_entry["数据类型"] = 'text' 
    result.append(new_entry)
    
    new_entry = copy.deepcopy(template)
    new_entry["数据类型"] = 'text' 
    new_entry["块id"] = "abstract"
    new_entry["文本"] = data["abstract"]
    result.append(new_entry)
    
    
    ref_entries = doc_parse["ref_entries"]
    for section, para_list in body_dict.items():
        template["块id"] = section
        for para in para_list:     
            new_entry = copy.deepcopy(template)
            new_entry["文本"] = para['text'] 
            new_entry["数据类型"]='text'
            result.append(copy.deepcopy(new_entry))
            for ref in para["ref_spans"]:
                if "ref_id" in ref and ref["ref_id"] in ref_entries:  
                    new_entry = copy.deepcopy(template)
                    new_entry["数据类型"] =ref_entries[ref["ref_id"]]['type_str']
                    new_entry["块id"] = section
                    if new_entry["数据类型"]=='figure':
                        path=os.path.join('s2orc-doc2json/temp_dir/latex',data['paper_id'],"".join(ref_entries[ref["ref_id"]]["uris"]))
                        # path=os.path.join('./temp_dir/latex',data['paper_id'],"".join(ref_entries[ref["ref_id"]]["uris"]))
                        new_entry["图片"]=read_image(path)   
                    new_entry["文本"] = ref_entries[ref["ref_id"]]['text']
                    filtered_entries = {k: v for k, v in ref_entries[ref["ref_id"]].items() if k != 'text' and 'ref_id' }
                    new_entry["额外信息"] = filtered_entries 
                    result.append(copy.deepcopy(new_entry))
               
            
            for ref in para["cite_spans"]:
                if ref["ref_id"] in ref_entries:  
                    new_entry = copy.deepcopy(template)
                    new_entry["数据类型"] =ref_entries[ref["ref_id"]]['type_str']   
                    new_entry["块id"] = section
                    new_entry["文本"] = ref_entries[ref["ref_id"]]['text'] 
                    filtered_entries = {k: v for k, v in ref_entries[ref["ref_id"]].items() if k != 'text' and 'ref_id' }
                    new_entry["额外信息"] = filtered_entries
                    result.append(copy.deepcopy(new_entry))
            
            for ref in para["eq_spans"]:
                if ref["ref_id"] in ref_entries:  
                    new_entry = copy.deepcopy(template)
                    new_entry["数据类型"] =ref_entries[ref["ref_id"]]['type_str']   
                    new_entry["块id"] = section
                    new_entry["文本"] = ref_entries[ref["ref_id"]]['text'] 
                    filtered_entries = {k: v for k, v in ref_entries[ref["ref_id"]].items() if k != 'text' and 'ref_id' }
                    new_entry["额外信息"] = filtered_entries
                    result.append(copy.deepcopy(new_entry))
    
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run S2ORC TEX2JSON")
    parser.add_argument("-i", "--input", default=None, help="path to the input TEX zip file")
    parser.add_argument("-t", "--temp", default='temp', help="path to a temp dir for partial files")
    parser.add_argument("-o", "--output", default='output', help="path to the output dir for putting json files")
    parser.add_argument("-l", "--log", default='log', help="path to the log dir")
    parser.add_argument("-k", "--keep", default=True, help="keep temporary files")

    args = parser.parse_args()

    input_path = args.input
    temp_path = args.temp
    output_path = args.output
    log_path = args.log
    keep_temp = args.keep

    start_time = time.time()

    os.makedirs(temp_path, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)

    _,output_file=process_tex_file(input_path, temp_path, output_path, log_path, keep_temp)
  

    runtime = round(time.time() - start_time, 3)
  
    
    template = {"文件md5": None, "文件id": None, "页码": None, "块id": None, "文本": None, "图片": None, "处理时间": None, "数据类型": None, "bounding_box": None, "额外信息": None}
    # json_path = '/root/autodl-tmp/s2orc-doc2json/output_dir/2004.14974.json'
    with open(output_file, 'r') as file:
        data = json.load(file)
        result = convert_to_target_format_cyp(data, template)
        
    output_json_path = os.path.splitext(output_file)[0] + ".parquet"
    save_to_parquet(result, output_json_path)
    print("runtime: %s seconds " % (runtime))
    print('done.')
