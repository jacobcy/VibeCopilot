#!/usr/bin/env node
/**
 * 文档链接检查工具
 *
 * 这个脚本检查文档中的链接是否有效，可以作为pre-commit钩子或CI步骤运行
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// 匹配Markdown链接: [text](link)
const mdLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;

// 匹配图片链接: ![alt](src)
const imgLinkRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;

// 匹配HTML链接: <a href="link">text</a>
const htmlLinkRegex = /<a\s+(?:[^>]*?\s+)?href="([^"]*)"([^>]*)>(.*?)<\/a>/g;

// 匹配HTML图片: <img src="src" ... />
const htmlImgRegex = /<img\s+(?:[^>]*?\s+)?src="([^"]*)"([^>]*)>/g;

// 忽略的链接模式
const ignorePatterns = [
  /^https?:\/\//,  // 外部链接
  /^#/,            // 页内锚点
  /^mailto:/,      // 邮件链接
  /^tel:/          // 电话链接
];

// 获取命令行参数
const args = process.argv.slice(2);
let docsDir = 'docs';
const strict = args.includes('--strict');
const verbose = args.includes('--verbose');

// 处理--dir参数
const dirIndex = args.indexOf('--dir');
if (dirIndex !== -1 && dirIndex + 1 < args.length) {
  docsDir = args[dirIndex + 1];
}

/**
 * 检查链接是否应该被忽略
 */
function shouldIgnoreLink(link) {
  return ignorePatterns.some(pattern => pattern.test(link));
}

/**
 * 检查文件是否存在
 */
function fileExists(filepath) {
  try {
    return fs.existsSync(filepath);
  } catch (err) {
    return false;
  }
}

/**
 * 检查文件中的链接
 */
function checkLinksInFile(filepath, docsRoot) {
  const content = fs.readFileSync(filepath, 'utf8');
  const dir = path.dirname(filepath);
  const brokenLinks = [];

  // 检查Markdown链接
  let match;
  while ((match = mdLinkRegex.exec(content)) !== null) {
    const [fullMatch, text, link] = match;
    if (shouldIgnoreLink(link)) continue;

    let targetPath;
    if (link.startsWith('/')) {
      // 绝对路径 (相对于docsRoot)
      targetPath = path.join(docsRoot, link);
    } else {
      // 相对路径
      targetPath = path.join(dir, link);
    }

    // 处理没有扩展名的链接 (Docusaurus会自动添加.html)
    let fileToCheck = targetPath;
    if (!path.extname(targetPath)) {
      fileToCheck = `${targetPath}.md`;
    }

    // 检查文件是否存在
    if (!fileExists(fileToCheck)) {
      brokenLinks.push({
        type: 'markdown',
        link,
        text,
        targetPath: fileToCheck,
        position: match.index
      });
    }
  }

  // 检查图片链接
  while ((match = imgLinkRegex.exec(content)) !== null) {
    const [fullMatch, alt, src] = match;
    if (shouldIgnoreLink(src)) continue;

    let targetPath;
    if (src.startsWith('/')) {
      // 绝对路径 (相对于docsRoot)
      targetPath = path.join(docsRoot, src);
    } else {
      // 相对路径
      targetPath = path.join(dir, src);
    }

    // 检查文件是否存在
    if (!fileExists(targetPath)) {
      brokenLinks.push({
        type: 'image',
        link: src,
        text: alt,
        targetPath,
        position: match.index
      });
    }
  }

  // 检查HTML链接
  while ((match = htmlLinkRegex.exec(content)) !== null) {
    const [fullMatch, href, attrs, text] = match;
    if (shouldIgnoreLink(href)) continue;

    let targetPath;
    if (href.startsWith('/')) {
      // 绝对路径 (相对于docsRoot)
      targetPath = path.join(docsRoot, href);
    } else {
      // 相对路径
      targetPath = path.join(dir, href);
    }

    // 处理没有扩展名的链接 (Docusaurus会自动添加.html)
    let fileToCheck = targetPath;
    if (!path.extname(targetPath)) {
      fileToCheck = `${targetPath}.md`;
    }

    // 检查文件是否存在
    if (!fileExists(fileToCheck)) {
      brokenLinks.push({
        type: 'html-link',
        link: href,
        text,
        targetPath: fileToCheck,
        position: match.index
      });
    }
  }

  // 检查HTML图片
  while ((match = htmlImgRegex.exec(content)) !== null) {
    const [fullMatch, src, attrs] = match;
    if (shouldIgnoreLink(src)) continue;

    let targetPath;
    if (src.startsWith('/')) {
      // 绝对路径 (相对于docsRoot)
      targetPath = path.join(docsRoot, src);
    } else {
      // 相对路径
      targetPath = path.join(dir, src);
    }

    // 检查文件是否存在
    if (!fileExists(targetPath)) {
      brokenLinks.push({
        type: 'html-image',
        link: src,
        text: 'Image',
        targetPath,
        position: match.index
      });
    }
  }

  return brokenLinks;
}

/**
 * 主函数
 */
function main() {
  console.log(`检查 ${docsDir} 中的链接...`);

  // 获取所有Markdown文件
  const mdFiles = glob.sync(`${docsDir}/**/*.md`);
  console.log(`找到 ${mdFiles.length} 个Markdown文件`);

  // 检查每个文件
  let totalBrokenLinks = 0;
  let filesWithBrokenLinks = 0;

  mdFiles.forEach(file => {
    const brokenLinks = checkLinksInFile(file, docsDir);

    if (brokenLinks.length > 0) {
      filesWithBrokenLinks++;
      totalBrokenLinks += brokenLinks.length;

      // 打印详情
      console.log(`\n文件: ${file}`);
      console.log(`发现 ${brokenLinks.length} 个无效链接:`);

      brokenLinks.forEach(link => {
        console.log(`  - [${link.type}] "${link.text}" -> ${link.link}`);
        if (verbose) {
          console.log(`    目标路径: ${link.targetPath}`);
          console.log(`    位置: 字符 ${link.position}`);
        }
      });
    }
  });

  // 打印总结
  console.log(`\n总结:`);
  console.log(`- 检查了 ${mdFiles.length} 个文件`);
  console.log(`- ${filesWithBrokenLinks} 个文件中发现问题`);
  console.log(`- 共发现 ${totalBrokenLinks} 个无效链接`);

  // 如果是严格模式，发现问题就返回非零状态码
  if (strict && totalBrokenLinks > 0) {
    console.error('严格模式：发现无效链接，检查失败');
    process.exit(1);
  }

  process.exit(0);
}

// 运行主函数
main();
