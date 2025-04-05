/**
 * Notion到Markdown导出工具主模块
 * 
 * 此模块作为程序入口点，负责解析环境变量并启动导出流程
 */

import { NotionExportConfig } from './types';
import { exportNotionPage } from './exporter';
import dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

// 从环境变量加载配置
const config: NotionExportConfig = {
    apiKey: process.env.NOTION_API_KEY || "",
    pageId: process.env.NOTION_PAGE_ID || "",
    outputFilename: process.env.OUTPUT_FILENAME || "exported_notion_page.md",
    outputDir: process.env.OUTPUT_DIR || "exports",
    recursive: process.env.RECURSIVE === "true",
    maxDepth: process.env.MAX_DEPTH ? parseInt(process.env.MAX_DEPTH) : 0,
    usePageTitleAsFilename: process.env.USE_PAGE_TITLE_AS_FILENAME === "true"
};

// 主执行函数
(async () => {
    try {
        await exportNotionPage(config);
        console.log("导出完成！");
        process.exit(0);
    } catch (error: unknown) {
        if (error instanceof Error) {
            console.error(`致命错误: ${error.message}`);
            if (error.stack) {
                console.error(error.stack);
            }
        } else {
            console.error('发生未知致命错误');
        }
        process.exitCode = 1; // 使用exitCode而不是立即退出
    }
})();
