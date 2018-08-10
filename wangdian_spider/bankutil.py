from lxml import etree
from scrapy.selector import Selector
from wangdian_spider.TextTool import re_text
from wangdian_spider.TextTool import format_date
import re
import requests
import json
import uuid
import demjson
import execjs
import time
import traceback
import os



def request_util(method,url,column=None,node=None,node1=None,op=None,parm=None,poi=None,
                 data=None,headers=None,extra=None,_id=False,expr=None,replacev=None,special_col=None,
                 backlist=False,readdress=None,cookies=None,dictkey=False,*args,**kwargs):
    '''
    :param method:
    :param url:
    :param column:
    :param node:
    :param node1:
    :param op:
    :param parm:
    :param poi:
    :param data:
    :param headers:
    :param extra:
    :param _id:
    :param expr:
    :param special_col:
    :param replacev:
    :param backlist:
    :param readdress:
    :param cookies:
    :param dictkey:  代表字典的key 是否是恒定的，False是恒定的比如{key：[value1],key：[value2]}，True是不恒定的 比如 {key1：[value1],key2：[value2]}
    :param args:
    :param kwargs:
    :return:
    '''
    blist = []
    out_dict = {}
    try:
        con = requests.request(method=method, url=url, params=parm, headers=headers, data=data, cookies=cookies)
        try:
           con = con.content.decode('utf-8')
        except:
           con = con.content.decode('gbk')

        if expr is not None:
            pattern = re.compile(expr)
            con = re.findall(pattern,con)
            if len(con) == 1:
                con = con[0]
            else:
                print('其它值跳出')
                return None
        if replacev is not None:
            for i in replacev:
               con.replace(i[0],i[1])

        if isinstance(con,str):
            # data = json.loads(con)
            data = demjson.decode(con) #用它是因为 key 值可能没有引号 比如: {a : 1,b:'sss'} 这种情况，用它可以给key值加上引号，这个比标准库慢些
            #data = execjs.eval(con)  #这个也可以
        else:
            pass #其它的类型会报错，比如字典
    except Exception as e:
        traceback.print_exc()
        print('error', e)
        #print(url, parm, headers, out_dictname)
        return None

    if node is not None:
        for n in node.split('.'):
            data = data[n]

    if dictkey:
        tdata = []
        for d in data:
            if isinstance(data[d],list):
                for _d in data[d]:
                    tdata .append(_d)
        data = tdata

    for ci in data:
        o_dict = {}
        try:
            if _id :
                o_dict['_id'] = uuid.uuid1()  # ObjectId(bytes(str(round(time.time()*100)).encode('utf-8')))
            if extra is not None:
                if isinstance(extra,dict):
                    for e_ in extra:
                        o_dict[e_] = extra[e_]
            if column is not None:
                if isinstance(column, dict):
                   if node1 is not None:
                       for c_ in column:
                           o_dict[c_] = re_text(ci[node1][column[c_]])
                   else:
                       for c_ in column:
                           o_dict[c_] = re_text(ci[column[c_]])
                elif isinstance(column,list):
                    out_dict[ci[column[0]]] = ci[column[1]]
            if special_col is not None:
                if isinstance(special_col, list) and isinstance(special_col[0], tuple) and len(special_col[0]) == 4 and isinstance(special_col[0][2],list):
                    for s in special_col:
                        ol = o_dict[s[0]].split(s[1])
                        cl = special_col[0][2]
                        for c_ in cl:
                            if s[3] == 'date':
                                o_dict[c_] = format_date(ol[cl.index(c_)])
                            else:
                                o_dict[c_] = ol[cl.index(c_)]
                elif isinstance(special_col, list) and isinstance(special_col[0], tuple) and len(special_col[0]) == 2:
                    for s in special_col:
                        if s[1] == 'date':
                            o_dict[s[0]] = format_date(o_dict[s[0]])
                else:
                    print('special_col 格式不正确')
            if poi is not None:
                if readdress is not None:
                    if o_dict[poi] == readdress:
                        latlon = checkaddress(readdress)
                    else:
                        continue
                else:
                    ta = re.findall('(.*?)[#|（]',o_dict[poi])
                    if len(ta) > 0:
                        o_dict[poi] = ta[0]
                    latlon = checkaddress(o_dict[poi])

                if latlon:
                    o_dict.update(latlon)
                else:
                    print('百度API没有查询到经纬度,请重新跑')
                    print('地址为:',o_dict[poi])
            if op is not None:
               op.I_Mongodb(o_dict)
            if backlist:
                blist.append(o_dict)
        except Exception as e:
            traceback.print_exc()
            pass


    if  len(out_dict)>0 and not backlist:
        return out_dict
    elif backlist:
        return blist
    else:
        return data

