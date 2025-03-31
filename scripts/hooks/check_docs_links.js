#!/usr/bin/env node
/**
 * pre-commit钩子：文档链接检查
 *
 * 这个脚本作为pre-commit钩子运行，检查提交的文档文件中的链接
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// 获取提交的文件列表
function getStagedFiles() {
  const output = execSync('git diff --cached --name-only --diff-filter=ACM').toString();
  return output.split('\n').filter(file => file.trim() !== '');
}

// 过滤Markdown文件
function filterMarkdownFiles(files) {
  return files.filter(file => file.endsWith('.md') && file.startsWith('website/docs/'));
}

// 主函数
function main() {
  try {
    // 获取提交的文件
    const stagedFiles = getStagedFiles();
    const mdFiles = filterMarkdownFiles(stagedFiles);

    if (mdFiles.length === 0) {
      console.log('没有Markdown文件需要检查');
      process.exit(0);
    }

    console.log(`检查 ${mdFiles.length} 个Markdown文件中的链接...`);

    // 构建命令
    const scriptPath = path.join(__dirname, '../docs/tools/check_links.js');
    const docsDir = 'website/docs';

    // 运行检查脚本
    try {
      execSync(`node ${scriptPath} --dir ${docsDir}`, { stdio: 'inherit' });
      console.log('链接检查通过');
      process.exit(0);
    } catch (error) {
      console.error('链接检查发现问题，但不阻止提交');
      console.log('请检查文档中的链接，确保它们指向正确的目标');
      // 不中断提交流程
      process.exit(0);
    }
  } catch (error) {
    console.error('运行链接检查时出错:', error.message);
    // 工具错误不应阻止提交
    process.exit(0);
  }
}

// 运行主函数
main();
