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
其中

