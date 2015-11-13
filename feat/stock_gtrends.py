import requests
import json

stocks = [
'ABHI', 'AEGY', 'AGIN', 'AHII', 'AJGH', 'AMBS', 'AMMX', 'AMPG', 'AMZZ', 'ANDI',
'ANSU', 'APRE', 'AQUM', 'ASCC', 'ASKH', 'AVEW', 'AXCG', 'AXLX', 'AXXE', 'AZFL',
'BANJ', 'BAYP', 'BBDA', 'BCHS', 'BETS', 'BICX', 'BIGG', 'BLTA', 'BLUU', 'BMSN',
'BMTL', 'BNXR', 'BONI', 'BONU', 'BRIZF', 'BRWC', 'BVII', 'BWVI', 'BYRG', 'BYSD',
'CADY', 'CANA', 'CBAK', 'CBGI', 'CBYI', 'CDII', 'CEHC', 'CGCC', 'CGRA', 'CHICF',
'CHLO', 'CNTO', 'COHO', 'COLTF', 'CPRX', 'CTLE', 'CVAT', 'CWNM', 'CYBK', 'CYDI',
'DARA', 'DBMM', 'DCLT', 'DEQI', 'DEWM', 'DGRI', 'DKAM', 'DMHI', 'DNAD', 'DOMK',
'DPSM', 'DRAG', 'DRGV', 'DRMC', 'DSCR', 'EAPH', 'ECDP', 'EDWY', 'EDXC', 'EHOS',
'EKNL', 'ELRA', 'EMBR', 'ENDO', 'ENRT', 'EPAZ', 'EPGG', 'ERBB', 'ERFB', 'ETAK',
'ETEK', 'FBCD', 'FCCN', 'FDFT', 'FDMF', 'FFFC', 'FITX', 'FLPC', 'FLST', 'FNRC',
'FRCN', 'FRMC', 'FRTD', 'GACR', 'GASE', 'GAWK', 'GBEN', 'GEFI', 'GFOX', 'GKIN',
'GLCO', 'GLDG', 'GLDN', 'GLER', 'GMUI', 'GNCC', 'GNCP', 'GOHE', 'GPLH', 'GRAS',
'GRDH', 'GRNE', 'GRNH', 'GRPR', 'GYST', 'HCTI', 'HEMP', 'HFCO', 'HIMR', 'HNIN',
'HPJ', 'HPNN', 'HPTG', 'HRAL', 'HYII', 'IBRC', 'ICBU', 'IDOI', 'IGPK', 'IHSI',
'ILIV', 'IMDC', 'IMTC', 'INNO', 'INOH', 'INOL', 'INVA', 'IOGA', 'ISCO', 'ISR',
'ITNS', 'IWEB', 'KALO', 'KBLB', 'KGET', 'KRED', 'LATF', 'LIBE', 'LIGA', 'LIVE',
'LJPC', 'LKEN', 'LRDR', 'LTNC', 'LVGI', 'LVVV', 'LXRP', 'MCGI', 'MCII', 'MDCE',
'MDDD', 'MDIN', 'MDNT', 'MEDA', 'MEDT', 'MFTH', 'MINE', 'MMRF', 'MNGA', 'MONK',
'MSPC', 'MVRM', 'MWWC', 'MYEC', 'MYRY', 'NBRI', 'NDEV', 'NGHT', 'NGMC', 'NHPI',
'NNAN', 'NNRX', 'NNVC', 'NOHO', 'NPWZ', 'NTEK', 'NXHD', 'OCFN', 'OCTX', 'OGNG',
'OMVS', 'OPXS', 'ORGC', 'OSLH', 'PBHG', 'PEII', 'PESI', 'PGCX', 'PGLO', 'PGSY',
'PHOT', 'PIEX', 'PIHN', 'PLPL', 'PLUG', 'PMXO', 'POIL', 'PPJE', 'PROP', 'PSID',
'PTAH', 'PTGEF', 'PTOG', 'PTOO', 'PUGE', 'PWDY', 'PZOO', 'QASP', 'QFOR', 'QLTS',
'QUNI', 'RBIZ', 'REFG', 'REVI', 'RHCO', 'RIHT', 'RITE', 'ROSV', 'SAFS', 'SAMP',
'SANB', 'SANP', 'SAPX', 'SBFM', 'SCFR', 'SCRC', 'SDON', 'SEEK', 'SEGI', 'SFPI',
'SGDH', 'SGOC', 'SHMN', 'SIMH', 'SING', 'SIPC', 'SITO', 'SITS', 'SKTO', 'SLGI',
'SMVR', 'SNET', 'SOF', 'SOUL', 'SPCL', 'SPMI', 'SREH', 'STBV', 'SUBB', 'SWET',
'SWRF', 'TALK', 'TAUG', 'TCEL', 'TDEY', 'TGGI', 'TLNUF', 'TLTFF', 'TNKE', 'TPAC',
'TPNI', 'TQLA', 'TRII', 'TRLR', 'TRTB', 'TRTC', 'TTEG', 'TUNG', 'TWSI', 'TXGE',
'TXTM', 'TXTMD', 'UBQU', 'UMEWF', 'UNLA', 'URHN', 'USEI', 'USNU', 'USTC', 'USTU',
'UTRM', 'VIDG', 'VMGI', 'VTIFF', 'VTMB', 'VTPI', 'WAFR', 'WBSI', 'WBXU', 'WILD',
'WNTR', 'WPWR', 'WSHE', 'WTCG', 'WTER', 'WWPW', 'XCHO', 'XDSL', 'XNRG', 'XSNX', 'XTRM'
]

