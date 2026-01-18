# Playwright 操作参考

本文件提供商品上新各步骤的 Playwright MCP 操作示例。
当收到用户的真实系统信息后，替换下方占位符即可执行。

## 通用操作模式

### 登录流程（通用）

```javascript
// 1. 导航到登录页
await browser_navigate({ url: "https://system.example.com/login" });

// 2. 等待页面加载完成，获取快照
await browser_snapshot();

// 3. 填写登录表单
await browser_fill_form({
  fields: [
    { name: "用户名", type: "textbox", ref: "用户名输入框ref", value: "username" },
    { name: "密码", type: "textbox", ref: "密码输入框ref", value: "password" }
  ]
});

// 4. 点击登录按钮
await browser_click({ element: "登录按钮", ref: "登录按钮ref" });

// 5. 等待登录成功
await browser_wait_for({ text: "欢迎" });
```

## Step 1: 商品中台 - 创建商品

```javascript
// 导航到创建商品页面
await browser_navigate({ url: "${PRODUCT_CENTER_URL}/product/create" });
await browser_snapshot();

// 填写商品基本信息
await browser_fill_form({
  fields: [
    { name: "商品名称", type: "textbox", ref: "商品名称ref", value: "${product_name}" },
    { name: "商品分类", type: "combobox", ref: "分类下拉框ref", value: "${category}" },
    { name: "销售价格", type: "textbox", ref: "价格输入框ref", value: "${price}" }
  ]
});

// 如果有规格选项
// await browser_click({ element: "添加规格", ref: "添加规格按钮ref" });
// 循环添加每个规格...

// 保存商品
await browser_click({ element: "保存按钮", ref: "保存按钮ref" });

// 等待保存成功，获取商品ID
await browser_wait_for({ text: "保存成功" });
await browser_snapshot();
// 从页面提取商品ID用于后续步骤
```

## Step 2: POS 后台 - 配置门店可售

```javascript
// 导航到 POS 后台菜单管理
await browser_navigate({ url: "${POS_ADMIN_URL}/menu/products" });
await browser_snapshot();

// 搜索刚创建的商品
await browser_type({
  element: "搜索框",
  ref: "搜索框ref",
  text: "${product_name}",
  submit: true
});

await browser_wait_for({ text: "${product_name}" });
await browser_snapshot();

// 点击商品进入编辑
await browser_click({ element: "商品行", ref: "搜索结果第一行ref" });

// 启用门店可售
await browser_click({ element: "启用开关", ref: "门店可售开关ref" });

// 同步到门店
await browser_click({ element: "同步按钮", ref: "同步到门店按钮ref" });
await browser_wait_for({ text: "同步成功" });
```

## Step 3: 小程序后台 - 配置 C 端展示

```javascript
// 导航到小程序后台商品列表
await browser_navigate({ url: "${MP_ADMIN_URL}/products" });
await browser_snapshot();

// 搜索商品
await browser_type({
  element: "搜索框",
  ref: "商品搜索框ref",
  text: "${product_name}",
  submit: true
});

await browser_wait_for({ text: "${product_name}" });

// 点击编辑
await browser_click({ element: "编辑按钮", ref: "编辑按钮ref" });
await browser_snapshot();

// 上传商品图片（需要本地图片路径）
// await browser_file_upload({ paths: ["/path/to/product-image.jpg"] });

// 选择上架区域
await browser_click({ element: "区域选择器", ref: "区域选择器ref" });
// 勾选对应区域...

// 发布上架
await browser_click({ element: "发布按钮", ref: "发布按钮ref" });
await browser_wait_for({ text: "发布成功" });
```

## Step 4: 验证上架结果

```javascript
// 验证商品中台
await browser_navigate({ url: "${PRODUCT_CENTER_URL}/product/${product_id}" });
await browser_snapshot();
// 检查状态是否为「已上架」

// 验证 POS 后台
await browser_navigate({ url: "${POS_ADMIN_URL}/menu/products?search=${product_name}" });
await browser_snapshot();
// 检查是否显示「可售」

// 验证小程序（可选：使用小程序开发者工具预览）
await browser_navigate({ url: "${MP_ADMIN_URL}/products?search=${product_name}" });
await browser_snapshot();
// 检查状态是否为「已上架」
```

## 错误处理模式

```javascript
// 带重试的操作
async function withRetry(operation, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await operation();
      return;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await browser_wait_for({ time: 2 }); // 等待2秒后重试
    }
  }
}

// 截图保存证据
await browser_take_screenshot({
  filename: "product-launch-step1-complete.png"
});
```

## 注意事项

1. **ref 值获取**：每次 `browser_snapshot()` 后，从返回的快照中获取准确的 ref 值
2. **动态等待**：使用 `browser_wait_for` 等待页面加载完成，避免操作失败
3. **截图记录**：关键步骤截图保存，便于问题排查和审计
4. **变量替换**：`${variable}` 格式的变量会在执行时替换为实际值
