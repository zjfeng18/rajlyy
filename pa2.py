# -*- coding: utf-8 -*-
import requests,time,os,re # requests作为我们的html客户端
import jieba #分词并取关键词
import jieba.analyse
from pyquery import PyQuery as Pq # pyquery来操作dom
from tools.mysql import Mysql


class Getshow(object):

    def __init__(self, url): # 参数为在id
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
        return self.clearInput(self.dom('title').text()) # 关于选择器可以参考css selector或者jquery selector, 它们在pyquery下几乎都可以使用
    # 内容
    @property
    def content(self):
        return self.clearInput(self.dom('.nr').html()) # 直接获取html 胆子就是大 以后再来过滤


    def mysave(self,tocatid):
        self.database=Mysql(host="121.199.48.196",  user="root", pwd="rajltool321123", db="m_wxhs120_com")
        self.tocatid=tocatid
        # self.sDir = "d:/uploadfile/"#图片本地目录
        # self.sDir = "/mnt/xvdb1/virtualhost/vmO2xqlA/uploadfile/"#图片本地目录
        # self.picurl = "http://imgs.najiaoluo.com/"#远程图片域名
        # if os.path.exists(self.sDir)==False:
        #     os.mkdir(sDir)
        #     os.chmod(sDir,0o777) #其实makedirs默认就是777权限，不知为什么不可以
        # sName = sDir+str(int(time.time()))+'.txt'
        print('正在采集--'+self.title+'--文章')



        title = self.title.encode('gbk','ignore').decode('gbk')
        if (title.strip()==''):
            print("标题,不采集！")
            return
        isexist1=""
        try:
            sql="select id from v9_news where title='%s' and catid='%s' order by title desc" % (title,self.tocatid)
            # print(sql)
            isexist1 = self.database.ExecQuery(sql)
        except Exception as e:
            print("查询信息出错，错误信息：%s" % (e))
            pass
        if isexist1:
            print(title+'-----> 有重复不提交！')
        else:#无相关记录时提交数据
             # pass
             self.addnews()

   # 文章入库
    def addnews(self):
       #批量替换旧内容中的图片的路径

        title = self.title.encode('gbk','ignore').decode('gbk')
        # content=(self.content) #这里对内容进行转义,提交变量时不用加'，因为后面转义过后会自动加引号
        content=self.database.conn.escape(self.content.encode('gbk','ignore').decode('gbk')) #这里对内容进行转义,提交变量时不用加'，因为后面转义过后会自动加引号
        catid=self.tocatid #保存到的栏目
        # weixinid=str(self.wxid)
        ndir=time.strftime("%Y/%m%d/")
        # nthumb="http://img03.sogoucdn.com/net/a/04/link?appid=100520034&url="+self.thumb #这里对大图片进行缩放到512宽 id改100520034为300 100520031为121
        # thumb=self.getimg(nthumb,self.random_str(6)+".jpg",self.sDir+"thumb/"+ndir,self.picurl+"thumb/"+ndir) #下载图片
        thumb=""
        typeid=0
        tags=jieba.analyse.extract_tags(title, 6)
        keywords=(",".join(tags))
        description=Pq(self.content).text()[0:180].encode('gbk','ignore').decode('gbk')
        url=''
        listorder=0
        status=99
        username='admin'
        inputtime=updatetime=int(time.time())
        insertbooksql ="insert into v9_news (title,catid,thumb,typeid,keywords,description,url,listorder,status,username,inputtime,updatetime) VALUES ( '{title}',{catid}, '{thumb}',{typeid}, '{keywords}', '{description}', '{url}',{listorder},{status}, '{username}', {inputtime}, {updatetime})"
        insert1 = insertbooksql.format(title=title, catid=catid,thumb=thumb, typeid=typeid, keywords=keywords, description=description,url=url,listorder=listorder,status=status,username=username,inputtime=inputtime,updatetime=updatetime)
        # print(insert1)
        try:#这是用到了事务处理
            self.database.cur.execute(insert1)
            lastid=self.database.cur.lastrowid
            paginationtype = 2
            groupids_view = ""
            maxcharperpage = 0
            template = ""
            insertbooksql ="insert into v9_news_data (id,content,paginationtype,groupids_view,maxcharperpage,template) VALUES ({lastid}, {content}, {paginationtype},'{groupids_view}',{maxcharperpage},'{template}')"
            insert2 = insertbooksql.format(lastid=lastid, content=content, paginationtype=paginationtype,groupids_view=groupids_view,maxcharperpage=maxcharperpage,template=template)
            # print(insert2)
            self.database.cur.execute(insert2)
            #新增hits表这里modelid＝12 文章modelid＝1
            hitsid = "c-1-"+str(lastid)
            insertsql="INSERT INTO `v9_hits`(`hitsid`,`catid`,`updatetime`) VALUES ('{hitsid}',{catid},{updatetime}) "
            insert3 = insertsql.format(hitsid=hitsid, catid=catid,updatetime=updatetime)
            # print(insert3)
            self.database.cur.execute(insert3)
            sql="select url from v9_category where catid="+str(catid)+" order by catid desc"
            isurl = self.database.ExecQuery(sql)
            # print(isurl)
            # #更新文章主表url
            url =str(isurl[0][0])+str(lastid)+".html"
            # # print(url)
            insertsql="update  `v9_news` set url='{url}' where id = {lastid} order by id desc"
            insert4 = insertsql.format(url=url, lastid=lastid)
            # print(insert4)
            self.database.cur.execute(insert4)

            # database.cur.close()
            self.database.conn.commit()
            print('文章%s入库成功！' % title)
        except Exception as e:
            print("文章%s数据库保存出错，错误信息：%s" % (title,e) )
            # database.conn.close()
            self.database.conn.rollback()
        # with open(sName,'wb') as file:
        #     file.write(new_m.encode())
        # file.close()

    def clearInput(self,txt):
        txt=txt.replace('白求恩医学基金定点：','')
        txt=txt.replace('连续10年荣获国家A级医院：','')
        txt=txt.replace('被评为国家示范妇科科研基地、国家妇科疾病重点诊疗基地，更是连续10年被评为&quot;A级妇科医院','')
        txt=txt.replace('丽水市囿山路568号(民政局旁)','无锡市锡山区东亭二泉东路195号')
        txt=txt.replace('丽水慈爱医院','无锡华山医院')
        txt=txt.replace('丽水','无锡')
        txt=txt.replace('慈爱','华山')
        txt=txt.replace('湖南','湖南')

        txt=txt.replace('0578-2292111','0510-88200585')
        txt=txt.replace('05782292111','051088200585')
        txt=txt.replace('0578-23292111','0510-88200585')
        txt=txt.replace('057823292111','051088200585')

        txt=txt.replace('972963352','493709817')
        txt=txt.replace('预约68元妇科检查套餐','预约0元妇科检查套餐')
        txt=txt.replace('专家','医生')
        txt=txt.replace('24年','')
        txt=txt.replace('非营利性','专业')
        txt=txt.replace('着名','专业')
        txt=txt.replace('白求恩医学基金无锡唯一定点医院','瑞安专业医院')

        txt=txt.replace('世界','')
        txt=txt.replace('白求恩医学基金无锡唯一定点医院','瑞安专业医院')
        txt=txt.replace('德国蓝氧净疗杀菌技术','华山妇科炎症治疗技术')
        txt=txt.replace('德国O3蓝氧净疗技术','华山妇科炎症治疗技术')
        txt=txt.replace('权威','专业')
        txt=txt.replace('汪爱云，女，1949年生，从事妇科临床、教学工作四十余年，并多次在国内着名的三甲医院研究深造。','从事妇科临床、教学工作二十余年')
        txt=txt.replace('临床经验超过40年','临床经验超过20年')
        txt=txt.replace('汪爱云主任','李医生')
        txt=txt.replace('王爱云主任','李医生')
        txt=txt.replace('汪爱云','李医生')
        txt=txt.replace('王爱云','李医生')
        txt=txt.replace('陈汉娇','李医生')
        txt=txt.replace('陈向宇','李医生')
        txt=txt.replace('楼美丽','李医生')
        txt=txt.replace('68元妇科六项套餐 关爱健康从体检开始','0元妇科检查套餐 关爱健康从检查开始')
        txt=txt.replace('68元六大项妇科检查','0元妇科检查套餐')
        txt=txt.replace('68元','0元')
        txt=txt.replace('熊国伟','曹医生')
        txt=txt.replace('董广胜','曹医生')
        txt=txt.replace('李涛','曹医生')
        txt=txt.replace('王益鑫','曹医生')
        txt=txt.replace('包皮环切术只需580元是吗','华山包皮环切术有优惠哦')
        txt=txt.replace('包皮环切术','华山包皮环切术')
        txt=txt.replace('副主任医师/博士后','')
        txt=txt.replace('男，泌尿外科副主任医师，医学博士后。在国内较早开展前列腺癌表观遗传、微小RNA的研究，现为上海泌尿男科学会青年会员。','')
        txt=txt.replace('副主任医师/博士后','')
        txt=txt.replace('上海同济医院泌尿外科','泌尿外科')
        txt=txt.replace('副教授','')
        txt=txt.replace('博士后','')
        txt=txt.replace('公立甲等','')
        txt=txt.replace('沪浙','')
        txt=txt.replace('著名','')
        txt=txt.replace('沪浙','')
        txt=txt.replace('沪浙','')
        txt=txt.replace('李医生、李医生、李医生主任','李医生')
        txt=txt.replace('白求恩基金会携手','')
        txt=txt.replace('白求恩基金会','')

        txt=txt.replace('40年','20年')
        txt=txt.replace('，被评为国家示范妇科科研基地、国家科学技术进步奖二等奖，不孕不育重点诊疗基地、全国十佳妇科医院，更是连续10年被评为国家A级妇科医院','')
        txt=txt.replace('阴茎背神经选择性切断术','华山早泄治疗术')
        txt=txt.replace('阴茎助勃器植入术','华山阳痿治疗术')
        txt=txt.replace('检查价格仅需30元','常规检查价格0元')
        txt=txt.replace('30元','0元')

        # 正则替换
        # text=re.sub('\[[0-9]*\]','',text)
       # txt=re.sub(r"<img[^>]+src\s*=(\s*)['\"]([^'\"]+)['\"][^>]*>","<a href=\"/swt\" rel=\"nofollow\"><img src=\"\\2\" /></a>",txt)
        txt=re.sub(r"<img[^>]+src\s*=(\s*)['\"]([^'\"]+)['\"][^>]*>","<a href=\"/swt\" rel=\"nofollow\"><img src=\"http://m.wxhs120.com/uploadfile/2015/1010/20151010085553617.gif\" /></a>",txt)
        return txt


