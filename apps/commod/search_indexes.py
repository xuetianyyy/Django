# 定义索引类


from haystack import indexes  # 导入生成索引模块
from .models import *         # 导入需要的模型类


# 索引类名的格式通常为: 模型类名 + Index
class CommodSKUIndex(indexes.SearchIndex, indexes.Indexable):
    """ 指定对于某个类的某些数据建立索引, 需要继承以上两个父类 """
    # 创建索引字段
    # document=True 指定这是一个索引字段
    # use_template=True 指定根据表中哪些字段建立索引的说明放在一个文件中
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        """ 这里需要返回模型类 """
        return CommodSKU

    def index_queryset(self, using=None):
        """ 建立索引数据 """
        # 返回模型类中的所有数据
        return self.get_model().objects.all()
