# ZZZeroUID

<p align="center">
  <a href="https://github.com/gakkiri/ZZZeroUID"><img src="https://s2.loli.net/2024/04/19/hOEDmsoUFy6nH5d.jpg" width="480" height="270" alt="ZZZeroUID"></a>
</p>
<h1 align="center">ZZZeroUID 2.6.0</h1>
<h4 align="center">基于 gsuid_core 的绝区零 Bot 插件（支持 OneBot(QQ)、QQ频道、微信、开黑啦、Telegram）</h4>
<div align="center">
  <a href="https://docs.sayu-bot.com/" target="_blank">安装文档</a> &nbsp; · &nbsp;
  <a href="https://docs.sayu-bot.com/插件帮助/ZZZeroUID.html" target="_blank">指令文档</a> &nbsp; · &nbsp;
  <a href="https://docs.sayu-bot.com/常见问题/" target="_blank">常见问题</a>
</div>

## 安装提醒

- 本插件为 [gsuid_core](https://github.com/Genshin-bots/gsuid_core) 扩展。
- 已安装并更新 core 后，可直接发送 `core安装插件zzzerouid`，重启 core 生效。
- 默认命令前缀请以你的 Bot 配置为准（文档示例通常使用 `zzz`）。

## 功能总览（当前完整能力）

### 1. 账号与绑定

- 绑定 UID：`绑定UID100740568` / `绑定`
- 切换 UID：`切换UID100740568` / `切换`
- 删除 UID：`删除UID100740568` / `解绑`

### 2. 基础查询与战绩

- 基础信息总览：`查询`
- 实时便笺：`mr`、`便签`、`便笺`
- 式舆防卫战：`深渊`、`上期深渊`、`完整深渊`
- 危局强袭战：`强袭战`、`危局强袭战`、`上期强袭战`
- 临界推演：`临界推演`、`临界`、`推演`
- 零号空洞：`零号空洞`

### 3. 面板与练度

- 刷新面板：`刷新面板`、`更新面板`
- 查询角色面板：`查询露西`、`露西面板`、`角色面板露西`
- 伤害面板：`露西伤害`、`露西伤害3`
- 练度统计/角色列表：`练度统计`、`角色列表`

### 4. 抽卡与卡池

- 抽卡记录：`抽卡记录`
- 刷新抽卡记录：`刷新抽卡记录`、`全量刷新抽卡记录`
- 当前卡池：`卡池`、`当前卡池`、`本期卡池`
- 版本卡池：`2.6卡池`、`2.6上半卡池`
- 卡池历史：`卡池历史`、`卡池记录`
- 复刻统计与单角色/音擎记录：`五星角色复刻记录`、`四星音擎复刻记录`、`艾莲复刻记录`

### 5. Wiki 与攻略

- 角色图鉴：`角色图鉴露西`
- 角色攻略：`角色攻略露西`、`露西攻略`
- 音擎攻略：`音擎攻略硫磺石`
- 驱动盘图鉴：`驱动盘啄木鸟电音`
- 突破材料：`突破材料露西`
- 武器快捷查询：`武器硫磺石`
- 邦布图鉴：`邦布招财布`

### 6. 排行榜（群功能）

- 查询群排名：`深渊排名`、`危局排名`、`临界排名`
- 个人显示/隐藏：`显示深渊排名`、`隐藏危局排名`
- 群开关（管理员）：`开启群深渊排名`、`关闭群危局排名`
- 排名重置（管理员）：`重置深渊排名`、`清空临界排名`

### 7. 挑战提醒（新增）

- 个人开关：`开启挑战提醒`、`关闭挑战提醒`
- 个人阈值：`设置深渊阈值6`、`设置危局阈值9`
- 提醒时间：`设置个人提醒时间每日20时`、`个人提醒时间`、`重置个人提醒时间`
- 状态查询：`查询挑战状态`
- 全局配置（管理员）：`开启全局挑战提醒` / `关闭全局挑战提醒`
- 全局提醒时间（管理员）：`设置全局提醒时间每周六20时`
- 全局阈值（管理员）：`设置全局深渊阈值6` / `设置全局危局阈值9`

### 8. 设备绑定（新增）

- 帮助：`绑定设备帮助`
- 绑定：`绑定设备 {"device_id":"...","device_fp":"..."}`
- 解绑：`解绑设备`
- 设置默认设备（管理员）：`设置默认设备 {"device_id":"...","device_fp":"..."}`

### 9. 社区与自动化

- 社区签到：`签到`
- 全部重签（管理员）：`全部重签`
- 推送总开关：`开启推送`、`关闭推送`
- 体力推送：`开启体力推送`、`设置体力阈值160`
- 自动签到：`开启自动签到`
- 清空公告红点：`清空公告红点`
- 自动清红：`开启自动清红`、`关闭自动清红`

### 10. 其他功能

- 绳网月报：`绳网月报`、`月历`、`札记`
- 活动日历（新增）：`日历`、`cal`
- 前瞻兑换码：`兑换码`
- 资源补全（管理员）：`下载全部资源`
- 帮助：`帮助`

## 资源与数据同步（对齐 ZZZ-Plugin）

### 游戏数据同步

```bash
python ZZZeroUID/tools/sync_game_data_from_zzz_plugin.py
```

用于同步角色/音擎/驱动盘/邦布/别名等数据。

### 插件素材全量同步

```bash
python ZZZeroUID/tools/sync_zzz_plugin_resources.py --source auto
```

- `--source auto`：优先本地 `ZZZ-Plugin` 仓库，不存在则从 GitHub 拉取。
- `--source local`：仅从本地仓库同步。
- `--source github`：仅从 GitHub 压缩包同步。

本地素材目录：`ZZZeroUID/utils/zzz_plugin_resources`

## 说明

- 当前版本已完成核心用户功能对齐，重点补齐：排行榜、挑战提醒、设备绑定、卡池历史、活动日历、伤害面板等能力。
- 底层实现保持 ZZZeroUID/gsuid_core 风格，不照搬 yunzai 架构。
- 部分功能依赖米哈游接口与公告源，遇到网络或风控时会出现失败提示。

## 致谢

- [听雨惊花](https://github.com/Nwflower/zzz-atlas) - 部分角色攻略来源
- [猫冬](https://bbs.mihoyo.com/ys/accountCenter/postList?id=74019947) - 部分角色攻略来源

## License

- [GPL-3.0 License](https://github.com/gakkiri/ZZZeroUID/blob/master/LICENSE)