#栏目页 http://www.0731gch.com/paixie/bianmi/index_26_2.html
#getpages限制取几页
class Getlist(object):
    #zurl查询网址ttp://www.0731gch.com/paixie/bianmi/index_26_
    #scatid保存到的栏目id
    #getpages要采集的页数
    #page分页码
    def __init__(self, url , scatid ,getpages , page=1):
        self.url=url
        # self.url = zurl+"%d.html" % (page)
        # self.catid = zurl.split('_')[1]
        self.page = page
        self._dom = None
        self.getpages=getpages
        self.scatid=scatid

    @property
    def dom(self):
        if not self._dom:
            document = requests.get(self.url)
            document.encoding = 'utf-8'
            self._dom = Pq(document.text)
            self._dom.make_links_absolute(base_url="http://m.ciaifuke.com/") # 相对链接变成绝对链接 爽
        return self._dom


    @property
    def urls(self):
        return [url.attr('href') for url in self.dom('.kk a').items()]

    @property
    def has_next_page(self): # 看看还有没有下一页，这个有必要
        return bool(self.dom('.fy ul .nextPage')) # 看看有木有下一页

    def next_page(self): # 把这个蜘蛛杀了， 产生一个新的蜘蛛 抓取下一页。 由于这个本来就是个动词，所以就不加@property了
        if self.has_next_page :
            self.__init__(zurl=self.url,scatid=self.scatid,getpages=self.getpages,page=self.page+1)
        else:
            return None

    def crawl(self): # 采集当前分页
        # sf_ids = [url for url in self.urls]
        con=len(self.urls)
        print('此页共要采集%s篇文章' %con)
        i=1
        for url in self.urls:
            print('此页第%d篇文章采集中' %i)
            Getshow(url).mysave(self.scatid)
            i+=1
            time.sleep(1)

    def crawl_all_pages(self):
        while True:
            print(u'正在抓取栏目页:%s%d.html, 分页:%d ,共需抓 %d 页' % (self.url,self.page, self.page, self.getpages))
            self.crawl()
            if int(self.page) >= int(self.getpages)  :
            # if int(self.page) >= int(self.getpages) or not self.has_next_page :
            # if not self.has_next_page :
                print('停止')
                break
            else:
                # self.next_page()
                pass

