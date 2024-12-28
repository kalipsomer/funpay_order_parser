import asyncio
import aiohttp
import aiofiles
import colorama
import random
import time
from bs4 import BeautifulSoup
from colorama import Fore
from aiohttp_socks import ProxyConnector

colorama.init(autoreset=True)

BASE_URL = "https://funpay.com/lots/offer?id="

async def fetch_proxies():
    """Ну пиздец, прокси дергаем из файла, а хули делать."""
    try:
        async with aiofiles.open("proxy.txt", "r") as f:
            raw_proxies = await f.readlines()
        return [p.strip() for p in raw_proxies if p.strip()]  # Надо эту хуйню почистить
    except FileNotFoundError:
        print(f"{Fore.YELLOW}Э, бля, а где файлик 'proxy.txt'? Проебали?{Fore.RESET}")
        return []

async def load_processed_ids():
    """Смотрим, какие ID мы уже оттрахали, чтобы по второму кругу не идти, нахуй."""
    try:
        async with aiofiles.open("data.txt", "r", encoding="utf-8") as f:
            lines = await f.readlines()
        # Вытаскиваем эти ебучие ID
        return {line.split("id=")[1].split()[0] for line in lines if "id=" in line}
    except FileNotFoundError:
        return set()  # Да и хуй с ним, если файла нет

async def extract_offer_details(page_content, page_url):
    """Ковыряемся в этом HTML дерьме, чтобы вытащить описание оффера."""
    soup = BeautifulSoup(page_content, "html.parser")
    param_items = soup.find_all("div", class_="param-item")
    description = None
    for item in param_items:
        header = item.find("h5")
        if header and "Краткое описание" in header.text:
            info_div = item.find("div")
            if info_div:
                description = info_div.text.strip()
                break
    return f"{page_url} - {description}" if description else f"{page_url} - Описания, блядь, нет"

async def scrape_data(session, offer_id, proxy_list, processed_ids):
    """Пытаемся спиздить данные, используя прокси как ебучий ниндзя."""
    target_url = BASE_URL + str(offer_id)
    if str(offer_id) in processed_ids:
        print(f"{Fore.CYAN}[~] ID {offer_id}? Да мы эту хуйню уже сделали, пошли дальше...{Fore.RESET}")
        return

    while True:
        selected_proxy = random.choice(proxy_list)
        connector = ProxyConnector.from_url(f"socks4://{selected_proxy}")
        async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=3)) as temp_session:
            try:
                async with temp_session.get(target_url) as response:
                    if response.status == 200:
                        page_text = await response.text()
                        offer_info = await extract_offer_details(page_text, target_url)
                        async with aiofiles.open("data.txt", "a", encoding="utf-8") as output_file:
                            await output_file.write(offer_info + "\n")
                        print(f"{Fore.GREEN}[+] Заебись! {offer_info}{Fore.RESET}")
                        return  # Получилось, нахуй, можно выходить
                    elif response.status == 404:
                        print(f"{Fore.RED}[-] Не найдено: {target_url}{Fore.RESET}")
                        return  # Ну и хуй с ним, не судьба
                    else:
                        print(f"{Fore.RED}[-] Ошибка с {target_url}, статус: {response.status}{Fore.RESET}")
                        await asyncio.sleep(1)  # Подождем секунду, авось просрется
            except aiohttp.ClientError as client_err:
                print(f"{Fore.RED}[-] Ошибка клиента с прокси {selected_proxy}: {client_err}{Fore.RESET}")
            except asyncio.TimeoutError:
                print(f"{Fore.RED}[-] Прокси {selected_proxy} сдох, ленивая скотина.{Fore.RESET}")
            except Exception as unexpected_error:
                print(f"{Fore.RED}[-] Какая-то хуйня с прокси {selected_proxy}: {unexpected_error}{Fore.RESET}")
            # Если что-то пошло не так, меняем прокси, ебать его в рот
            print(f"{Fore.YELLOW}[!] Меняем прокси и пробуем еще раз, сука!{Fore.RESET}")

async def main_scraper(num_threads):
    """Главная ебучая функция, запускаем эту карусель дерьма."""
    proxies = await fetch_proxies()
    already_done_ids = await load_processed_ids()
    scraping_tasks = []
    start_range = random.randint(20000000, 40000000)
    end_range = random.randint(20000000, 40000000)
    if start_range > end_range:
        start_range, end_range = end_range, start_range
    print()
    print(f"{Fore.YELLOW}[!] Начинаем дрочить диапазон: {start_range} - {end_range}{Fore.RESET}")
    print(f"{Fore.YELLOW}[!] Запускаем {num_threads} потоков этой хуйни.{Fore.RESET}")
    print(f"{Fore.YELLOW}[!] Проксей нарыли аж {len(proxies)} штук.{Fore.RESET}")
    print(f"{Fore.YELLOW}[!] Уже обработали {len(already_done_ids)} ID, нихуево.{Fore.RESET}")
    print()
    print(f"{Fore.YELLOW}[!] Ну что, погнали, блядь!{Fore.RESET}")
    time.sleep(3)  # Дадим секунду на раздумья, а может и нет
    for offer_id in range(start_range, end_range):
        scraping_tasks.append(scrape_data(None, offer_id, proxies, already_done_ids))
        if len(scraping_tasks) >= num_threads:
            await asyncio.gather(*scraping_tasks)
            scraping_tasks = []
    if scraping_tasks:
        await asyncio.gather(*scraping_tasks)

if __name__ == "__main__":
    threads_count = int(input("Сколько ебаных потоков запускаем? "))
    asyncio.run(main_scraper(threads_count))