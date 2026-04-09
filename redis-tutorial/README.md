# Redis 完整学习教程 🚀

> 以 **电商系统** 为贯穿项目，从零到精通 Redis 实战

---

## 📖 为什么要学 Redis？

### Redis 是什么？

Redis（Remote Dictionary Server）是一个开源的、基于内存的键值数据库。它速度快、功能丰富，是目前互联网行业使用最广泛的 NoSQL 数据库之一。

### 为什么要学？

1. **几乎必修** —— 后端开发岗位面试必考，实际项目中 90% 以上的互联网公司都在用
2. **性能利器** —— 单机 QPS 可达 10 万+，轻松应对高并发场景
3. **功能强大** —— 不只是缓存，还能做消息队列、分布式锁、排行榜、地理位置等
4. **生态完善** —— 主流语言都有成熟客户端，.NET 生态有 StackExchange.Redis、CSRedis
5. **面试加分** —— 缓存穿透/击穿/雪崩、集群方案、持久化策略，都是高频面试题

### Redis 在电商系统中的角色

```
┌─────────────────────────────────────────────────┐
│                  电商系统架构                      │
│                                                   │
│  用户端 → Nginx → API网关 → .NET服务 → MySQL     │
│                               ↕                   │
│                           Redis 缓存层            │
│                                                   │
│  Redis 负责：                                      │
│  ✅ 商品信息缓存（减少数据库压力）                   │
│  ✅ 购物车数据（Hash 结构，快速读写）                │
│  ✅ 秒杀库存扣减（原子操作，防超卖）                  │
│  ✅ 销量排行榜（ZSet 实时排名）                     │
│  ✅ 分布式锁（防止重复下单）                        │
│  ✅ 用户会话（Session 共享）                        │
│  ✅ 验证码存储（带过期时间）                        │
│  ✅ 消息队列（异步处理订单）                        │
└─────────────────────────────────────────────────┘
```

---

## 🗺️ 学习路线图

```
Week 1: 基础入门
├── Day 1-2: 安装部署 + 配置详解 ────→ 01-redis-setup.md
├── Day 3-4: 5大基础数据类型 ────────→ 02-data-types.md
└── Day 5-7: 高级数据结构 ──────────→ 03-advanced-structures.md

Week 2: 进阶实战
├── Day 1-2: 缓存模式与策略 ────────→ 04-cache-patterns.md
├── Day 3-5: 实战应用场景 ──────────→ 05-redis-in-practice.md
└── Day 6-7: 性能优化与架构 ────────→ 06-performance.md

Week 3: .NET 集成与项目实战
└── Day 1-7: C# 集成 + 电商项目实战 → 07-dotnet-redis.md
```

---

## 📚 教程目录

| 章节 | 内容 | 关键知识点 |
|------|------|-----------|
| [01-redis-setup](./01-redis-setup.md) | 安装部署与配置 | Linux/Docker/Windows 安装、配置文件详解、连接测试 |
| [02-data-types](./02-data-types.md) | 5大基础数据类型 | String/Hash/List/Set/ZSet 命令 + 电商场景 |
| [03-advanced-structures](./03-advanced-structures.md) | 高级数据结构 | Bitmap/HyperLogLog/GEO/Stream |
| [04-cache-patterns](./04-cache-patterns.md) | 缓存模式与策略 | Cache Aside、双写、缓存预热、缓存问题解决 |
| [05-redis-in-practice](./05-redis-in-practice.md) | 实战应用场景 | 分布式锁、排行榜、秒杀、消息队列、Session |
| [06-performance](./06-performance.md) | 性能优化与架构 | 持久化、主从、哨兵、集群、大Key热Key |
| [07-dotnet-redis](./07-dotnet-redis.md) | .NET 集成 Redis | StackExchange.Redis、CSRedis、电商API集成 |

---

## 🎯 电商贯穿项目说明

本教程使用一套 **电商系统** 作为贯穿项目，涵盖：

- **商品模块**：商品缓存、分类缓存、搜索热词
- **用户模块**：登录验证、Session 共享、用户画像标签
- **购物车模块**：添加/修改/删除购物车商品
- **订单模块**：秒杀库存、防超卖、异步下单
- **营销模块**：签到、投票、排行榜、红包雨

### 技术栈

- 后端：ASP.NET Core Web API
- 数据库：MySQL + Redis
- ORM：Entity Framework Core / Dapper
- Redis 客户端：StackExchange.Redis / CSRedis

---

## 💡 学习建议

1. **边学边练** —— 每个命令都手动敲一遍，不要只看
2. **先跑通再深入** —— 先把基础命令会用，再理解底层原理
3. **结合项目思考** —— 想想电商系统中哪里能用 Redis
4. **关注面试考点** —— 每章末尾有面试题，重点掌握
5. **踩坑记录** —— 把实际遇到的问题记录下来

---

## 📋 前置知识

- 基本的 Linux 命令行操作
- 了解 TCP/IP 网络基础
- C#/.NET 基础（用于第7章）
- 了解关系型数据库（MySQL/SQL Server）

---

## 🔗 参考资源

- [Redis 官方文档](https://redis.io/documentation)
- [Redis 命令参考](https://redis.io/commands)
- [StackExchange.Redis 文档](https://stackexchange.github.io/StackExchange.Redis/)
- [CSRedis 文档](https://github.com/2881099/csredis)

---

> 💬 Redis 不难，但用好需要经验。跟着教程一步步来，你一定能掌握！
