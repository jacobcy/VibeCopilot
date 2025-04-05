/**
 * Notion客户端模块
 * 负责与Notion API交互
 */

import { Client } from "@notionhq/client";
import { NotionConverter } from 'notion-to-md';
import { NotionExportConfig, ExportResult } from './types';
import { convertToMarkdown } from './markdown-converter';
import fs from 'fs/promises';
import path from 'path';

/**
 * 创建Notion客户端
 * @param apiKey - Notion API密钥
 * @returns Notion客户端实例
 */
export function createNotionClient(apiKey: string): Client {
    return new Client({
        auth: apiKey
    });
}

/**
 * 导出单个Notion页面到Markdown
 * @param config - 导出配置
 * @returns 导出结果，包含内容、原始数据和页面标题
 * @throws {Error} 如果导出失败
 */
export async function exportPage(config: NotionExportConfig): Promise<ExportResult | null> {
    // 创建Notion客户端
    const notion = createNotionClient(config.apiKey);
    
    // 创建文件系统导出目录
    const outputDirPath: string = path.resolve(config.outputDir);
    await fs.mkdir(outputDirPath, { recursive: true });
    const outputPath: string = path.join(outputDirPath, config.outputFilename);
    
    // 使用NotionConverter API
    const converter = new NotionConverter(notion);
    
    // 保存导出数据
    let exportedContent: any = null;
    let rawData: any = null;
    
    // 创建导出器
    const markdownExporter = {
        export: async (data: any): Promise<void> => {
            // 保存原始数据用于子页面提取
            rawData = data;
            
            // 尝试使用默认渲染器生成Markdown
            let markdown = '';
            let pageTitle = '';
            
            if (data.renderer && typeof data.renderer.output === 'string') {
                markdown = data.renderer.output;
            } else if (data.output && typeof data.output === 'string') {
                markdown = data.output;
            } else {
                console.warn('警告: 无法找到渲染后的Markdown内容，尝试手动构建');
                
                // 手动构建Markdown
                try {
                    const result = convertToMarkdown(data);
                    markdown = result.markdown;
                    pageTitle = result.pageTitle;
                } catch (error) {
                    console.error('手动构建 Markdown 失败:', error);
                    // 如果所有方法都失败，则输出原始 JSON
                    markdown = JSON.stringify(data, null, 2);
                }
            }
            
            // 保存内容用于返回
            exportedContent = markdown;
            
            // 写入文件
            await fs.writeFile(outputPath, markdown, 'utf-8');
            console.log(`成功导出到 ${outputPath}`);
        }
    };
    
    // 配置转换器
    converter
        .downloadMediaTo({
            outputDir: outputDirPath,
            preserveExternalUrls: true
        })
        .withExporter(markdownExporter);
    
    try {
        // 执行转换
        console.log(`开始转换页面: ${config.pageId}`);
        await converter.convert(config.pageId);
        console.log(`转换完成`);
        
        // 从原始数据中提取页面标题
        let pageTitle = '';
        if (rawData && rawData.blockTree && rawData.blockTree.properties && rawData.blockTree.properties.title) {
            const titleBlock = rawData.blockTree.properties.title;
            if (titleBlock.title && titleBlock.title.length > 0) {
                pageTitle = titleBlock.title.map((t: any) => t.plain_text || t.text?.content || '').join('');
            }
        }
        
        return { 
            content: exportedContent || '', 
            rawData,
            title: pageTitle
        };
    } catch (conversionError) {
        console.error(`转换过程中出错:`, conversionError);
        
        // 尝试使用另一种格式的页面ID
        try {
            // 尝试添加连字符格式
            const formattedId = `${config.pageId.slice(0,8)}-${config.pageId.slice(8,12)}-${config.pageId.slice(12,16)}-${config.pageId.slice(16,20)}-${config.pageId.slice(20)}`;
            console.log(`尝试使用带连字符的ID格式: ${formattedId}`);
            await converter.convert(formattedId);
            console.log(`使用带连字符的ID格式转换成功`);
            
            // 从原始数据中提取页面标题
            let pageTitle = '';
            if (rawData && rawData.blockTree && rawData.blockTree.properties && rawData.blockTree.properties.title) {
                const titleBlock = rawData.blockTree.properties.title;
                if (titleBlock.title && titleBlock.title.length > 0) {
                    pageTitle = titleBlock.title.map((t: any) => t.plain_text || t.text?.content || '').join('');
                }
            }
            
            return { 
                content: exportedContent || '', 
                rawData,
                title: pageTitle
            };
        } catch (retryError) {
            console.error(`使用带连字符的ID格式仍然失败:`, retryError);
            throw conversionError; // 抛出原始错误
        }
    }
}
