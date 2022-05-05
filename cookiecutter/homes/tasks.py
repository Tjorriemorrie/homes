import logging
import re
from datetime import timedelta

import requests
from bs4 import BeautifulSoup
from django.db.models import Count
from django.utils.timezone import now

from config import celery_app
from homes.constants import TOP_PRICE
from homes.models import Home, Match

logger = logging.getLogger(__name__)


BEDROOMS = 0
BATHROOMS = 0
GARAGES = 0
HOST = 'https://www.privateproperty.co.za'
URLS = [
    # houses
    f'/for-sale/north-west/north-west/bloemhof/494?tp={TOP_PRICE}&page=',
    f'/for-sale/eastern-cape/eastern-cape-interior/oviston/10005445?tp={TOP_PRICE}&page=',

    # gauteng (west)
    f'/farms-for-sale/gauteng/west-rand/far-west-merafong/842?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/gauteng/west-rand/randfontein/841?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/gauteng/west-rand/krugersdorp/840?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/gauteng/west-rand/roodepoort/37?tp={TOP_PRICE}&page=',

    # noordwes
    # f'/farms-for-sale/north-west/brits/904?tp={TOP_PRICE}&page=',  # brits
    f'/farms-for-sale/north-west/hartbeespoort-dam/74?tp={TOP_PRICE}&page=',  # harties
    f'/farms-for-sale/north-west/klerksdorp/1411?tp={TOP_PRICE}&page=',  # klerksdorp
    f'/farms-for-sale/north-west/north-west/73?tp={TOP_PRICE}&page=',  # noordwes
    f'/farms-for-sale/north-west/potchefstroom/1409?tp={TOP_PRICE}&page=',  # potchefstroom
    # f'/farms-for-sale/north-west/rustenburg/903?tp={TOP_PRICE}&page=',  # rustenburg
    f'/farms-for-sale/north-west/vryburg-and-surrounds/1410?tp={TOP_PRICE}&page=',  # vryburg
    f'/for-sale/north-west/north-west/bloemhof/494',

    # limpopo
    # f'/farms-for-sale/limpopo/bela-bela-and-bushveld/mookgophong-naboomspruit/2710?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/limpopo/bela-bela-and-bushveld/leeupoort/2707?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/limpopo/bela-bela-and-bushveld/bela-bela/1217?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/limpopo/bela-bela-and-bushveld/modimolle-nylstroom/2708?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/limpopo/bela-bela-and-bushveld/rooiberg/2712?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/limpopo/bela-bela-and-bushveld/vaalwater/2714?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/limpopo/tzaneen-and-surrounds/1248?tp={TOP_PRICE}&page=',

    # free state (northern)
    f'/farms-for-sale/free-state/northern-free-state/parys-and-vaal-river/2348?tp={TOP_PRICE}&page=',

    # free state (eastern)
    f'/farms-for-sale/free-state/eastern-free-state/frankfort/2873?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/free-state/eastern-free-state/harrismith/2874?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/free-state/eastern-free-state/memel/2878?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/free-state/eastern-free-state/senekal/2881?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/free-state/eastern-free-state/villiers/2883?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/free-state/eastern-free-state/vrede/2884?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/free-state/eastern-free-state/warden/2885?tp={TOP_PRICE}&page=',

    # free state (welkom and surrounds)
    f'/farms-for-sale/free-state/welkom-and-goldfields/bothaville/2601?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/free-state/welkom-and-goldfields/bultfontein/2602?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/free-state/welkom-and-goldfields/hoopstad/2604?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/free-state/welkom-and-goldfields/wesselsbron/2609?tp={TOP_PRICE}&page=',

    # natal midlands
    # f'/farms-for-sale/kwazulu-natal/kzn-midlands/greytown/2537?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/kwazulu-natal/kzn-midlands/hilton/2538?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/kwazulu-natal/kzn-midlands/howick/2331?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/kwazulu-natal/kzn-midlands/midlands-meander/11?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/kwazulu-natal/kzn-midlands/mooi-river/2539?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/kwazulu-natal/kzn-midlands/wartburg/2540?tp={TOP_PRICE}&page=',

    # natal (drakensberg)
    # f'/farms-for-sale/kwazulu-natal/drakensberg/underberg-and-surrounds/2532?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/kwazulu-natal/drakensberg/northern-drakensberg/2531?tp={TOP_PRICE}&page=',

    # natal (northern)
    f'/farms-for-sale/kwazulu-natal/northern-kzn/dannhauser/2525?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/kwazulu-natal/northern-kzn/dundee/2526?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/kwazulu-natal/northern-kzn/ladysmith-and-surrounds/648?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/kwazulu-natal/northern-kzn/newcastle/2045?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/kwazulu-natal/northern-kzn/paulpietersburg/2527?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/kwazulu-natal/northern-kzn/vryheid/2528?tp={TOP_PRICE}&page=',

    # western cape (garden route)
    # f'/farms-for-sale/western-cape/garden-route/albertinia/3060?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/western-cape/garden-route/calitzdorp/3061?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/western-cape/garden-route/de-rust/3062?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/george/921?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/great-brak-river-to-glentana/2390?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/western-cape/garden-route/heidelberg/3063?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/jongensfontein/2715?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/klein-brak-and-tergniet/2772?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/knysna/923?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/western-cape/garden-route/ladismith/3064?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/mossel-bay/924?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/western-cape/garden-route/oudtshoorn/922?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/plettenberg-bay/925?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/western-cape/garden-route/riversdale/3065?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/sedgefield/1977?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/stilbaai/926?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/western-cape/garden-route/uniondale/3066?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/western-cape/garden-route/vanwyksdorp/3067?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/vlees-bay-to-gouritz/2716?tp={TOP_PRICE}&page=',
    # f'/farms-for-sale/western-cape/garden-route/wilderness/2349?tp={TOP_PRICE}&page=',

    # northern cape (green kalahari)
    f'/farms-for-sale/northern-cape/kalahari-and-green-kalahari/kakamas/2792?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/kalahari-and-green-kalahari/kathu/2191?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/kalahari-and-green-kalahari/keimoes/2793?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/kalahari-and-green-kalahari/kenhardt/2795?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/kalahari-and-green-kalahari/kuruman/2796?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/kalahari-and-green-kalahari/olifantshoek/2797?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/kalahari-and-green-kalahari/postmasburg/2794?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/kalahari-and-green-kalahari/upington/2192?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/karoo/62?tp={TOP_PRICE}&page=',

    # northern cape (kimberley and diamond fields)
    f'/farms-for-sale/northern-cape/kimberley-and-diamond-fields/barkly-west/2799?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/kimberley-and-diamond-fields/hartswater/2800?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/kimberley-and-diamond-fields/jan-kempdorp/2801?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/kimberley-and-diamond-fields/kimberley/2193?tp={TOP_PRICE}&page=',

    # northern cape (namakwa)
    f'/farms-for-sale/northern-cape/namakwa/brandvlei/2828?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/calvinia/2829?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/fraserburg/2830?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/garies/2831?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/hondeklip-bay/2832?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/kleinsee/2833?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/loeriesfontein/2834?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/nieuwoudtville/2835?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/port-nolloth/2836?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/springbok/2190?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/sutherland/2837?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/vioolsdrift/2838?tp={TOP_PRICE}&page=',
    f'/farms-for-sale/northern-cape/namakwa/williston/2839?tp={TOP_PRICE}&page=',
]


