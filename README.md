# StarBot-plugins-querier
一个StarBot的查询插件，目前仅有查询b站用户是否为up上舰

## 安装插件
下载代码解压或者使用git克隆代码 到main.py 所在的文件夹中  
如果文件夹名称带 -main 请手动删除，确保文件夹名称为 StarBot_plugins_querier

## 启用插件
```
# 加载查询模块
config.set("CUSTOM_COMMANDS_PACKAGE","StarBot_plugins_querier")
# 为哪个up主上舰
config.set("ONBOARD_FOR_UP",)
```