/**
 * 类型定义文件
 * 包含 Notion 导出相关的所有类型定义
 */

import { Client } from "@notionhq/client";

/**
 * Notion 导出配置接口
 */
export interface NotionExportConfig {
    /** Notion API key */
    apiKey: string;
    /** ID of the Notion page to export */
    pageId: string;
    /** Output filename (must end with .md) */
    outputFilename: string;
    /** Output directory path */
    outputDir: string;
    /** Whether to recursively export subpages */
    recursive?: boolean;
    /** Maximum recursion depth (0 means no limit) */
    maxDepth?: number;
    /** 是否使用页面标题作为文件名 */
    usePageTitleAsFilename?: boolean;
}

/**
 * 导出结果接口
 */
export interface ExportResult {
    /** 导出的内容 */
    content: string;
    /** 原始数据，用于子页面提取 */
    rawData?: any;
    /** 页面标题 */
    title?: string;
}

/**
 * 子页面信息接口
 */
export interface SubpageInfo {
    /** 子页面ID */
    id: string;
    /** 子页面标题 */
    title: string;
}

/**
 * Notion 客户端包装器
 */
export interface NotionClientWrapper {
    client: Client;
}
