#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : PSBC.py
# @Author: Yangyao
# @Date  : 2018/8/8
# @license : Copyright(C), Pactera
# @Contact : yao.yang@pactera.com 
# @Software : PyCharm
# @Desc  : 中国邮政储蓄银行网点信息爬取

import requests
from scrapy.selector import Selector
import re
from wangdian_spider.bankutil import request_util
from wangdian_spider.bankutil import request_util_html

class PSBC:

    def PSBC_Branch_Info(self):
        # 爬取公用函数
        def getList(url, parm, xpath):
            r = requests.get(url, params=parm).content.decode('utf-8')
            html = Selector(text=r)
            list = html.xpath(xpath).extract()
            return list

        # 各省（直辖市）、市、县（区）行政级url
        url1 = 'http://www.psbc.com/cms/WdjgQuery.do'
        url2 = 'http://www.psbc.com/cms/CityQuery.do'
        url3 = 'http://www.psbc.com/cms/XianQuery.do'
        url4 = 'http://www.psbc.com/cms/WangdianQuery.do'

        # 获取省级列表
        xpath1 = '//*[@id="province"]/option/text()'
        xpath2 = '//*[@id="province"]/option/@value'

        r1 = requests.get(url1).content.decode('utf-8')
        pListValue = getList(url1, {}, xpath2)

        # 获取市级列表
        xpath3 = '//*[@id="city"]/li/a/text()'
        xpath4 = '//*[@id="city"]/li/a/@onclick'
        reg = r"(\d{4})"

        # 获取县级（区级）列表
        xpath5 = '//*[@id="xian"]/li/a/text()'
        xpath6 = '//*[@id="xian"]/li/a/@onclick'
        reg1 = r"(\d{6})"

        # 获取网点列表信息
        # xpath7 = '//div[@class="area_bank_list"]/table/tr/td/text()'
        node = '//div[@class="area_bank_list"]/table/tr'

        # 当前地区网点总数
        xpath8 = '//div[@class="pagediv clearfix"]/table/tr/td/text()[1]'
        reg2 = r'(\d*)条'

        # 定义字典key
        keyList = ['branchName', 'branchAddr', 'businessHours', 'contactPhoneNumber']
        parm = {}
        formdata = {}  # 分页请求参数
        column = {'name': 'td[1]/text()',
                  'address': 'td[2]/text()',
                  'opentime': 'td[3]/text()',
                  'phone': 'td[4]/text()'}
        column1 = {}

        for i in pListValue:
            parm['Param'] = i
            cList = getList(url2, parm, xpath4)
            cityName = getList(url2, parm, xpath3)
            for j in cList:
                cCode = re.findall(reg, j)
                parm['Param'] = cCode[0]
                column1['city'] = cityName[0]
                column1['citycode'] = cCode[0]
                xList = getList(url3, parm, xpath6)
                for k in xList:
                    wdCode = re.findall(reg1, k)
                    parm['Param'] = wdCode
                    wdTotal = getList(url4, parm, xpath8)[0]
                    wdCount = re.findall(reg2, wdTotal)[0]
                    final_url = url4 + '?Param=%s' % wdCode[0]
                    formdata['recordNumber'] = wdCount
                    for s in range(0, int(int(wdCount) / 10) + 1):
                        formdata['currentIndex'] = s * 10
                        data = request_util_html(method='POST', url=final_url, node=node, data=formdata, column=column,
                                                 backlist=True,extra=column1)
                        realdata = data[1:]
                        print(realdata)
                        # import time
                        # time.sleep(111)

    def PSBC_Fund(self):
        pass

    def PSBC_Financial_Products(self):
        pass

PSBC().PSBC_Branch_Info()
