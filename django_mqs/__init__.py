import os,time,json,signal,threading
from multiprocessing import Pool,Lock,Manager
from concurrent.futures import ThreadPoolExecutor

def mq_init(base_url):
    file_path = os.path.join(base_url,'models.py')
    fp = open(file_path,'r',encoding='utf-8')
    if 'DB_django_task_mq' in fp.read():
        print('Please don`t repeat this,or you can delete "class DB_django_task_mq" from "models.py",then do this again!')
        fp.close()
    else:
        fp = open(file_path,'a+')
        fp.writelines(['\n'*4,'class DB_django_task_mq(models.Model):','\n    topic = models.CharField(max_length=100,null=True,blank=True,default="")',
                       '\n    message = models.TextField(default="{}")','\n    status = models.BooleanField(default=True)','\n    def __str__(self):','\n        return self.topic'])
        fp.close()
        file_path = os.path.join(base_url,'admin.py')
        fp = open(file_path,'a+')
        fp.writelines(['\n'*4,'admin.site.register(DB_django_task_mq)'])
        fp.close()
        time.sleep(0.5)

def mq_producer(DB_django_task_mq,topic,message):
    mq = DB_django_task_mq.objects.create(topic=topic,message=json.dumps(message))
    return mq.id

def mq_consumer(DB_django_task_mq,fun,topic,lock):
    pid = os.getpid()
    try:
        while True:
            time.sleep(1)
            lock.acquire()
            mq = DB_django_task_mq.objects.filter(status=True,topic=topic).first()
            if mq:
                print(f'\n[BEGIN-{pid}]:',mq.id,mq.topic)
                mq.status = False
                mq.save()
                lock.release()
                try:
                    fun(mq)
                except:
                    try:
                        fun(mq.message)
                    except Exception as e:
                        print(f'[ERROR-{pid}]:',e)
                finally:
                    mq.delete()
                    print(f'[OVER-{pid}]')
            else:
                lock.release()
    except KeyboardInterrupt:
        os.kill(pid,signal.SIGKILL)

def mq_consumer_process(DB_django_task_mq,fun_topics=[{'fun':None,'topic':None}],worker=2):
    manager = Manager()
    lock = manager.Lock()
    tasks = []
    for f in fun_topics:
        if f.get('fun',None) and f.get('topic',None):
            tasks += [(DB_django_task_mq,f['fun'],f['topic'],lock) for _ in range(worker//len(fun_topics) or 1)]
    with Pool(processes=worker) as pool:
        pool.starmap(mq_consumer, tasks)

def mq_consumer_thread(DB_django_task_mq,fun_topics=[{'fun':None,'topic':None}],worker=2):
    lock = threading.Lock()
    tasks = []
    for f in fun_topics:
        if f.get('fun',None) and f.get('topic',None):
            tasks += [(DB_django_task_mq,f['fun'],f['topic'],lock) for _ in range(worker//len(fun_topics) or 1)]
    with ThreadPoolExecutor(max_workers=worker) as pool:
        pool.starmap(mq_consumer, tasks)
