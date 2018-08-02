#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : ImgReader.py
# @Author: Yangyao
# @Date  : 2018/8/1
# @license : Copyright(C), Pactera
# @Contact : yao.yang@pactera.com 
# @Software : PyCharm
# @Desc  : read the images

from PIL import Image
import pytesseract
# 上面都是导包，只需要下面这一行就能实现图片文字识别
text = pytesseract.image_to_string(Image.open('test.jpg'), lang='chi_sim')
print(text)