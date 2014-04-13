#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""@author: Sean Wang
   @weibo: http://weibo.com/fclef
"""
from __future__ import unicode_literals
from os.path import getsize, splitext, basename
from hashlib import md5 as hashlib_md5
from json import loads as json_loads
from sys import argv, getfilesystemencoding
#Python3 support
try:
    from urllib.request import Request, urlopen, urlretrieve
    from urllib.parse import urlencode
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import Request, urlopen, HTTPError
    from urllib import urlencode, urlretrieve

VIDEO_TYPES = (".avi", ".mp4", ".mkv", ".mpg", ".mpeg")
SHOOTER_URL = 'http://shooter.cn/api/subapi.php'
SUBDB_URL = lambda hash: "http://api.thesubdb.com/?action=download&hash={}&language=en".format(hash)
PGS_UA = {'User-Agent': "SubDB/1.0 (PyGetSubTitle/0.1; http://github.com/truebit/PyGetSubtitle)"}


def md5_hash(file_path):
    """this hash function receives the name of the file and returns the hash code"""
    readsize = 64 * 1024
    with open(file_path, 'rb') as f:
        data = f.read(readsize)
        f.seek(-readsize, 2)
        data += f.read(readsize)
    return hashlib_md5(data).hexdigest()


def shooter_hash(file_path):
    "see https://docs.google.com/document/d/1w5MCBO61rKQ6hI5m9laJLWse__yTYdRugpVyz4RzrmM/preview"
    f_size = getsize(file_path)
    if f_size < 8196:
        print '文件太小了……你确定选中的是视频文件么……'
        return None
    with open(file_path, 'rb') as f:
        f_size_3rd = int(f_size / 3)
        # 中间两个顺序反了？作者文档上就是这么写的。。。
        offsets = (4096, f_size_3rd * 2, f_size_3rd, f_size - 8192)
        result = []
        for offset in offsets:
            f.seek(offset)
            result.append(hashlib_md5(f.read(4096)).hexdigest())
        return ';'.join(result)


def request(url, data, headers=PGS_UA):
    """not using requests library due to rule of no-3rd-party-lib"""
    if data and isinstance(data, dict):
        data = dict([k.encode('utf-8'), v.encode('utf-8')] for k, v in data.items())
        data = urlencode(data)
    req = Request(url, data=data, headers=headers)
    resp = urlopen(req).read()
    return resp

def shooter_downloader(file_path):
    """ see https://docs.google.com/document/d/1ufdzy6jbornkXxsD-OGl3kgWa4P9WO5NZb6_QYZiGI0/preview
    """
    resp = request(SHOOTER_URL,
                   data={'filehash': shooter_hash(file_path), 'pathinfo': basename(file_path), 'format': 'json'})
    try:
        r_json = json_loads(resp)
    except:
        print '射手网没有找到字幕'
        return False
    else:
        f_name, file_extension = splitext(file_path)
        result = []
        for info in r_json:
            for f_info in info['Files']:
                # 不下载idx和sub版本的字幕
                if f_info['Ext'] not in ('sub', 'idx'):
                    result.append((f_info['Link'], f_info['Ext']))
        if len(result) < 1:
            print '射手网没有找到字幕'
            return False
        elif len(result) == 1:
            urlretrieve(result[0][0], filename='{}.{}'.format(f_name, result[0][1]))
            print '字幕下载完成'
        else:
            for idx, value in enumerate(result):
                urlretrieve(value[0], filename='{}_{}.{}'.format(f_name, idx + 1, value[1]))
                print '第{}个字幕下载完成'.format(idx + 1)
        return True


def subdb_downloader(file_path):
    """see http://thesubdb.com/api/"""
    hash = md5_hash(file_path)
    try:
        resp = request(SUBDB_URL(hash), None)
    except HTTPError as he:
        if he.code == 404:
            print 'no subtitle found on thesubdb.com'
        elif he.code == 400:
            print 'invalid request to thesubdb.com'
        return False
    f_name, file_extension = splitext(file_path)
    with open('{}.srt'.format(f_name), "wb") as subtitle:
        subtitle.write(resp)
    return True


def main(path):
    status = shooter_downloader(path)
    if status:
        return
    else:
        subdb_downloader(path)


if __name__ == "__main__":
    fp = argv[1].decode(getfilesystemencoding())
    main(fp)