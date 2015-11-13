#
#  Copyright 2015, Jack Poulson
#  All rights reserved.
#
#  This file is part of Pumps, which was produced as part of the DARPA XDATA
#  project, and is under the BSD 2-Clause License, which can be found at 
#  http://opensource.org/licenses/BSD-2-Clause
#
import bz2, gzip, os, pandas, time
# import utils

home_dir = os.path.expanduser("~")

def resample_daily(filename,new_filename='',return_df=False,suffix='_daily'):
  """
  Reduce an NxCore CSV file to its back-filled mean daily prices.
  """
  # >>> import pumps
  # >>> pumps.resample_daily('/path/to/file.csv')
  # >>> pumps.resample_daily('/path/to/file.csv.bz2')
  # >>> pumps.resample_daily('/path/to/file.csv.gz')
  # >>> df = pumps.resample_daily('/path/to/file.csv.gz',return_df=True)
  # >>> read_time, resample_time, write_time = pumps.resample_daily('file.csv')

  if filename.endswith('.csv'):
    date_tags = {"DateTime":['Date']}
    kept_cols = ['Date','Close']
  else:
    date_tags = {'DateTime':['System Date','System Time','System Time Zone']}
    kept_cols = ['System Date','System Time','System Time Zone','Trade Price']
  tokens = filename.split('.')
  if len(tokens) < 2:
    print "WARNING: Skipping %s because too few tokens" % filename
    return 0, 0, 0
  if tokens[-1] == 'csv':
    base = tokens[0]
    for j in xrange(1,len(tokens)-1):
      base = base + '.' + tokens[j]
    print "Processing plain CSV:", filename
    print "  reading..."
    start_read_time = time.clock()
    df = pandas.read_csv(filename,parse_dates=date_tags,index_col='DateTime',
      usecols=kept_cols)
    read_time = time.clock() - start_read_time
  elif tokens[-2] == 'csv' and tokens[-1] == 'bz2':
    base = tokens[0]
    for j in xrange(1,len(tokens)-2):
      base = base + '.' + tokens[j]
    print "Processing bzip2 CSV:", filename
    print "  reading..."
    start_read_time = time.clock()
    df = pandas.read_csv(filename,parse_dates=date_tags,compression='bz2',
      index_col='DateTime',usecols=kept_cols)
    read_time = time.clock() - start_read_time
  elif tokens[-2] == 'csv' and tokens[-1] == 'gz':
    base = tokens[0]
    for j in xrange(1,len(tokens)-2):
      base = base + '.' + tokens[j]
    print "Processing gzipped CSV:", filename
    print "  reading..."
    start_read_time = time.clock()
    df = pandas.read_csv(filename,parse_dates=date_tags,compression='gzip',
      index_col='DateTime',usecols=kept_cols)
    read_time = time.clock() - start_read_time
  else:
    print "WARNING: Skipping", filename
    return 0, 0, 0

  print "  resampling..."
  start_resample_time = time.clock()
  df.sort_index(inplace=True)
  new_df = df.resample('D',how='mean',fill_method='bfill')
  resample_time = time.clock() - start_resample_time

  if new_filename == '':
    new_filename = base+suffix+'.csv'
  new_filedir = os.path.dirname(new_filename)
  if new_filedir == '':
    # The path was relative, e.g., 'ePTOO.csv', and should live in '.'
    new_filedir = '.'
  if os.access(new_filedir,os.W_OK|os.X_OK):
    print "  writing..."
    start_write_time = time.clock()
    new_df.to_csv(new_filename)
    write_time = time.clock() - start_write_time
  else:
    print "  did not have write permissions for", new_filedir
    write_time = 0

  if return_df:
    return new_df
  else:
    return read_time, resample_time, write_time

