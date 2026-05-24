# 贡献指南

感谢您对ROS2虚拟无人机系统的兴趣！本文档将指导您如何做出贡献。

## 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们作为贡献者和维护者承诺：

- 对所有年龄、体型、残障、种族、民族、性别、性别认同和表达、经验水平、国籍、外表、种族或宗教的人使用欢迎和包容的语言
- 接受建设性批评
- 关注最有利于社区的情况
- 尊重持不同意见的人

### 不可接受的行为

包括：
- 使用性暗示语言或意象
- 人身攻击或贬低性评论
- 骚扰或欺凌
- 公开或私下骚扰
- 未经许可发布他人私人信息
- 其他可能被合理认为在专业环境中不适当的行为

### 我们的责任

项目维护者负责阐明可接受行为的标准，并应对任何不可接受行为采取适当和公平的纠正措施。

项目维护者有权和责任删除、编辑或拒绝与本行为准则不符的评论、提交、代码、Wiki编辑、问题和其他贡献。

## 如何贡献

### 报告问题

在创建问题报告之前，请检查问题列表，因为您可能会发现问题已经报告过。如果您找到一个闭合的问题与您的问题几乎相同，请打开一个新问题并链接到旧问题。

在创建错误报告时，请包括尽可能多的详细信息：

#### 有效的问题报告应包含

- **简洁的总结** - 使用描述性标题
- **环境信息**
  - OS和版本
  - ROS2版本 (`echo $ROS_DISTRO`)
  - PX4版本 (`~/development/PX4-Autopilot -v`)
  - Python版本 (`python3 --version`)
  
- **具体示例重现问题**
  - 提供具体步骤来重现问题
  - 提供您在步骤中使用的特定示例
  - 描述您在执行步骤后看到的行为
  - 解释您期望的行为以及为什么
  
- **日志和错误信息**
  - 包含完整的错误跟踪或日志
  - 运行诊断: `python3 test_system.py`
  
- **附加上下文**
  - 尽可能提供更多信息
  - 屏幕截图或视频（如果适用）

### 提交改进建议

改进建议通过GitHub问题跟踪。创建问题并提供以下信息：

- **清晰的描述** - 您想要的改进是什么
- **逐步的示例** - 如何使用改进
- **可能的实现** - 如果您有想法的话

### Pull Request流程

1. **Fork** 这个仓库
2. **创建您的功能分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **打开一个Pull Request**

#### Pull Request检查清单

在提交PR前，请确保：

- [ ] 代码遵循项目的代码风格
- [ ] 更新了相关文档
- [ ] 添加或更新了测试
- [ ] 本地测试通过 (`python3 -m pytest`)
- [ ] 运行诊断通过 (`python3 test_system.py`)
- [ ] PR描述清晰明确

## 开发设置

### 本地开发环境

```bash
# 克隆您的fork
git clone https://github.com/your-username/FlyControl.git
cd FlyControl/ros2_fc

# 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip3 install -r requirements.txt

# 编译项目
colcon build --symlink-install

# 运行测试
python3 test_system.py
python3 -m pytest
```

### 代码风格

我们遵循以下代码风格指南：

#### Python
- PEP 8 - [https://pep8.org/](https://pep8.org/)
- 使用4个空格进行缩进
- 最大行长: 100字符
- 使用类型提示（建议）

```python
def process_data(data: List[float]) -> Dict[str, float]:
    """处理数据的文档字符串."""
    result: Dict[str, float] = {}
    for value in data:
        result['mean'] = sum(data) / len(data)
    return result
```

#### XML (launch文件)
- 2个空格缩进
- 属性按字母顺序排序

```xml
<node
  name="my_node"
  output="screen"
  package="my_package"
  type="my_type" />
```

#### Markdown
- 使用标准Markdown语法
- 最大行长: 100字符（代码块除外）
- 内部链接使用相对路径

### 测试

编写和运行测试对维护代码质量至关重要。

```bash
# 运行所有测试
python3 -m pytest

# 运行特定的测试
python3 -m pytest test/test_offboard.py

# 运行测试并显示覆盖率
python3 -m pytest --cov=drone_control test/
```

## 文档

### 更新文档

- 主文档: `README_MAIN.md`
- 用户指南: `USER_GUIDE.md`
- 开发者指南: `DEVELOPER_GUIDE.md`
- 快速参考: `QUICK_START.md`
- 安装指南: `INSTALL.md`

### 文档风格

- 使用清晰、简洁的语言
- 包含代码示例
- 包含相关截图或图表（如果有帮助）
- 保持与现有文档的一致性

## Commit消息

### Commit消息格式

使用以下格式的commit消息：

```
<type>: <subject>

<body>

<footer>
```

### 类型

- **feat**: 新功能
- **fix**: 错误修复
- **docs**: 文档更新
- **style**: 代码风格变更（不改变功能）
- **refactor**: 代码重构
- **test**: 添加或更新测试
- **chore**: 其他杂项更改

### 示例

```
feat: add circle trajectory support

Add support for circular trajectory planning with configurable radius and angular velocity.

- Implements CircleTrajectory class
- Adds test cases for circle trajectory
- Updates documentation

Fixes #123
```

## 发布流程

### 版本号

我们使用语义化版本号 (MAJOR.MINOR.PATCH)：

- **MAJOR**: 不兼容的API变更
- **MINOR**: 添加向后兼容的功能
- **PATCH**: 向后兼容的错误修复

### 发布步骤

1. 更新版本号 (`setup.py`, `package.xml`)
2. 更新 `CHANGELOG.md`
3. 提交变更
4. 创建tag: `git tag v0.1.0`
5. 推送tag: `git push origin v0.1.0`

## 额外资源

### 有用的链接
- [ROS2开发者指南](https://docs.ros.org/en/humble/How-To-Guides/Development-setup.html)
- [PX4开发者指南](https://docs.px4.io/main/en/development/development.html)
- [GitHub文档](https://docs.github.com/)

### 常见任务

#### 如何添加新功能？

1. 创建问题讨论功能
2. Fork项目
3. 创建功能分支
4. 实现功能并添加测试
5. 更新文档
6. 提交PR

#### 如何报告安全漏洞？

**不要** 公开发布安全漏洞。请通过邮件报告给 ywt@todo.todo

#### 如何变成维护者？

如果您的贡献一致被接受，我们可能会邀请您成为维护者。

## 社区支持

- 📧 邮件: ywt@todo.todo
- 💬 问题讨论: [GitHub Issues](https://github.com/your-repo/issues)
- 💡 功能建议: [GitHub Discussions](https://github.com/your-repo/discussions)

## 感谢

非常感谢您对项目的贡献！无论您做出什么贡献 - 无论是代码、文档、bug报告还是功能建议 - 我们都非常感谢！

---

**有问题？** 随时开启问题或联系维护者！

**最后更新**: 2026-05-22
