# Skills

## 天气查询

当用户询问天气相关信息时，使用以下命令查询天气：

```command
curl -s "https://wttr.in/北京?format=%t%l%w"
```

**说明**：
- 命令使用 wttr.in 服务查询天气
- `%t` 表示温度，`%l` 表示地点，`%w` 表示天气状况图标
- 返回格式：温度 + 地点 + 天气图标

**示例**：
- 用户："北京今天天气怎么样？"
- AI 执行：`curl -s "https://wttr.in/北京？format=%t%l%w"`
- 返回：`-5°C 北京 ⛅`

**其他城市**：
- 上海：`curl -s "https://wttr.in/上海？format=%t%l%w"`
- 深圳：`curl -s "https://wttr.in/深圳？format=%t%l%w"`
- 广州：`curl -s "https://wttr.in/广州？format=%t%l%w"`

**注意事项**：
1. 城市名使用中文或英文均可
2. 如果查询失败，可以尝试只用城市名：`curl -s "https://wttr.in/北京"`
3. 返回结果可能包含多行，请综合判断天气情况
