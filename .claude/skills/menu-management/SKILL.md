---
name: menu-management
description: |
  菜单运营管理。调整门店菜单结构、商品排序、分类管理。
  当用户提到：菜单调整、菜单排序、分类管理、菜单上下架、调整菜单时使用。
allowed-tools:
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_click
  - mcp__playwright__browser_type
  - mcp__playwright__browser_snapshot
  - mcp__playwright__browser_fill_form
  - Read

# ============================================
# 企业扩展字段
# ============================================
version: "1.0"
category: 菜单管理
owner: 门店运营组
tags: [菜单, 分类, 排序, 门店]

inputs:
  - name: operation_type
    type: enum
    required: true
    options: [调整排序, 上架商品, 下架商品, 新建分类, 删除分类]
    description: 操作类型

  - name: store_scope
    type: enum
    required: true
    options: [全部门店, 指定区域, 指定门店]
    description: 生效范围

  - name: store_ids
    type: array
    required: false
    description: 指定门店ID列表（store_scope为指定门店时必填）

  - name: category_name
    type: string
    required: false
    description: 分类名称（分类操作时必填）

  - name: product_ids
    type: array
    required: false
    description: 商品ID列表（商品操作时必填）

  - name: sort_order
    type: object
    required: false
    description: 排序配置，格式 {product_id: order_number}

target_systems:
  - name: POS后台
    type: WEB
    description: 门店菜单配置

approval:
  required_when:
    - condition: "store_scope == '全部门店'"
      approvers: [运营总监]
      reason: "全部门店生效需运营总监审批"

estimated_duration: 10min
risk_level: low
rollback_supported: true
---

# 菜单运营管理

## 场景说明

本技能用于管理门店菜单，包括：
- 调整商品在菜单中的排序
- 商品上架/下架到指定门店
- 创建/删除菜单分类
- 批量配置门店菜单

## 支持的操作类型

### 1. 调整排序
调整商品在菜单分类中的显示顺序，影响门店 POS 和 C 端展示。

### 2. 上架商品
将已有商品添加到指定门店菜单，使其可售。

### 3. 下架商品
从指定门店菜单移除商品，停止销售但保留商品数据。

### 4. 新建分类
创建新的菜单分类，如"季节限定"、"早餐系列"。

### 5. 删除分类
删除空的菜单分类（分类下有商品时需先移走商品）。

## 执行步骤

### Step 1: 确认操作范围

根据 `store_scope` 确定影响范围：
- 全部门店：需特别谨慎，建议先小范围测试
- 指定区域：按区域批量操作
- 指定门店：精确到具体门店

### Step 2: 登录 POS 后台

```
1. 打开 POS 后台：[待配置URL]
2. 进入「菜单管理」
3. 选择对应的门店/区域
```

### Step 3: 执行具体操作

根据 `operation_type` 执行对应操作，详见各操作类型的详细步骤。

### Step 4: 同步到门店

```
1. 确认修改内容
2. 点击「同步到门店」
3. 等待同步完成
4. 验证门店 POS 菜单已更新
```

## 常见问题处理

### Q1: 同步后门店未更新
- 原因：门店 POS 缓存未刷新
- 解决：门店重启 POS 应用或等待自动刷新（通常15分钟）

### Q2: 无法删除分类
- 原因：分类下仍有商品
- 解决：先将商品移到其他分类

## 回滚操作

菜单变更支持回滚：
1. 进入「操作历史」
2. 找到对应变更记录
3. 点击「回滚」恢复原状态

## 相关技能

- [product-launch](../product-launch/SKILL.md) - 商品上新
- [price-adjustment](../price-adjustment/SKILL.md) - 价格调整

## 变更记录

| 版本 | 日期 | 变更说明 | 作者 |
|------|------|---------|------|
| 1.0 | 2024-01 | 初始版本 | - |
