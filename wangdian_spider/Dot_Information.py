from lxml import etree
from bson.objectid import ObjectId
from Competitive_Analysis.OpMongon import Op_MongoDB
from wangdian_spider.bankutil import request_util
from wangdian_spider.bankutil import request_util_html
from wangdian_spider.bankutil import checkaddress
from Competitive_Analysis.useragent import user_agent_list
from wangdian_spider.TextTool import re_text
from urllib.parse import unquote
from scrapy.selector import Selector
import requests
import time
import json
import uuid
import datetime
import random
import re


header = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'
}

def I_Data(op,data):
    try:
        op.I_Mongodb(data)
    except:
        n = 0
        for i in range(5):
            try:
                print('%d time reconnection.....' % i)
                op.I_Mongodb(data)
                break
            except:
                n = n + 1
                time.sleep(2)
        if n > 4:
            raise 'reconnection time pass 5 time'

def dict_division(d,pid,pname,cid,cname,rid,rname):
    try:
        d['provinceid'] = pid
        d['province'] = pname
        d['citycode'] = cid
        d['city'] = cname
        d['regionid'] = rid
        d['region'] = rname
    except Exception as e:
        print(e)
        print(d,pid,pname,cid,cname,rid,rname)
        return False
    return d

def object_id_from_datetime(from_datetime=None, span_days=0, span_hours=0, span_minutes=0, span_seconds=0,
                            span_weeks=0):
    '''根据时间手动生成一个objectid，此id不作为存储使用'''
    if not from_datetime:
        from_datetime = datetime.datetime.now().microsecond

    # if span_days==0:
    #     span_days = round(random.random()*10)

    from_datetime = from_datetime + datetime.timedelta(days=span_days, hours=span_hours, minutes=span_minutes,
                                                       weeks=span_weeks)

    return ObjectId.from_datetime(generation_time=from_datetime)

