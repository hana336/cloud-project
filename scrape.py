import os
import requests
import time
import urllib3
import socket
from bs4 import BeautifulSoup
from urllib.parse import urljoin

#تعطيل تحذيرات SSL لاغراض التطوير بس 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_files():
    try:
        DOWNLOAD_FOLDER = "data/raw"
        BASE_URL = "https://www.gutenberg.org"
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive'
        }
        

    

    
    
        # اختبار الاتصال بالاول  
        print("Testing connection to project Gutenberg... ")

        try:
            test_response = requests.get(f"{BASE_URL}/robots.txt", headers=headers, timeout=10, verify=False)
            test_response.raise_for_status()
            print("Connection test passed!")
        except Exception as e:
            print(f"Connection test Failed: {str(e)}")
            print("Trying alternative approach...")
            BASE_URL = "https://gutenberg.pglaf.org"
            test_response = requests.get(f"{BASE_URL}/robots.txt", headers=headers, timeout=10, verify=False)
            test_response.raise_for_status()

        
        #   البحث عن كتب
        print("\nSearching for books...")
        search_url = f"{BASE_URL}/ebooks/search/?query=technology&sort_order=downloads"

        with requests.Session() as session:
            session.headers.update(headers)
            session.verify = False

            #نجيب صفحة البحث 
            try:
                response = session.get(search_url, timeout=15)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch search page: {str(e)}")
                return False
            
            soup = BeautifulSoup(response.text, "html.parser") #هان بنصحح الخطأ الاملائي 

        # جمع روابط الكتب 
        book_links = []
        for link in soup.select('li.booklink a[href^="/ebooks/"]'):
            book_id = link['href'].split('/')[-1]
            if book_id.isdigit():
                full_url = urljoin(BASE_URL, f"/ebooks/{book_id}")
                book_links.append(full_url)

        if not book_links:
            print("No books found in search ersults")
            return False

        print(f"Found {len(book_links)} books")        

        # نحدد عدد الكتب لعدم اثقال الخادم
        success_count = 0
        for book_url in book_links[2]: #2 للتجربة
            try:
                print(f"\nProcessing book: {book_url}")

                #جلب صفحة الكتاب 
                book_response = session.get(book_url, timeout=15)
                book_response.raise_for_status()
                book_soup = BeautifulSoup(book_response.text, "html.parser")

                #للبحث عن روابط تنزيل بطريقة تانية
                pdf_links = []
                for link in book_soup.find_all('a', href = True):
                    href = link['href']
                    if 'pdf' in href and (href.endswith('pdf') or 'format=pdf' in href):
                        pdf_links.append(urljoin(BASE_URL, link['href']))

                if not pdf_links:
                    print("No PDF download links found for this book")
                    continue

                pdf_url = pdf_links[0]
                filename = f"book_{book_url.split('/')[-1]}.pdf" #اسم ملف امن
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)

                #تجنب التنزيل المكرر
                if os.path.exists(filepath):
                    print(f"File already exists:{filename}")
                    success_count +=1
                    continue

            
                #تنزيل الملف
                print(f"Downloading {filename}...")
                try:
                    file_response = session.get(pdf_url, stream=True, timeout=20)
                    file_response.raise_for_status()

                    with open(filepath, "wb") as f:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    print(f"Successfully downloaded: {filename}")
                    success_count +=1

                    #تاخير بين التنزيلات 
                    time.sleep(5)
            
                except Exception as e:
                    print(f"Download failes{str(e)}")
                    continue

            except Exception as e:
                print(f"Book proccessing failed: {str(e)}")
                continue

        #النتائج
        print("\n"+ '='*50)
        if success_count > 0:
            print(f"Successfully downloaded {success_count} file(s)")
            return True
        else:
            print("No files were downloaded")
            return False

    except Exception as e:
        print(f"Error in scrapping:{e}")
        return False                            
 
if __name__ == "__main__":
  scrape_files()