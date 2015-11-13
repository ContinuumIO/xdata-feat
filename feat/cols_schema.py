schema = [('System Date', 'yyyy-mm-dd'),
('System Time',  'hh:mm:ss.FFF'),
('System Time Zone', int    ),
('DST Indicator', int   ),
('Number of Days Since 1883-01-01',  int),
('Day of Week',  int),
('Day of Year',  'yyyy-mm-dd'),
('Session Date',  int),
('Session DST Indicator', int),
('Session Number of Days Since 1883-01-01' , int),
('Session Day of Week' , int),
('Session Day of Year',  int),
('Exchange Timestamp',   'hh:mm:ss.FFF'),
('Exchange Timestamp Time Zone',  int),
('Symbol',  str),
('SymbolExtra',  str),
('Listed Exchange Index',  int ),
('Reporting Exchange Index',   int  ),
('Session ID',   int),
('Trade Price Flags',  int ),
('Trade Condition Flag',   int  ),
('Trade Condition Index',   int ),
('Trade Volume Type',    str),
('Trade BATE Code',    int ),
('Trade Size',   int),
('Trade Exchange Sequence', int   ),
('Trade Records Back',   int ),
('Trade Total Volume',   float),
('Trade Tick Volume',    float),
('Trade Price',  float),
('Trade Price (Open)', float  ),
('Trade Price (High)',   float),
('Trade Price (Low)',    float),
('Trade Price (Last)',   float ),
('Trade Tick',   float),
('Trade Price Net Change', int   ),
('Analysis Filter Threshold', int    ),
('Analysis Filtered Bool', int   ),
('Analysis Filter Level', int    ),
('Analysis SigHiLo Type', int    ),
('Analysis SigHiLo Seconds', int     ),
('Quote Match Distance (RGN)', int   ),
('Quote Match Distance (BBO)', int   ),
('Quote Match Flags (BBO)', int  ),
('Quote Match Flag (RGN)', int   ),
('Quote Match Type (BBO)', int   ),
('Quote Match Type (RGN)', int   ),]

numeric_columns = [s for idx,s in enumerate(schema) if s[1] == float]