# 测试

# s = Getshow('http://m.ciaifuke.com/web/fkjb/fkyz/ydy/1132.html')
# print(s.title)
# print(s.content)
# s.mysave()
# str='http://www.0731gch.com/paixie/bianmi/index_26_'
# print(str.split('_')[1])
# s=Getlist('http://www.0731gch.com/paixie/bianmi/index_26_',2)
# for url in s.urls:
#      show =Getshow(url)
#      print(show.title+':'+url)
#女性体检
s=Getlist('http://m.ciaifuke.com/web/jktj/nxtja/',699,1,1)
s.crawl_all_pages()
#男性体检
s=Getlist('http://m.ciaifuke.com/web/jktj/nxtj/',698,1,1)
s.crawl_all_pages()
#腋臭
s=Getlist('http://m.ciaifuke.com/web/yc/',700,1,1)
s.crawl_all_pages()

#痔疮
s=Getlist('http://m.ciaifuke.com/web/gcjb/zc/',701,1,1)
s.crawl_all_pages()


# #前列腺炎
# s=Getlist('http://m.ciaifuke.com/web/mnsz/qlx/qlxy/',597,1,1)
# s.crawl_all_pages()
# #前列腺增生
# s=Getlist('http://m.ciaifuke.com/web/mnsz/qlx/qlxzs/',596,1,1)
# s.crawl_all_pages()
# #早泄
# s=Getlist('http://m.ciaifuke.com/web/mnsz/xgnza/zx/',606,1,1)
# s.crawl_all_pages()
# #阳痿
# s=Getlist('http://m.ciaifuke.com/web/mnsz/xgnza/yw/',607,1,1)
# s.crawl_all_pages()
# #不射精
# s=Getlist('http://m.ciaifuke.com/web/mnsz/xgnza/bsj/',605,1,1)
# s.crawl_all_pages()
# #射精无力
# s=Getlist('http://m.ciaifuke.com/web/mnsz/xgnza/sjwl/',603,1,1)
# s.crawl_all_pages()



