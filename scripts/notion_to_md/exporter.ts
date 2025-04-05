/**
 * 导出器模块
 * 负责处理Notion页面导出逻辑
 */

import { NotionExportConfig, ExportResult, SubpageInfo } from './types';
import { validateConfig, validateEnvironment, extractSubpages, generateSafeFilename, ensureDirectoryExists } from './utils';
import { exportPage } from './notion-client';
import path from 'path';

/**
 * 递归导出Notion页面及其子页面
 * @param config - 导出配置
 * @param currentDepth - 当前递归深度
 * @param processedIds - 已处理的页面ID集合（防止循环引用）
 * @throws {Error} 如果导出失败
 */
export async function exportPageRecursive(
    config: NotionExportConfig, 
    currentDepth: number = 0, 
    processedIds: Set<string> = new Set<string>()
): Promise<void> {
    // 防止重复处理同一页面（处理循环引用）
    if (processedIds.has(config.pageId)) {
        console.log(`跳过已处理的页面: ${config.pageId}`);
        return;
    }
    
    // 记录当前页面ID为已处理
    processedIds.add(config.pageId);
    
    // 检查是否超过最大深度（如果设置了）
    if (config.maxDepth && currentDepth > config.maxDepth) {
        console.log(`达到最大递归深度 ${config.maxDepth}，停止递归`);
        return;
    }
    
    console.log(`导出页面 (深度 ${currentDepth}): ${config.pageId}`);
    
    // 导出当前页面
    const result = await exportPage(config);
    
    // 如果启用了递归导出
    if (config.recursive && result) {
        // 从原始数据中提取子页面信息
        const subpages = extractSubpages(result.rawData || result.content);
        
        if (subpages.length > 0) {
            console.log(`发现 ${subpages.length} 个子页面:`);
            subpages.forEach(subpage => {
                console.log(`  - ${subpage.title} (${subpage.id})`);
            });
            
            // 递归导出每个子页面
            for (const subpage of subpages) {
                console.log(`处理子页面: ${subpage.title} (${subpage.id})`);
                
                // 生成文件名
                const filename = generateSafeFilename(
                    subpage.id, 
                    subpage.title, 
                    config.usePageTitleAsFilename
                );
                
                // 为子页面创建新的配置
                const subpageConfig: NotionExportConfig = {
                    ...config,
                    pageId: subpage.id,
                    outputFilename: filename
                };
                
                try {
                    // 递归导出子页面
                    await exportPageRecursive(subpageConfig, currentDepth + 1, processedIds);
                } catch (error) {
                    console.error(`导出子页面 ${subpage.title} (${subpage.id}) 失败:`, error);
                    // 继续处理其他子页面
                }
            }
        } else {
            console.log('没有发现子页面');
        }
    }
}

/**
 * 导出Notion页面到Markdown
 * 这是主要的导出函数，根据配置决定是否递归导出子页面
 * @param config - 导出配置
 * @throws {Error} 如果导出失败
 */
export async function exportNotionPage(config: NotionExportConfig): Promise<void> {
    try {
        validateEnvironment();
        validateConfig(config);
        
        // 确保输出目录存在
        await ensureDirectoryExists(path.resolve(config.outputDir));
        
        if (config.recursive) {
            console.log(`启用递归导出，最大深度: ${config.maxDepth || '无限制'}`);
            await exportPageRecursive(config);
        } else {
            // 导出单个页面
            const result = await exportPage(config);
            
            // 如果配置了使用页面标题作为文件名，并且成功获取到了标题
            if (config.usePageTitleAsFilename && result?.title) {
                // 生成基于标题的文件名
                const newFilename = generateSafeFilename(
                    config.pageId, 
                    result.title, 
                    true
                );
                
                // 创建新的配置
                const newConfig = {
                    ...config,
                    outputFilename: newFilename
                };
                
                // 重新导出到新文件名
                await exportPage(newConfig);
                console.log(`使用页面标题重命名为: ${newFilename}`);
            }
        }
    } catch (error: unknown) {
        if (error instanceof Error) {
            console.error(`导出失败: ${error.message}`);
            if (error.stack) {
                console.error(error.stack);
            }
            throw error; // Re-throw for main error handler
        }
        throw new Error('导出过程中发生未知错误');
    }
}
