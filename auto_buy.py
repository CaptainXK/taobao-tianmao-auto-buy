#python3.6.5
#coding:utf-8

'''
@time:2019-02-16 16:50
@author: 李铭

程序利用自动测试工具模拟用户下单操作，完成商品的抢购
仅作为学习过程中的实践，无商业用途
'''

from selenium import webdriver
import datetime
import time
import json
import re
import threading
import signal

force_quit = False

def sig_handle(signum, frame):
    print("Got signal")
    force_quit = True

# good class
class Goods:
    url=""
    mall_type=0
    start_time=""

    def __init__(self, _url, _mall_type_str, _start_time):
        self.url = _url
        self.mall_type = 1 if _mall_type_str=="taobao" else 2
        self.start_time = _start_time
    
    def __show__(self):
        print("---url: " + self.url)
        print("---mall type: %d"%(self.mall_type) )
        print("---start time: " + self.start_time)

# worker load class
class Worker_load (threading.Thread):
    goods = None

    def __init__(self, threadID, name, counter, _goods):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter 
        self.goods = _goods

    def run(self):
        self.main_mission(self.goods)
    
        # main mission
    def main_mission(self, _goods):
        #create browser object and disable error log output
        options= webdriver.ChromeOptions()
        options.add_argument('--log-level=3')
        driver = webdriver.Chrome(chrome_options=options)
        # driver.maximize_window()

        print("start a purchase thread, start to go at %s"%(_goods.start_time))

        # login to e-store
        self.login(_goods.url, _goods.mall_type, driver)

        # do purchasing
        self.buy(_goods.start_time, _goods.mall_type, driver)

    # login func
    def login(self, url,mall,driver):
        '''
        login def

        url : link to good
        mall ： e-store type, 1 for taobao, 2 for tmall
        '''
        driver.get(url)
        print("Access: " + url)
        driver.implicitly_wait(10)
        time.sleep(2)

        #淘宝和天猫的登陆链接文字不同
        if mall=='1':
            #找到并点击淘宝的登陆按钮
            driver.find_element_by_link_text("亲，请登录").click()
        else:
            #找到并点击天猫的登陆按钮
            driver.find_element_by_link_text("请登录").click()

        print("please login in in 30 seconds:")
        _counter = 30
        time.sleep(30)

    # purchase func
    def buy(self, buy_time,mall,driver):
        '''
        purchase def

        buy_time:start time
        mall:e-store type

        css_selector to find target button
        '''
        if mall=='1':
            #"立即购买"的css_selector
            btn_buy='#J_juValid > div.tb-btn-buy > a'
            #"立即下单"的css_selector
            btn_order='#submitOrder_1 > div.wrapper > a'
        else:
            # btn_buy='#J_LinkBuy'
            btn_buy='#J_LinkBasket'
            btn_order='#submitOrder_1 > div > a'

        while True and not force_quit:
            #现在时间大于预设时间则开售抢购
            if datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')>buy_time:
                try:
                    print("try add to shopping cart...")
                    #找到“立即购买”，点击
                    if driver.find_element_by_css_selector(btn_buy):
                        driver.find_element_by_css_selector(btn_buy).click()
                        break
                    time.sleep(0.1)
                except:
                    print("add error...")
                    time.sleep(0.3)

        while True and not force_quit:
            try:
                #找到“立即下单”，点击，
                if driver.find_element_by_css_selector(btn_order):
                    driver.find_element_by_css_selector(btn_order).click()
                    #下单成功，跳转至支付页面
                    print("operation done...")
                    break
            except:
                time.sleep(0.5)
    

# json parser
def json_parser(_json_file):
    global_start_time = ""
    goods_list = []
    with open(_json_file, 'r') as jsf:
        json_to_dict = json.load(jsf)

        # get global start time
        global_start_time = json_to_dict['start_time']

        #traverse json dict
        for key in json_to_dict:
            if isinstance(json_to_dict[key], dict):
                json_parse_one(json_to_dict[key], goods_list, global_start_time)
    
    return goods_list

# parse one item in json file
def json_parse_one(_cur_dict, _goods_list, _global_start_time):
    _ret_url = ""
    _ret_estore_type = 0
    _ret_start_time = ""

    # parse url
    _ret_url = _cur_dict['url']

    # parse web store according to url
    matchObj = re.match('taobao', _ret_url)
    if matchObj:
        _ret_estore_type = 1
    
    matchObj = re.match('tmall', _ret_url)
    if matchObj:
        _ret_estore_type = 2

    # parse start time if needed

    if 'start_time' in _cur_dict:
        _ret_start_time = _cur_dict['start_time']
    else:
        _ret_start_time = _global_start_time

    # instantiate a goods obj
    goods_item = Goods(_ret_url, _ret_estore_type, _ret_start_time)

    _goods_list.append(goods_item)

         
if __name__ == "__main__":
    json_file_path = "goods.json"
    goods_list=[]
    workers_pool=[]

    goods_list = json_parser(json_file_path)

    signal.signal(signal.SIGINT, sig_handle)
    signal.signal(signal.SIGTERM, sig_handle)

    _counter = 0
    for goods in goods_list:
        print("[item#%d]"%(_counter))
        goods.__show__()
        _counter += 1
        worker_item = Worker_load(_counter, "item" + str(_counter), _counter, goods)
        workers_pool.append(worker_item)

    for worker in workers_pool:
        worker.start()

    for worker in workers_pool:
        worker.join()

        
    