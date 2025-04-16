#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理工具

提供处理记忆服务文本内容的工具函数，包括文本清理、规范化和相似度计算等。
"""

import difflib
import html
import re
import unicodedata
from collections import Counter
from typing import List, Optional, Tuple

# 常用正则表达式
URL_PATTERN = re.compile(r"https?://\S+")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
MULTIPLE_WHITESPACE_PATTERN = re.compile(r"\s+")
NONVISIBLE_CHARS_PATTERN = re.compile(r"[\x00-\x1F\x7F-\x9F]")


def clean_text(text: str) -> str:
    """
    清理文本，移除多余空白字符、控制字符等。

    Args:
        text: 待清理的文本

    Returns:
        清理后的文本
    """
    if not text:
        return ""

    # 解码HTML实体
    text = html.unescape(text)

    # 移除不可见字符
    text = NONVISIBLE_CHARS_PATTERN.sub("", text)

    # 规范化空白字符
    text = MULTIPLE_WHITESPACE_PATTERN.sub(" ", text)

    return text.strip()


def normalize_text(text: str, lowercase: bool = True, remove_punctuation: bool = False) -> str:
    """
    规范化文本，包括大小写转换、Unicode规范化等。

    Args:
        text: 待规范化的文本
        lowercase: 是否转换为小写，默认为True
        remove_punctuation: 是否移除标点符号，默认为False

    Returns:
        规范化后的文本
    """
    if not text:
        return ""

    # 清理文本
    text = clean_text(text)

    # Unicode NFKC规范化（兼容等价规范化）
    text = unicodedata.normalize("NFKC", text)

    # 大小写转换
    if lowercase:
        text = text.lower()

    # 移除标点符号
    if remove_punctuation:
        text = re.sub(r"[^\w\s]", "", text)

    return text


def extract_plain_text(text: str) -> str:
    """
    从Markdown或HTML文本中提取纯文本。

    Args:
        text: 包含Markdown或HTML标记的文本

    Returns:
        提取的纯文本
    """
    if not text:
        return ""

    # 替换Markdown链接为纯文本
    text = MARKDOWN_LINK_PATTERN.sub(r"\1", text)

    # 移除HTML标签
    text = HTML_TAG_PATTERN.sub("", text)

    # 清理文本
    return clean_text(text)


def truncate_text(text: str, max_length: int, add_ellipsis: bool = True) -> str:
    """
    截断文本到指定长度。

    Args:
        text: 待截断的文本
        max_length: 最大长度
        add_ellipsis: 是否在截断处添加省略号，默认为True

    Returns:
        截断后的文本
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    truncated = text[:max_length].rstrip()

    if add_ellipsis:
        truncated += "..."

    return truncated


def split_text(text: str, max_chunk_size: int = 512, overlap: int = 0) -> List[str]:
    """
    将文本分割为固定大小的块。

    Args:
        text: 待分割的文本
        max_chunk_size: 每个块的最大大小
        overlap: 块之间的重叠字符数

    Returns:
        文本块列表
    """
    if not text:
        return []

    # 确保重叠不超过块大小
    overlap = min(overlap, max_chunk_size - 1)

    # 分割文本
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + max_chunk_size, text_length)

        # 如果不是最后一块且不在单词边界，则向后查找空格
        if end < text_length and not text[end].isspace():
            # 寻找最近的空格
            space_pos = text.rfind(" ", start, end)
            if space_pos > start:
                end = space_pos + 1

        chunks.append(text[start:end])

        # 考虑重叠
        start = end - overlap if overlap > 0 else end

    return chunks


def extract_keywords(text: str, top_n: int = 10) -> List[Tuple[str, int]]:
    """
    从文本中提取关键词。

    简单实现，使用词频统计，更复杂实现可考虑TF-IDF或其他NLP方法。

    Args:
        text: 待分析的文本
        top_n: 返回的关键词数量

    Returns:
        关键词列表，每项为(关键词, 频率)元组
    """
    if not text:
        return []

    # 规范化并分词
    normalized = normalize_text(text, lowercase=True, remove_punctuation=True)
    words = normalized.split()

    # 计算词频
    word_counts = Counter(words)

    # 移除停用词（简化实现，实际应用需要完整的停用词表）
    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "if",
        "of",
        "to",
        "in",
        "for",
        "with",
        "on",
        "at",
        "from",
        "by",
        "about",
        "as",
        "into",
        "like",
        "through",
        "after",
        "over",
        "between",
        "out",
        "against",
        "during",
        "without",
        "before",
        "under",
        "around",
        "among",
    }

    for word in stopwords:
        if word in word_counts:
            del word_counts[word]

    # 返回前N个高频词
    return word_counts.most_common(top_n)


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    计算两段文本的相似度。

    使用SequenceMatcher实现，返回0-1之间的相似度值。

    Args:
        text1: 第一段文本
        text2: 第二段文本

    Returns:
        相似度分数，范围[0, 1]
    """
    if not text1 or not text2:
        return 0.0

    # 规范化文本
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    # 计算相似度
    return difflib.SequenceMatcher(None, text1, text2).ratio()


def highlight_text(text: str, query: str, context_size: int = 50) -> List[str]:
    """
    在文本中查找查询并提取包含查询的上下文片段。

    Args:
        text: 待搜索的文本
        query: 查询字符串
        context_size: 查询前后的上下文字符数

    Returns:
        包含查询的上下文片段列表
    """
    if not text or not query:
        return []

    # 规范化文本和查询
    normalized_text = normalize_text(text)
    normalized_query = normalize_text(query)

    # 查找所有匹配
    highlights = []
    start = 0

    while True:
        pos = normalized_text.find(normalized_query, start)
        if pos == -1:
            break

        # 计算上下文范围
        context_start = max(0, pos - context_size)
        context_end = min(len(normalized_text), pos + len(normalized_query) + context_size)

        # 提取原始文本的对应部分
        highlight = text[context_start:context_end]

        # 添加省略号表示截断
        if context_start > 0:
            highlight = "..." + highlight
        if context_end < len(text):
            highlight = highlight + "..."

        highlights.append(highlight)

        # 继续查找下一个匹配
        start = pos + len(normalized_query)

    return highlights


def contains_chinese(text: str) -> bool:
    """
    检查文本是否包含中文字符。

    Args:
        text: 待检查的文本

    Returns:
        如果包含中文字符则返回True，否则返回False
    """
    if not text:
        return False

    # 中文Unicode范围
    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            return True

    return False


def detect_language(text: str) -> Optional[str]:
    """
    简单检测文本语言。

    注意：这是一个非常简化的实现，只能区分有限的几种语言。
    实际应用中应使用更复杂的语言检测库。

    Args:
        text: 待检测的文本

    Returns:
        检测到的语言代码（'zh', 'en', 'ja', 'ko', 'unknown'）
    """
    if not text:
        return None

    # 简化的语言检测逻辑
    text = text[:100]  # 只检查前100个字符

    # 检查中文
    if contains_chinese(text):
        return "zh"

    # 检查日文特有字符
    for char in text:
        if "\u3040" <= char <= "\u309F" or "\u30A0" <= char <= "\u30FF":
            return "ja"

    # 检查韩文特有字符
    for char in text:
        if "\uAC00" <= char <= "\uD7A3":
            return "ko"

    # 默认为英文
    return "en"
