#### （可选）创建虚拟环境
```
# 创建虚拟环境 (可选，但在专业开发中推荐)
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate
```

#### 一键配置项目所有依赖项
```
pip install -r requirements.txt
```


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

##### 其他人如何访问
这里以我作为主机，我使用 Radmin 的主机虚拟IP为：26.27.68.168
则虚拟局域网内的成员在浏览器中输入：http://26.27.68.168:8000/admin/


#### 员工权限分组
首先要运行自动化脚本
```
python manage.py init_permissions
```
它会创建5中不同的员工组，它们分别拥有不同的权限


#### 已实现并发控制访问
并发测试脚本：根目录下 `test_concurrency.py`
执行测试脚本：
```
python test_concurrency.py
```