@celery_app.task()
def scrape_task():
    for url in URLS:
        scrape_page.delay(url, 1)


@celery_app.task()
def scrape_page(url: str, page: int):
    logger.info(f'Scraping {url}{page}')
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    res = requests.get(f'{HOST}{url}{page}', headers=headers)
    res.raise_for_status()

    html = BeautifulSoup(res.content, 'html.parser')
    if 'There were no listings' in html.text:
        return

    listings = html.find_all('a', class_='listingResult')
    # parser = parser_()
    for listing in listings:
        # url
        href = listing.get('href')

        # add image
        img_tag = listing.find_all('img')[0]
        img = img_tag.get('data-src')

        # title
        try:
            title = listing.find('div', class_='title').text
            title_bits = title.split()
            size = float(title_bits.pop(0))
            mul = title_bits.pop(0)
            if mul == 'ha':
                size *= 10000
            category = Home.CATEGORY_FARM
            area = title_bits[2:]
        except ValueError:
            size = 1000
            category = Home.CATEGORY_FARM
            area = ''

        # fix size
        if size < 100:
            size *= 10_000
        # if size > 10_000 * 80:
        #     size /= 10_000

        # address
        try:
            address = listing.find('div', class_='address').text.title()
        except AttributeError:
            address = ''

        # price
        price_text = listing.find('div', class_='priceDescription').text
        if price_text in ['Sold', 'Price on Application']:
            continue
        if price_text in ['On Auction', 'Bank Negotiable']:
            price = 999_999
        else:
            try:
                price = re.findall(r'(\d+)', price_text.replace(' ', ''))[0]
            except (IndexError, AttributeError):
                raise Exception(f'Price? {price_text}')

        try:
            bedrooms = listing.find('div', class_='bedroom').previous_sibling.previous_sibling.text
        except AttributeError:
            bedrooms = 0
        try:
            bathrooms = listing.find('div', class_='bathroom').previous_sibling.previous_sibling.text
        except AttributeError:
            bathrooms = 0
        try:
            cars = listing.find('div', class_='garage').previous_sibling.previous_sibling.text
        except AttributeError:
            cars = 0

        home, created = Home.objects.update_or_create(
            url=href,
            defaults={
                'size': size,
                'category': category,
                'area': ' '.join(area),
                'address': address,
                'price': price,
                'bedrooms': float(bedrooms),
                'bathrooms': float(bathrooms),
                'cars': float(cars),
                'img': img,
            }
        )
        # logger.info(f'Saved {home}')

    scrape_page.delay(url, page + 1)


@celery_app.task()
def time_since_updated():
    day_ago = now() - timedelta(hours=24*2)
    Home.objects.filter(
        id__in=list(
            Home.objects.filter(updated_at__lte=day_ago).values_list('pk', flat=True)[:10]
        )
    ).delete()


@celery_app.task()
def drop_matches():
    matches_count = Match.objects.count() // 100
    logger.info(f'Deleting {matches_count} matches as 1%')
    if matches_count:
        matches = Match.objects.order_by('created_at').all()[:matches_count]
        for match in matches:
            match.delete()

    # homes = Home.objects.annotate(match_count=Count('match')).filter(
    #     match_count__lte=0
    # ).filter(
    #     hidden=True
    # ).all()
    # logger.info(f'Found {len(homes)} homes without matches')

