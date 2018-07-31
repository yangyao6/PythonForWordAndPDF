# 抓取并读取网页pdf
# pdf READ operation
from urllib.request import urlopen
from urllib.error import URLError
from urllib.error import HTTPError
from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from io import StringIO, open
import sys
import os


# 也可以读取由pdffile=open("../../readme.pdf")语句打开的本地文件。
url = sys.argv[1]
# url = 'http://www.ynhtbank.com/ynhtyh/resource/cms/article/sub295208/378927/2018072715111046526.pdf'


def readPDF(filename):
    resmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    device = TextConverter(resmgr, retstr, laparams=laparams)

    process_pdf(resmgr, device, filename)
    device.close()

    content = retstr.getvalue()
    retstr.close()
    return content


try:
    pdffile = urlopen(url)


except (URLError, HTTPError) as e:
    print("Errors:\n")
    print(e)


# 写到文件pdftext.txt中
if os.path.exists(r'C:\PythonWorkspace/pdftext.txt'):
    os.remove('C:\PythonWorkspace/pdftext.txt')

outputString = readPDF(pdffile)
with open('C:\PythonWorkspace/pdftext.txt', 'a', encoding='utf-8') as f:
    f.write(''.join(outputString))
pdffile.close()


# 输出到console控制台
# outputString = readPDF(pdffile)
# print(outputString)
# pdffile.close()
