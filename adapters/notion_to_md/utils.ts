/**
 * 工具函数模块
 * 包含各种辅助函数
 */

import { SubpageInfo } from './types';
import path from 'path';
import fs from 'fs/promises';

/**
 * 从数据中提取子页面信息
 * @param data - 可能是字符串或JSON对象
 * @returns 子页面信息数组
 */
export function extractSubpages(data: any): SubpageInfo[] {
    const subpages: SubpageInfo[] = [];
    
    // 如果数据为空，返回空数组
    if (!data) return subpages;
    
    // 如果数据是字符串，尝试从字符串中提取链接
    if (typeof data === 'string') {
        // 尝试匹配Markdown链接格式: [标题](32位页面ID)
        const regex = /\[(.*?)\]\(([a-f0-9]{32})\)/g;
        let match;
        while ((match = regex.exec(data)) !== null) {
            subpages.push({
                title: match[1] || 'Untitled',
                id: match[2]
            });
        }
        
        // 如果找到了链接，直接返回
        if (subpages.length > 0) {
            return subpages;
        }
        
        // 如果是JSON字符串，尝试解析
        try {
            if (data.trim().startsWith('{')) {
                data = JSON.parse(data);
            }
        } catch (e) {
            // 忽略解析错误，返回已找到的链接
            console.warn('无法解析JSON字符串');
            return subpages;
        }
    }
    
    // 递归遍历对象查找子页面
    function findChildPages(obj: any) {
        // 如果不是对象或数组，直接返回
        if (!obj || typeof obj !== 'object') return;
        
        // 检查是否是子页面块
        if (obj.type === 'child_page' && obj.id) {
            const title = obj.child_page?.title || 'Untitled';
            console.log(`发现子页面: ${obj.id}, 标题: ${title}`);
            subpages.push({ id: obj.id, title });
        }
        
        // 检查子页面属性
        if (obj.child_page && obj.id) {
            const title = obj.child_page.title || 'Untitled';
            console.log(`发现子页面属性: ${obj.id}, 标题: ${title}`);
            subpages.push({ id: obj.id, title });
        }
        
        // 遍历数组
        if (Array.isArray(obj)) {
            for (const item of obj) {
                findChildPages(item);
            }
            return;
        }
        
        // 检查blocks属性
        if (obj.blocks && Array.isArray(obj.blocks)) {
            for (const block of obj.blocks) {
                findChildPages(block);
            }
        }
        
        // 检查children属性
        if (obj.children && Array.isArray(obj.children)) {
            for (const child of obj.children) {
                findChildPages(child);
            }
        }
        
        // 遍历对象的所有属性
        for (const key in obj) {
            if (obj.hasOwnProperty(key) && typeof obj[key] === 'object') {
                findChildPages(obj[key]);
            }
        }
    }
    
    // 开始递归遍历
    findChildPages(data);
    
    // 去除重复的ID
    const uniqueSubpages: SubpageInfo[] = [];
    const ids = new Set<string>();
    
    for (const subpage of subpages) {
        if (!ids.has(subpage.id)) {
            ids.add(subpage.id);
            uniqueSubpages.push(subpage);
        }
    }
    
    return uniqueSubpages;
}

/**
 * 从Notion页面ID生成安全的文件名
 * @param pageId - 页面ID
 * @param title - 页面标题
 * @param useTitle - 是否使用标题作为文件名
 * @returns 安全的文件名
 */
export function generateSafeFilename(pageId: string, title?: string, useTitle = false): string {
    if (useTitle && title) {
        // 将标题转换为安全的文件名
        const safeTitle = title
            .replace(/[\\/:*?"<>|]/g, '_') // 替换不安全的字符
            .replace(/\s+/g, '-')          // 空格替换为连字符
            .replace(/-+/g, '-')           // 多个连字符替换为一个
            .replace(/^-|-$/g, '')         // 移除开头和结尾的连字符
            .substring(0, 100);            // 限制长度
        
        return `${safeTitle}-${pageId.substring(0, 8)}.md`;
    }
    
    return `${pageId}.md`;
}

/**
 * 确保目录存在
 * @param dirPath - 目录路径
 */
export async function ensureDirectoryExists(dirPath: string): Promise<void> {
    try {
        await fs.mkdir(dirPath, { recursive: true });
    } catch (error) {
        console.error(`创建目录失败: ${dirPath}`, error);
        throw error;
    }
}

/**
 * 验证Notion导出配置
 * @param config - 导出配置
 * @throws {Error} 如果配置无效
 */
export function validateConfig(config: any): void {
    if (!config.apiKey) {
        throw new Error("Invalid configuration: apiKey is required");
    }
    
    if (!config.pageId) {
        throw new Error("Invalid configuration: pageId is required");
    }
    
    if (!config.outputFilename.endsWith('.md')) {
        throw new Error("Invalid configuration: outputFilename must end with .md");
    }
    
    // 页面ID格式检查
    const cleanPageId = config.pageId.replace(/[\s-]/g, '');
    if (!/^[a-f0-9]{32}$/.test(cleanPageId)) {
        console.warn(`警告: 页面ID格式可能不正确: ${config.pageId}`);
        console.warn('页面ID应该是32位十六进制字符串，可能包含连字符');
        console.warn('例如: 1ca73a85-7f76-800e-b2f9-e4502426d717 或 1ca73a857f76800eb2f9e4502426d717');
    }
    
    // 清理页面ID（移除连字符和空格）
    config.pageId = cleanPageId;
}

/**
 * 验证环境变量
 * @throws {Error} 如果缺少必要的环境变量
 */
export function validateEnvironment(): void {
    const requiredVars = ['NOTION_API_KEY', 'NOTION_PAGE_ID'];
    const missingVars = requiredVars.filter(varName => !process.env[varName]);

    if (missingVars.length > 0) {
        throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
    }
}
