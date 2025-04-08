# 文档采集工具

这是一个用于采集网页文档的 Python 脚本。它可以从 sitemap.xml 文件中读取链接，并将网页内容转换为 Markdown 格式保存。

## 功能特点

- 支持从 sitemap.xml 文件读取链接
- 可配置 URL 关键词过滤
- 自动重试失败的链接
- 支持断点续传
- 自动使用网站域名作为输出目录
- 保存原始链接信息
- 支持自定义配置参数

## 安装要求

- Python 3.6+
- Google Chrome 浏览器
- ChromeDriver（与 Chrome 版本匹配）

### 依赖包

```
selenium
beautifulsoup4
html2text
```

## 安装步骤

1. 克隆或下载此仓库
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```
3. 下载与你的 Chrome 浏览器版本匹配的 ChromeDriver
4. 将 ChromeDriver 放在项目根目录下

## 配置文件

在项目根目录创建 `scraper_config.json` 文件：

```json
{
    "base_url": "",           // 可选，基础 URL
    "url_keyword": "",        // 可选，URL 关键词过滤
    "output_dir": "",         // 可选，输出目录（为空时使用网站域名）
    "max_retries": 3,         // 最大重试次数
    "initial_delay": 5,       // 初始等待时间（秒）
    "second_pass_retries": 5, // 二次重试次数
    "second_pass_delay": 10   // 二次重试等待时间（秒）
}
```

## 使用方法

1. 准备 sitemap.xml 文件：

   - 将网站的 sitemap.xml 文件放在项目根目录
   - 或者使用其他方式获取的 sitemap.xml 文件
2. 配置参数（可选）：

   - 修改 `scraper_config.json` 文件
   - 设置 URL 关键词过滤
   - 设置输出目录名称
3. 运行脚本：

   ```bash
   python docs_scraper.py
   ```

## 输出结果

- 采集的内容将保存在以网站域名命名的目录中（如果未指定输出目录）
- 每个页面都会转换为 Markdown 格式
- 文件名基于 URL 路径生成
- 原始 URL 会保存在文件末尾

## 断点续传

- 脚本会自动保存采集进度
- 意外中断后可以从上次的位置继续
- 已完成的页面不会重复采集
- 失败的链接会在所有页面采集完成后重试

## 注意事项

1. 确保 Chrome 浏览器已正确安装
2. ChromeDriver 版本必须与 Chrome 浏览器版本匹配
3. 如果遇到权限问题，请以管理员身份运行
4. 网络不稳定时，脚本会自动重试失败的链接

## 故障排除

如果遇到问题：

1. 检查 Chrome 浏览器是否正确安装
2. 确认 ChromeDriver 版本是否匹配
3. 检查 sitemap.xml 文件是否存在且格式正确
4. 查看错误信息并参考配置说明
