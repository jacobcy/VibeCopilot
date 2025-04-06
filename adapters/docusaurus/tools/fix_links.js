#!/usr/bin/env node
/**
 * 文档链接自动修复工具
 *
 * 这个脚本使用check-md库自动修复文档中的无效链接
 * 可以作为独立工具或从链接检查工具中调用
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// 获取命令行参数
const args = process.argv.slice(2);
let docsDir = 'docs';
const verbose = args.includes('--verbose');
const dryRun = args.includes('--dry-run');

// 处理--dir参数
const dirIndex = args.indexOf('--dir');
if (dirIndex !== -1 && dirIndex + 1 < args.length) {
  docsDir = args[dirIndex + 1];
}

/**
 * 使用check-md修复链接
 */
function fixLinks(dirPath, dryRun = false) {
  try {
    console.log(`尝试修复 ${dirPath} 中的链接...`);

    const fixCmd = dryRun
      ? `npx check-md -c ${dirPath}`
      : `npx check-md -c ${dirPath} -f`;

    const output = execSync(fixCmd, { encoding: 'utf8' });

    if (verbose) {
      console.log(output);
    } else {
      // 提取并显示简洁的结果
      const deadLinksMatch = output.match(/(\d+) dead links was found/);
      if (deadLinksMatch) {
        console.log(`发现 ${deadLinksMatch[1]} 个无效链接。`);
      }

      if (!dryRun) {
        const fixedLinksMatch = output.match(/Fixed (\d+) issues/);
        if (fixedLinksMatch) {
          console.log(`已修复 ${fixedLinksMatch[1]} 个问题。`);
        } else {
          console.log('没有问题被修复。');
        }
      }
    }

    return true;
  } catch (error) {
    if (verbose) {
      console.error('修复链接时出错:', error.message);
      if (error.stdout) {
        console.log(error.stdout.toString());
      }
      if (error.stderr) {
        console.error(error.stderr.toString());
      }
    } else {
      // 提取并显示简洁的结果
      let errorOutput = error.stdout ? error.stdout.toString() : '';
      const deadLinksMatch = errorOutput.match(/(\d+) dead links was found/);
      if (deadLinksMatch) {
        console.log(`发现 ${deadLinksMatch[1]} 个无效链接。`);
      }

      if (!dryRun) {
        const fixedLinksMatch = errorOutput.match(/Fixed (\d+) issues/);
        if (fixedLinksMatch) {
          console.log(`已修复 ${fixedLinksMatch[1]} 个问题。`);
        } else {
          console.log('没有问题被修复。');
        }
      }
    }

    return false;
  }
}

/**
 * 主函数
 */
function main() {
  const absolutePath = path.resolve(docsDir);

  if (!fs.existsSync(absolutePath)) {
    console.error(`错误: 目录 "${docsDir}" 不存在。`);
    process.exit(1);
  }

  console.log(`检查并修复 ${docsDir} 中的链接...`);

  if (dryRun) {
    console.log('注意: 以干运行模式执行，不会实际修改文件。');
  }

  const success = fixLinks(absolutePath, dryRun);

  if (success) {
    console.log('链接检查和修复过程完成。');
    process.exit(0);
  } else {
    console.error('链接修复过程中出现错误。');
    process.exit(1);
  }
}

// 执行主函数
main();
