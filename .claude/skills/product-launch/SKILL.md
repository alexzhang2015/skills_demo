---
name: product-launch
description: |
  商品上新流程。将新商品从创建到全渠道上架。
  当用户提到：新品上架、商品上新、创建新SKU、上新品、添加新商品时使用。
allowed-tools:
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_click
  - mcp__playwright__browser_type
  - mcp__playwright__browser_snapshot
  - mcp__playwright__browser_fill_form
  - mcp__playwright__browser_take_screenshot
  - Read
  - Write
  - Bash

# ============================================
# 企业扩展字段（P1/P2 阶段 Agent SDK 解析使用）
# Claude Code 会忽略这些字段，不影响 P0 使用
# ============================================
version: "1.0"
category: 商品管理
owner: 商品运营组
tags: [商品, 上新, SKU, 全渠道]

inputs:
  - name: product_name
    type: string
    required: true
    description: 商品名称
    example: "冰美式咖啡"

  - name: sku_code
    type: string
    required: false
    description: SKU编码，不填则自动生成
    example: "SKU202401001"

  - name: category
    type: enum
    required: true
    options: [咖啡, 茶饮, 果饮, 小食, 甜点, 周边]
    description: 商品分类

  - name: price
    type: number
    required: true
    description: 销售价格（元）
    example: 28.00

  - name: cost
    type: number
    required: false
    description: 成本价（元），用于毛利计算

  - name: specs
    type: array
    required: false
    description: 规格选项
    example: ["中杯", "大杯", "超大杯"]

  - name: regions
    type: array
    required: false
    description: 上架区域，默认全国
    default: ["全国"]

  - name: launch_date
    type: date
    required: false
    description: 计划上架日期，不填则立即上架

target_systems:
  - name: 商品中台
    type: WEB
    description: 商品主数据管理
  - name: POS后台
    type: WEB
    description: 门店POS配置
  - name: 小程序后台
    type: WEB
    description: C端展示配置

approval:
  required_when:
    - condition: "price > 50"
      approvers: [商品经理]
      reason: "高价商品需商品经理审批"
    - condition: "regions contains '全国'"
      approvers: [运营总监]
      reason: "全国上架需运营总监审批"

estimated_duration: 15min
risk_level: medium
rollback_supported: true
---

# 商品上新

## 场景说明

本技能用于将新商品完成全渠道上架，包括：
1. 在商品中台创建商品主数据
2. 同步到 POS 后台配置门店可售
3. 同步到小程序后台配置 C 端展示

## 前置条件

- 已获取商品中台、POS后台、小程序后台的登录权限
- 商品图片已准备好（主图、详情图）
- 商品定价已确认

## 执行步骤

### Step 1: 登录商品中台

```
1. 打开商品中台：[待配置URL]
2. 使用企业账号登录
3. 进入「商品管理」->「新建商品」
```

### Step 2: 创建商品主数据

在商品中台填写以下信息：

| 字段 | 值 | 说明 |
|------|-----|------|
| 商品名称 | ${product_name} | 必填 |
| SKU编码 | ${sku_code} | 不填则自动生成 |
| 商品分类 | ${category} | 必填 |
| 销售价格 | ${price} | 必填 |
| 成本价 | ${cost} | 选填，用于毛利分析 |
| 规格选项 | ${specs} | 如中杯/大杯 |

操作完成后点击「保存」，记录生成的商品ID。

### Step 3: 同步到 POS 后台

```
1. 打开 POS 后台：[待配置URL]
2. 进入「菜单管理」->「商品配置」
3. 搜索刚创建的商品
4. 配置：
   - 门店可售状态：启用
   - 按钮位置：根据分类自动分配
   - 打印设置：默认模板
5. 点击「同步到门店」
```

### Step 4: 同步到小程序后台

```
1. 打开小程序后台：[待配置URL]
2. 进入「商品管理」->「商品列表」
3. 找到待上架商品，点击「编辑」
4. 上传商品图片（主图 + 详情图）
5. 配置：
   - 上架区域：${regions}
   - 上架时间：${launch_date} 或立即上架
   - 商品标签：新品
6. 点击「发布」
```

### Step 5: 验证上架结果

执行以下验证：
- [ ] 商品中台：商品状态为「已上架」
- [ ] POS 后台：门店可查询到该商品
- [ ] 小程序：C 端可正常浏览和下单

如验证失败，参考下方「常见问题处理」。

## 常见问题处理

### Q1: SKU 编码重复
- 原因：该编码已被其他商品使用
- 解决：修改编码或使用自动生成

### Q2: POS 同步失败
- 原因：网络超时或门店离线
- 解决：等待 5 分钟后重试，或联系 IT 支持

### Q3: 小程序图片上传失败
- 原因：图片尺寸或格式不符合要求
- 解决：确保图片为 JPG/PNG，尺寸 750x750px

### Q4: 部分门店未同步
- 原因：门店 POS 版本过低
- 解决：联系 IT 安排门店 POS 升级

## 回滚操作

如需撤销上架：
1. 小程序后台：将商品状态改为「下架」
2. POS 后台：将门店可售状态改为「停售」
3. 商品中台：将商品状态改为「草稿」

## 相关技能

- [menu-management](../menu-management/SKILL.md) - 菜单运营
- [price-adjustment](../price-adjustment/SKILL.md) - 价格调整
- [inventory-check](../inventory-check/SKILL.md) - 库存查询

## 变更记录

| 版本 | 日期 | 变更说明 | 作者 |
|------|------|---------|------|
| 1.0 | 2024-01 | 初始版本 | - |
