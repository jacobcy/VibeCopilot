# Notion 集成设置指南

## 1. 创建 Notion 集成

1. 访问 [Notion Integrations](https://www.notion.so/my-integrations) 页面
2. 点击 "New integration" 按钮
3. 填写集成名称（例如 "VibeCopilot Export"）
4. 选择关联的工作区
5. 设置适当的权限（至少需要 "Read content" 权限）
6. 创建集成并复制生成的 API 密钥（已配置在 `config/default/.env.notion` 文件中）

## 2. 授予集成访问页面的权限

这是最关键的步骤，也是导致当前错误的原因：

1. 打开你想要导出的 Notion 页面：[Research for VibeCopilot](https://www.notion.so/Research-for-VibeCopilot-1ca73a857f76800eb2f9e4502426d717)
2. 点击右上角的 "Share" 按钮
3. 在弹出的共享菜单中，点击 "Invite" 下拉菜单
4. 找到并选择你刚刚创建的集成（例如 "VibeCopilot Export"）
5. 点击 "Invite" 按钮确认

![Notion Share with Integration](https://help.notion.so/images/pages/integrations/share-page-with-integration.png)

## 3. 验证页面 ID

确保你使用的页面 ID 正确：

1. 从页面 URL 中提取 ID：`https://www.notion.so/Research-for-VibeCopilot-1ca73a857f76800eb2f9e4502426d717`
2. 正确的 ID 是 URL 末尾的 32 位字符串：`1ca73a857f76800eb2f9e4502426d717`

## 4. 运行导出脚本

完成上述步骤后，重新运行导出脚本：

```bash
./scripts/run_export_notion.sh
```

## 常见问题排查

如果仍然遇到问题，请检查：

1. 确认集成已被授权访问页面（这是最常见的问题）
2. 验证 API 密钥是否正确
3. 确认页面 ID 格式正确
4. 检查 Notion API 是否有服务中断
