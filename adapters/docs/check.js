#!/usr/bin/env node
/**
 * 文档语法和链接检查工具
 *
 * 这个脚本检查指定文件或目录中的Markdown文件的语法和链接问题，
 * 并提供详细的错误报告，包括问题文件、行号和问题描述。
 *
 * 用法:
 *   node scripts/docs/check.js <path> [--fix]
 *
 * 参数:
 *   path        要检查的文件或目录路径
 *   --fix       自动修复可以修复的问题
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// 获取命令行参数
const args = process.argv.slice(2);
const targetPath = args[0] || 'docs';
const shouldFix = args.includes('--fix');

// 主函数
function main() {
  if (!fs.existsSync(targetPath)) {
    console.error(`错误: 指定的路径不存在: ${targetPath}`);
    process.exit(1);
  }

  console.log(`===== 文档检查工具 =====`);
  console.log(`检查路径: ${targetPath}`);
  console.log(`自动修复: ${shouldFix ? '是' : '否'}`);
  console.log('');

  // 检查语法
  checkMarkdownLint();

  // 检查链接
  checkLinks();

  console.log('');
  console.log('检查完成');
}

// 检查Markdown语法
function checkMarkdownLint() {
  console.log(`----- 检查Markdown语法 -----`);

  try {
    const fixArg = shouldFix ? '--fix' : '';
    const cmd = `npx markdownlint ${fixArg} --verbose "${targetPath}"`;

    try {
      const output = execSync(cmd, { encoding: 'utf8' });
      console.log('✅ Markdown语法检查通过');
    } catch (error) {
      console.log('⚠️ Markdown语法检查发现问题:');
      console.log(error.stdout);
    }
  } catch (error) {
    console.error(`运行markdownlint时出错: ${error.message}`);
  }

  console.log('');
}

// 检查链接
function checkLinks() {
  console.log(`----- 检查文档链接 -----`);

  try {
    // 确定目标目录
    let docsDir = 'docs';
    if (fs.existsSync(targetPath) && fs.statSync(targetPath).isDirectory()) {
      docsDir = targetPath;
    } else {
      docsDir = path.dirname(targetPath);
    }

    const scriptPath = path.join(__dirname, 'tools/check_links.js');
    const cmd = `node ${scriptPath} --dir "${docsDir}" --verbose`;

    try {
      const output = execSync(cmd, { encoding: 'utf8' });
      console.log('✅ 链接检查通过');
    } catch (error) {
      console.log('⚠️ 链接检查发现问题:');
      if (error.stdout) {
        console.log(error.stdout);
      } else {
        console.log('未能获取详细的链接错误信息');
      }
    }
  } catch (error) {
    console.error(`运行链接检查时出错: ${error.message}`);
  }
}

// 运行主函数
main();
