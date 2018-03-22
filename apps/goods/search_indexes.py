"""商品搜索框检索, 索引文件生成"""
'''
@Time    : 2018/3/15 下午8:45
@Author  : scrappy_zhang
@File    : search_indexes.py
'''

from haystack import indexes
from apps.goods.models import GoodsSKU

#指定对于某个类的某些数据建立索引

class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return GoodsSKU

    def index_queryset(self, using=None):
        return  self.get_model().objects.all()
