# -*- coding: utf-8 -*-
import requests,time,os,re # requests作为我们的html客户端
from pyquery import PyQuery as Pq # pyquery来操作dom
# https://segmentfault.com/a/1190000002549756
# 文章详情页 http://www.0731gch.com/paixie/bianmi/18086.html
class Getshow(object):

    def __init__(self, url): # 参数为在vccoo上的id
        self.url = url
        self._dom = None # 弄个这个来缓存获取到的html内容，一个蜘蛛应该之访问一次

    @property
    def dom(self): # 获取html内容
        if not self._dom:
            document = requests.get(self.url)
            document.encoding = 'utf-8'
            self._dom = Pq(document.text)
        return self._dom
    # 标题
    @property
    def title(self): # 让方法可以通过s.title的方式访问 可以少打对括号
        return self.dom('.atr_bt h1').text() # 关于选择器可以参考css selector或者jquery selector, 它们在pyquery下几乎都可以使用
    # 内容
    @property
    def content(self):
        return self.dom('.art_content').html() # 直接获取html 胆子就是大 以后再来过滤

   # 暂时保存成文档
    def save(self):
        sDir='d:/test/'
        #图片地址
        img_dir = 'img'
        if os.path.exists(sDir)==False:
            os.mkdir(sDir)
        sName = sDir+str(int(time.time()))+'.txt'
        print('正在下载'+self.title+'文章')
        m = self.clearInput(self.title)+'\n'+self.clearInput(self.content)
        #批量替换旧内容中的图片的路径
        img_patt = re.compile('src=".*?/(\w+\.\w+)"')
        new_m = img_patt.sub(r'src="./%s/\1"'%img_dir,m)
        with open(sName,'wb') as file:
            file.write(new_m.encode())
        file.close()
        #真正下载图片
        img_patt = re.compile('src="(.*?)"')
        img_patt = img_patt.findall(m)
        i =0
        for img in img_patt:
            i+=1
            #图片名称
            img_name = os.path.join(img_dir,img.split('/')[-1])
             #获取图片资源
            if os.path.exists(sDir+img_dir)==False:
                os.mkdir(sDir+img_dir)
            #合并路径
            imgpath=os.path.join(sDir,img_name)
            f = open(imgpath, 'wb')
            f.write(requests.get(img, stream=True).content)
            f.close()

    def clearInput(self,txt):
        txt=txt.replace('长沙医博肛肠医院','瑞安九龙医院')
        txt=txt.replace('长沙','瑞安')
        txt=txt.replace('医博','九龙')
        txt=txt.replace('湖南','湖南')
        txt=txt.replace('YEBO','九龙')
        txt=txt.replace('0731-89917766','0577-65913333')
        txt=txt.replace('0731-82296120','0577-65913333')
        txt=txt.replace('800040095','2812882905')
        txt=txt.replace('YiBo','九龙')
        # 正则替换
        # text=re.sub('\[[0-9]*\]','',text)
        return txt


#栏目页 http://www.0731gch.com/paixie/bianmi/index_26_2.html
#getpages限制取几页
class Getlist(object):

    def __init__(self, zurl , getpages , page=1):
        self.zurl=zurl
        self.url = zurl+"%d.html" % (page)
        self.page = page
        self._dom = None
        self.getpages=getpages

    @property
    def dom(self):
        if not self._dom:
            document = requests.get(self.url)
            document.encoding = 'utf-8'
            self._dom = Pq(document.text)
            self._dom.make_links_absolute(base_url="http://www.0731gch.com/") # 相对链接变成绝对链接 爽
        return self._dom


    @property
    def urls(self):
        return [url.attr('href') for url in self.dom('.case_list dl dd h3 a').items()]

    @property
    def has_next_page(self): # 看看还有没有下一页，这个有必要
        return bool(self.dom('.fy ul .nextPage')) # 看看有木有下一页

    def next_page(self): # 把这个蜘蛛杀了， 产生一个新的蜘蛛 抓取下一页。 由于这个本来就是个动词，所以就不加@property了
        if self.has_next_page :
            self.__init__(zurl=self.zurl,getpages=self.getpages,page=self.page+1)
        else:
            return None

    def crawl(self): # 采集当前分页
        # sf_ids = [url for url in self.urls]
        con=len(self.urls)
        print('此页共要采集%s篇文章' %con)
        i=1
        for url in self.urls:
            print('此页第%d篇文章采集中' %i)
            Getshow(url).save()
            i+=1
            time.sleep(1)

    def crawl_all_pages(self):
        while True:
            print(u'正在抓取栏目:%s, 分页:%d ,共需抓 %d 页' % (self.zurl, self.page, self.getpages))
            self.crawl()
            if int(self.page) > int(self.getpages) or not self.has_next_page :
            # if not self.has_next_page :
                print('停止')
                break
            else:
                self.next_page()

# 测试

# s = Getshow('http://www.0731gch.com/paixie/bianmi/18070.html')
# print(s.title)
# print(s.content)


# s=Getlist('http://www.0731gch.com/paixie/bianmi/index_26_',2)
# for url in s.urls:
#      show =Getshow(url)
#      print(show.title+':'+url)



s=Getlist('http://www.0731gch.com/paixie/bianmi/index_26_',2,2)
# if not s.has_next_page:
#     print('没有下一页')
# else:
#     print('有下一页')
s.crawl_all_pages()