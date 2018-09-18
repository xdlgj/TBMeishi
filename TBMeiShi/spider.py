from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

#创建浏览器驱动
options = Options()
options.add_argument('-headless')
browser = webdriver.Firefox(firefox_options = options)
wait = WebDriverWait(browser,10)
def search():
	print('正在搜索')
	try:
		browser.get("https://www.taobao.com/")
		'''在抛出TimeoutException异常之前将等待10秒或者在10秒内发现了查找的元素。
		WebDriverWait 默认情况下会每500毫秒调用一次ExpectedCondition直到结果成功返回。 
		ExpectedCondition成功的返回结果是一个布尔类型的true或是不为null的返回值。'''
		input = wait.until(
			EC.presence_of_element_located((By.CSS_SELECTOR, "#q"))
	    )
		submit = wait.until(
			EC.element_to_be_clickable((By.CSS_SELECTOR,".btn-search"))
		)
		input.send_keys(KEY_WORD)
		submit.click()
		total = wait.until(
			EC.presence_of_element_located((By.CSS_SELECTOR,".total"))
		)
		get_products()
		return total.text
	except TimeoutException:
		return search()

def next_page(page_number):
	print('正在翻页',page_number)
	try:
		input = wait.until(
			EC.presence_of_element_located((By.CSS_SELECTOR, "input.input:nth-child(2)"))
		)
		submit = wait.until(
			EC.element_to_be_clickable((By.CSS_SELECTOR,"span.btn:nth-child(4)"))
		)
		input.clear()
		input.send_keys(page_number)
		submit.click()
		wait.until(
			EC.text_to_be_present_in_element((By.CSS_SELECTOR,"span.num"),str(page_number))
		)
		get_products()
	except TimeoutException:
		next_page(page_number)

def get_products():
	wait.until(
		EC.presence_of_element_located((By.CSS_SELECTOR,"#mainsrp-itemlist .items .item"))
	)
	html = browser.page_source
	doc = pq(html)
	items = doc("#mainsrp-itemlist .items .item").items()
	for item in items:
		product = {
			'image':item.find('.pic .img').attr('src'),
			'price':item.find('.price').text(),
			'deal':item.find('.deal-cnt').text()[:-3],
			'title':item.find('.title').text(),
			'shop':item.find('.shop').text(),
			'location':item.find('.location').text()
		}
		print(product)
		save_to_mongo(product)

def save_to_mongo(result):
	try:
		if db[MONGO_TABLE].insert(result):
			print("存储到MONGO成功",result)
	except Exception:
		print('存储到MONGO失败',result)


def main():
	try:
		#共 100 页，转换为100
		total = int(search().split(" ")[1])
		for i in range(2,total+1):
			next_page(i)
	except Exception:
		print('出错了')
	finally:
		browser.close()
if __name__ == "__main__":
	main()

