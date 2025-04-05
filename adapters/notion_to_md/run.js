/**
 * Notion导出工具启动脚本
 * 这个脚本用于解决TypeScript模块导入问题
 */

// 使用require而非import，避免ESM模块系统问题
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// 获取当前脚本所在目录
const scriptDir = __dirname;

// 构建环境变量对象
function buildEnvVars() {
  // 从命令行参数中提取配置
  const args = process.argv.slice(2);
  const envVars = {};
  
  // 处理命令行参数
  args.forEach(arg => {
    if (arg === '--recursive') {
      envVars.RECURSIVE = 'true';
    } else if (arg.startsWith('--max-depth=')) {
      envVars.MAX_DEPTH = arg.split('=')[1];
    } else if (arg === '--use-title') {
      envVars.USE_PAGE_TITLE_AS_FILENAME = 'true';
    }
  });
  
  return envVars;
}

// 主函数
function main() {
  try {
    console.log('开始执行Notion导出脚本...');
    
    // 构建环境变量
    const envVars = buildEnvVars();
    const envVarString = Object.entries(envVars)
      .map(([key, value]) => `${key}=${value}`)
      .join(' ');
    
    // 构建命令
    const command = `cd "${scriptDir}" && ${envVarString} npx ts-node --transpile-only index.ts`;
    
    // 执行命令
    execSync(command, { 
      stdio: 'inherit',
      env: {
        ...process.env,
        ...envVars
      }
    });
    
    console.log('脚本执行成功!');
  } catch (error) {
    console.error('错误: 脚本执行失败', error);
    process.exit(1);
  }
}

// 执行主函数
main();
