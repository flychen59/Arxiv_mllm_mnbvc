# Arxiv文档解析(LaTex->Parquet)

## 安装环境

```
conda create -n doc2json python=3.8 pytest
conda activate doc2json
pip install -r requirements.txt
apt install texlive-extra-utils tralics
python setup.py develop
```

## 安装Grobid
```
bash scripts/setup_grobid.sh
bash scripts/run_grobid.sh
```
ps:安装结束后，运行grobid的时候，进度条可能卡在91%，这个是正常状态

## 开始解析
将LaTex压缩包放入/test/latex中，设置输出文件夹，首先启动Groid,运行代码。代码运行例子如下：
```
cd s2orc-doc2json
bash scripts/run_grobid.sh
python doc2json/tex2json/process_tex.py -i test/latex/1911.02782.gz -t temp_dir/ -o output_dir/
```
结果可以在output_dir查看，其中输入文件名的json文件是使用Grobid解析的结果，parquet文件为最终结果。

 
## json中提取信息的方法：
```
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

            ####提取图片信息####
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
               
            ####提取公式####
            for ref in para["cite_spans"]:
                if ref["ref_id"] in ref_entries:  
                    new_entry = copy.deepcopy(template)
                    new_entry["数据类型"] =ref_entries[ref["ref_id"]]['type_str']   
                    new_entry["块id"] = section
                    new_entry["文本"] = ref_entries[ref["ref_id"]]['text'] 
                    filtered_entries = {k: v for k, v in ref_entries[ref["ref_id"]].items() if k != 'text' and 'ref_id' }
                    new_entry["额外信息"] = filtered_entries
                    result.append(copy.deepcopy(new_entry))

            ####提取公式####
            for ref in para["eq_spans"]:
                    new_entry = copy.deepcopy(template)
                    new_entry["数据类型"] ='formula'
                    new_entry["块id"] = section
                    new_entry["文本"] =str(ref)
                    result.append(copy.deepcopy(new_entry))
    
    return result
```

结果如下所示：
{"文件md5":null,"文件id":"2004.14974","页码":null,"块id":"title","文本":"Fact or Fiction: Verifying Scientific Claims","图片":null,"处理时间":"2024-07-21T16:39:40.100123Z","数据类型":"text","bounding_box":null,"额外信息":null}

提取多模态信息一览：
| 类型      | Caption |
|-----------|-----|
| 图片     |"数据类型":"figure","文本":"A SciFact claim refuted by evidence. To refute this claim,....","图片": {"0":137,"1":80,"2":78,"3":71,"4":13,"5":10,"6":26,"7":10,"8":0} ,"数据类型":"figure"| 
| 表格       |  "数据类型":"table","额外信息":{"content":[],"fig_num":null,"html":"","num":"1","parent":null,"type_str":"table","uris":null}}| 
| 网址   |  "数据类型":"footnote","文本":"https://colab.research.google.com/" | 
| 标题  |  "数据类型":"section","文本":"Related Work" | 
| 公式  |  "数据类型":"formula","文本":'{\'start\': 297, \'end\': 308, \'text\': \'n  test  \', \'latex\': \'n_{\\\\textrm {test}}\', \'mathml\': \'<math xmlns="http://www.w3.org/1998/Math/MathML" display="inline"><mrow><msub><mi>n</mi><mrow><mi>\\\\textrm</mi><mrow><mi>t</mi><mi>e</mi><mi>s</mi><mi>t</mi></mrow></mrow></msub></mrow></math>\', \'ref_id\': \'INLINEFORM2\'}'" | 

      

图文通用语料的格式说明：
文件md5: 这个字段存储文件的MD5哈希值。MD5是一种广泛使用的哈希函数，它产生一个128位（16字节）的哈希值，通常用于确保数据的完整性。在这里，它可以用来唯一标识文件，或者检查文件是否被更改。

文件id: 文件的唯一标识符。这可以是一个数据库中的主键，或者任何用于唯一标识文件的系统。

页码: 如果数据源是一个多页文档（如PDF文件），这个字段表示文本或图片所在的具体页码。

块id: 一个实体对象内的标识符。用于确定一条数据内的一个部分数据。parquet 行的最小单元。设置为读取部分所在文章中的意义，比如title。

文本: 存储文档中的文本内容。特定段落或页面的文本，或者图表所涉及到的相关内容

图片: 如果文档中包含图片，这个字段存储图片的数据。用二进制进行保存。

时间: 处理文本的时间

数据类型: 数据类型文本，图片，表格，公式，引用

bounding box: 四点坐标（两点坐标请补全到四点），用以支持版面分析等数据。请本文档作者补充数据示例。

额外信息: 存放各种额外信息，比如 在假如数据类型为图片，则存放的可以是一个json格式文本大字段(text存储，需要解析一下)。