def resample_daily_dir(directory,silent=False):
  """
  Back-fill the NxCore CSV files in a directory with their mean daily prices.
  """
  # >>> import pumps
  # >>> pumps.resample_daily_dir('/home/poulson/trade_data/P/')
  if not os.path.isdir(directory):
    print "ERROR: directory", directory, "does not exist"
    return

  start_time = time.clock()
  filename_list = os.listdir(directory)
  num_files = 0
  for filename in filename_list:
    if os.path.isfile(filename):
      num_files += 1

  total_files = 0
  total_read_time = 0
  total_resample_time = 0
  total_write_time = 0
  for filename in filename_list:
    if not os.path.isfile(filename):
      continue
    if not silent:
      print "Processing file %d/%d" % (total_files,num_files)
    total_files += 1
    read_time, resample_time, write_time = resample_daily(filename)
    total_read_time     += read_time
    total_resample_time += resample_time
    total_write_time    += write_time

  if not silent:
    print ""
    print "Total time:", time.clock()-start_time, "seconds"
    print "  reading:   ", total_read_time,     "seconds"
    print "  resampling:", total_resample_time, "seconds"
    print "  writing:   ", total_write_time,    "seconds"
    print ""

# >>> import pumps
# >>> pumps.find_pumps('ePTOO_daily.csv')
# Candidate pump: (2014-04-12,2014-04-24,2014-05-20)=(0.550000,0.575000,0.887500)
# (('2014-04-12',), ('2014-04-24',), ('2014-05-20',), (0.55000000000000004,), (0.57499999999999996,), (0.88749999999999996,))
#
# >>> pumps.find_pumps('ePTOO_daily.csv',growth_tol=0.25)
#Candidate pump: (2014-02-14,2014-03-04,2014-03-14)=(0.750000,0.754286,1.093333)
#Candidate pump: (2014-04-12,2014-04-24,2014-05-23)=(0.550000,0.575000,0.760000)
#Candidate pump: (2014-05-02,2014-05-12,2014-06-11)=(0.610000,0.610000,0.790000)
#(('2014-02-14', '2014-04-12', '2014-05-02'), ('2014-03-04', '2014-04-24', '2014-05-12'), ('2014-03-14', '2014-05-23', '2014-06-11'), (0.75, 0.55000000000000004, 0.60999999999999999), (0.75428571428571434, 0.57499999999999996, 0.60999999999999999), (1.0933333333333335, 0.76000000000000001, 0.79000000000000004))
#
# >>> pumps.find_pumps('ePTOO_daily.csv',growth_tol=0.25,silent=True)
#(('2014-02-14', '2014-04-12', '2014-05-02'), ('2014-03-04', '2014-04-24', '2014-05-12'), ('2014-03-14', '2014-05-23', '2014-06-11'), (0.75, 0.55000000000000004, 0.60999999999999999), (0.75428571428571434, 0.57499999999999996, 0.60999999999999999), (1.0933333333333335, 0.76000000000000001, 0.79000000000000004))
#
# If the 'verbose=True' argument is added, then the details of each search 
# are summarized.
#
def find_pumps(filename,process=False,resampled_filename='',min_quiet_days=10,quiet_tol=0.05,
  min_growth_days=1,max_growth_days=30,growth_tol=0.5,
  silent=False,verbose=False):

  if process:
    df = resample_daily(filename,resampled_filename,return_df=True)
  else:
    tokens = filename.split('.')
    if len(tokens) < 2:
      print "ERROR: Invalid filename,", filename
      return
    if tokens[-1] == 'csv':
      df = pandas.read_csv(filename,index_col='DateTime')
    elif tokens[-2] == 'csv' and tokens[-1] == 'gz':
      df = pandas.read_csv(filename,index_col='DateTime',compression='gzip')
    elif tokens[-2] == 'csv' and tokens[-1] == 'bz2':
      df = pandas.read_csv(filename,index_col='DateTime',compression='bz2')
    else:
      print "ERROR: Invalid filename,", filename 
      return

  if min_quiet_days < 0:
    print "ERROR: min_quiet_days must be non-negative"
    return
  if quiet_tol <= 0.:
    print "ERROR: quiet_tol must be positive"
  if min_growth_days <= 0:
    print "ERROR: min_growth_days must be positive"
  if max_growth_days < min_growth_days:
    print "ERROR: max_growth_days must be at least as large as min_growth_days"
  if growth_tol <= 0.:
    print "ERROR: growth_tol must be positive"

  # Search for the intervals where the mean price did not deviate by more than 
  # a given percentage, for a given number of days, and then has an overall
  # growth of more than a given percentage for a given number of days.
  #
  # The current search works in a way which might appear to be quadratic 
  # complexity, but should be expected to have near-linear complexity since
  # each search forward from a starting point should ideally be O(1) in length
  # (with the only possible exception being if the stock is essentially only
  # quiet). It should be possible to reduce the complexity in such cases with
  # minor changes.
  # 
  # Also note that the current algorithm can be viewed as being 
  # 'forward greedy', as it will search for the maximum quiet time period, 
  # followed by the maximum allowable pump period, and that it would be possible
  # to formulate a time series which is *almost* detected via the current scheme
  # but would be detected by a scheme which was not greedy with the initial 
  # quiet period (e.g., if there is a slight up-tick in the last quiet day, 
  # it should be easy to construct a case where the subsequent raise in price 
  # is too small to be considered a pump, but it would pass the threshold if the
  # pump was considered to have started the day before the "quiet" up-tick).
  # But since these cases should be borderline, they should not be worth 
  # initially worrying about.
  #
  # It is also possible to debate which data point the deviation should be 
  # formulated relative to when deciding whether a period of (e.g., 10 days)
  # is sufficiently 'quiet'. The current scheme uses the starting price, whereas
  # a slightly better approach might be to use the central price over each 
  # candidate quiet period.
  #
  # TODO: Consider allowing the growth tolerance to be based upon the average 
  #       daily relative growth rather than a simple relative growth bound.
  #
  start_dates = ()
  last_quiet_dates = ()
  end_dates = ()
  start_prices = ()
  last_quiet_prices = ()
  end_prices = ()
  num_days = len(df.ix[:,0])
  start_day = 0
  while start_day+max(1,min_quiet_days) < num_days:
    start_price = df.ix[start_day,0]
    start_date = df.index[start_day]
    if start_price <= 0.:
      print "ERROR: Price on %s was %f" % (start_date,start_price)
      start_day += 1
      continue
    if verbose:
      print "Searching from start_date=%s (start_price=%f)" % \
        (start_date,start_price)

    stayed_quiet = True
    for day in xrange(start_day+1,num_days):
      price = df.ix[day,0]
      if abs(price-start_price)/start_price > quiet_tol:
        stayed_quiet = False
        if verbose:
          print "  quiet threshold exceeded on %s with price=%f" % \
            (df.index[day],price)
        break
    if stayed_quiet or day-start_day < min_quiet_days:
      if verbose:
        print "  insufficient quiet time"
      start_day += 1
      continue

    # Now look for a sufficiently fast rise so that we have a pump candidate
    last_quiet_day = day-1
    last_quiet_date = df.index[last_quiet_day]
    last_quiet_price = df.ix[last_quiet_day,0]
    # This assertion shouldn't be necessary, but just in case...
    if last_quiet_price <= 0.:
      print "ERROR: Price on %s was %f" % (last_quiet_day,last_quiet_price)
      start_day += 1
      continue
    fast_rise = False
    search_start_day = last_quiet_day + min_growth_days
    search_stop_day = min(last_quiet_day+max_growth_days+1,num_days)
    for day in xrange(search_start_day,search_stop_day):
      price = df.ix[day,0]
      if (price-last_quiet_price)/last_quiet_price > growth_tol:
        fast_rise = True
        end_day = day
        end_price = price
        end_date = df.index[end_day]
        if verbose:
          print "  setting end_date=%s and end_price=%f" % (end_date,end_price)
    if fast_rise:
      start_dates      += (start_date,)
      last_quiet_dates += (last_quiet_date,)
      end_dates        += (end_date,)

      start_prices      += (start_price,)
      last_quiet_prices += (last_quiet_price,)
      end_prices        += (end_price,)
      
      # 'quiet' is already in use as another technical term...so use 'silent'
      if not silent:
        print "Candidate pump: (%s,%s,%s)=(%f,%f,%f)" % \
          (start_date, last_quiet_date, end_date,
           start_price,last_quiet_price,end_price)

      # Conservatively advance the starting day of the next search
      start_day = last_quiet_day+1
    else:
      if verbose:
        print "  no sufficiently fast rise detected in time band"
      start_day += 1

  return start_dates,  last_quiet_dates,  end_dates, \
         start_prices, last_quiet_prices, end_prices

