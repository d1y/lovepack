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


'''
  @tips { 获取`HOME`路径 }
'''
_USERNAME = os.getenv("SUDO_USER") or os.getenv("USER") 
_HOME = os.path.expanduser('~'+_USERNAME)

def _Path( pack = '', debug = False ):
  '''
    @tips { auto create home /lovepack }
    @parmas {str} - pack
  '''
  _path = _HOME+'/lovepack'
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
  if not pack[0] == '/':
    pack = '/' + pack
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
  _api = 'https://live.kuaishou.com/profile/'
  _headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
  }
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
  _html = pq(_r.text)
  _con = _html('#app').next().next().text()
  if debug:
    _file = open(_Path('ks.json', debug = True),'w')
    _file.write(_con)
  # get json text
  _firstStr = _con.index('{')
  _lastStr = _con.rindex('}')
  _code = _con[_firstStr:_lastStr]
  _code = _code[: int( _code.rindex('}') )+1]
  data_obj = json.loads(_code)['defaultClient']

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

def downKuaishou(arr = []):
  '''
    @tips { 传递一个拿到的数组,依次下载 }
    @parmas {list} - arr
    @retrun
  '''
  # _fs = open(_Path('env', True),'r')
  # _con = json.loads(_fs.read())
  _tempID = 'WJKGYL_0921'
  _con =  kuaishouURL( flag = True, debug = True, id = _tempID or 'longjunzhu815')
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
  for _res in _lists:
    _file = _genPath(_res['title'])
    _urls = _res['list']
    for _i,_url in enumerate(_urls):
      _nw = _file+'/'+str(_i)+'.webp'
      save2webp(
        _url = _url,
        _file = _nw
      )

def save2webp( _url,_file ):
  _r = requests.get(_url)
  open(_file, 'wb').write(_r.content)
  _now = _file.replace('.webp','.jpg')
  print(
    color('create image: '+_now, fore="blue")
  )
  _im = Image.open(_file).convert('RGB')
  _im.save( _now, 'jpeg' )
  os.unlink(_file)
  return _file

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
      # _text = kuaishouURL(
      #   flag = _flag,
      #   debug = _debug,
      #   id = _id
      # )
      if _debug:
        print('_id: ',_id, '_flag: ', _flag, '_debug: ', _debug)
    downKuaishou()
    pass