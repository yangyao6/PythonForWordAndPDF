import urllib
import time
import os
import re
import jsonpath
import json
import random
import datetime

log_dir='C:/Users/Administrator/Desktop/'
img_dir='D:/photo/ZTB/'
config_dir='F:/python/config'
data_dir='C:/Users/Administrator/Desktop/'
#data_dir='C:/Users/Administrator/Desktop/DAIYUYING/'
channel_name='pactera'

#写入日志
def GetLog(name,data):
    datetime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    date=time.strftime("%Y-%m-%d",time.localtime())
    data='[%s]%s:::::%s' %(str(datetime),str(date),data)
    file = '%s%s_%s_%s.txt' % (log_dir,name, 'LOG',str(date))
    with open(file, 'a', encoding='utf-8') as f:
        f.write(data)
        f.write('\n')

#下载图片
def GetImg(dir,url,img_name):

    urllib.request.urlretrieve(url, '%s%s' % (dir, img_name))
    '''
    try:
         #conn = urllib.request.urlopen(url)
         urllib.request.urlretrieve(url,'%s%s' %(img_dir, img_name))
    except Exception as e:
         print(e)
         print(url)
         print('无法下载请检查路径')
         GetLog('dzdp_deatail','%s:%s' %(url,'无法下载请检查路径'))
         return None
    '''
    #img = conn.read()
    #with open('%s%s' %(img_dir, img_name), 'wb') as f:
     #   f.write(img)

#写入文件
def GetFile(filename,data,type,count):
    # 没有文件夹生成
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    # 没有文件的话生成文件
    if os.path.exists(r'%s%s_variable.txt' %(config_dir,filename)):
        pass
    else:
        with open('%s%s_variable.txt' %(config_dir,filename), 'w', encoding='utf-8') as f:
            pass

    variable = len(open('%s%s_variable.txt' %(config_dir,filename),encoding='utf-8').readlines())
    file='%s%s_%s_%d.txt' % (data_dir,channel_name, filename,variable)
    # 没有文件的话生成文件
    if os.path.exists(r'%s' % file):
        pass
    else:
        with open(file, 'w', encoding='utf-8') as f:
            pass

    if type==1:
        with open(file, 'a', encoding='utf-8') as f:
           f.write(data)
           f.write('\n')
    if type==3:
        sum = -1
        for sum, line in enumerate(open(r"%s" % file, 'rU', encoding='utf-8')):
            pass
        sum += 1
        if sum<count:
            with open(file, 'a', encoding='utf-8') as f:
                f.write(data)
                f.write('\n')
        else:
            with open('%s%s_variable.txt' %(config_dir,filename), 'a', encoding='utf-8') as f:
                f.write('global')
                f.write('\n')
            variable = len(open('%s%s_variable.txt' %(config_dir,filename),encoding='utf-8').readlines())
            file = '%s%s_%s_%d.txt' % (data_dir,channel_name, filename, variable)
            with open(file, 'a', encoding='utf-8') as f:
                f.write(data)
                f.write('\n')


def re_text(s):
    '''替换特殊字符
    :param str:
    :return:
    '''
    regular = ['\xa0','\u3000','\t','\n',' ','\r','\r\n','\n\r','"']
    if s is None:
        print('检查数据，re_text()方法现在的输入数据为',s)
        return ''

    if isinstance(s,str):
        for r in regular:
            try:
                s = s.replace(r,'')
            except:
                print('errodata:',str)
        s = s.strip()
        return s
    else:
        return s

def deal_text(str):
    '''把文本的换行等换成|，其它的去掉
    :param str:
    :return:
    '''
    regular = ['\xa0', '\u3000', '\t', ' ']
    huiche = ['\n','\r','\r\n','\n\r']
    special = [{'code':'"','expr':'\\"'}]
    for r in huiche:
        str = str.replace(r,'|')
    for r in regular:
        str = str.replace(r,'')
    for r in special:
        str = str.replace(r['code'], r['expr'])
    str = str.strip()
    return str

def replace_special_text(str):
    '''替换多个|
    :param str:
    :return:
    '''
    expr1 = '[|]+'
    str = re.sub(expr1, '|', str)  # 把连续的\r\n（1个到多个连续的）替换为|
    expr2 = '^[|]'
    str = re.sub(expr2, '', str)  # 替换最开头|为空
    return str

def join_group(group,lengroup):
    '''  [('','b')，('a','')] 这种合并成['a','b']
    :param group:
    :return:
    '''
    l = ['']*lengroup
    #for i_ in group:

    for i in group:
        for j in i:
            if j != '':
                index = i.index(j)
                #l.insert(index, j)
                l[index] = j
    return l

def str_encode(s):
    '''将一个字符串转换为相应的二进制串（01形式表示）
    :param s:
    :return:
    '''
    return ' '.join([bin(ord(c)).replace('0b', '') for c in s])

def str_decode(s):
    '''够将这个二进制串再转换回原来的字符串
    :param s:
    :return:
    '''
    return ''.join([chr(i) for i in [int(b, 2) for b in s.split(' ')]])


def get_jp_value(data, expr):
    if isinstance(data,str):
        data =json.loads(data)
    return jsonpath.jsonpath(data, expr)

def format_date(s):
    if s == '' or s == 'None' or s == 'True' or s == 'False':
        return s

    if isinstance(s,str):
       if '年' in s and '月' in s and '日' in s:
            return s
       if '.' in s:
           s = s.split('.')
           if len(s[0]) == 2:
               s[0] = '20' + s[0]
       elif '-' in s:
           s = s.split('-')
           if len(s[0]) == 2:
               s[0] = '20' + s[0]
       elif '/' in s:
           s = s.split('/')
           if len(s[0]) == 2:
               s[0] = '20' + s[0]
       elif len(s) == 8:
           s = [s[:4],s[4:6],s[6:]]
       return '%s年%s月%s日' %(s[0],s[1],s[2])
    elif isinstance(s,int):
        if len(str(s)) == 13:
            s = int(s/1000)
        timeArray = time.localtime(s)
        return '%s年%s月%s日' %(time.strftime('%Y', timeArray),time.strftime('%m',timeArray),time.strftime('%d',timeArray))


def unique_time():
    #nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 生成当前时间
    time.sleep(0.001)
    nowTime = str(int(time.time()*1000))[7:]
    randomNum = random.randint(0, 100)  # 生成的随机整数n，其中0<=n<=100
    if randomNum <= 10:
        randomNum = str(0) + str(randomNum)
    randomNum1 = random.randint(1, 100)
    uniqueNum = str(nowTime) + str(randomNum) + str(randomNum1)
    return uniqueNum