# Docusaurus 文档工具

这个目录包含用于管理和部署Docusaurus文档网站的脚本。

## 快速开始

### Windows用户

1. **启动开发环境**：双击 `start_docusaurus.bat` 启动开发服务器和文档同步
2. **构建和部署**：双击 `build_deploy.bat` 构建静态网站并选择性部署

### Mac/Linux用户

1. **启动开发环境**：
   ```bash
   chmod +x start_docusaurus.sh
   ./start_docusaurus.sh
   ```

2. **构建和部署**：
   ```bash
   chmod +x build_deploy.sh
   ./build_deploy.sh
   ```

## 脚本功能

### start_docusaurus
启动完整的开发环境，包括：
- 检查并安装依赖
- 生成侧边栏配置
- 启动文档同步监控
- 启动Docusaurus开发服务器

### build_deploy
构建和部署文档网站，步骤包括：
- 同步所有文档
- 验证文档链接
- 生成侧边栏配置
- 构建静态网站
- 可选部署到GitHub Pages

## 常见问题

1. **Node.js版本**：确保Node.js版本 >= 16.14
2. **依赖问题**：如遇npm依赖问题，尝试删除`node_modules`目录后重新安装
3. **部署失败**：检查GitHub配置和权限

## 更多信息

详细的Docusaurus使用指南请参阅：
- `/docs/user/tutorials/docusaurus/docusaurus_guide.md`
- `/docs/user/tutorials/docusaurus/obsidian_docusaurus_integration.md`
