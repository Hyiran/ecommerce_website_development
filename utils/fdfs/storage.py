"""自定义上传存储文件类、连接FDFS"""
'''
@Time    : 2018/3/12 下午4:23
@Author  : scrappy_zhang
@File    : storage.py
'''

import os
from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client


# Django默认保存文件时，会调用Storage类中的save方法
# Storage类中的save方法会调用DEFAULT_FILE_STORAGE配置项指定的类中_save方法
# _save方法的返回值最终会保存在表的image字段中

# Django保存文件之前，会调用DEFAULT_FILE_STORAGE配置项指定的类中exists方法
# 判断文件在系统中是否存在，防止同名的文件被覆盖


class FDFSStorage(Storage):
    """fast dfs文件存储类"""

    def __init__(self, client_conf=None, nginx_url=None):
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF

        self.client_conf = client_conf

        if nginx_url is None:
            nginx_url = settings.FDFS_NGINX_URL

        self.nginx_url = nginx_url

    def _save(self, name, content):
        """保存文件时调用"""
        # name: 上传文件的名称 a.txt
        # content: File类的对象，包含了上传文件的内容

        # 上传文件到FDFS文件存储系统
        # client = Fdfs_client('客户配置文件路径')
        # client = Fdfs_client(os.path.join(settings.BASE_DIR, 'utils/fdfs/client.conf'))
        client = Fdfs_client(self.client_conf)


        # 获取上传文件内容
        file_content = content.read()

        # 上传文件
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id, # 保存的文件id
        #     'Status': 'Upload successed.', # 上传是否成功
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # } if success else None

        response = client.upload_by_buffer(file_content)

        if response is None or response.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fast dfs系统失败')

        # 获取保存文件id
        file_id = response.get('Remote file_id')

        # 返回file_id
        return file_id

    def exists(self, name):
        """判断文件是否存在"""
        return False

    def url(self, name):
        """返回可访问到文件的url地址"""
        # return 'http://172.16.110.128:8888/' + name
        return self.nginx_url + name
