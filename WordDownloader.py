import urllib.request
import sys
import re
import os

# open the url and read
def getHtml(url):
    page = urllib.request.urlopen(url)
    html = page.read()
    page.close()
    return html

# compile the regular expressions and find
# all stuff we need
def getUrl(html):
    reg = r'(?:href|HREF)="?((?:http://)?.+?\.doc(?:x|))'
    url_re = re.compile(reg)
    html = html.decode('utf-8')  # python3
    url_lst = re.findall(url_re, html)
    return(url_lst)

def getFile(url):
    file_name = url.split('/')[-1]
    u = urllib.request.urlopen(url)
    f = open(file_name, 'wb')

    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        f.write(buffer)
    f.close()
    print("Successful to download" + " " + file_name)

# 附件下载固定url
root_url = sys.argv[1]
# 内容详情页面url
raw_url = sys.argv[2]

# root_url = 'http://www.uccb.com.cn/'
#
# raw_url = 'http://www.uccb.com.cn/notice/noticedetail.aspx?info=IVZwcTyzpEs='

html = getHtml(raw_url)
url_lst = getUrl(html)

isExists = os.path.exists(r'C:\PythonWorkspace\ldf_download')
if not isExists:
    os.mkdir('ldf_download')
os.chdir(os.path.join(os.getcwd(), 'ldf_download'))

for url in url_lst[:]:
    url = root_url + url
    getFile(url)