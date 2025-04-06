# 简单测试规则

这是一个用于测试的简单规则文件，没有Front Matter。

## 规则条目

* 所有代码文件不得超过200行
* 函数长度不得超过30行
* 使用有意义的变量名

## 示例

```python
# 好的示例
def calculate_total(items):
    """计算总价"""
    return sum(item.price for item in items)
```

```python
# 不好的示例
def calc(i):
    """计算"""
    return sum(x.p for x in i)
```
