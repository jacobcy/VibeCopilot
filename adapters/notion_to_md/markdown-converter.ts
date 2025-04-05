/**
 * Markdown转换模块
 * 负责将Notion数据转换为Markdown格式
 */

/**
 * 将Notion数据手动转换为Markdown
 * @param data - Notion数据
 * @returns 包含Markdown内容和页面标题的对象
 */
export function convertToMarkdown(data: any): { markdown: string; pageTitle: string } {
    let markdown = '';
    let pageTitle = '';
    
    // 如果有页面标题，添加为一级标题
    if (data.pageId && data.blockTree && data.blockTree.properties && data.blockTree.properties.title) {
        const titleBlock = data.blockTree.properties.title;
        if (titleBlock.title && titleBlock.title.length > 0) {
            pageTitle = titleBlock.title.map((t: any) => t.plain_text || t.text?.content || '').join('');
            markdown += `# ${pageTitle}\n\n`;
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
        return `[📑 ${pageTitle}](${pageId})`;
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
    
    return { markdown, pageTitle };
}
