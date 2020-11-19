## About Crawler_kol

### Tech Stack

* backEnd
    * python3
* other tool
    * Selenium
 
 ### 基本說明
 
 * 使用Selenium 抓取SPA類型網站資料
 * 抓取第三方平台,KOL資料
 * 轉存json格式檔案, 提供其他網站做圖像視覺呈現與分析 
 * 使用 多線程 , 可選擇決定要開啟多少worker , 加快抓取速度
 
 ### 程式執行流程
 
 * 1. getKolMainPageUrl.py , 抓取網站上所有kol main Page Url, 存成檔案放置storage
 * 2. trimKolDRowFile.py , 將rowFiel 依各別kol與擁有的social media, 彙整資訊整合一個檔案
 * 3. getKolDetail.py , 依照檔案開始逐項抓取
 
 ## show case
 
 getKolMainPageUrl.py
 ![image](https://raw.githubusercontent.com/shaunlin064/crawler_kol/main/resource/img/demo.gif 'review')

