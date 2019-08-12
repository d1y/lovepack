#!/usr/bin/env python3
# coding=utf-8

import os
import sys
import json
import requests
from pyquery import PyQuery as pq
from colr import color
from urllib.parse import parse_qs
from PIL import Image
from datetime import datetime
import tqdm


'''
  @tips { 获取`HOME`路径 }
'''
_USERNAME = os.getenv("SUDO_USER") or os.getenv("USER") 
_HOME = os.path.expanduser('~'+_USERNAME)

_api = 'https://live.kuaishou.com/profile/'
_headers = {
  'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}

def str2JSON( html, flag = False ):
  '''
    @tips { 先把拿到的数据转为`dict` }
    @param {str} - html
    @return {dict}
  '''
  _html = pq(html)
  _con = _html('#app').next().next().text()
  _firstStr = _con.index('{')
  _lastStr = _con.rindex('}')
  _code = _con[_firstStr:_lastStr]
  _code = _code[: int( _code.rindex('}') )+1]
  data_obj = json.loads(_code)['defaultClient']
  if flag:
    _title = _html('.profile-user-name').text()
    return {
      "title": _title,
      "data": data_obj
    };
  return data_obj;

def _Path( pack = '', debug = False ):
  '''
    @tips { auto create home /lovepack }
    @parmas {str} - pack
  '''
  _path = _HOME+'/lovepack'
  if not pack[0] == '/':
    pack = '/' + pack
  if not os.path.isdir(_path):
    print(
      color('create dir: '+ _path, fore='blue')
    )
    os.makedirs(_path)
    '''
      @tips { debug 调试目录 }
    '''
    _dd = _path+'/debug'
    print(
      color('create dir: '+ _dd, fore='blue')
    )
    os.makedirs(_dd)
  else:
    if not os.path.isdir(_path+pack):
      os.makedirs(_path+pack)
  if debug:
    return _path+"/debug"+pack;
  return _path+pack;

def kuaishouURL( id = 'WJKGYL_0921', flag = False, debug = False ):
  '''
    @tips { 获取某个`id`用户的作品 }
    @parmas {str} - id
    @parmas {bool} - flag 是否生成 `markdown` 文件
    @parmas {bool} - debug 调试
    @retrun {list}
  '''
  if debug:
    print(
      'GET:',
      color(_api+id, fore="red")
    )
  if not id:
    print(
      color('请输入用户id', fore="green")
    )
    exit()
  _r = requests.get(_api+id, headers=_headers)
  data_obj = str2JSON(_r.text)

  _key = '$ROOT_QUERY.publicFeeds({"count":24,"pcursor":"","principalId":"'+id+'"})'

  _lists = data_obj[_key]
  if not len(_lists['list']):
    print(
      color('  => 获取失败,对方可能没有作品或者`id`错误', fore='red')
    )
    return [];
  _result = []
  for _index,_list in enumerate(_lists['list']):
    _now = _key + '.list.' + str(_index)
    _result.append(
      data_obj[_now]
    )
  if debug:
    '''
      @tips 打印获取的数据,方便测试
    '''
    _fs = open(_Path('env', debug = True),'w+')
    _fs.write(
      json.dumps(_result)
    )
  _INFO = data_obj['User:'+id]
  if flag:
    '''
      @tips 将用户信息写入 `.md` 文件
    '''
    markdown(_INFO)

  return {
    "result": _result,
    "path": _INFO['name']
  };

def kuaishouVideosURL( photoID, ID ):
  '''
    @tips { 获取视频视频下载地址 }
    @parmas {str} photoID - 图片地址
    @parmas {str} ID - 用户id
  '''
  _r = requests.get(
    'https://live.kuaishou.com/u/'+ID+'/'+photoID,
    headers=_headers
  )
  _data = str2JSON(
    html = _r.text,
    flag = True)
  _name = _Path(_data['title']+'/videos')
  if not os.path.isdir(_name):
    os.makedirs(_name)
  _key = '$ROOT_QUERY.feedById({"photoId":"%s","principalId":"%s"}).currentWork' % (photoID, ID)
  _play = _data['data'][_key]
  _url = _play['playUrl']
  _file = _play['caption']+'.mp4'
  _fullpath = _name+'/'+_file
  save2Media(
    url = _url,
    filename = _fullpath
  )


def downKuaishou( id, flag, debug ):
  '''
    @tips { 传递一个拿到的数组,依次下载 }
    @parmas {str} - id
    @parmas {bool} - flag
    @parmas {bool} - debug
    @retrun
  '''
  # _fs = open(_Path('env', True),'r')
  # _con = json.loads(_fs.read())
  _con =  kuaishouURL(
    id = id,
    flag = flag,
    debug = debug
  )
  _run = {
    'path': _con['path'],
    'result': []
  }
  for _area in _con['result']:
    '''
      @tips { 视频或者图片 }
      @warn { 图片格式 `.webp` 需要格式化 }
      @test { 数据类型只有可能是 `视频` 或者 `图片` }
    '''
    _type = _area['workType']
    _caption = _area['caption']
    if len(_caption) >= 8:
      _caption = _caption[0:5]+'..'
    _lists = _area['imgUrls']['json']
    if _area['workType'] == 'video':
      _ed = _area['user']['id'].split(':')[1]
      _sd = _area['photoId']
      kuaishouVideosURL(
        photoID = _sd,
        ID = _ed
      ) 
      pass
    elif _lists:
      _run['result'].append(
        {
          "list": _lists,
          "title": _caption
        }
      )
      webp2jpg( _run )

def markdown(con):
  '''
    @tips 生成 `.md` 文件内容
    @parmas {dict} - con
    @return
  '''
  _dir = con['name']
  _fullpath = _Path(_dir)
  '''
    @tips 创建的文件: README.md
  '''
  _file = 'README'
  if not os.path.isdir(_fullpath):
    print(
      color('create dir: '+ _fullpath, fore='blue')
    )
    os.makedirs(_fullpath)
  _READFILE = _fullpath+'/'+_file+'.md'
  if not os.path.isfile(_READFILE):
    print(
      color('create file: '+ _READFILE, fore="blue")
    )
    _README = open(_READFILE, 'w+')
    _open = loveFormat(con)
    _README.write(
      _open
    )
    _README.close()
    pass

def webp2jpg( p2 ):
  '''
    @tips { webp to jpg }
    @parmas {dict} - p2
  '''
  _path = p2['path']
  _lists = p2['result']
  def _genPath( title ):
    _tempPath = _Path(pack = _path+'/'+'images/'+title)
    if not os.path.isdir(_tempPath):
      print(
        color('create dir: '+_tempPath, fore="blue")
      )
      os.makedirs(_tempPath)
    return _tempPath;
  def _genTimeFile(num):
    _full = datetime.now()
    _love = _full.strftime('%Y-%m-%d')+'-'+str(num)+'.webp'
    return _love;
  for _res in _lists:
    _file = _genPath(_res['title'])
    _urls = _res['list']
    for _i,_url in enumerate(_urls):
      _nw = _file+'/'+_genTimeFile(_i)
      save2webp(
        _url = _url,
        _file = _nw
      )

def save2webp( _url,_file ):
  # _r = requests.get(_url)
  # open(_file, 'wb').write(_r.content)
  save2Media(
    url = _url,
    filename = _file
  )
  _now = _file.replace('.webp','.jpg')
  # print(
  #   color('create image: '+_now, fore="blue")
  # )
  _im = Image.open(_file).convert('RGB')
  _im.save( _now, 'jpeg' )
  os.unlink(_file)
  return _file

def save2Media( url, filename ):
  '''
    @tips { 下载大文件显示进度条 }
    @param {str} - url
    @param {str} - filename
  '''
  r = requests.get(url, stream=True)
  file_size = int(r.headers['Content-Length'])
  chunk = 1
  chunk_size= 1024
  num_bars = int(file_size / chunk_size)
  with open(filename, 'wb') as fp:
    for chunk in tqdm.tqdm(
      r.iter_content(chunk_size=chunk_size),
      total= num_bars,
      unit = 'KB',
      desc = filename,
      leave = True
    ):
      fp.write(chunk)

def loveFormat( env ):
  '''
    @tips { 得到格式化的内容 }
    @parmas {dict} - env
    @return {string}
  '''
  _action = (
    env['profile'],
    env['name'],
    env['id'],
    env['description'],
    env['id'],
    env['sex'],
    env['cityName'],
    env['userId']
  )
  # print(_action)
  _decode = """# Profile \n
![](%s) \n 
昵称: [%s](https://live.kuaishou.com/profile/%s) \n 
一句话介绍: %s \n
快手ID: %s \n
性别: %s \n
居住城市: %s \n
用户ID: %s""" % _action
  return _decode;

if __name__ == "__main__":
    '''
      @tips { 下载需要传递参数 }
    '''
    _argv = sys.argv
    _argvLen = len(_argv)
    '''
      @tips { 默认参数 }
    '''
    _flag = False
    _debug = False

    if _argvLen <= 1:
      print(
        color(' Warn: 请传递用户`id`参数\n', fore="red"),
        color('Usage: kwai [--id] [--flag] [--debug]\n', fore="blue"),
        color(' ├── id: 用户`id`\n', fore="green"),
        color(' ├── flag: 是否下载用户信息 `.md`\n', fore="green"),
        color(' ├── debug: 调试', fore="green")
      )
    else:
      _id = ''
      for _arg in _argv:
        if _arg == '--flag':
            _flag = True
        if _arg == '--debug':
          _debug = True
        if _arg.find('=') >= 0:
          _parmas = parse_qs(_arg)
          if '--id' in _parmas.keys():
            _id = _parmas['--id'][0]
          else:
            os.system("pause")
      if _debug:
        print('_id: ',_id, '_flag: ', _flag, '_debug: ', _debug)
      downKuaishou(
        flag = _flag,
        debug = _debug,
        id = _id
      )
    pass