class Bank_DI:

    def __init__(self,collname,key):
        self.collname = collname
        self.key = key
        self.op = Op_MongoDB(db='BankCompetitive',coll=collname+'DI',key=key)

    def BOC(self):

        def Get_Data(html,exitdata,area):
            dilist = html.xpath('//*[@id="documentContainer"]/tr')
            for di in dilist:
                orgdata = {}
                organization = di.xpath('td[1]')
                if len(organization) == 0:
                    continue
                orgdata['name'] = organization[0].text
                if orgdata['name'] in exitdata:
                    continue
                orgdata['location'] = di.xpath('td[2]')[0].text
                orgdata['mechanism_level'] = di.xpath('td[3]')[0].text
                orgdata['address'] = di.xpath('td[4]')[0].text
                ta = re.findall('(.*?)[#|（]', orgdata['address'])
                if len(ta) > 0:
                    orgdata['address'] = ta[0]
                data = checkaddress(orgdata['address'])
                if data:
                    orgdata.update(data)
                else:
                    orgdata['lng'] = ''
                    orgdata['lat'] = ''
                orgdata['phone'] = di.xpath('td[5]')[0].text
                orgdata['status'] = di.xpath('td[6]')[0].text
                if area == '天津保税区':
                    area = '天津市'
                orgdata['city'] = area
                try:
                    self.op.I_Mongodb(orgdata)
                except:
                    n = 0
                    for i in range(5):
                        try:
                            print('%d time reconnection.....' % i)
                            self.op.I_Mongodb(orgdata)
                            break
                        except:
                            n = n + 1
                            time.sleep(2)
                    if n > 4:
                        raise 'reconnection time pass 5 time'

        exitdata = self.op.S_Mongodb(output='name')
        area = {}
        url = 'http://www.bankofchina.com/sourcedb/operations/'
        conn = requests.request(method='GET',url=url)
        html = etree.HTML(conn.content.decode('utf-8'))
        arealist = html.xpath('//*[@id="apDiv1"]/div/table/tr/td/table//tr/td/a')
        for p in arealist:
            area[p.text] = p.attrib['href']

        data = True
        for a in area:
            if data is None:
                break
            try:
                url = 'http://www.bankofchina.com/sourcedb/operations'+ str(area[a]).replace('.','')
                con = requests.request(method='GET', url=url, headers=header)
                html = etree.HTML(con.content.decode('utf-8'))
                Get_Data(html,exitdata,a)
                total = html.xpath('//div[@class="turn_page"]/p/span')
                if len(total)>0:
                    totalpage = int(total[0].text)
                    for i in range(1,totalpage):
                        url = 'http://www.bankofchina.com/sourcedb/operations'+ str(area[a]).replace('.','') + '/index_%d.htm' %i
                        con = requests.request(method='GET', url=url, headers=header)
                        html = etree.HTML(con.content.decode('utf-8'))
                        Get_Data(html,exitdata,a)
            except Exception as e:
                print(e)

    def CCB(self):
        '''
        ###武汉和郑州抛异常
        :return:
        '''
        url = 'http://www.ccb.com/tran/WCCMainPlatV5?'
        proparm = {'CCB_IBSVersion':'V5','SERVLET_NAME':'WCCMainPlatV5','isAjaxRequest':'true','TXCODE':'NAREA1','type':'1','areacode':'110000'}
        proparm['_'] = str(int(time.time()*1000))

        provincedata = requests.request(method='GET',url=url,params=proparm,headers=header)

        province = {}
        for area in eval(provincedata.text)['arealist']:
            try:
                areacode = area['areacode']
                NET_NAME = area['NET_NAME']
                province[NET_NAME] = areacode
            except:
                pass

        city = {}
        for codename in province:
            cparm = {'CCB_IBSVersion':'V5','SERVLET_NAME':'WCCMainPlatV5','isAjaxRequest':'true','TXCODE':'NAREA1','type':'2'}
            cparm['areacode'] = province[codename]
            countrydata = requests.request(method='GET', url=url, params=cparm, headers=header)
            for area in eval(countrydata.text)['arealist']:
                try:
                    areacode = area['areacode']
                    NET_NAME = area['NET_NAME']
                    city[NET_NAME] = areacode
                except:
                    pass


        def doi(url,parm,header,name,aname):
            di = {}
            try:
              data = json.loads(requests.request(method='GET', url=url, params=parm, headers=header).text)
            except Exception as e :
              print('error',e)
              print(url,parm,header,name,aname)
              return None

            for c in data['ARRAY_CMG001']:
                try:
                    di['_id'] = uuid.uuid1()#ObjectId(bytes(str(round(time.time()*100)).encode('utf-8')))
                    di['name'] = c['NET_NAME']
                    di['netcode'] = c['NET_ID']
                    di['address'] = c['NET_AREA']
                    di['NET_DCC'] = c['NET_DCC']
                    di['lat'] = c['Y_COORDINATE']
                    di['lng'] = c['X_COORDINATE']
                    di['phone'] = c['NET_PHONE']
                    di['city'] = name
                    di['area'] = aname
                    self.op.I_Mongodb(di)
                except:
                    pass

            return data

        for cityname in city:
            rparm = {'CCB_IBSVersion': 'V5', 'SERVLET_NAME': 'WCCMainPlatV5', 'isAjaxRequest': 'true',
                     'TXCODE': 'NAREA1', 'type': '3'}
            rparm['areacode'] = city[cityname]
            regiondata = requests.request(method='GET', url=url, params=rparm, headers=header)
            region = {}
            for reg in eval(regiondata.text)['arealist']:
                try:
                    areacode = reg['areacode']
                    NET_NAME = reg['NET_NAME']
                    region[NET_NAME] = areacode
                except:
                    pass

            for area in  region:

                aparm = {'CCB_IBSVersion': 'V5', 'SERVLET_NAME': 'WCCMainPlatV5', 'isAjaxRequest': 'true',
                         'TXCODE': 'NZX001','NET_KEYWORD':' ','NET_FLAG':'1','CURRENT_PAGE':'1'}
                aparm['AREA_NAME'] = region[area]
                adata = doi(url,aparm,header,cityname,area)
                if adata is None:
                    continue
                CURRENT_PAGE = adata['CURRENT_PAGE']
                TOTAL_PAGE = adata['TOTAL_PAGE']
                while CURRENT_PAGE < TOTAL_PAGE:
                    aparm['CURRENT_PAGE'] = str(int(aparm['CURRENT_PAGE']) + 1)
                    adata = doi(url,aparm,header,cityname,area)
                    if adata is None:
                        CURRENT_PAGE = aparm['CURRENT_PAGE']
                        continue
                    CURRENT_PAGE = adata['CURRENT_PAGE']

    def ABC(self):
        columnname = {'name': 'Name',
                      'address':'Address',
                      'superiorlevel1':'SuperiorLevel1',
                      'superiorlevel2':'SuperiorLevel2',
                      'branchlevel':'BranchLevel',
                      'lat':'Latitude',
                      'lng':'Longitude'
                  }

        url1 = 'http://app.abchina.com/branch/common/BranchService.svc/District'
        column = ['Name','Id']
        province = request_util('GET',url=url1,column=column)

        for p in province:
            url2 = url1 + '/' + str(province[p])
            city = request_util('GET', url=url2, column=column)
            for c in city:
                url3 = url1 + '/Any/' + str(city[c])
                region = request_util('GET', url=url3, column=column)
                for r in region:
                    url = 'http://app.abchina.com/branch/common/BranchService.svc/Branch'
                    parm = {'q':'','t':'1','z':'0','i':'0'}
                    parm['p'] = province[p]
                    parm['c'] = city[c]
                    parm['b'] = region[r]

                    didata = request_util(method='GET', url=url, column=columnname,parm=parm,node='BranchSearchRests',node1='BranchBank',backlist=True)

                    if len(didata) == 0:
                        continue

                    if len(city) == 1 :
                        cname = c
                    else:
                        if '吉林市' in c:
                            cname = '吉林市'

                        if c in ['山南地区','哈密地区']:
                            cname = c.replace('地区', '市')
                        else:
                            cname = c.replace(p,'')

                        if cname in ['石家庄']:
                            cname = cname + '市'

                    data = dict_division(didata[0],province[p],p,city[c],cname,region[r],r)
                    if data:
                       I_Data(self.op,data)
                    else:
                        continue

    def ICBC(self):
        pass

    def BOCOM(self):
        url = 'http://www.bankcomm.com/BankCommSite/zonghang/cn/node/queryCityResult.do'
        header['Accept'] = '*/*'
        data = request_util('GET', url=url,node='citys')
        for i in data:
            province = i.split('|')[1]
            citydata = data[i]
            for cityid in citydata:
                cid = cityid
                cityname = citydata[cityid]['d']
                de = citydata[cityid]['de']
                postdata = {'cityName':cityname+'市'}
                url = 'http://www.bankcomm.com/BankCommSite/zonghang/cn/node/queryCountyByCityName.do'
                areadata = request_util(method='POST', url=url, node='citys',headers=header,data=postdata)
                dename = de+'|'+cityname
                try:
                  regiondata = areadata[dename]
                except:
                  continue
                for regionid in regiondata:
                    rid = regionid
                    regionname = regiondata[regionid]['d']
                    url = 'http://www.bankcomm.com/BankCommSite/zonghang/cn/node/queryBranchResult.do'
                    postdata = {'city': cityname + '市','countyName':regionname,'urlType':''}
                    didata = request_util(method='POST', url=url, node='data',headers=header,data=postdata)
                    for d in didata:
                        di = {}
                        di['name'] = didata[d]['n']
                        di['lng'] = didata[d]['x']
                        di['lat'] = didata[d]['y']
                        di['phone'] = didata[d]['p']
                        di['address'] = unquote(didata[d]['a'])
                        di = dict_division(di,'',province,cid,cityname+'市',rid,regionname)
                        self.op.I_Mongodb(di)

    def CDRCB(self):
        url = 'http://www.cdrcb.com/map/cdnsmapdata.php'
        fromdata = { 'query_prov': '四川','query_city': '',
                     'query_area': '','query_type': '',
                     'query_key': '',
                     'query_page':'1'}
        data = requests.request(method='POST',url=url,data=fromdata)
        didata = eval(data.text.replace('42|+|1|+|11',''))
        for d in  didata:
            di = {}
            di['name'] = d[2]
            di['lng'] = d[0]
            di['lat'] = d[1]
            di['phone'] = d[3].split('：')[2]
            di['address'] = d[3].split('：')[1].replace('<br/>电话','')
            di = dict_division(di, '', d[5], '', d[6]+'市', '', d[7])
            self.op.I_Mongodb(di)

    def BJRCB(self):
        columnname = {'name': 'name',
                      'address': 'address',
                      'phone':'phone',
                      'opentime':'openTime'
                      }
        url = 'http://channel1.mapbar.com/thememap/bjrcb/listSearch.jsp'
        data = {'infoType': '810',
                'post': 'listSearch.jsp',
                'dist': '',
                'addr': ''
                }
        expr = 'pois =([\s\S]*?)function'
        # data = request_util(method='POST',url=url,data=data,headers=header,expr=expr,node='poi',
        #                     column=columnname,backlist=True,poi='address',op=self.op,_id=True)

        data['totalnum'] = '492'
        data['infoType'] = '810'

        extra = {'city':'北京市'}

        for i in range(9,11):
            data['page'] = str(i)
            request_util(method='POST', url=url, data=data, headers=header, extra=extra,expr=expr, node='poi',
                                column=columnname, backlist=True, poi='address', op=self.op, _id=True)

        # a = '%BA%A3%B5%ED%C7%F8'
        # print(unquote(a,encoding='gbk'))
        # a = '海淀区'
        # print(quote(a,encoding='gbk'))

    def HXB(self):
        a = '118.637531.32.063424'
        url = 'http://www.hxb.com.cn/hxmap/get_area.jsp'
        parm = {'jsonpcallback': 'jQuery1124016609334159130995_1532621553580',
                '_': int(time.time()*1000)
                }
        expr = '\((.*?)\)'
        province = request_util(method='GET',url=url,parm=parm,expr=expr)
        expr = '\(([\s\S]*)\)'

        columnname = {'name': 'bankName',
                      'address': 'address',
                      'opentime': 'time',
                      'citycode': 'branchCode',
                      'bankid': 'bankId',
                      'netcode':'bankCode',
                      'YX': 'posYX'
                      }

        url = 'http://www.hxb.com.cn/hxmap/get_bank.jsp'
        url1 = 'http://www.hxb.com.cn/hxmap/get_branch.jsp'
        parms = {  'jsonpcallback': 'jQuery1124022206501609783658_%s' %str(int(time.time()*1000)),
                    'params.status': '1',
                    '_': int(time.time()*1000)}

        parm['jsonpcallback'] = 'jQuery1124004991335373059802_1532672616956'
        parm['params.branchCode'] = ''
        parm['params.bankName'] = ''
        parm['params.bankType'] = '0'
        parm['page'] = 1
        parm['params.status'] = '1'

        cookie = {'toorbar_view':'false',
                  'toorbar_tview':'false',
                  'toorbar_tips':'false',
                  'toorbar_pagez':'',
                  'fsize_i':'0',
                  'toorbar_clo':'',
                  'toorbar_guidesSwitch':'false',
                  'toorbar_tipsSwitch':'false',
                  'toorbar_pySwitch':'true',
                  'JSESSIONID':'00006g-q_HXkyQ3dZCMgBTLByCp:1bhr1d0ap	'}

        for p in province:
            if p['areaNo'] == 'BEJ' or  p['areaNo'] == 'TAJ' or p['areaNo'] == 'SHH' or  p['areaNo'] == 'CHQ':
                continue
            if p['areaNo'] == 'ANH' or  p['areaNo'] == 'FUJ' or p['areaNo'] == 'GAN' or  p['areaNo'] == 'GUD':
                continue
            if p['areaNo'] == 'GUI' or  p['areaNo'] == 'GXI' or p['areaNo'] == 'HAI' or  p['areaNo'] == 'HEB':
                continue
            if p['areaNo'] == 'HEN' or  p['areaNo'] == 'HKG' or p['areaNo'] == 'HLJ' or  p['areaNo'] == 'HUB':
                continue
            if p['areaNo'] == 'HUN' or  p['areaNo'] == 'JIL' or p['areaNo'] == 'JSU' or  p['areaNo'] == 'JXI':
                continue
            if p['areaNo'] == 'LIA' or  p['areaNo'] == 'NMG' or p['areaNo'] == 'NXA' or  p['areaNo'] == 'QIH':
                continue
            if p['areaNo'] == 'SCH' or  p['areaNo'] == 'SHA' or p['areaNo'] == 'SHD' or  p['areaNo'] == 'SHX':
                continue
            if p['areaNo'] == 'TAI' or  p['areaNo'] == 'TIB' or p['areaNo'] == 'XIN' or  p['areaNo'] == 'YUN':
                continue
            if p['areaNo'] == 'ZHJ' or  p['areaNo'] == 'TIB' or p['areaNo'] == 'XIN' or  p['areaNo'] == 'YUN':
                continue
            rt = random.uniform(1.154651,5.54616)
            time.sleep(rt)
            result = []
            parm['params.proNo'] = p['areaNo']
            parms['params.proNo'] = p['areaNo']
            parm['_'] = int(time.time() * 1000)

            data = request_util(method='GET',headers=header, url=url, parm=parm,expr=expr)
            page = data['page']
            pageCount = data['pageCount']
            rowCount = data['rowCount']
            #print(p['areaNo'],data)
            for i in range(page,pageCount+1):
                parm['page'] = i
                parm['_'] = int(time.time()*1000)
                header['User-Agent'] = random.choice(user_agent_list)
                data = request_util(method='GET', url=url,headers=header, parm=parm, expr=expr, node='list', column=columnname,cookies=cookie,backlist=True)
                if len(data)<1:
                    print('有问题',i,p['areaNo'])
                for d in data:
                    try:
                        d['lat'] = d['YX'][11:]
                        d['lng'] = d['YX'][:10]
                    except:
                        d['lat'] = ''
                        d['lng'] = ''
                    self.op.I_Mongodb(d)
            #         result.append(td)
            # if len(result) > 0:
            #    self.op.I_Mongodb(result)

    def CEB(self):
        url = 'http://www.cebbank.com/eportal/ui'
        parm = {'struts.portlet.action':'/portlet/emapFront!getCityList.action',
                'moduleId':'12853'}
        node = 'cityList'
        city = request_util(method='GET',url=url,parm=parm,node=node,dictkey=True)
        parm['struts.portlet.action'] = '/portlet/emapFront!queryEmapDotList.action'
        parm['pageId'] = 484657
        parm['keyword'] = ''

        colnum = { 'netcode':'id',
                   'name': 'name',
                   'address': 'address',
                   'phone':'phone',
                   'lng': 'pointX',
                   'lat':'pointY'
                  }
        for c_ in city:
            parm['cityId'] = c_['id']
            city = c_['name']
            if city == '吴江市':
                city = '吴江区'
            if city == '香港':
                city = '香港特别行政区'
            data = request_util(method='GET', url=url, parm=parm, node='dotList',column=colnum,extra={'city':city},op=self.op)

    def BOB(self):
        url = 'http://www.bankofbeijing.com.cn/branch/index.html'
        column = {'subbranch': 'span/a/text()',
                  'burl': 'span/a/@href',
                  }
        branch = request_util_html(method='GET',url=url,headers=header,node='//div[@class="title_in f_000_12"]',column=column,backlist=True)

        columnname = {'name': 'td[1]//text()',
                  'address': 'td[2]/text()',
                  'phone':'td[3]/text()'
                  }
        for b in branch:
            burl = 'http://www.bankofbeijing.com.cn' + b['burl']
            if b['subbranch'] =='香港代表处':
                continue
            data = request_util_html(method='GET', url=burl, headers=header, node='//div[@class="list"]/table//tr',column=columnname,poi='address', backlist=True)

            if len(data) == 0:
                print('数据为空:',burl)

            for d in data:
                d['city'] = b['subbranch'].replace('分行','').replace('地区','') + '市'
                self.op.I_Mongodb(d)

    def CMB(self):
        url = 'http://branch.cmbchina.com/'
        data = requests.get(url=url)
        from  scrapy.selector import Selector
        data = Selector(text=data.content).xpath('//table[@class="content"]/tr/td/div/table')
        parm = {
        'type': 'B',
        '_': int(time.time()*1000),
        '{}':''
        }
        url = 'http://map.cmbchina.com/Service/branch.aspx'
        for i in data:
            city = i.xpath('tr//a/text()').extract()
            if len(city) > 0:
                for c in city:
                    c = re_text(c)
                    parm['city'] = c.replace('市','').encode("unicode_escape").decode('utf-8').replace('\\','%')
                    doi = eval(requests.request(method='GET',url=url,params=parm,headers=header).text)
                    for d_ in doi['branches']:
                        d_['phone'] = d_.pop('tel')
                        d_['city'] = c
                        if c == '连云港':
                            d_['city'] = '连云港市'
                        if c == '香港':
                            d_['city'] = '香港特别行政区'
                        del d_['msg']
                        del d_['branchno']
                        del d_['type']
                        self.op.I_Mongodb(d_)

    def CMBC(self):
        url = 'http://www.cmbc.com.cn/channelApp/ajax/QueryArea'
        url1 = 'http://www.cmbc.com.cn/channelApp/ajax/QueryArea2'

        colnum = {'netcode': 'bankid',
                  'name': 'bankname',
                  'address': 'address',
                  'opentime':'time',
                  'phone': 'banktel',
                  'lng': 'posy',
                  'lat': 'posx',
                  'citycode':'cityno'
                  }

        # 请求头设置
        payloadHeader = {
            'Content-Type': 'application/json;charset=UTF-8',
            'User-Agent': random.choice(user_agent_list)
        }
        #原生AJAX POST请求
        payloadData = {
            "request":{"body":{"parNo":"parentnoisnull"},
            "header": {"device":{ "model":"SM-N7508V","osVersion":"4.3","imei":"352203064891579","isRoot":"1","nfc":"1","brand":"samsung","mac":"B8:5A:73:94:8F:E6","":"45cnqzgwplsduran7ib8fw3aa","osType":"01"},
                                    "appId":"1",
                                    "net":{"ssid":"oa-wlan","netType":"WIFI_oa-wlan","cid":"17129544","lac":"41043","isp":"","ip":"195.214.145.199"},
                                    "appVersion":"3.60",
                                    "transId":"QueryArea",
                                    "reqSeq":"0"
                                   } }}

        province = eval(requests.post(url=url,data=json.dumps(payloadData),headers=payloadHeader).text.replace('null','""'))


        for p in province['returnData']:
            areaname = p['areaname']
            areano = p['areano']
            payloadData['request']['body']['parNo'] = areano
            payloadData['request']['header']['device']['transId'] = 'QueryArea2'
            city = eval(requests.post(url=url, data=json.dumps(payloadData), headers=payloadHeader).text.replace('null','""'))

            for c in city['returnData']:
                cityno = c['areano']
                cityname = c['areaname']

                payloadData['request']['body']['row'] = 9
                payloadData['request']['body']['page'] = 1
                payloadData['request']['body']['cityno'] = cityno
                payloadData['request']['body']['areano'] = ''
                payloadData['request']['body']['banktype'] = 0
                payloadData['request']['header']['device']['transId'] = 'QueryBranchBank'


                postUrl = 'http://www.cmbc.com.cn/channelApp/ajax/QueryBranchBank'
                r = eval(requests.post(postUrl, data=json.dumps(payloadData), headers=payloadHeader).text.replace('null','""'))

                pageCount = r['returnData']['pageCount']
                rowCount = r['returnData']['rowCount']

                if rowCount > 0 :
                    for i in range(1,pageCount+1):
                        payloadData['request']['body']['page'] = i
                        data = request_util(method='POST',url=postUrl,column=colnum,node='returnData.list',
                                            data=json.dumps(payloadData),replacev=[('null','""')],
                                            backlist=True)

                        for d in data:
                            d['netcode'] = d['netcode'].strip()
                            d['phone'] = d['phone'].strip()
                            d['lng'] = float(d['lng'])
                            d['lat'] = float(d['lat'])
                            d['city'] = cityname
                            if '市辖' in cityname:
                                d['city'] = areaname
                                d['citycode'] = areano
                            if d['city'] in ['北京','上海','重庆','天津','贵阳','遵义','葫芦岛','淄博','湖州']:
                                d['city'] = d['city'] +  '市'
                            self.op.I_Mongodb(d)

    def CZB(self):
        url = 'http://czbank.com/cn/add/201610/t20161017_10959.shtml'

        html = Selector(text=requests.get(url=url).content)
        n = 0
        city = ''
        doi = {}
        for sel in html.xpath('//table/tbody/tr'):
            d = []
            n = n + 1
            tn = 0
            if n == 1 or n == 2:
                continue

            data = sel.xpath('td').extract()

            if len(data) < 7:
                continue

            d.append(''.join(sel.xpath('td[1]//span//text()').extract()))
            d.append(''.join(sel.xpath('td[2]//span//text()').extract()))
            d.append(''.join(sel.xpath('td[3]//span//text()').extract()))
            d.append(''.join(sel.xpath('td[4]//span//text()').extract()))
            d.append(''.join(sel.xpath('td[5]//span//text()').extract()))

            expr = '\d{3,4}-\d{7,8}'
            try:
                r = re.findall(expr,d[4])
            except:
                r = []

            if len(r) > 0:
                city = d[0].replace('分行','市')
                print(city)
                tn = 1

            doi['name'] = d[tn]
            if doi['name'] == '分行':
                doi['name'] = '分行营业部'

            doi['address'] = d[tn+1]
            doi['phone'] = d[tn+2] + ',' + d[tn+3]
            doi['city'] = city
            doi['_id'] = uuid.uuid1()

            lation = checkaddress(doi['address'])
            if lation:
               doi.update(lation)
            else:
                doi['lng'] = ''
                doi['lat'] = ''

            self.op.I_Mongodb(doi)

    def SDPB(self):
        url = 'http://www.spdb.com.cn/was5/web/search'

        pformdata = {'metadata': '名称',
                    'perpage': '1000',
                    'channelid': '231964',
                    'searchword': '(父名称=%中国%)*(类型=%省%)'}

        provinces = eval(requests.request(method='POST',url=url,data=pformdata).text)

        colnum = {'netcode': 'deptinfo_orgid',
                  'name': 'deptinfo_name',
                  'address': 'deptinfo_address',
                  'phone': 'deptinfo_telno',
                  'lng': 'deptinfo_longitude',
                  'lat': 'deptinfo_dimensions'
                  }

        formdata = {}

        for p in provinces['rows']:
            pname = p['名称']
            pformdata['searchword'] = '(父名称=%'+pname+'%)*(类型=%市%)'
            citys =  eval(requests.request(method='POST',url=url,data=pformdata).text)
            for c in citys['rows']:
                cname = c['名称']
                if cname == '吴江市':
                    cname = '吴江区'
                formdata['metadata'] = 'deptinfo_orgid|deptinfo_name|deptinfo_address|deptinfo_postcode|deptinfo_telno|deptinfo_longitude|deptinfo_dimensions'
                formdata['channelid'] = '243263'
                formdata['page'] = 1
                formdata['searchword'] = '((deptinfo_address,deptinfo_name)+=%)*(deptinfo_province=%'+pname+'%)*(deptinfo_city=%'+cname+'%)'
                request_util(method='POST',url=url,data=formdata,column=colnum,node='rows',extra={'city':cname,'province':pname},op=self.op)

