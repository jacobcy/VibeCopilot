import { Client } from "@notionhq/client";
import fs from 'fs/promises';
import path from 'path';
import { NotionConverter } from 'notion-to-md';
import dotenv from 'dotenv';

dotenv.config();

/**
 * Configuration for Notion export
 */
interface NotionExportConfig {
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
}

/**
 * Represents a Notion block
 */
interface NotionBlock {
    id: string;
    type: string;
    [key: string]: unknown;
}

/**
 * Represents markdown conversion result
 */
interface MarkdownResult {
    parent: string;
    children: MarkdownResult[];
    [key: string]: unknown;
}

// Load configuration from environment variables
const config: NotionExportConfig = {
    apiKey: process.env.NOTION_API_KEY || "",
    pageId: process.env.NOTION_PAGE_ID || "",
    outputFilename: process.env.OUTPUT_FILENAME || "exported_notion_page.md",
    outputDir: process.env.OUTPUT_DIR || "exports",
    recursive: process.env.RECURSIVE === "true",
    maxDepth: process.env.MAX_DEPTH ? parseInt(process.env.MAX_DEPTH) : 0
};

function validateEnvironment(): void {
    const requiredVars = ['NOTION_API_KEY', 'NOTION_PAGE_ID'];
    const missingVars = requiredVars.filter(varName => !process.env[varName]);

    if (missingVars.length > 0) {
        throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
    }
}

function validateConfig(config: NotionExportConfig): void {
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
    if (!config.pageId) {
        throw new Error("Invalid configuration: pageId is required");
    }

    // 注意这里不清理ID，因为我们在exportNotionPage函数中处理
    if (!/^[a-f0-9]{32}$/.test(config.pageId.replace(/[\s-]/g, ''))) {
        console.warn(`警告: 页面ID格式可能不正确: ${config.pageId}`);
        console.warn('页面ID应该是32位十六进制字符串，可能包含连字符');
        console.warn('例如: 1ca73a85-7f76-800e-b2f9-e4502426d717 或 1ca73a857f76800eb2f9e4502426d717');
    }
}
/**
 * 从内容中提取子页面ID
 * @param content - Markdown内容
 * @returns 子页面ID数组
 */
function extractSubpageIds(content: string): string[] {
    // 匹配Notion页面链接格式: [标题](32位页面ID)
    const regex = /\[.*?\]\(([a-f0-9]{32})\)/g;
    const matches = [];
    let match;

    while ((match = regex.exec(content)) !== null) {
        matches.push(match[1]);
    }

    return matches;
}

// 定义导出结果类型
/**
 * 导出结果接口
 */
interface ExportResult {
    /** 导出的内容 */
    content: string;
    /** 原始数据，用于子页面提取 */
    rawData?: any;
}

/**
 * 递归导出Notion页面及其子页面
 * @param config - 导出配置
 * @param currentDepth - 当前递归深度
 * @param processedIds - 已处理的页面ID集合（防止循环引用）
 * @throws {Error} 如果导出失败
 */
async function exportNotionPageRecursive(
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
    const result = await exportSinglePage(config);

    // 如果启用了递归导出
    if (config.recursive && result) {
        // 从原始数据中提取子页面ID
        const subpageIds = extractSubpageIds(result.rawData || result.content);

        if (subpageIds.length > 0) {
            console.log(`发现 ${subpageIds.length} 个子页面: ${subpageIds.join(', ')}`);

            // 递归导出每个子页面
            for (const subpageId of subpageIds) {
                console.log(`处理子页面: ${subpageId}`);

                // 为子页面创建新的配置
                const subpageConfig: NotionExportConfig = {
                    ...config,
                    pageId: subpageId,
                    outputFilename: `${subpageId}.md` // 使用页面ID作为文件名
                };

                try {
                    // 递归导出子页面
                    await exportNotionPageRecursive(subpageConfig, currentDepth + 1, processedIds);
                } catch (error) {
                    console.error(`导出子页面 ${subpageId} 失败:`, error);
                    // 继续处理其他子页面
                }
            }
        } else {
            console.log('没有发现子页面');
        }
    }
}

/**
 * 导出单个Notion页面到Markdown
 * @param config - 导出配置
 * @returns 导出结果，包含内容和原始数据
 * @throws {Error} 如果导出失败
 */
