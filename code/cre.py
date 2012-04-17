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
	p        = re.compile(r'<.*?>')
	stripped = html_breakstrip(p.sub('', string))
	return p.sub(' ', stripped)

def unescape(string):
	pars = HTMLParser.HTMLParser()
	p    = re.compile(r'\s+')
	return pars.unescape(p.sub(' ', string))

def html_breakstrip(html):
	return html.replace("\n", "").replace("\r", "")

def spacestrip(text):
	return re.sub(" +", " ", text)

def prettify(text):
	return unescape(htmlstrip(html_breakstrip(spacestrip(text))))