monthly_data = []
weekly_data = []
no_data = []
try_again = []

weekly_stock_trends = [['symbol']]
monthly_stock_trends = [['symbol']]

weekly_table_columned = False
monthly_table_columned = False

def scrub_data(text, delimiter):
    data = text.split(delimiter)[1].split('Top')[0]
    return [x for x in data.split('\n') if x != '']

def list_data(stock_trends, data, columned):
    stock_trends.append([data.pop(0)])
    for datum in data:
        if not columned:
            stock_trends[0].append(datum.split(',')[0])
        try:
            stock_trends[-1].append(datum.split(',')[1])
        except:
            print('')
            print('error in datum parsing')
            print(datum)
            print('')

def write_to_csv(listed_stock_trends, csv_file):
    with open(csv_file, 'w') as textfile:
        for trend in listed_stock_trends:
            textfile.write(','.join(trend))
            textfile.write('\n')

def fetch_stock_data(stocks):
    global weekly_table_columned
    global weekly_stock_trends
    global weekly_data
    global monthly_table_columned
    global monthly_stock_trends
    global monthly_data
    global no_data
    global try_again
    for stock in stocks:
        url = 'https://www.google.com/trends/trendsReport?hl=en-US&q=' + stock + '&date=1%2F2010%2067m&cmpt=q&tz=Etc%2FGMT-2&tz=Etc%2FGMT-2&content=1&export=1'
        headers = {
            'dnt': '1',
            'accept-encoding': 'gzip, deflate, sdch',
            'accept-language': 'en-US,en;q=0.8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.124 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'authority': 'www.google.com',
            'cookie': 'I4SUserLocale=en_US; HSID=A8lwdnbNtuPdzSb1h; SSID=AGRPc77IGg1OIIkN5; APISID=mmYSBG_SBvmRtPg7/APsrEzZqNxFBE4yjI; SAPISID=YKR8oFjIBYh0FsOc/ApaWaF9keAEps068t; GoogleAccountsLocale_session=en; SID=DQAAABsBAACvbfUUsTZ2DFgQvgUFcyN71NC93s8K4Ts4594XnaqGEwFcYlf75sBYz9db9vdMfglLvzOCcLq17M_aBAqv4_tnhittCWaLguyKqFSZyISswNkoC-WZJJtzBJKWbeHj7UmAc-z-6iSIoUXwB5jEso7e_MRyI1Sah_jvbuTAPcVTSLsW5XrYyXO0Ae4piNpvCumHS5FXqU0yzmRRnytOOCXa3mWUir1fAUss_nuT04nrBpPbf8sUn74SxsPHXyWfXYki6_0nE3isHHWlHqxG0_7P_5OrTq7kbXGMjTfSU-EQEofUUNW_SWzMOh8JULsAo1I2zcTDsSfEbrxkEF14kTg6q5oqQmXrOX7CwG9IszFJxs9yTJPguDUlJM_bK7gg9CI; NID=68=mIQQQv4BAVb9PxPyjWwLYt3HWb6Q8f7qzcEyc2l1B0SNQD2BWCxCptzmtWH0yV6bkvcQ1TlBzn1HZOb4tgm-j-dZBER4w77Tp7B0QtoWoXyC1kA7fVU5QcUkgzdJ62z7lMpWLqoWtwSvpTg2JZnXlKlph-oimSStSYgHmJQ3sTG94S2p8UYz9mLWqKbs2ovuQQPgMReLFm9BFwLox_33J8WsPK15PKLskj0kbzoSJg; PREF=ID=1111111111111111:U=8be405d2262cc3b4:FF=0:LD=en:TM=1433781247:LM=1434571620:GM=1:S=Q2sHjUohO2Cz53aq; S=quotestreamer=Z_okAI7hcxJxhh1giFUT3A:izeitgeist-ad-metrics=8-dHGkd8mKU',
            'x-client-data': 'CI+2yQEIo7bJAQiptskBCMS2yQEI6ojKAQi1lcoB'
        }

        r = requests.get(url, headers=headers)

        if 'Week,' in r.text:
            data = scrub_data(r.text, 'Week,')
            list_data(weekly_stock_trends, data, weekly_table_columned)
            weekly_table_columned = True
            weekly_data.append(stock)
            while stock in try_again: try_again.remove(stock)
            print(stock + ' has weekly data')
        elif 'Month,' in r.text:
            data = scrub_data(r.text, 'Month,')
            list_data(monthly_stock_trends, data, monthly_table_columned)
            monthly_table_columned = True
            monthly_data.append(stock)
            while stock in try_again: try_again.remove(stock)
            print(stock + ' has monthly data')
        elif 'You have reached your quota limit' in r.text or 'may be sending automated queries' in r.text:
            try_again.append(stock)
            print(stock + ' will try again due to quota limit')
        else:
            print(r.text)
            no_data.append(stock)
            while stock in try_again: try_again.remove(stock)
            print(stock + ' has no data')

def try_stocks_again():
    global try_again
    if len(try_again) > 0:
        print('')
        print('Try Agains:')
        print(try_again)
        print('')
        fetch_stock_data(try_again)
        try_stocks_again()

fetch_stock_data(stocks)
try_stocks_again()

write_to_csv(weekly_stock_trends, 'weekly_stock_trends.csv')
write_to_csv(monthly_stock_trends, 'monthly_stock_trends.csv')

print('Had Monthly Data:')
print(monthly_data)
print('')
print('Had Weekly Data:')
print(weekly_data)
print('')
print('Had No Data:')
print(no_data)
print('')
print('Try Agains (hopefully none)')
print(try_again)