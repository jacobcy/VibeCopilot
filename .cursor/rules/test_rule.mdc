---
id: test-frontmatter-rule
name: 前事项测试规则
type: manual
description: 这是一个带Front Matter的测试规则
globs: ["*.ts", "*.tsx"]
always_apply: true
---

# 前事项测试规则

这是一个带有Front Matter的测试规则文件。

## 规则条目

<!-- BLOCK START id=rule-item-1 type=rule -->
**R1: TypeScript命名约定**

* 接口名称必须以I开头
* 类型名称必须使用PascalCase
* 变量和函数必须使用camelCase
<!-- BLOCK END -->

<!-- BLOCK START id=rule-item-2 type=rule -->
**R2: 导入顺序**

* 标准库导入放在最上面
* 第三方库导入放在第二部分
* 本地模块导入放在最后
<!-- BLOCK END -->

## 示例

<!-- BLOCK START id=example-1 type=example -->
```typescript
// 好的示例
interface IUserProps {
  firstName: string;
  lastName: string;
}

function formatUserName(user: IUserProps): string {
  return `${user.firstName} ${user.lastName}`;
}
```
<!-- BLOCK END -->

<!-- BLOCK START id=example-2 type=example -->
```typescript
// 不好的示例
interface UserProps {
  FirstName: string;
  LastName: string;
}

function Format_User_Name(User: UserProps): string {
  return User.FirstName + " " + User.LastName;
}
```
<!-- BLOCK END -->
