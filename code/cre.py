# -*- coding: utf-8 -*-
import re, HTMLParser

def between(first, second, string):
    tmp = re.compile(first + '(.*?)' + second, re.DOTALL |  re.IGNORECASE).findall(string)
    try:
        tmp = tmp[0]
    except:
        tmp = ""
    return tmp

def all_between(first, second, string):
    return re.compile(first + '(.*?)' + second, re.DOTALL |  re.IGNORECASE).findall(string)
    
def htmlstrip(string):
	p = re.compile(r'<.*?>')
	stripped = html_breakstrip(p.sub('', string))
	p = re.compile(r'\s+')
	#pars = HTMLParser.HTMLParser()
	#return pars.unescape(p.sub(' ', stripped))
	return p.sub(' ', stripped)

def html_multispacefix(html):
	return html.replace("\n", "").replace("\r", "")

def spacestrip(text):
	return re.sub(" +", " ", text)