# @utils.lru_cache(150)
def find_pumps_easy(symbol,orig_dir='/team6/trade',cache_dir=home_dir+'/.team6/resampled/',suffix='_daily',
  min_quiet_days=10,quiet_tol=0.05,
  min_growth_days=1,max_growth_days=30,growth_tol=0.5,
  silent=False,verbose=False):
  """ 
  A thin wrapper around find_pumps which provides a few conveniences at the 
  expense of requiring more hard-coded information.
  """
  # >>> import pumps 
  # >>> pumps.find_pumps_easy('eIFT',growth_tol=0.1)
  # Will use gzipped CSV /team6/trade/eIFT.csv.gz
  # Processing gzipped CSV: /team6/trade/eIFT.csv.gz
  #   reading...
  #   resampling...
  #   did not have write permissions for /team6/trade/eIFT_daily.csv
  # Candidate pump: (2014-02-22 00:00:00,2014-03-13 00:00:00,2014-04-10 00:00:00)=(5.491670,5.673065,6.289004)
  # Candidate pump: (2014-03-14 00:00:00,2014-04-07 00:00:00,2014-05-07 00:00:00)=(5.817291,5.978300,6.786954)
  # ((Timestamp('2014-02-22 00:00:00', offset='D'), Timestamp('2014-03-14 00:00:00', offset='D')), (Timestamp('2014-03-13 00:00:00', offset='D'), Timestamp('2014-04-07 00:00:00', offset='D')), (Timestamp('2014-04-10 00:00:00', offset='D'), Timestamp('2014-05-07 00:00:00', offset='D')), (5.4916701754386024, 5.8172905405405189), (5.6730647911338368, 5.9782997050147282), (6.2890035868006358, 6.7869537671232765))
  #

  # Start by ensuring that, if the default cache_dir was specified, that the
  # necessary folders exist
  if not os.path.exists(home_dir+'/.team6'):
    if not silent:
      print "Creating %s" % (home_dir+'/.team6')
    os.mkdir(home_dir+'/.team6')
  if not os.path.exists(home_dir+'/.team6/resampled'):
    if not silent:
      print "Creating %s" % (home_dir+'/.team6/resampled')
    os.mkdir(home_dir+'/.team6/resampled')

  cached_file = cache_dir+'/'+symbol+suffix+'.csv'
  plain_file = orig_dir+'/'+symbol+'.csv'
  gzip_file = orig_dir+'/'+symbol+'.csv.gz'
  bz2_file = orig_dir+'/'+symbol+'.csv.bz2'
  if os.path.isfile(cached_file):
    if not silent:
      print "Will use cached processed CSV,", cached_file
    candidates = find_pumps(cached_file,False,'',
      min_quiet_days,quiet_tol,
      min_growth_days,max_growth_days,growth_tol,
      silent,verbose)
  elif os.path.isfile(plain_file):
    if not silent:
      print "Will use plain CSV,", plain_file
    candidates = find_pumps(plain_file,True,cached_file,
      min_quiet_days,quiet_tol,
      min_growth_days,max_growth_days,growth_tol,
      silent,verbose)
  elif os.path.isfile(gzip_file):
    if not silent:
      print "Will use gzipped CSV", gzip_file
    candidates = find_pumps(gzip_file,True,cached_file,
      min_quiet_days,quiet_tol,
      min_growth_days,max_growth_days,growth_tol,
      silent,verbose)
  elif os.path.isfile(bz2_file):
    if not silent:
      print "Will use bz2 CSV", bz2_file
    candidates = find_pumps(bz2_file,True,cached_file,
      min_quiet_days,quiet_tol,
      min_growth_days,max_growth_days,growth_tol,
      silent,verbose)
  else:
    print "ERROR: Could not find csv for symbol", symbol
    return
  return candidates

def to_dicts(candidates):
  import utils
  """
  Converts find_pumps results (tuple of 6 tuples) into and array of dicts
  """
  sds,  lqds,  eds, sps, lqps, eps = candidates
  res = [{'start': utils.to_seconds(s),
          'end': utils.to_seconds(e),
          'last_quiet_date': lqd,
          'start_prices': sp,
          'last_quiet_price': lqp,
          'end_price': ep,
          }
         for (s, e, lqd, sp, lqp, ep) in zip(sds, eds, lqds, sps, lqps, eps) if s
  ]
  res = {
    'start': [utils.to_seconds(s) for s in sds],
    'end': [utils.to_seconds(e) for e in eds],
    'last_quiet_date': lqds,
    'start_prices': sps,
    'last_quiet_price': lqps,
    'end_price': eps,
  }
  return res
  # return sorted(res, key=lambda x: x['start'])