#
# #女性膀胱炎
# s=Getlist('http://m.ciaifuke.com/web/fkjb/fkyz/nxbgy/',660,1,1)
# s.crawl_all_pages()
# #女性尿道炎
# s=Getlist('http://m.ciaifuke.com/web/fkjb/fkyz/nxndy/',710,1,1)
# s.crawl_all_pages()
# #外阴炎
# s=Getlist('http://m.ciaifuke.com/web/fkjb/fkyz/wyy/',656,1,1)
# s.crawl_all_pages()
# #附件炎
# s=Getlist('http://m.ciaifuke.com/web/fkjb/fkyz/fjy/',659,1,1)
# s.crawl_all_pages()
# #宫颈炎
# s=Getlist('http://m.ciaifuke.com/web/fkjb/fkyz/gjy/',657,1,1)
# s.crawl_all_pages()
#
# #月经不调
# s=Getlist('http://m.ciaifuke.com/web/fkjb/cjbz/yjbd/',676,1,1)
# s.crawl_all_pages()
#
# #白带异常
# s=Getlist('http://m.ciaifuke.com/web/fkjb/cjbz/bdyc/',677,1,1)
# s.crawl_all_pages()
#
#
# #阴道流血
# s=Getlist('http://m.ciaifuke.com/web/fkjb/cjbz/ydlx/',679,1,1)
# s.crawl_all_pages()
#
# #外阴瘙痒
# s=Getlist('http://m.ciaifuke.com/web/fkjb/cjbz/wysy/',680,1,1)
# s.crawl_all_pages()
#
# #下腹疼痛
# s=Getlist('http://m.ciaifuke.com/web/fkjb/cjbz/xftt/',681,1,1)
# s.crawl_all_pages()
# #尿路感染
# s=Getlist('http://m.ciaifuke.com/web/fkjb/cjbz/nlgr/',702,1,1)
# s.crawl_all_pages()
# #宫颈糜烂
# s=Getlist('http://m.ciaifuke.com/web/fkjb/zgjb/gjml/',669,1,1)
# s.crawl_all_pages()
# #子宫肌瘤
# s=Getlist('http://m.ciaifuke.com/web/fkjb/fkzl/zgjl/',672,1,1)
# s.crawl_all_pages()
# #卵巢囊肿
# s=Getlist('http://m.ciaifuke.com/web/fkjb/fkzl/lcnz/',673,1,1)
# s.crawl_all_pages()
# #宫颈囊肿
# s=Getlist('http://m.ciaifuke.com/web/fkjb/fkzl/gjnz/',670,1,1)
# s.crawl_all_pages()
# #处女膜修复
# s=Getlist('http://m.ciaifuke.com/web/fkjb/smzx/cnmxf/',684,1,1)
# s.crawl_all_pages()
#
# #阴道紧缩
# s=Getlist('http://m.ciaifuke.com/web/fkjb/smzx/ydjss/',685,1,1)
# s.crawl_all_pages()
#
# #阴道炎
# s=Getlist('http://m.ciaifuke.com/web/fkjb/fkyz/ydy/',654,1,1)
# s.crawl_all_pages()
# #盆腔炎
# s=Getlist('http://m.ciaifuke.com/web/fkjb/fkyz/pqy/',655,1,1)
# s.crawl_all_pages()