async function exportSinglePage(config: NotionExportConfig): Promise<ExportResult | null> {
    try {
        validateEnvironment();
        validateConfig(config);

        // 处理页面ID
        // Notion API要求页面ID不带连字符，但在调用时会自动添加连字符
        const cleanPageId = config.pageId.replace(/[\s-]/g, '');

        console.log(`原始页面ID: ${config.pageId}`);
        console.log(`处理后的页面ID: ${cleanPageId}`);
        console.log(`尝试获取Notion页面内容...`);

        // 更新配置中的页面ID
        config.pageId = cleanPageId;

        // 创建Notion客户端
        const notion: Client = new Client({
            auth: config.apiKey,
        });

        // 创建文件系统导出目录
        const outputDirPath: string = path.resolve(config.outputDir);
        await fs.mkdir(outputDirPath, { recursive: true });
        const outputPath: string = path.join(outputDirPath, config.outputFilename);

        // 使用NotionConverter API
        const converter = new NotionConverter(notion);

        // 创建一个导出器，将内容写入文件并返回内容供递归处理
        let exportedContent: any = null;
        let rawData: any = null;

        const markdownExporter = {
            export: async (data: any): Promise<void> => {
                // 保存原始数据用于子页面提取
                rawData = data;

                // 尝试使用默认渲染器生成Markdown
                let markdown = '';

                if (data.renderer && typeof data.renderer.output === 'string') {
                    markdown = data.renderer.output;
                } else if (data.output && typeof data.output === 'string') {
                    markdown = data.output;
                } else {
                    console.warn('警告: 无法找到渲染后的Markdown内容，尝试手动构建');

                    // 手动构建简单的Markdown
                    try {
                        markdown = convertToMarkdown(data);
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

        /**
         * 手动将Notion数据转换为Markdown
         * @param data - Notion数据
         * @returns Markdown字符串
         */
        function convertToMarkdown(data: any): string {
            let markdown = '';

            // 如果有页面标题，添加为一级标题
            if (data.pageId && data.blockTree && data.blockTree.properties && data.blockTree.properties.title) {
                const titleBlock = data.blockTree.properties.title;
                if (titleBlock.title && titleBlock.title.length > 0) {
                    const titleText = titleBlock.title.map((t: any) => t.plain_text || t.text?.content || '').join('');
                    markdown += `# ${titleText}\n\n`;
                }
            }

            // 递归处理块
            function processBlocks(blocks: any[]) {
                if (!blocks || !Array.isArray(blocks)) return '';

                let result = '';

                for (const block of blocks) {
                    // 根据块类型处理
                    switch (block.type) {
                        case 'paragraph':
                            result += processParagraph(block) + '\n\n';
                            break;
                        case 'heading_1':
                            result += processHeading(block, 1) + '\n\n';
                            break;
                        case 'heading_2':
                            result += processHeading(block, 2) + '\n\n';
                            break;
                        case 'heading_3':
                            result += processHeading(block, 3) + '\n\n';
                            break;
                        case 'bulleted_list_item':
                            result += processBulletedListItem(block) + '\n';
                            break;
                        case 'numbered_list_item':
                            result += processNumberedListItem(block) + '\n';
                            break;
                        case 'to_do':
                            result += processToDo(block) + '\n';
                            break;
                        case 'toggle':
                            result += processToggle(block) + '\n\n';
                            break;
                        case 'child_page':
                            result += processChildPage(block) + '\n\n';
                            break;
                        case 'code':
                            result += processCode(block) + '\n\n';
                            break;
                        case 'quote':
                            result += processQuote(block) + '\n\n';
                            break;
                        case 'divider':
                            result += '---\n\n';
                            break;
                        case 'callout':
                            result += processCallout(block) + '\n\n';
                            break;
                        default:
                            // 处理未知块类型
                            if (block.child_page) {
                                result += processChildPage(block) + '\n\n';
                            } else {
                                result += `[Unsupported block type: ${block.type}]\n\n`;
                            }
                    }

                    // 如果块有子块，递归处理
                    if (block.children && Array.isArray(block.children) && block.children.length > 0) {
                        result += processBlocks(block.children);
                    }
                }

                return result;
            }

            // 处理段落
            function processParagraph(block: any): string {
                if (!block.paragraph) return '';
                return processRichText(block.paragraph.rich_text || block.paragraph.text || []);
            }

            // 处理标题
            function processHeading(block: any, level: number): string {
                const headingKey = `heading_${level}`;
                if (!block[headingKey]) return '';
                const prefix = '#'.repeat(level) + ' ';
                return prefix + processRichText(block[headingKey].rich_text || block[headingKey].text || []);
            }

            // 处理富文本
            function processRichText(richTextArray: any[]): string {
                if (!richTextArray || !Array.isArray(richTextArray)) return '';

                return richTextArray.map(textObj => {
                    let content = textObj.plain_text || textObj.text?.content || '';

                    // 应用文本样式
                    if (textObj.annotations) {
                        if (textObj.annotations.bold) content = `**${content}**`;
                        if (textObj.annotations.italic) content = `*${content}*`;
                        if (textObj.annotations.strikethrough) content = `~~${content}~~`;
                        if (textObj.annotations.code) content = `\`${content}\``;
                        if (textObj.annotations.underline) content = `<u>${content}</u>`;
                    }

                    // 处理链接
                    if (textObj.href || textObj.text?.link) {
                        const link = textObj.href || textObj.text.link.url;
                        content = `[${content}](${link})`;
                    }

                    return content;
                }).join('');
            }

            // 处理无序列表项
            function processBulletedListItem(block: any): string {
                if (!block.bulleted_list_item) return '';
                return `- ${processRichText(block.bulleted_list_item.rich_text || block.bulleted_list_item.text || [])}`;
            }

            // 处理有序列表项
            function processNumberedListItem(block: any): string {
                if (!block.numbered_list_item) return '';
                return `1. ${processRichText(block.numbered_list_item.rich_text || block.numbered_list_item.text || [])}`;
            }

            // 处理待办事项
            function processToDo(block: any): string {
                if (!block.to_do) return '';
                const checkbox = block.to_do.checked ? '[x]' : '[ ]';
                return `${checkbox} ${processRichText(block.to_do.rich_text || block.to_do.text || [])}`;
            }

            // 处理折叠块
            function processToggle(block: any): string {
                if (!block.toggle) return '';
                return `<details>\n<summary>${processRichText(block.toggle.rich_text || block.toggle.text || [])}</summary>\n\n${block.children ? processBlocks(block.children) : ''}\n</details>`;
            }

            // 处理子页面
            function processChildPage(block: any): string {
                const pageTitle = block.child_page?.title || 'Untitled';
                const pageId = block.id;
                return `[📏 ${pageTitle}](${pageId})`;
            }

            // 处理代码块
            function processCode(block: any): string {
                if (!block.code) return '';
                const language = block.code.language || '';
                const code = processRichText(block.code.rich_text || block.code.text || []);
                return `\`\`\`${language}\n${code}\n\`\`\``;
            }

            // 处理引用
            function processQuote(block: any): string {
                if (!block.quote) return '';
                return `> ${processRichText(block.quote.rich_text || block.quote.text || [])}`;
            }

            // 处理提示块
            function processCallout(block: any): string {
                if (!block.callout) return '';
                const emoji = block.callout.icon?.emoji || '';
                return `> ${emoji} ${processRichText(block.callout.rich_text || block.callout.text || [])}`;
            }

            // 处理主要内容
            if (data.blockTree && data.blockTree.blocks) {
                markdown += processBlocks(data.blockTree.blocks);
            }

            return markdown;
        }

        // 配置转换器
        converter
            .downloadMediaTo({
                outputDir: outputDirPath,
                preserveExternalUrls: true
            })
            .withExporter(markdownExporter);

        // 执行转换
        try {
            console.log(`开始转换页面: ${config.pageId}`);
            await converter.convert(config.pageId);
            console.log(`转换完成`);
            return { content: exportedContent || '', rawData }; // 返回导出的内容和原始数据
        } catch (conversionError) {
            console.error(`转换过程中出错:`, conversionError);

            // 尝试使用另一种格式的页面ID
            try {
                // 尝试添加连字符格式
                const formattedId = `${config.pageId.slice(0,8)}-${config.pageId.slice(8,12)}-${config.pageId.slice(12,16)}-${config.pageId.slice(16,20)}-${config.pageId.slice(20)}`;
                console.log(`尝试使用带连字符的ID格式: ${formattedId}`);
                await converter.convert(formattedId);
                console.log(`使用带连字符的ID格式转换成功`);
                return { content: exportedContent || '', rawData }; // 返回导出的内容和原始数据
            } catch (retryError) {
                console.error(`使用带连字符的ID格式仍然失败:`, retryError);
                throw conversionError; // 抛出原始错误
            }
        }
    } catch (error: unknown) {
        if (error instanceof Error) {
            console.error(`Export failed: ${error.message}`);
            if (error.stack) {
                console.error(error.stack);
            }
            throw error; // Re-throw for main error handler
        }
        throw new Error('An unknown error occurred during export');
    }
}

/**
 * 导出Notion页面到Markdown
 * 这是主要的导出函数，根据配置决定是否递归导出子页面
 * @param config - 导出配置
 * @throws {Error} 如果导出失败
 */
async function exportNotionPage(config: NotionExportConfig): Promise<void> {
    try {
        validateEnvironment();
        validateConfig(config);

        if (config.recursive) {
            console.log(`启用递归导出，最大深度: ${config.maxDepth || '无限制'}`);
            await exportNotionPageRecursive(config);
        } else {
            await exportSinglePage(config);
        }
    } catch (error: unknown) {
        if (error instanceof Error) {
            console.error(`Export failed: ${error.message}`);
            if (error.stack) {
                console.error(error.stack);
            }
            throw error; // Re-throw for main error handler
        }
        throw new Error('An unknown error occurred during export');
    }
}

// Main execution
(async () => {
    try {
        await exportNotionPage(config);
        process.exit(0);
    } catch (error: unknown) {
        if (error instanceof Error) {
            console.error(`Fatal error: ${error.message}`);
            if (error.stack) {
                console.error(error.stack);
            }
        } else {
            console.error('An unknown fatal error occurred');
        }
        process.exitCode = 1; // Use exitCode instead of immediate exit
    }
})();
