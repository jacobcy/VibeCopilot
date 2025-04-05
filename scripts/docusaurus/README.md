# Docusaurus 文档工具

这个目录包含用于管理和部署Docusaurus文档网站的脚本。

## 快速开始

### Windows用户

1. **修复依赖问题**：首先运行 `fix_dependencies.bat` 来解决React 19的兼容性问题
2. **启动开发环境**：运行 `start_docusaurus.bat` 启动开发服务器
3. **构建和部署**：运行 `build_deploy.bat` 或简单的 `build_website.bat` 构建静态网站

### Mac/Linux用户

1. **修复依赖问题**：
   ```bash
   chmod +x fix_dependencies.sh
   ./fix_dependencies.sh
   ```

2. **启动开发环境**：
   ```bash
   chmod +x start_docusaurus.sh
   ./start_docusaurus.sh
   ```

3. **构建网站**：
   ```bash
   chmod +x build_website.sh
   ./build_website.sh
   ```

## 常见问题排除

### 构建失败

如果构建或启动开发服务器失败，通常是由以下原因造成：

1. **React版本不兼容**：
   - 错误信息：`Invalid hook call...`
   - 解决方案：运行 `fix_dependencies.sh` 或 `fix_dependencies.bat` 降级React版本

2. **Node.js版本过低**：
   - 错误信息：`Minimum Node.js version not met`
   - 解决方案：升级Node.js到18.0或更高版本

3. **依赖冲突**：
   - 错误信息：`Conflicting peer dependency`
   - 解决方案：删除node_modules目录并重新安装依赖

## 脚本说明

- **fix_dependencies.sh/bat**: 将React从19降级到18，解决兼容性问题
- **build_website.sh/bat**: 简化版构建脚本，只执行构建过程
- **start_docusaurus.sh/bat**: 启动开发服务器和文档同步
- **build_deploy.sh/bat**: 构建和可选部署到GitHub Pages

## 更多信息

详细的Docusaurus使用指南请参阅：

- `/docs/user/tutorials/docusaurus/docusaurus_guide.md`
- `/docs/user/tutorials/docusaurus/obsidian_docusaurus_integration.md`
