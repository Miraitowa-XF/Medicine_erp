#### 初始化数据库
1. 生成迁移文件
   ```
   python manage.py makemigrations
   ```
2. 应用迁移到数据库
   ```
   python manage.py migrate
   ```
   
#### 创建超级管理员
```
python manage.py createsuperuser
```
> (可选)检查配置有没有明显的语法错误或逻辑漏洞的命令
> `python manage.py check`


#### 完成供应商多值属性的完善
(如果你在2025年12月26日下午14:30之前进行过初始化数据库，则还需要进行如下的操作)

因为涉及到修改了表结构（删了一个字段，加了一张表），必须处理数据库的迁移：
请在命令行中分别进行如下的两行命令执行：
```
python manage.py makemigrations
python manage.py migrate
```


#### 修改支持虚拟局域网访问，运行时需要执行如下的命令：
```
python manage.py runserver 0.0.0.0:8000
```
> 0.0.0.0 监听所有网卡接口