def request_util_html(method,url,parm=None,headers=None,data=None,node=None,column=None,op=None,_id=False,
                      backlist=None,special_col=None,poi=None,readdress=None,extra=None):
    out_dict = {}
    blist = []
    try:
        con = requests.request(method=method, url=url, params=parm, headers=headers, data=data)
        data = Selector(text=con.content)
    except Exception as e:
        print(e)
        traceback.print_exc()
        return False

    if node is not None:
        data = data.xpath(node)

    if not isinstance(data,list):
        data = [data]

    for sel in data:
         o_dict ={}
         try:
             if _id:
                 o_dict['_id'] = uuid.uuid1()  # ObjectId(bytes(str(round(time.time()*100)).encode('utf-8')))
             if extra is not None:
                 if isinstance(extra, dict):
                     for e_ in extra:
                         o_dict[e_] = extra[e_]
             if column is not None:
                 if isinstance(column, dict):
                     for c_ in column:
                         o_dict[c_] = re_text(sel.xpath(column[c_]).extract_first())
                 if isinstance(column,list):
                     for c_ in column:
                         out_dict[c_[0]] = re_text(sel.xpath(c_[1]).extract_first())
             if special_col is not None:
                 if len(out_dict) > 0 :
                     o_dict = out_dict
                 if isinstance(special_col, list) and isinstance(special_col[0], tuple) and \
                                 len(special_col[0]) == 4 and isinstance(special_col[0][2], list):
                     for s in special_col:
                         ol = o_dict[s[0]].split(s[1])
                         cl = special_col[0][2]
                         for c_ in cl:
                             if s[3] == 'date':
                                 o_dict[c_] = format_date(ol[cl.index(c_)])
                             else:
                                o_dict[c_] = ol[cl.index(c_)]
                 elif isinstance(special_col, list) and isinstance(special_col[0], tuple) and len(special_col[0]) == 2:
                     for s in special_col:
                         if s[1] == 'date':
                             o_dict[s[0]] = format_date(o_dict[s[0]])
                 else:
                     print('special_col 格式不正确')
             if poi is not None:
                 if readdress is not None:
                     if o_dict[poi] == readdress:
                         latlon = checkaddress(readdress)
                     else:
                         continue
                 else:
                     latlon = checkaddress(o_dict[poi])

                 if latlon:
                     o_dict.update(latlon)
                 else:
                     o_dict['lng'] = ''
                     o_dict['lat'] = ''
                     print('百度API没有查询到经纬度,请重新跑')
                     print('地址为:', o_dict[poi])
             if op is not None:
                 op.I_Mongodb(o_dict)
             if backlist:
                 blist.append(o_dict)
         except Exception as e:
             traceback.print_exc()
             print(e,url)
             pass

    if  len(out_dict)>0 and not backlist:
        return out_dict
    elif backlist:
        return blist
    else:
        return data

def checkaddress(adress):
    time.sleep(0.5)
    #ak = '4baNkPn8A7OcUCD8oe04eLxYUaUc3elu'
    file = 'F:/python/Competitive_Analysis/ak.txt'
    ak = []
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.replace('\n', '')
            if line.split(':')[1] == '可用':
                ak.append(line.split(':')[0])

    if len(ak) == 0:
        print('没有ak用了')
        return False

    # r = requests.get('http://api.map.baidu.com/geocoder?output=json&address=%s' %adress.replace(' ','').replace('\n',''))
    r = requests.get('http://api.map.baidu.com/geocoder/v2/?address=%s&output=json&ak=%s' % (
    adress.replace(' ', '').replace('\n', ''), ak[0]))
    json_data = eval(r.text)
    data = {}
    if json_data[u'status'] == 0:
        try:
            lng = json_data[u'result'][u'location'][u'lng']
            lat = json_data[u'result'][u'location'][u'lat']
            data['lng'] = lng
            data['lat'] = lat
        except:
            data['lng'] = ''
            data['lat'] = ''

        return data
    elif json_data[u'status'] == 4 or json_data[u'status'] == 302:
        print('服务当日调用次数已超限')

        with open(file, "r", encoding="utf-8") as f1, open("%s.bak" % file, "w", encoding="utf-8") as f2:
            for line in f1:
                f2.write(re.sub('%s:可用\n' % ak[0], '%s:不可用\n' % ak[0], line))

        os.remove(file)

        os.rename("%s.bak" % file, file)

        return None
    else:
        return False
