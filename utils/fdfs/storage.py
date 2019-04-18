from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client


class FDFSStorage(Storage):
    """ fastdfs 文件存储类 """

    def __init__(self, client_conf=None, base_url=None):
        """
        :client_url: 需要传递一个fdfs_client配置文件的路径
        :base_url: nginx服务器的地址及端口
        """
        if client_conf is None:
            client_conf = './utils/fdfs/client.conf'
        self.client_conf = client_conf

        if base_url is None:
            base_url = 'http://127.0.0.1:8888/'
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        # 注意: 如果你将配置文件拷贝在了项目目录中, 那么在设置这个配置文件路径的时候, 是基于当前根目录的./代表当前项目根目录下
        client = Fdfs_client(self.client_conf)  # 创建客户端对象

        # 上传文件到Fdfs_client系统中
        res = client.upload_by_buffer(content.read())

        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fastdfs失败')

        # 获取返回文件的ID
        file_name = res.get('Remote file_id')

        return file_name

    def exists(self, name):
        """ Django判断文件名是否可用 """
        return False

    def url(self, name):
        """ 返回url访问的路径 """
        return self.base_url + name
