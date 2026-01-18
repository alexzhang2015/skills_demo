# 系统配置

本文件用于配置商品上新涉及的各系统 URL 和登录信息。
**注意：不要在此文件中存储真实密码，使用环境变量或密钥管理服务。**

## 商品中台

```yaml
url: https://product.example.com  # TODO: 替换为真实URL
login_page: /login
home_page: /dashboard
create_product_page: /product/create

# 页面元素选择器（用于 Playwright 操作）
selectors:
  username_input: "#username"
  password_input: "#password"
  login_button: "button[type='submit']"
  product_name_input: "#product-name"
  category_select: "#category"
  price_input: "#price"
  save_button: ".btn-save"
```

## POS 后台

```yaml
url: https://pos-admin.example.com  # TODO: 替换为真实URL
login_page: /login
menu_config_page: /menu/products

selectors:
  search_input: ".search-box input"
  search_button: ".search-box button"
  enable_toggle: ".store-enable-toggle"
  sync_button: ".sync-to-stores"
```

## 小程序后台

```yaml
url: https://mp-admin.example.com  # TODO: 替换为真实URL
login_page: /login
product_list_page: /products

selectors:
  product_search: "#product-search"
  edit_button: ".btn-edit"
  image_upload: "input[type='file']"
  region_select: "#region-selector"
  publish_button: ".btn-publish"
```

## 环境变量配置

在 `.env` 文件中配置以下变量：

```bash
# 商品中台
PRODUCT_CENTER_URL=https://product.example.com
PRODUCT_CENTER_USER=your_username

# POS 后台
POS_ADMIN_URL=https://pos-admin.example.com
POS_ADMIN_USER=your_username

# 小程序后台
MP_ADMIN_URL=https://mp-admin.example.com
MP_ADMIN_USER=your_username
```

## 配置更新记录

| 日期 | 系统 | 变更内容 | 操作人 |
|------|------|---------|--------|
| - | - | 初始模板 | - |
