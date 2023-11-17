# django_mqs
支持django的多线程，多进程MQ组件
【申明】
本工具初始版本来自【测试开发干货】我去热饭的原创，经过授权后同意开源，附上链接
https://mp.weixin.qq.com/s/HDxmA69R4KJhUEAF4YQ4Mw

【背景】
测开平台开发中，往往需要使用MQ中间件来异步处理同步严重的自动化代码，而市面上的MQ要么过于复杂，要么部署困难，故自研一个继承在django上的轻量级MQ工具。

【原理】
原理很简单，借助django的orm技术，在数据库中新建持久消息表，结合算法成为先进先出的栈。

【优点】
理解和使用简单，不需要复杂的安装和各种依赖，支持各种系统，轻量级，适用于中小型消息队列需求。

【升级】
支持了多线程，多进程启动，横纵向扩展性都更好，管理和部署更轻量级。

【食用】
首先要下载：pip3 install django-mqs

然后先打开你的django项目目录，找到你的app目录，在app目录内，新建一个任意名称的.py文件。

然后在这个文件内直接粘贴复制下面代码，之后独立用python3来运行该文件

import os

from django_mqs import mq_init 

mq_init(os.path.dirname(os.path.abspath(__file__)))

这步的目的是初始化消息内容表，它会自动重写你的models.py和admin.py。

然后你要手动的去控制台执行数据库同步的俩个命令：

python3 manage.py makemigrations

python3 manage.py migrate

到此，表就弄好了，你可以在admin后台看到了。

注意，此初始化函数只能执行一次，所以之后请清空文件内容，你不删除这句它就会提醒你重复执行，虽然也没啥报错等后果。


（二：设置生产者）

在你想要新建生产者的函数内，导入并调用mq_producer函数即可。具体可以参考示例：

from django_mqs import mq_producer 

mq_producer(DB_django_task_mq,topic='',message={}) 

注意，第一个DB_django_task_mq为上一步中自动创建的消息表本体，你需要自行导入，如from MyApp.models import * 。不过，在一般django的views.py中，你肯定早就一开始就导入了所有表了...

topic为管道/标识符/过滤符/分类名 等等意思。

message为字典类型的数据存储，你可以任意往里面写内容。

之后，当这个函数被调用，就会在消息表中新增一条消息记录。

（三：新增消费者）

消费者本质上是一个进程，这个进程是在执行一个文件，这个文件在监控数据库消息表，并且按照先进先出规定来消费消息。

还是在一开始新建的这个文件，导入并调用 mq_consumer_process 或 mq_consumer_thread 函数。

import os,sys,django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '%s.settings'%'') # 引号中请输入您的setting父级目录名

os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

django.setup()

from MyApp.models import DB_django_task_mq

from django_task_mq import mq_consumer_process,mq_consumer_thread 

from views import run_task,debug_task 


if __name__ == '__main__':

    mq_consumer_process(DB_django_task_mq,fun_topics=[{'fun':debug_task,'topic':'debug'},{'fun':run_task,'topic':'run'}],worker=2)
    
    # mq_consumer_thread(DB_django_task_mq,fun_topics=[{'fun':debug_task,'topic':'debug'},{'fun':run_task,'topic':'run'}],worker=2) 


mq_consumer_process 入参说明： 
DB_django_task_mq即第一步初始化的MQ表；
fun_topics 是一个列表嵌套字典，字典也是fun是你的消费者函数，topic是对应的消费标识，可以存在多个消费者方法；
worker 是代表启动多少个线程或进程消费，最低2个，不推荐设置超过CPU核数；
