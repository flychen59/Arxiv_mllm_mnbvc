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

结果如下所示：
{"文件md5":null,"文件id":"2004.14974","页码":null,"块id":"title","文本":"Fact or Fiction: Verifying Scientific Claims","图片":null,"处理时间":"2024-07-21T16:39:40.100123Z","数据类型":"text","bounding_box":null,"额外信息":null}

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

